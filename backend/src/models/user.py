"""
User model for tracking protocol participants.
"""

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """
    User entity representing a protocol participant.
    
    Attributes:
        id: Primary key
        address: Liquid address (unique identifier)
        health_factor: Current health factor in RAY (10^27)
        supply_positions: Related supply positions
        debt_positions: Related debt positions
    """
    
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Liquid address (e.g., lq1q...)
    address: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    
    # Current health factor in RAY (10^27)
    # health_factor = (collateral_value * liquidation_threshold) / debt_value
    # Healthy if >= 1.0 * RAY
    health_factor: Mapped[int] = mapped_column(
        BigInteger,
        nullable=True,
        comment="Health factor in RAY precision (10^27)"
    )
    
    # Relationships
    supply_positions: Mapped[list["SupplyPosition"]] = relationship(
        "SupplyPosition",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    debt_positions: Mapped[list["DebtPosition"]] = relationship(
        "DebtPosition",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<User(address={self.address}, health_factor={self.health_factor})>"
