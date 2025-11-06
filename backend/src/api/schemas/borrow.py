"""
Pydantic schemas for borrow operations.
"""

from pydantic import BaseModel, Field


class BorrowIntent(BaseModel):
    """Intent to borrow assets against collateral."""
    
    user_address: str = Field(
        ...,
        description="User's Liquid address",
        min_length=10,
        max_length=100
    )
    
    collateral_asset_id: str = Field(
        ...,
        description="Asset used as collateral",
        min_length=10,
        max_length=100
    )
    
    collateral_amount: int = Field(
        ...,
        description="Amount of collateral (satoshis)",
        gt=0
    )
    
    borrow_asset_id: str = Field(
        ...,
        description="Asset to borrow",
        min_length=10,
        max_length=100
    )
    
    borrow_amount: int = Field(
        ...,
        description="Amount to borrow (satoshis)",
        gt=0
    )


class RepayIntent(BaseModel):
    """Intent to repay borrowed assets."""
    
    user_address: str = Field(
        ...,
        description="User's Liquid address",
        min_length=10,
        max_length=100
    )
    
    position_id: int = Field(
        ...,
        description="Debt position ID",
        gt=0
    )
    
    repay_amount: int = Field(
        ...,
        description="Amount to repay (satoshis), 0 for full repayment",
        ge=0
    )


class BorrowResponse(BaseModel):
    """Response for borrow operation."""
    
    position_id: int
    user_address: str
    collateral_asset_id: str
    collateral_amount: int
    borrowed_asset_id: str
    borrowed_amount: int
    health_factor: int
    tx_id: str | None = None
    
    class Config:
        from_attributes = True


class DebtPositionResponse(BaseModel):
    """Response for debt position query."""
    
    position_id: int
    user_address: str
    borrowed_asset_id: str
    collateral_asset_id: str
    principal: int
    current_debt: int
    accrued_interest: int
    collateral_amount: int
    health_factor: int
    created_at: str
    
    class Config:
        from_attributes = True
