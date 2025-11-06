"""
SupplyPosition model for tracking user supply positions.
"""

from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class SupplyPosition(Base, TimestampMixin):
    """
    User's supply position in a lending pool.
    
    Tracks aToken holdings which represent a share of the reserve pool.
    The underlying value grows via liquidityIndex (cumulative interest).
    
    Attributes:
        id: Primary key
        user_id: Foreign key to User
        asset_id: Liquid asset ID being supplied
        atoken_amount: Amount of aTokens held (constant)
        liquidity_index_at_supply: Index when position was created
        user: Relationship to User model
    """
    
    __tablename__ = "supply_positions"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Foreign key to users table
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Asset being supplied (Liquid asset ID)
    asset_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        comment="Liquid asset ID"
    )
    
    # aToken amount (stays constant, value grows via index)
    atoken_amount: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        comment="aToken amount held (satoshis)"
    )
    
    # Liquidity index when position was created (for interest calculation)
    liquidity_index_at_supply: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        comment="Liquidity index at supply time (RAY)"
    )
    
    # Relationship to User
    user: Mapped["User"] = relationship("User", back_populates="supply_positions")
    
    def calculate_underlying_amount(self, current_liquidity_index: int) -> int:
        """
        Calculate current underlying asset amount.
        
        Formula: atoken_amount * current_index / index_at_supply
        
        Args:
            current_liquidity_index: Current reserve liquidity index
        
        Returns:
            Underlying asset amount in satoshis
        """
        from ..utils.ray_math import ray_mul, ray_div, RAY
        
        # Normalize aToken to underlying
        # underlying = atoken * (current_index / initial_index)
        index_ratio = ray_div(current_liquidity_index, self.liquidity_index_at_supply)
        underlying = ray_mul(self.atoken_amount * RAY, index_ratio) // RAY
        
        return underlying
    
    def __repr__(self) -> str:
        return (
            f"<SupplyPosition(user_id={self.user_id}, "
            f"asset_id={self.asset_id[:8]}..., "
            f"atoken_amount={self.atoken_amount})>"
        )
