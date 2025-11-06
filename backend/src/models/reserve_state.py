"""
ReserveState model for tracking on-chain reserve UTXO state.
"""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class ReserveState(Base, TimestampMixin):
    """
    Off-chain mirror of Reserve UTXO state.
    
    Tracks the current state of a lending pool reserve for a specific asset.
    This mirrors the on-chain Reserve UTXO (~320 bytes).
    
    Attributes:
        id: Primary key
        asset_id: Liquid asset ID (hex string)
        utxo_id: Current Reserve UTXO txid:vout
        total_liquidity: Total supplied assets in satoshis
        total_borrowed: Total borrowed assets in satoshis
        liquidity_index: Cumulative supply interest index (RAY)
        variable_borrow_index: Cumulative borrow interest index (RAY)
        current_liquidity_rate: Current supply APY in RAY
        current_variable_borrow_rate: Current borrow APY in RAY
        last_update_timestamp: Last index update time (Unix timestamp)
        reserve_factor: Protocol fee percentage in RAY (e.g., 0.1 * RAY = 10%)
    """
    
    __tablename__ = "reserve_states"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Asset identifier (Liquid asset ID hex)
    asset_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
        comment="Liquid asset ID"
    )
    
    # Current Reserve UTXO reference (txid:vout)
    utxo_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Current Reserve UTXO (txid:vout)"
    )
    
    # Liquidity amounts (in satoshis)
    total_liquidity: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
        comment="Total supplied assets (satoshis)"
    )
    
    total_borrowed: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
        comment="Total borrowed assets (satoshis)"
    )
    
    # Cumulative indices (RAY precision 10^27)
    liquidity_index: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        comment="Cumulative supply interest index (RAY)"
    )
    
    variable_borrow_index: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        comment="Cumulative borrow interest index (RAY)"
    )
    
    # Current rates (RAY precision, per second)
    current_liquidity_rate: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
        comment="Current supply rate per second (RAY)"
    )
    
    current_variable_borrow_rate: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
        comment="Current borrow rate per second (RAY)"
    )
    
    # Timestamp of last update (Unix timestamp)
    last_update_timestamp: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        comment="Last update timestamp (Unix seconds)"
    )
    
    # Protocol fee (RAY precision)
    reserve_factor: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        comment="Protocol fee percentage (RAY)"
    )
    
    @property
    def available_liquidity(self) -> int:
        """Calculate available liquidity for borrowing."""
        return max(0, self.total_liquidity - self.total_borrowed)
    
    @property
    def utilization_rate(self) -> int:
        """
        Calculate utilization rate in RAY.
        
        Formula: total_borrowed / total_liquidity
        Returns 0 if no liquidity.
        """
        if self.total_liquidity == 0:
            return 0
        
        from ..utils.ray_math import RAY
        return (self.total_borrowed * RAY) // self.total_liquidity
    
    def __repr__(self) -> str:
        return (
            f"<ReserveState(asset_id={self.asset_id[:8]}..., "
            f"liquidity={self.total_liquidity}, "
            f"borrowed={self.total_borrowed})>"
        )
