"""
Transaction history service for audit logging.
"""

import json
from datetime import datetime
from typing import List, Optional

from loguru import logger
from sqlalchemy import select, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.transaction import Transaction, TransactionType, TransactionStatus


class TransactionService:
    """Service for transaction history and audit logging."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def log_transaction(
        self,
        tx_type: TransactionType,
        user_address: str,
        asset_id: str,
        amount: int,
        metadata: Optional[dict] = None,
        position_id: Optional[int] = None,
        tx_hash: Optional[str] = None,
        status: TransactionStatus = TransactionStatus.PENDING,
    ) -> Transaction:
        """
        Log a transaction to the audit trail.
        
        Args:
            tx_type: Type of transaction (supply, borrow, etc.)
            user_address: User's Liquid address
            asset_id: Asset ID involved
            amount: Transaction amount in satoshis
            metadata: Additional context (dict)
            position_id: Related position ID if applicable
            tx_hash: On-chain transaction hash
            status: Transaction status
        
        Returns:
            Created Transaction record
        """
        try:
            tx = Transaction(
                tx_type=tx_type.value,
                user_address=user_address,
                asset_id=asset_id,
                amount=amount,
                metadata=json.dumps(metadata) if metadata else None,
                position_id=position_id,
                tx_hash=tx_hash,
                status=status.value,
                reserve_asset_id=asset_id,
            )
            
            self.session.add(tx)
            await self.session.commit()
            await self.session.refresh(tx)
            
            logger.info(
                f"Transaction logged: type={tx_type.value}, "
                f"user={user_address[:10]}..., amount={amount}, id={tx.id}"
            )
            
            return tx
        
        except Exception as e:
            logger.error(f"Failed to log transaction: {e}", exc_info=True)
            await self.session.rollback()
            raise
    
    async def update_transaction_status(
        self,
        transaction_id: int,
        status: TransactionStatus,
        tx_hash: Optional[str] = None,
        result_data: Optional[dict] = None,
        error_message: Optional[str] = None,
    ) -> Transaction:
        """
        Update transaction status.
        
        Args:
            transaction_id: Transaction ID to update
            status: New status
            tx_hash: On-chain transaction hash
            result_data: Result data (dict)
            error_message: Error message if failed
        
        Returns:
            Updated Transaction record
        """
        try:
            result = await self.session.execute(
                select(Transaction).where(Transaction.id == transaction_id)
            )
            tx = result.scalar_one_or_none()
            
            if not tx:
                raise ValueError(f"Transaction {transaction_id} not found")
            
            tx.status = status.value
            
            if tx_hash:
                tx.tx_hash = tx_hash
            
            if result_data:
                tx.result_data = json.dumps(result_data)
            
            if error_message:
                tx.error_message = error_message
            
            if status == TransactionStatus.CONFIRMED:
                tx.confirmed_at = datetime.utcnow()
            
            await self.session.commit()
            await self.session.refresh(tx)
            
            logger.info(
                f"Transaction {transaction_id} updated: status={status.value}"
            )
            
            return tx
        
        except Exception as e:
            logger.error(f"Failed to update transaction {transaction_id}: {e}")
            await self.session.rollback()
            raise
    
    async def get_user_transactions(
        self,
        user_address: str,
        tx_type: Optional[TransactionType] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Transaction]:
        """
        Get transaction history for a user.
        
        Args:
            user_address: User's Liquid address
            tx_type: Filter by transaction type (optional)
            limit: Maximum number of results
            offset: Pagination offset
        
        Returns:
            List of Transaction records
        """
        try:
            query = select(Transaction).where(
                Transaction.user_address == user_address
            )
            
            if tx_type:
                query = query.where(Transaction.tx_type == tx_type.value)
            
            query = query.order_by(desc(Transaction.created_at))
            query = query.limit(limit).offset(offset)
            
            result = await self.session.execute(query)
            transactions = result.scalars().all()
            
            logger.debug(
                f"Retrieved {len(transactions)} transactions for user {user_address[:10]}..."
            )
            
            return list(transactions)
        
        except Exception as e:
            logger.error(f"Failed to get user transactions: {e}")
            raise
    
    async def get_asset_transactions(
        self,
        asset_id: str,
        tx_type: Optional[TransactionType] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Transaction]:
        """
        Get transaction history for an asset.
        
        Args:
            asset_id: Asset ID
            tx_type: Filter by transaction type (optional)
            limit: Maximum number of results
            offset: Pagination offset
        
        Returns:
            List of Transaction records
        """
        try:
            query = select(Transaction).where(
                Transaction.asset_id == asset_id
            )
            
            if tx_type:
                query = query.where(Transaction.tx_type == tx_type.value)
            
            query = query.order_by(desc(Transaction.created_at))
            query = query.limit(limit).offset(offset)
            
            result = await self.session.execute(query)
            transactions = result.scalars().all()
            
            logger.debug(
                f"Retrieved {len(transactions)} transactions for asset {asset_id[:8]}..."
            )
            
            return list(transactions)
        
        except Exception as e:
            logger.error(f"Failed to get asset transactions: {e}")
            raise
    
    async def get_recent_transactions(
        self,
        limit: int = 50,
        tx_type: Optional[TransactionType] = None,
        status: Optional[TransactionStatus] = None,
    ) -> List[Transaction]:
        """
        Get recent transactions across all users.
        
        Args:
            limit: Maximum number of results
            tx_type: Filter by transaction type (optional)
            status: Filter by status (optional)
        
        Returns:
            List of Transaction records
        """
        try:
            query = select(Transaction)
            
            conditions = []
            if tx_type:
                conditions.append(Transaction.tx_type == tx_type.value)
            if status:
                conditions.append(Transaction.status == status.value)
            
            if conditions:
                query = query.where(and_(*conditions))
            
            query = query.order_by(desc(Transaction.created_at))
            query = query.limit(limit)
            
            result = await self.session.execute(query)
            transactions = result.scalars().all()
            
            logger.debug(f"Retrieved {len(transactions)} recent transactions")
            
            return list(transactions)
        
        except Exception as e:
            logger.error(f"Failed to get recent transactions: {e}")
            raise
    
    async def get_transaction_by_hash(self, tx_hash: str) -> Optional[Transaction]:
        """
        Get transaction by on-chain hash.
        
        Args:
            tx_hash: On-chain transaction hash
        
        Returns:
            Transaction record or None
        """
        try:
            result = await self.session.execute(
                select(Transaction).where(Transaction.tx_hash == tx_hash)
            )
            return result.scalar_one_or_none()
        
        except Exception as e:
            logger.error(f"Failed to get transaction by hash: {e}")
            raise
    
    async def get_transaction_stats(self, user_address: Optional[str] = None) -> dict:
        """
        Get transaction statistics.
        
        Args:
            user_address: Filter by user (optional)
        
        Returns:
            Statistics dictionary
        """
        try:
            query = select(Transaction)
            if user_address:
                query = query.where(Transaction.user_address == user_address)
            
            result = await self.session.execute(query)
            transactions = result.scalars().all()
            
            stats = {
                "total_transactions": len(transactions),
                "by_type": {},
                "by_status": {},
                "total_volume": 0,
            }
            
            for tx in transactions:
                # Count by type
                stats["by_type"][tx.tx_type] = stats["by_type"].get(tx.tx_type, 0) + 1
                
                # Count by status
                stats["by_status"][tx.status] = stats["by_status"].get(tx.status, 0) + 1
                
                # Sum volume
                stats["total_volume"] += tx.amount
            
            return stats
        
        except Exception as e:
            logger.error(f"Failed to get transaction stats: {e}")
            raise
