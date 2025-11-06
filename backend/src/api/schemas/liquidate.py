"""
Pydantic schemas for liquidation operations.
"""

from pydantic import BaseModel, Field


class LiquidateIntent(BaseModel):
    """Intent to liquidate an unhealthy debt position."""

    liquidator_address: str = Field(
        ...,
        description="Liquidator's Liquid address",
        min_length=10,
        max_length=100,
    )

    position_id: int = Field(
        ...,
        description="Debt position ID to liquidate",
        gt=0,
    )

    repay_amount: int | None = Field(
        default=None,
        description="Amount to repay (satoshis). If omitted, repay full debt.",
        ge=0,
    )


class LiquidationResponse(BaseModel):
    """Response for liquidation operation."""

    position_id: int
    liquidator_address: str
    repaid_amount: int
    collateral_seized: int
    health_factor_after: int
    tx_id: str | None = None


class LiquidatablePosition(BaseModel):
    """Liquidatable position details."""

    position_id: int
    user_address: str
    borrowed_asset_id: str
    collateral_asset_id: str
    current_debt: int
    collateral_amount: int
    health_factor: int
