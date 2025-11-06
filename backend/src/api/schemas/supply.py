"""
Pydantic schemas for supply operations.
"""

from pydantic import BaseModel, Field, field_validator


class SupplyIntent(BaseModel):
    """
    Intent to supply assets to a lending pool.
    
    Attributes:
        user_address: User's Liquid address
        asset_id: Asset to supply (Liquid asset ID)
        amount: Amount to supply in satoshis
        signature: Transaction signature (optional for MVP)
    """
    
    user_address: str = Field(
        ...,
        description="User's Liquid address",
        min_length=10,
        max_length=100
    )
    
    asset_id: str = Field(
        ...,
        description="Liquid asset ID (hex)",
        min_length=10,
        max_length=100
    )
    
    amount: int = Field(
        ...,
        description="Amount to supply (satoshis)",
        gt=0
    )
    
    signature: str | None = Field(
        default=None,
        description="Transaction signature (optional)"
    )
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v: int) -> int:
        """Validate supply amount is positive."""
        if v <= 0:
            raise ValueError("Amount must be positive")
        if v < 1000:  # Minimum 1000 satoshis
            raise ValueError("Amount must be at least 1000 satoshis")
        return v


class WithdrawIntent(BaseModel):
    """
    Intent to withdraw supplied assets.
    
    Attributes:
        user_address: User's Liquid address
        asset_id: Asset to withdraw
        amount: Amount to withdraw in satoshis (0 = withdraw all)
        signature: Transaction signature (optional for MVP)
    """
    
    user_address: str = Field(
        ...,
        description="User's Liquid address",
        min_length=10,
        max_length=100
    )
    
    asset_id: str = Field(
        ...,
        description="Liquid asset ID (hex)",
        min_length=10,
        max_length=100
    )
    
    amount: int = Field(
        ...,
        description="Amount to withdraw (satoshis), 0 for all",
        ge=0
    )
    
    signature: str | None = Field(
        default=None,
        description="Transaction signature (optional)"
    )


class SupplyResponse(BaseModel):
    """
    Response for supply operation.
    
    Attributes:
        position_id: Created position ID
        user_address: User's address
        asset_id: Asset supplied
        amount_supplied: Amount supplied (satoshis)
        atoken_amount: aTokens minted
        liquidity_index: Index at supply time
        tx_id: Transaction ID (if broadcast)
    """
    
    position_id: int
    user_address: str
    asset_id: str
    amount_supplied: int
    atoken_amount: int
    liquidity_index: int
    tx_id: str | None = None
    
    class Config:
        from_attributes = True


class WithdrawResponse(BaseModel):
    """
    Response for withdraw operation.
    
    Attributes:
        user_address: User's address
        asset_id: Asset withdrawn
        amount_withdrawn: Underlying amount withdrawn (satoshis)
        atoken_burned: aTokens burned
        liquidity_index: Index at withdrawal time
        tx_id: Transaction ID (if broadcast)
    """
    
    user_address: str
    asset_id: str
    amount_withdrawn: int
    atoken_burned: int
    liquidity_index: int
    tx_id: str | None = None
    
    class Config:
        from_attributes = True


class PositionResponse(BaseModel):
    """
    Response for position query.
    
    Attributes:
        position_id: Position ID
        user_address: User's address
        asset_id: Asset supplied
        atoken_amount: aTokens held
        underlying_amount: Current underlying value
        accrued_interest: Interest earned
        liquidity_index_at_supply: Index when supplied
        current_liquidity_index: Current index
        created_at: Position creation time
    """
    
    position_id: int
    user_address: str
    asset_id: str
    atoken_amount: int
    underlying_amount: int
    accrued_interest: int
    liquidity_index_at_supply: int
    current_liquidity_index: int
    created_at: str
    
    class Config:
        from_attributes = True
