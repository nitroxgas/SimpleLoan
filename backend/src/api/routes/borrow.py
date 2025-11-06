"""
Borrow and repay API routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from ...api.schemas.borrow import BorrowIntent, BorrowResponse, RepayIntent
from ...services.debt_service import DebtService
from ..dependencies import get_db_session

router = APIRouter()


@router.post(
    "/borrow",
    response_model=BorrowResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Borrow Assets Against Collateral",
    description="""
    Borrow assets by locking collateral in a debt position.
    
    ## Process Flow
    1. Validates collateral and borrow amounts
    2. Checks available liquidity in borrow reserve
    3. Validates Loan-to-Value (LTV) ratio ≤ 75%
    4. Creates debt position linked to collateral
    5. Updates reserve state (decreases liquidity, increases borrowed)
    6. Calculates initial health factor
    7. Returns position details with health factor
    
    ## LTV Calculation
    ```
    LTV = borrow_value / collateral_value
    Max LTV = 75%
    ```
    
    ## Health Factor
    ```
    Health Factor = (collateral_value * liquidation_threshold) / debt_value
    Liquidation Threshold = 80%
    Safe: HF >= 1.0
    Liquidatable: HF < 1.0
    ```
    
    ## Example (Borrow USDT with BTC collateral)
    ```json
    {
      "user_address": "lq1qq2xm7k0kz23r24h0v5s...",
      "collateral_asset_id": "6f0279e9ed041c3d...",
      "collateral_amount": 100000000,
      "borrow_asset_id": "ce091c998b83c78b...",
      "borrow_amount": 50000000000
    }
    ```
    
    ## Risk Parameters
    - Maximum LTV: 75%
    - Liquidation Threshold: 80%
    - Liquidation Bonus: 5%
    """,
    responses={
        201: {
            "description": "Borrow successful",
            "content": {
                "application/json": {
                    "example": {
                        "position_id": 1,
                        "user_address": "lq1qq2xm7k0kz23r24h0v5s...",
                        "collateral_amount": 100000000,
                        "borrow_amount": 50000000000,
                        "health_factor": 1920000000000000000000000000,
                        "current_debt": 50000000000,
                        "tx_id": "f6a1b2c3d4e5..."
                    }
                }
            }
        },
        400: {"description": "Invalid request (LTV too high, insufficient liquidity, etc.)"},
        500: {"description": "Internal server error during borrow"}
    },
    tags=["Borrow & Repay"]
)
async def borrow_assets(
    intent: BorrowIntent,
    session: AsyncSession = Depends(get_db_session),
) -> BorrowResponse:
    """Borrow assets by locking collateral."""
    try:
        logger.info(
            f"Borrow request: user={intent.user_address}, "
            f"collateral={intent.collateral_amount}, "
            f"borrow={intent.borrow_amount}"
        )
        
        debt_service = DebtService(session)
        
        # Create borrow position
        position = await debt_service.borrow(
            user_address=intent.user_address,
            collateral_asset_id=intent.collateral_asset_id,
            collateral_amount=intent.collateral_amount,
            borrow_asset_id=intent.borrow_asset_id,
            borrow_amount=intent.borrow_amount,
        )
        
        # Calculate health factor
        health_factor = await debt_service.calculate_health_factor(intent.user_address)
        
        logger.info(
            f"Borrow successful: position_id={position.id}, "
            f"health_factor={health_factor}"
        )
        
        return BorrowResponse(
            position_id=position.id,
            user_address=intent.user_address,
            collateral_asset_id=intent.collateral_asset_id,
            collateral_amount=intent.collateral_amount,
            borrowed_asset_id=intent.borrow_asset_id,
            borrowed_amount=intent.borrow_amount,
            health_factor=health_factor or 0,
            tx_id=None,  # TODO: Implement actual transaction
        )
    
    except ValueError as e:
        logger.warning(f"Borrow validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except Exception as e:
        logger.error(f"Borrow error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process borrow"
        )


@router.post("/repay", status_code=status.HTTP_200_OK)
async def repay_debt(
    intent: RepayIntent,
    session: AsyncSession = Depends(get_db_session),
):
    """
    Repay borrowed assets (partial or full).
    
    Note: Full implementation pending. This is a stub for MVP.
    
    Args:
        intent: Repay intent with position and amount
        session: Database session
    
    Returns:
        Repayment confirmation
    
    Raises:
        HTTPException: Not implemented yet
    """
    logger.info(
        f"Repay request: user={intent.user_address}, "
        f"position={intent.position_id}, amount={intent.repay_amount}"
    )
    
    # TODO: Implement repayment logic
    # 1. Get debt position
    # 2. Calculate current debt
    # 3. Validate repay amount
    # 4. Update debt or close position
    # 5. Return collateral if full repayment
    
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Repayment not yet implemented in MVP"
    )
