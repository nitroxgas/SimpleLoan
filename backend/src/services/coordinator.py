"""
Coordinator Service for UTXO Transaction Assembly

Handles the assembly and broadcasting of UTXO transactions for supply operations.
Manages UTXO locks to prevent race conditions.

This is a simplified MVP implementation. Production version would need:
- Distributed locking (Redis)
- Transaction queue management
- Retry logic with exponential backoff
- UTXO selection optimization
- Fee estimation
"""

from datetime import datetime, timedelta
from typing import Optional
import asyncio

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.reserve_state import ReserveState
from ..models.supply_position import SupplyPosition
from ..utils.liquid_client import LiquidClient


class UTXOLock:
    """
    Simple in-memory UTXO lock for MVP.
    
    Production should use Redis or similar distributed lock.
    """
    
    _locks: dict[str, datetime] = {}
    _lock_timeout = timedelta(seconds=30)
    
    @classmethod
    def acquire(cls, utxo_id: str) -> bool:
        """
        Try to acquire lock on UTXO.
        
        Args:
            utxo_id: UTXO identifier
            
        Returns:
            True if lock acquired, False if already locked
        """
        now = datetime.utcnow()
        
        # Clean expired locks
        expired = [
            uid for uid, lock_time in cls._locks.items()
            if now - lock_time > cls._lock_timeout
        ]
        for uid in expired:
            del cls._locks[uid]
        
        # Try to acquire
        if utxo_id in cls._locks:
            return False
        
        cls._locks[utxo_id] = now
        return True
    
    @classmethod
    def release(cls, utxo_id: str) -> None:
        """Release lock on UTXO."""
        cls._locks.pop(utxo_id, None)


