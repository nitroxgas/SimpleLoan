"""
Position query API routes.
"""

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...api.schemas.supply import PositionResponse
from ...models.supply_position import SupplyPosition
from ...models.user import User
from ...services.reserve_service import ReserveService
from ..dependencies import get_db_session

router = APIRouter()


@router.get("/positions/{user_address}", response_model=List[PositionResponse])
async def get_user_positions(
    user_address: str,
    session: AsyncSession = Depends(get_db_session),
) -> List[PositionResponse]:
    """
    Get all supply positions for a user.
    
    Args:
        user_address: User's Liquid address
        session: Database session
    
    Returns:
        List of position responses with current values
    
    Raises:
        HTTPException: If user not found
    """
    try:
        logger.info(f"Fetching positions for user: {user_address}")
        
        # Get user
        result = await session.execute(
            select(User).where(User.address == user_address)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            # Return empty list if user doesn't exist yet
            logger.info(f"User {user_address} not found, returning empty positions")
            return []
        
        # Get all supply positions
        result = await session.execute(
            select(SupplyPosition).where(SupplyPosition.user_id == user.id)
        )
        positions = result.scalars().all()
        
        # Create reserve service for index queries
        reserve_service = ReserveService(session)
        
        # Build responses with current values
        responses = []
        for position in positions:
            # Get current reserve state
            reserve = await reserve_service.get_reserve_state_with_accrued_interest(
                position.asset_id
            )
            
            if not reserve:
                continue
            
            # Calculate current underlying amount
            underlying_amount = position.calculate_underlying_amount(
                reserve.liquidity_index
            )
            
            # Calculate accrued interest
            initial_amount = position.calculate_underlying_amount(
                position.liquidity_index_at_supply
            )
            accrued_interest = underlying_amount - initial_amount
            
            responses.append(
                PositionResponse(
                    position_id=position.id,
                    user_address=user_address,
                    asset_id=position.asset_id,
                    atoken_amount=position.atoken_amount,
                    underlying_amount=underlying_amount,
                    accrued_interest=accrued_interest,
                    liquidity_index_at_supply=position.liquidity_index_at_supply,
                    current_liquidity_index=reserve.liquidity_index,
                    created_at=position.created_at.isoformat(),
                )
            )
        
        logger.info(f"Found {len(responses)} positions for user {user_address}")
        return responses
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error fetching positions: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch positions"
        )
