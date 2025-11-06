"""
Liquidation API routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from ...api.schemas.liquidate import (
    LiquidatablePosition,
    LiquidateIntent,
    LiquidationResponse,
)
from ...services.debt_service import DebtService
from ..dependencies import get_db_session

router = APIRouter()


@router.get(
    "/positions/liquidatable",
    response_model=list[LiquidatablePosition],
    status_code=status.HTTP_200_OK,
)
async def get_liquidatable_positions(
    session: AsyncSession = Depends(get_db_session),
) -> list[LiquidatablePosition]:
    """Return positions with health factor < 1.0."""
    try:
        debt_service = DebtService(session)
        positions = await debt_service.get_liquidatable_positions()
        return [LiquidatablePosition(**pos) for pos in positions]

    except Exception as e:
        logger.error(f"Error fetching liquidatable positions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch liquidatable positions",
        )


@router.post(
    "/liquidate",
    response_model=LiquidationResponse,
    status_code=status.HTTP_200_OK,
)
async def liquidate_position(
    intent: LiquidateIntent,
    session: AsyncSession = Depends(get_db_session),
) -> LiquidationResponse:
    """Liquidate an unhealthy position."""
    try:
        debt_service = DebtService(session)
        result = await debt_service.liquidate(
            liquidator_address=intent.liquidator_address,
            position_id=intent.position_id,
            repay_amount=intent.repay_amount,
        )

        return LiquidationResponse(**result)

    except ValueError as e:
        logger.warning(f"Liquidation validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    except Exception as e:
        logger.error(f"Liquidation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process liquidation",
        )