class CoordinatorService:
    """
    Coordinates UTXO transaction assembly and broadcasting.
    
    Responsibilities:
    - Assemble supply transactions
    - Manage UTXO locks
    - Broadcast transactions to Elements node
    - Handle transaction failures
    """
    
    def __init__(self, session: AsyncSession, liquid_client: Optional[LiquidClient] = None):
        """
        Initialize coordinator service.
        
        Args:
            session: Database session
            liquid_client: Elements RPC client (optional for testing)
        """
        self.session = session
        self.liquid_client = liquid_client or LiquidClient()
    
    async def assemble_supply_transaction(
        self,
        position: SupplyPosition,
        reserve: ReserveState,
        user_address: str,
        amount: int,
    ) -> Optional[str]:
        """
        Assemble and broadcast supply transaction.
        
        Process:
        1. Lock reserve UTXO
        2. Fetch UTXO from Elements node
        3. Create new reserve UTXO with updated state
        4. Create supply position UTXO
        5. Sign and broadcast transaction
        6. Release lock
        
        Args:
            position: Supply position to create
            reserve: Reserve state to update
            user_address: User's Liquid address
            amount: Amount being supplied
            
        Returns:
            Transaction ID if successful, None if failed
        """
        utxo_id = reserve.utxo_id if reserve.utxo_id else f"reserve_{reserve.asset_id}"
        
        try:
            # Try to acquire lock
            if not UTXOLock.acquire(utxo_id):
                logger.warning(f"UTXO {utxo_id} is locked, retrying...")
                await asyncio.sleep(0.5)
                
                # Retry once
                if not UTXOLock.acquire(utxo_id):
                    logger.error(f"Failed to acquire lock on UTXO {utxo_id}")
                    return None
            
            logger.info(f"Assembling supply transaction for {user_address}")
            
            # TODO: Implement actual UTXO transaction assembly
            # This is a placeholder for MVP
            # Production implementation would:
            # 1. Fetch reserve UTXO from Elements node
            # 2. Create transaction inputs (reserve UTXO + user funds)
            # 3. Create transaction outputs (new reserve UTXO + change)
            # 4. Sign transaction
            # 5. Broadcast to network
            
            # For MVP, we simulate transaction broadcast
            tx_id = await self._simulate_transaction_broadcast(
                user_address=user_address,
                asset_id=reserve.asset_id,
                amount=amount,
            )
            
            if tx_id:
                logger.info(f"Supply transaction broadcast: {tx_id}")
                
                # Update reserve UTXO ID
                reserve.utxo_id = f"utxo_{tx_id}_0"
                await self.session.commit()
            
            return tx_id
        
        except Exception as e:
            logger.error(f"Error assembling supply transaction: {e}", exc_info=True)
            return None
        
        finally:
            # Always release lock
            UTXOLock.release(utxo_id)
    
    async def _simulate_transaction_broadcast(
        self,
        user_address: str,
        asset_id: str,
        amount: int,
    ) -> Optional[str]:
        """
        Simulate transaction broadcast for MVP.
        
        In production, this would call Elements RPC to broadcast real transaction.
        
        Args:
            user_address: User's address
            asset_id: Asset being supplied
            amount: Amount being supplied
            
        Returns:
            Simulated transaction ID
        """
        # Generate fake transaction ID for MVP
        import hashlib
        
        tx_data = f"{user_address}:{asset_id}:{amount}:{datetime.utcnow().isoformat()}"
        tx_id = hashlib.sha256(tx_data.encode()).hexdigest()
        
        logger.info(
            f"[SIMULATED] Broadcasting supply transaction: "
            f"user={user_address[:10]}..., asset={asset_id[:8]}..., amount={amount}"
        )
        
        # Simulate network delay
        await asyncio.sleep(0.1)
        
        return tx_id
    
    async def verify_transaction(self, tx_id: str) -> bool:
        """
        Verify transaction was confirmed on-chain.
        
        Args:
            tx_id: Transaction ID to verify
            
        Returns:
            True if confirmed, False otherwise
        """
        try:
            # TODO: Implement actual transaction verification
            # For MVP, assume all transactions are confirmed
            logger.info(f"[SIMULATED] Verifying transaction {tx_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error verifying transaction {tx_id}: {e}")
            return False

    async def assemble_withdraw_transaction(
        self,
        user_address: str,
        asset_id: str,
        amount: int,
    ) -> Optional[str]:
        """
        Assemble and broadcast withdraw transaction (simulated for MVP).
        """
        try:
            logger.info(
                f"Assembling withdraw transaction: user={user_address[:10]}..., asset={asset_id[:8]}..., amount={amount}"
            )

            tx_id = await self._simulate_withdraw_broadcast(
                user_address=user_address,
                asset_id=asset_id,
                amount=amount,
            )

            if tx_id:
                logger.info(f"Withdraw transaction broadcast: {tx_id}")
            return tx_id

        except Exception as e:
            logger.error(f"Error assembling withdraw transaction: {e}", exc_info=True)
            return None

    async def _simulate_withdraw_broadcast(
        self,
        user_address: str,
        asset_id: str,
        amount: int,
    ) -> Optional[str]:
        """Simulate withdraw transaction broadcast."""
        import hashlib

        tx_data = f"{user_address}:{asset_id}:withdraw:{amount}:{datetime.utcnow().isoformat()}"
        tx_id = hashlib.sha256(tx_data.encode()).hexdigest()

        logger.info(
            f"[SIMULATED] Broadcasting withdraw transaction: "
            f"user={user_address[:10]}..., asset={asset_id[:8]}..., amount={amount}"
        )

        await asyncio.sleep(0.1)
        return tx_id
    
    async def get_utxo_state(self, utxo_id: str) -> Optional[dict]:
        """
        Fetch UTXO state from Elements node.
        
        Args:
            utxo_id: UTXO identifier
            
        Returns:
            UTXO data if found, None otherwise
        """
        try:
            # TODO: Implement actual UTXO fetching from Elements node
            # For MVP, return None (not implemented)
            logger.warning(f"[SIMULATED] Fetching UTXO {utxo_id} - not implemented")
            return None
        
        except Exception as e:
            logger.error(f"Error fetching UTXO {utxo_id}: {e}")
            return None
    
    async def assemble_borrow_transaction(
        self,
        user_address: str,
        collateral_asset_id: str,
        collateral_amount: int,
        borrow_asset_id: str,
        borrow_amount: int,
    ) -> Optional[str]:
        """
        Assemble and broadcast borrow transaction.
        
        Process:
        1. Lock collateral
        2. Create debt UTXO
        3. Transfer borrowed assets to user
        4. Sign and broadcast
        
        Args:
            user_address: User's address
            collateral_asset_id: Collateral asset
            collateral_amount: Collateral amount
            borrow_asset_id: Asset to borrow
            borrow_amount: Amount to borrow
            
        Returns:
            Transaction ID if successful, None if failed
        """
        try:
            logger.info(
                f"Assembling borrow transaction: "
                f"user={user_address[:10]}..., "
                f"collateral={collateral_amount} {collateral_asset_id[:8]}..., "
                f"borrow={borrow_amount} {borrow_asset_id[:8]}..."
            )
            
            # TODO: Implement actual UTXO transaction assembly
            # For MVP, simulate transaction
            tx_id = await self._simulate_borrow_broadcast(
                user_address=user_address,
                collateral_amount=collateral_amount,
                borrow_amount=borrow_amount,
            )
            
            if tx_id:
                logger.info(f"Borrow transaction broadcast: {tx_id}")
            
            return tx_id
        
        except Exception as e:
            logger.error(f"Error assembling borrow transaction: {e}", exc_info=True)
            return None
    
    async def _simulate_borrow_broadcast(
        self,
        user_address: str,
        collateral_amount: int,
        borrow_amount: int,
    ) -> Optional[str]:
        """
        Simulate borrow transaction broadcast for MVP.
        
        Args:
            user_address: User's address
            collateral_amount: Collateral amount
            borrow_amount: Borrow amount
            
        Returns:
            Simulated transaction ID
        """
        import hashlib
        
        tx_data = f"{user_address}:borrow:{collateral_amount}:{borrow_amount}:{datetime.utcnow().isoformat()}"
        tx_id = hashlib.sha256(tx_data.encode()).hexdigest()
        
        logger.info(
            f"[SIMULATED] Broadcasting borrow transaction: "
            f"user={user_address[:10]}..., collateral={collateral_amount}, borrow={borrow_amount}"
        )
        
        # Simulate network delay
        await asyncio.sleep(0.1)
        
        return tx_id

    async def assemble_liquidation_transaction(
        self,
        liquidator_address: str,
        position: Optional["DebtPosition"],
        repay_amount: int,
        collateral_seized: int,
    ) -> Optional[str]:
        """Assemble and broadcast liquidation transaction (simulated)."""
        try:
            logger.info(
                "Assembling liquidation transaction: "
                f"liquidator={liquidator_address[:10]}..., "
                f"repay={repay_amount}, collateral={collateral_seized}"
            )

            tx_id = await self._simulate_liquidation_broadcast(
                liquidator_address=liquidator_address,
                repay_amount=repay_amount,
                collateral_seized=collateral_seized,
                position_id=position.id if position else None,
            )

            if tx_id:
                logger.info(f"Liquidation transaction broadcast: {tx_id}")

            return tx_id

        except Exception as e:
            logger.error(f"Error assembling liquidation transaction: {e}", exc_info=True)
            return None

    async def _simulate_liquidation_broadcast(
        self,
        liquidator_address: str,
        repay_amount: int,
        collateral_seized: int,
        position_id: int | None,
    ) -> Optional[str]:
        """Simulate liquidation transaction broadcast."""
        import hashlib

        tx_data = (
            f"{liquidator_address}:liquidate:{repay_amount}:{collateral_seized}:"
            f"{position_id}:{datetime.utcnow().isoformat()}"
        )
        tx_id = hashlib.sha256(tx_data.encode()).hexdigest()

        logger.info(
            f"[SIMULATED] Broadcasting liquidation transaction: "
            f"liquidator={liquidator_address[:10]}..., repay={repay_amount}, "
            f"collateral={collateral_seized}"
        )

        await asyncio.sleep(0.1)
        return tx_id
