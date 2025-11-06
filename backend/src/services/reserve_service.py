"""
Reserve service for managing lending pool operations.
"""

import time
from typing import Optional

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.reserve_state import ReserveState
from ..models.supply_position import SupplyPosition
from ..models.user import User
from ..utils.ray_math import RAY
from .interest_calculator import InterestCalculator
from .interest_rate_model import InterestRateModel
from .coordinator import CoordinatorService


class ReserveService:
    """
    Service for managing reserve pool operations.
    
    Handles:
    - Supply operations (deposit assets, mint aTokens)
    - Index updates (accrue interest)
    - Reserve state management
    """
    
    def __init__(self, session: AsyncSession):
        """
        Initialize reserve service.
        
        Args:
            session: Database session
        """
        self.session = session
        self.interest_calculator = InterestCalculator()
        self.rate_model = InterestRateModel()
        self.coordinator = CoordinatorService(session)
    
    async def get_reserve_state(self, asset_id: str) -> Optional[ReserveState]:
        """
        Get current reserve state for an asset.
        
        Args:
            asset_id: Liquid asset ID
        
        Returns:
            ReserveState or None if not found
        """
        result = await self.session.execute(
            select(ReserveState).where(ReserveState.asset_id == asset_id)
        )
        return result.scalar_one_or_none()
    
    async def update_indices(self, reserve: ReserveState) -> ReserveState:
        """
        Update reserve indices to current time.
        
        Accrues interest by updating liquidityIndex and variableBorrowIndex.
        
        Args:
            reserve: Reserve state to update
        
        Returns:
            Updated reserve state
        """
        current_time = int(time.time())
        
        # Calculate new indices
        new_liquidity_index, new_borrow_index = (
            self.interest_calculator.accrue_indices(
                current_liquidity_index=reserve.liquidity_index,
                current_borrow_index=reserve.variable_borrow_index,
                liquidity_rate=reserve.current_liquidity_rate,
                borrow_rate=reserve.current_variable_borrow_rate,
                last_update_timestamp=reserve.last_update_timestamp,
            )
        )
        
        # Update reserve
        reserve.liquidity_index = new_liquidity_index
        reserve.variable_borrow_index = new_borrow_index
        reserve.last_update_timestamp = current_time
        
        logger.info(
            f"Updated indices for asset {reserve.asset_id[:8]}... - "
            f"liquidity_index: {new_liquidity_index}, "
            f"borrow_index: {new_borrow_index}"
        )
        
        return reserve

    def _update_current_rates(self, reserve: ReserveState) -> None:
        """Update current per-second rates from utilization using the rate model."""
        liq_rate, borrow_rate = self.rate_model.calculate_rates(
            total_liquidity=reserve.total_liquidity,
            total_borrowed=reserve.total_borrowed,
            reserve_factor=reserve.reserve_factor,
        )
        reserve.current_liquidity_rate = liq_rate
        reserve.current_variable_borrow_rate = borrow_rate
    
    async def supply(
        self,
        user_address: str,
        asset_id: str,
        amount: int,
    ) -> SupplyPosition:
        """
        Process supply operation.
        
        Steps:
        1. Get or create user
        2. Get reserve state
        3. Update indices
        4. Calculate aToken amount
        5. Create supply position
        6. Update reserve liquidity
        
        Args:
            user_address: User's Liquid address
            asset_id: Asset being supplied
            amount: Amount to supply (satoshis)
        
        Returns:
            Created supply position
        
        Raises:
            ValueError: If reserve not found or amount invalid
        """
        if amount <= 0:
            raise ValueError("Supply amount must be positive")
        
        # Get or create user
        user = await self._get_or_create_user(user_address)
        
        # Get reserve state
        reserve = await self.get_reserve_state(asset_id)
        if not reserve:
            raise ValueError(f"Reserve not found for asset {asset_id}")
        
        # Update indices to current time
        reserve = await self.update_indices(reserve)
        
        # Calculate aToken amount
        atoken_amount = self.interest_calculator.calculate_atoken_amount(
            underlying_amount=amount,
            liquidity_index=reserve.liquidity_index
        )
        
        # Create supply position
        position = SupplyPosition(
            user_id=user.id,
            asset_id=asset_id,
            atoken_amount=atoken_amount,
            liquidity_index_at_supply=reserve.liquidity_index,
        )
        
        self.session.add(position)
        
        # Update reserve liquidity
        reserve.total_liquidity += amount
        # Recalculate rates after liquidity change
        self._update_current_rates(reserve)
        
        logger.info(
            f"Supply: user={user_address}, asset={asset_id[:8]}..., "
            f"amount={amount}, atoken_amount={atoken_amount}"
        )
        
        await self.session.commit()
        await self.session.refresh(position)
        
        # Assemble and broadcast transaction (async, non-blocking for MVP)
        try:
            tx_id = await self.coordinator.assemble_supply_transaction(
                position=position,
                reserve=reserve,
                user_address=user_address,
                amount=amount,
            )
            
            if tx_id:
                logger.info(f"Supply transaction broadcast: {tx_id}")
            else:
                logger.warning("Supply transaction assembly failed (non-blocking)")
        except Exception as e:
            logger.error(f"Error in coordinator (non-blocking): {e}", exc_info=True)
        
        return position
    
    async def withdraw(
        self,
        user_address: str,
        asset_id: str,
        amount: int,
    ) -> tuple[int, int, int]:
        """
        Withdraw supplied assets.
        
        Args:
            user_address: User's address
            asset_id: Asset to withdraw
            amount: Underlying amount to withdraw in satoshis. If 0, withdraw all.
        
        Returns:
            Tuple (amount_withdrawn, atoken_burned, liquidity_index)
        """
        if amount < 0:
            raise ValueError("Withdraw amount cannot be negative")

        # Get user
        result = await self.session.execute(
            select(User).where(User.address == user_address)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("User not found")

        # Get reserve
        reserve = await self.get_reserve_state(asset_id)
        if not reserve:
            raise ValueError(f"Reserve not found for asset {asset_id}")

        # Update indices
        reserve = await self.update_indices(reserve)

        # Get user's supply positions for this asset
        result = await self.session.execute(
            select(SupplyPosition).where(
                SupplyPosition.user_id == user.id,
                SupplyPosition.asset_id == asset_id,
            )
        )
        positions = result.scalars().all()

        if not positions:
            raise ValueError("No supply positions for this asset")

        # Calculate total underlying available and total aTokens
        total_underlying = 0
        total_atokens = 0
        for pos in positions:
            total_underlying += pos.calculate_underlying_amount(reserve.liquidity_index)
            total_atokens += pos.atoken_amount

        if total_underlying <= 0 or total_atokens <= 0:
            raise ValueError("No balance to withdraw")

        # Determine withdrawal amount
        amount_to_withdraw = total_underlying if amount == 0 else amount
        if amount_to_withdraw > total_underlying:
            raise ValueError("Insufficient balance to withdraw the requested amount")

        # Check reserve liquidity
        if reserve.total_liquidity < amount_to_withdraw:
            raise ValueError(
                f"Insufficient reserve liquidity. Available: {reserve.total_liquidity}, "
                f"Requested: {amount_to_withdraw}"
            )

        # Calculate aTokens to burn using current index
        atoken_to_burn = self.interest_calculator.calculate_atoken_amount(
            underlying_amount=amount_to_withdraw,
            liquidity_index=reserve.liquidity_index,
        )
        if atoken_to_burn <= 0:
            raise ValueError("Calculated aToken burn amount is zero")

        # Burn aTokens from positions (FIFO)
        remaining_to_burn = atoken_to_burn
        for pos in positions:
            if remaining_to_burn <= 0:
                break
            burn_here = min(pos.atoken_amount, remaining_to_burn)
            pos.atoken_amount -= burn_here
            remaining_to_burn -= burn_here

        if remaining_to_burn > 0:
            # Guard: should not happen due to checks above
            raise ValueError("Not enough aTokens to burn for withdrawal")

        # Update reserve liquidity
        reserve.total_liquidity -= amount_to_withdraw

        # Recalculate rates based on new utilization
        self._update_current_rates(reserve)

        logger.info(
            f"Withdraw: user={user_address}, asset={asset_id[:8]}..., "
            f"amount={amount_to_withdraw}, atoken_burned={atoken_to_burn}"
        )

        await self.session.commit()

        # Assemble and broadcast withdraw transaction (simulated)
        try:
            tx_id = await self.coordinator.assemble_withdraw_transaction(
                user_address=user_address,
                asset_id=asset_id,
                amount=amount_to_withdraw,
            )
            if tx_id:
                logger.info(f"Withdraw transaction broadcast: {tx_id}")
            else:
                logger.warning("Withdraw transaction assembly failed (non-blocking)")
        except Exception as e:
            logger.error(f"Error in coordinator (non-blocking): {e}", exc_info=True)

        return amount_to_withdraw, atoken_to_burn, reserve.liquidity_index
    
    async def get_reserve_state_with_accrued_interest(
        self,
        asset_id: str
    ) -> Optional[ReserveState]:
        """
        Get reserve state with accrued interest (without persisting).
        
        Args:
            asset_id: Liquid asset ID
        
        Returns:
            Reserve state with updated indices
        """
        reserve = await self.get_reserve_state(asset_id)
        if not reserve:
            return None
        
        # Calculate updated indices without persisting
        current_time = int(time.time())
        time_delta = current_time - reserve.last_update_timestamp
        
        if time_delta > 0:
            new_liquidity_index, new_borrow_index = (
                self.interest_calculator.accrue_indices(
                    current_liquidity_index=reserve.liquidity_index,
                    current_borrow_index=reserve.variable_borrow_index,
                    liquidity_rate=reserve.current_liquidity_rate,
                    borrow_rate=reserve.current_variable_borrow_rate,
                    last_update_timestamp=reserve.last_update_timestamp,
                )
            )
            
            # Create a copy with updated values (don't modify original)
            reserve.liquidity_index = new_liquidity_index
            reserve.variable_borrow_index = new_borrow_index
        
        return reserve
    
    async def _get_or_create_user(self, address: str) -> User:
        """
        Get existing user or create new one.
        
        Args:
            address: User's Liquid address
        
        Returns:
            User instance
        """
        result = await self.session.execute(
            select(User).where(User.address == address)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(address=address)
            self.session.add(user)
            await self.session.flush()
            logger.info(f"Created new user: {address}")
        
        return user
