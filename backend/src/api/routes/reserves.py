from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.reserve_state import ReserveState
from ..schemas.reserves import ReserveResponse
from ..dependencies import get_db_session

router = APIRouter()


def _to_response(reserve: ReserveState) -> ReserveResponse:
    return ReserveResponse(
        asset_id=reserve.asset_id,
        utxo_id=reserve.utxo_id,
        total_liquidity=reserve.total_liquidity,
        total_borrowed=reserve.total_borrowed,
        liquidity_index=reserve.liquidity_index,
        variable_borrow_index=reserve.variable_borrow_index,
        current_liquidity_rate=reserve.current_liquidity_rate,
        current_variable_borrow_rate=reserve.current_variable_borrow_rate,
        last_update_timestamp=reserve.last_update_timestamp,
        reserve_factor=reserve.reserve_factor,
        utilization=reserve.utilization_rate,
    )


@router.get("/reserves", response_model=List[ReserveResponse])
async def get_reserves(
    session: AsyncSession = Depends(get_db_session),
) -> List[ReserveResponse]:
    try:
        result = await session.execute(select(ReserveState))
        reserves = result.scalars().all()
        return [_to_response(r) for r in reserves]
    except Exception as e:
        logger.error(f"Failed to fetch reserves: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch reserves",
        )


@router.get("/reserves/{asset_id}", response_model=ReserveResponse)
async def get_reserve(
    asset_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> ReserveResponse:
    try:
        result = await session.execute(
            select(ReserveState).where(ReserveState.asset_id == asset_id)
        )
        reserve = result.scalar_one_or_none()
        if not reserve:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reserve not found")
        return _to_response(reserve)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch reserve {asset_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch reserve",
        )
