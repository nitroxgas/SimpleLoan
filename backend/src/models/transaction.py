"""
Transaction history model for audit logging.
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import Column, Integer, String, DateTime, BigInteger, Text
from sqlalchemy.orm import declarative_base

from .base import Base


class TransactionType(str, Enum):
    """Transaction types."""
    SUPPLY = "supply"
    WITHDRAW = "withdraw"
    BORROW = "borrow"
    REPAY = "repay"
    LIQUIDATE = "liquidate"


class TransactionStatus(str, Enum):
    """Transaction status."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"


class Transaction(Base):
    """
    Transaction history for audit trail.
    
    Records all protocol operations for compliance and debugging.
    """
    
    __tablename__ = "transactions"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Transaction identification
    tx_hash = Column(String(64), nullable=True, index=True)  # On-chain transaction hash
    tx_type = Column(String(20), nullable=False, index=True)  # Transaction type
    status = Column(String(20), nullable=False, default="pending")  # Status
    
    # User information
    user_address = Column(String(100), nullable=False, index=True)  # Initiator
    
    # Asset information
    asset_id = Column(String(64), nullable=False, index=True)  # Primary asset
    amount = Column(BigInteger, nullable=False)  # Transaction amount (satoshis)
    
    # Additional context (JSON-serialized)
    metadata = Column(Text, nullable=True)  # JSON with tx-specific data
    
    # Results
    result_data = Column(Text, nullable=True)  # JSON with result details
    error_message = Column(Text, nullable=True)  # Error if failed
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    confirmed_at = Column(DateTime, nullable=True)  # When confirmed on-chain
    
    # Relationships (for analytics)
    position_id = Column(Integer, nullable=True)  # Related position if applicable
    reserve_asset_id = Column(String(64), nullable=True)  # Related reserve
    
    def __repr__(self) -> str:
        return (
            f"<Transaction(id={self.id}, type={self.tx_type}, "
            f"user={self.user_address[:10]}..., amount={self.amount}, "
            f"status={self.status})>"
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "tx_hash": self.tx_hash,
            "tx_type": self.tx_type,
            "status": self.status,
            "user_address": self.user_address,
            "asset_id": self.asset_id,
            "amount": self.amount,
            "metadata": self.metadata,
            "result_data": self.result_data,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "confirmed_at": self.confirmed_at.isoformat() if self.confirmed_at else None,
            "position_id": self.position_id,
            "reserve_asset_id": self.reserve_asset_id,
        }
