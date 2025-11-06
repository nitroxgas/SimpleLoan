"""
Debt Service for Borrow Operations

Handles borrowing, repayment, and health factor calculations.
"""

from typing import List, Optional

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.debt_position import DebtPosition
from ..models.reserve_state import ReserveState
from ..models.user import User
from ..utils.ray_math import RAY, ray_mul, ray_div
from .interest_calculator import InterestCalculator
from .oracle_service import OracleService
from .coordinator import CoordinatorService


class DebtService:
    """
    Service for managing debt operations.
    
    Handles:
    - Borrow operations (create debt position)
    - Repayment (partial or full)
    - Health factor calculation
    - Collateral management
    """
    
    # Protocol parameters (from AAVE)
    LTV_BTC = int(0.75 * RAY)  # 75% Loan-to-Value for BTC
    LIQUIDATION_THRESHOLD_BTC = int(0.80 * RAY)  # 80% liquidation threshold
    LIQUIDATION_BONUS = int(0.05 * RAY)  # 5% liquidation bonus
    
    def __init__(self, session: AsyncSession):
        """
        Initialize debt service.
        
        Args:
            session: Database session
        """
        self.session = session
        self.interest_calculator = InterestCalculator()
        self.oracle = OracleService()
        self.coordinator = CoordinatorService(session)
    
    async def borrow(
        self,
        user_address: str,
        collateral_asset_id: str,
        collateral_amount: int,
        borrow_asset_id: str,
        borrow_amount: int,
    ) -> DebtPosition:
        """
        Create a borrow position.
        
        Process:
        1. Get or create user
        2. Validate collateral value
        3. Check LTV ratio
        4. Get borrow reserve state
        5. Update borrow index
        6. Create debt position
        7. Update user health factor
        8. Update reserve borrowed amount
        
        Args:
            user_address: User's Liquid address
            collateral_asset_id: Asset used as collateral
            collateral_amount: Amount of collateral (satoshis)
            borrow_asset_id: Asset to borrow
            borrow_amount: Amount to borrow (satoshis)
        
        Returns:
            Created debt position
        
        Raises:
            ValueError: If validation fails
        """
        if collateral_amount <= 0:
            raise ValueError("Collateral amount must be positive")
        
        if borrow_amount <= 0:
            raise ValueError("Borrow amount must be positive")
        
        # Get or create user
        user = await self._get_or_create_user(user_address)
        
        # Get collateral value in USD
        collateral_value = await self.oracle.get_asset_value(
            collateral_amount,
            collateral_asset_id
        )
        
        if not collateral_value:
            raise ValueError(f"Cannot get price for collateral asset {collateral_asset_id}")
        
        # Get borrow value in USD
        borrow_value = await self.oracle.get_asset_value(
            borrow_amount,
            borrow_asset_id
        )
        
        if not borrow_value:
            raise ValueError(f"Cannot get price for borrow asset {borrow_asset_id}")
        
        # Check LTV ratio
        max_borrow_value = ray_mul(collateral_value, self.LTV_BTC)
        
        if borrow_value > max_borrow_value:
            raise ValueError(
                f"Borrow amount exceeds LTV limit. "
                f"Max borrow: ${max_borrow_value/RAY:,.2f}, "
                f"Requested: ${borrow_value/RAY:,.2f}"
            )
        
        # Get borrow reserve
        result = await self.session.execute(
            select(ReserveState).where(ReserveState.asset_id == borrow_asset_id)
        )
        reserve = result.scalar_one_or_none()
        
        if not reserve:
            raise ValueError(f"Reserve not found for asset {borrow_asset_id}")
        
        # Check available liquidity
        if reserve.total_liquidity < borrow_amount:
            raise ValueError(
                f"Insufficient liquidity. "
                f"Available: {reserve.total_liquidity}, "
                f"Requested: {borrow_amount}"
            )
        
        # Update borrow index
        reserve = await self._update_borrow_index(reserve)
        
        # Create debt position
        position = DebtPosition(
            user_id=user.id,
            borrowed_asset_id=borrow_asset_id,
            collateral_asset_id=collateral_asset_id,
            principal=borrow_amount,
            borrow_index_at_open=reserve.variable_borrow_index,
            collateral_amount=collateral_amount,
        )
        
        self.session.add(position)
        
        # Update reserve
        reserve.total_borrowed += borrow_amount
        reserve.total_liquidity -= borrow_amount
        
        # Update user health factor
        await self._update_user_health_factor(user)
        
        logger.info(
            f"Borrow: user={user_address}, "
            f"collateral={collateral_amount} {collateral_asset_id[:8]}..., "
            f"borrow={borrow_amount} {borrow_asset_id[:8]}..."
        )
        
        await self.session.commit()
        await self.session.refresh(position)
        
        return position
    
    async def calculate_health_factor(
        self,
        user_address: str
    ) -> Optional[int]:
        """
        Calculate user's health factor.
        
        Formula:
            health_factor = (collateral_value * liquidation_threshold) / debt_value
        
        Healthy if >= 1.0 * RAY
        Liquidatable if < 1.0 * RAY
        
        Args:
            user_address: User's address
        
        Returns:
            Health factor in RAY precision, None if no debt
        """
        # Get user
        result = await self.session.execute(
            select(User).where(User.address == user_address)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        # Get all debt positions
        result = await self.session.execute(
            select(DebtPosition).where(DebtPosition.user_id == user.id)
        )
        debt_positions = result.scalars().all()
        
        if not debt_positions:
            return None  # No debt, infinite health factor
        
        # Calculate total collateral value
        total_collateral_value = 0
        
        for position in debt_positions:
            collateral_value = await self.oracle.get_asset_value(
                position.collateral_amount,
                position.collateral_asset_id
            )
            
            if collateral_value:
                total_collateral_value += collateral_value
        
        # Calculate total debt value
        total_debt_value = 0
        
        for position in debt_positions:
            # Get current borrow index
            result = await self.session.execute(
                select(ReserveState).where(
                    ReserveState.asset_id == position.borrowed_asset_id
                )
            )
            reserve = result.scalar_one_or_none()
            
            if reserve:
                # Update index
                reserve = await self._update_borrow_index(reserve)
                
                # Calculate current debt
                current_debt = position.calculate_current_debt(
                    reserve.variable_borrow_index
                )
                
                # Get debt value in USD
                debt_value = await self.oracle.get_asset_value(
                    current_debt,
                    position.borrowed_asset_id
                )
                
                if debt_value:
                    total_debt_value += debt_value
        
        if total_debt_value == 0:
            return None  # No debt
        
        # Calculate health factor
        # health_factor = (collateral * threshold) / debt
        weighted_collateral = ray_mul(
            total_collateral_value,
            self.LIQUIDATION_THRESHOLD_BTC
        )
        
        health_factor = ray_div(weighted_collateral, total_debt_value)
        
        logger.debug(
            f"Health factor for {user_address}: {health_factor/RAY:.4f} "
            f"(collateral=${total_collateral_value/RAY:,.2f}, "
            f"debt=${total_debt_value/RAY:,.2f})"
        )
        
        return health_factor
    
    async def _update_borrow_index(self, reserve: ReserveState) -> ReserveState:
        """
        Update variable borrow index for a reserve.
        
        Args:
            reserve: Reserve state to update
        
        Returns:
            Updated reserve state
        """
        # Calculate time elapsed
        now = int(datetime.utcnow().timestamp())
        time_delta = now - reserve.last_update_timestamp
        
        if time_delta > 0:
            # Accrue interest on borrow index
            new_index = self.interest_calculator.accrue_index(
                current_index=reserve.variable_borrow_index,
                rate_per_second=reserve.variable_borrow_rate,
                time_delta=time_delta
            )
            
            reserve.variable_borrow_index = new_index
            reserve.last_update_timestamp = now
        
        return reserve

    async def _get_reserve_state(self, asset_id: str) -> Optional[ReserveState]:
        """Fetch reserve state for asset."""
        result = await self.session.execute(
            select(ReserveState).where(ReserveState.asset_id == asset_id)
        )
        return result.scalar_one_or_none()

    async def get_position_health_factor(self, position: DebtPosition) -> Optional[int]:
        """Calculate health factor for a specific debt position."""
        reserve = await self._get_reserve_state(position.borrowed_asset_id)
        if not reserve:
            return None

        reserve = await self._update_borrow_index(reserve)
        current_debt = position.calculate_current_debt(reserve.variable_borrow_index)
        if current_debt <= 0:
            return None

        debt_value = await self.oracle.get_asset_value(
            current_debt,
            position.borrowed_asset_id
        )
        collateral_value = await self.oracle.get_asset_value(
            position.collateral_amount,
            position.collateral_asset_id
        )

        if not debt_value or not collateral_value:
            return None

        weighted_collateral = ray_mul(
            collateral_value,
            self.LIQUIDATION_THRESHOLD_BTC
        )

        return ray_div(weighted_collateral, debt_value)

    async def liquidate(
        self,
        liquidator_address: str,
        position_id: int,
        repay_amount: int | None = None,
    ) -> dict:
        """Liquidate an unhealthy debt position."""
        logger.info(
            f"Liquidation initiated: position_id={position_id}, "
            f"liquidator={liquidator_address[:10]}..."
        )
        
        result = await self.session.execute(
            select(DebtPosition).where(DebtPosition.id == position_id)
        )
        position = result.scalar_one_or_none()

        if not position:
            logger.warning(f"Liquidation failed: Position {position_id} not found")
            raise ValueError(f"Debt position {position_id} not found")

        user = await self.session.get(User, position.user_id)
        if not user:
            logger.warning(f"Liquidation failed: Position owner not found for position {position_id}")
            raise ValueError("Position owner not found")

        reserve = await self._get_reserve_state(position.borrowed_asset_id)
        if not reserve:
            logger.warning(f"Liquidation failed: Reserve not found for {position.borrowed_asset_id[:8]}...")
            raise ValueError("Reserve not found for borrowed asset")

        reserve = await self._update_borrow_index(reserve)
        current_debt = position.calculate_current_debt(reserve.variable_borrow_index)

        if current_debt <= 0:
            logger.warning(f"Liquidation failed: Position {position_id} has no outstanding debt")
            raise ValueError("Position has no outstanding debt")

        health_factor = await self.get_position_health_factor(position)
        if health_factor is None:
            logger.warning(f"Liquidation failed: Unable to determine health factor for position {position_id}")
            raise ValueError("Unable to determine health factor")

        logger.info(
            f"Position {position_id} health factor: {health_factor/RAY:.4f}, "
            f"debt: {current_debt}, collateral: {position.collateral_amount}"
        )

        if health_factor >= RAY:
            logger.warning(
                f"Liquidation rejected: Position {position_id} is healthy "
                f"(HF={health_factor/RAY:.4f})"
            )
            raise ValueError("Position is healthy and cannot be liquidated")

        # Determine repay amount (full debt by default)
        if repay_amount is None or repay_amount <= 0 or repay_amount > current_debt:
            repay_amount = current_debt

        if repay_amount <= 0:
            raise ValueError("Repay amount must be positive")

        # Calculate proportional collateral to seize (with bonus)
        collateral_base = (position.collateral_amount * repay_amount) // current_debt
        bonus_collateral = (collateral_base * self.LIQUIDATION_BONUS) // RAY
        collateral_to_seize = min(
            position.collateral_amount,
            collateral_base + bonus_collateral
        )

        remaining_debt = current_debt - repay_amount
        is_full_liquidation = remaining_debt <= 0

        logger.info(
            f"Liquidation details: repay={repay_amount}, "
            f"collateral_seized={collateral_to_seize} "
            f"(base={collateral_base}, bonus={bonus_collateral}), "
            f"type={'FULL' if is_full_liquidation else 'PARTIAL'}"
        )

        # Update reserve balances
        reserve.total_borrowed = max(0, reserve.total_borrowed - repay_amount)
        reserve.total_liquidity += repay_amount

        if is_full_liquidation:
            collateral_to_seize = position.collateral_amount
            logger.info(f"Full liquidation: closing position {position_id}")
            await self.session.delete(position)
        else:
            # Reset position with remaining debt and reduced collateral
            position.collateral_amount -= collateral_to_seize
            position.principal = remaining_debt
            position.borrow_index_at_open = reserve.variable_borrow_index
            logger.info(
                f"Partial liquidation: position {position_id} remaining - "
                f"debt={remaining_debt}, collateral={position.collateral_amount}"
            )
            await self.session.flush()

        await self._update_user_health_factor(user)
        await self.session.flush()
        await self.session.commit()

        if not is_full_liquidation:
            await self.session.refresh(position)

        # Assemble liquidation transaction (simulated for MVP)
        tx_id = await self.coordinator.assemble_liquidation_transaction(
            liquidator_address=liquidator_address,
            position=None if is_full_liquidation else position,
            repay_amount=repay_amount,
            collateral_seized=collateral_to_seize,
        )

        new_health_factor = await self.calculate_health_factor(user.address)

        logger.info(
            f"Liquidation completed: position_id={position_id}, "
            f"liquidator={liquidator_address[:10]}..., "
            f"repaid={repay_amount}, seized={collateral_to_seize}, "
            f"new_hf={new_health_factor/RAY if new_health_factor else 'N/A':.4f}, "
            f"tx_id={tx_id[:16] if tx_id else 'None'}..."
        )

        return {
            "position_id": position_id,
            "liquidator_address": liquidator_address,
            "repaid_amount": repay_amount,
            "collateral_seized": collateral_to_seize,
            "health_factor_after": new_health_factor or 0,
            "tx_id": tx_id,
        }

    async def get_liquidatable_positions(self) -> List[dict]:
        """Return list of liquidatable positions with health factor."""
        result = await self.session.execute(select(DebtPosition))
        positions = result.scalars().all()
        liquidatable: List[dict] = []

        for position in positions:
            reserve = await self._get_reserve_state(position.borrowed_asset_id)
            if not reserve:
                continue

            reserve = await self._update_borrow_index(reserve)
            current_debt = position.calculate_current_debt(reserve.variable_borrow_index)
            if current_debt <= 0:
                continue

            debt_value = await self.oracle.get_asset_value(
                current_debt,
                position.borrowed_asset_id
            )
            collateral_value = await self.oracle.get_asset_value(
                position.collateral_amount,
                position.collateral_asset_id
            )

            if not debt_value or not collateral_value:
                continue

            weighted_collateral = ray_mul(
                collateral_value,
                self.LIQUIDATION_THRESHOLD_BTC
            )
            health_factor = ray_div(weighted_collateral, debt_value)

            if health_factor < RAY:
                user = await self.session.get(User, position.user_id)
                liquidatable.append({
                    "position_id": position.id,
                    "user_address": user.address if user else "",
                    "borrowed_asset_id": position.borrowed_asset_id,
                    "collateral_asset_id": position.collateral_asset_id,
                    "current_debt": current_debt,
                    "collateral_amount": position.collateral_amount,
                    "health_factor": health_factor,
                })

        return liquidatable

    
    async def _update_user_health_factor(self, user: User) -> None:
        """
        Update user's health factor.
        
        Args:
            user: User to update
        """
        health_factor = await self.calculate_health_factor(user.address)
        user.health_factor = health_factor
    
    async def _get_or_create_user(self, address: str) -> User:
        """
        Get existing user or create new one.
        
        Args:
            address: User's Liquid address
        
        Returns:
            User entity
        """
        result = await self.session.execute(
            select(User).where(User.address == address)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(address=address)
            self.session.add(user)
            await self.session.flush()
        
        return user


# Import datetime at module level
from datetime import datetime
