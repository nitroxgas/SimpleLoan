"""
Debt Position Model

Represents a user's borrowing position with collateral.
Tracks principal, accrued interest, and collateral.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin
from ..utils.ray_math import RAY, ray_mul, ray_div


class DebtPosition(Base, TimestampMixin):
    """
    Debt position tracking user's borrowed amount and collateral.
    
    Attributes:
        id: Position identifier
        user_id: Foreign key to User
        borrowed_asset_id: Asset being borrowed (e.g., USDT)
        collateral_asset_id: Asset used as collateral (e.g., BTC)
        principal: Original borrowed amount (satoshis)
        borrow_index_at_open: variableBorrowIndex when position opened
        collateral_amount: Amount of collateral locked (satoshis)
        created_at: Position creation timestamp
        updated_at: Last update timestamp
    
    Relationships:
        user: User who owns this position
    
    Interest Calculation:
        current_debt = principal * (current_borrow_index / borrow_index_at_open)
        accrued_interest = current_debt - principal
    """
    
    __tablename__ = "debt_positions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Asset identifiers
    borrowed_asset_id: Mapped[str] = mapped_column(String(100), nullable=False)
    collateral_asset_id: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # Debt tracking
    principal: Mapped[int] = mapped_column(BigInteger, nullable=False)
    borrow_index_at_open: Mapped[int] = mapped_column(BigInteger, nullable=False, default=RAY)
    
    # Collateral tracking
    collateral_amount: Mapped[int] = mapped_column(BigInteger, nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="debt_positions")
    
    def calculate_current_debt(self, current_borrow_index: int) -> int:
        """
        Calculate current debt including accrued interest.
        
        Formula:
            current_debt = principal * (current_index / initial_index)
        
        Args:
            current_borrow_index: Current variableBorrowIndex from reserve
        
        Returns:
            Current debt amount in satoshis
        """
        if self.borrow_index_at_open == 0:
            return self.principal
        
        # Use RAY math for precision
        return ray_mul(
            self.principal,
            ray_div(current_borrow_index, self.borrow_index_at_open)
        )
    
    def calculate_accrued_interest(self, current_borrow_index: int) -> int:
        """
        Calculate accrued interest on debt.
        
        Args:
            current_borrow_index: Current variableBorrowIndex
        
        Returns:
            Accrued interest in satoshis
        """
        current_debt = self.calculate_current_debt(current_borrow_index)
        return current_debt - self.principal
    
    def __repr__(self) -> str:
        return (
            f"<DebtPosition(id={self.id}, user_id={self.user_id}, "
            f"borrowed={self.borrowed_asset_id[:8]}..., "
            f"collateral={self.collateral_asset_id[:8]}..., "
            f"principal={self.principal}, collateral_amount={self.collateral_amount})>"
        )
