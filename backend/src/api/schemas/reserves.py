from pydantic import BaseModel


class ReserveResponse(BaseModel):
    asset_id: str
    utxo_id: str
    total_liquidity: int
    total_borrowed: int
    liquidity_index: int
    variable_borrow_index: int
    current_liquidity_rate: int
    current_variable_borrow_rate: int
    last_update_timestamp: int
    reserve_factor: int
    utilization: int

    class Config:
        from_attributes = True
