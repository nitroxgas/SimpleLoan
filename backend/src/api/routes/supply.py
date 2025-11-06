"""
Supply operation API routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from ...api.schemas.supply import (
    SupplyIntent,
    SupplyResponse,
    WithdrawIntent,
    WithdrawResponse,
)
from ...services.reserve_service import ReserveService
from ..dependencies import get_db_session

router = APIRouter()


@router.post(
    "/supply",
    response_model=SupplyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Supply Assets to Lending Pool",
    description="""
    Supply assets to the lending pool and receive aTokens representing your deposit.
    
    ## Process Flow
    1. Validates user address, asset ID, and amount
    2. Updates reserve interest indices based on time elapsed
    3. Calculates aToken amount based on current liquidity index
    4. Creates or updates supply position for the user
    5. Increments reserve total liquidity
    6. Returns position details with aToken balance
    
    ## aToken Calculation
    ```
    aToken_amount = amount / liquidity_index
    ```
    
    ## Interest Accrual
    Your aTokens automatically accrue interest as the liquidity index increases over time.
    No manual claim required - simply withdraw to realize gains.
    
    ## Minimum Amount
    - Minimum supply: 1,000 satoshis (0.00001 BTC)
    
    ## Example
    ```json
    {
      "user_address": "lq1qq2xm7k0kz23r24h0v5s...",
      "asset_id": "6f0279e9ed041c3d710a9f...",
      "amount": 100000000
    }
    ```
    """,
    responses={
        201: {
            "description": "Supply successful",
            "content": {
                "application/json": {
                    "example": {
                        "position_id": 1,
                        "user_address": "lq1qq2xm7k0kz23r24h0v5s...",
                        "asset_id": "6f0279e9ed041c3d710a9f...",
                        "amount_supplied": 100000000,
                        "atoken_amount": 99500000,
                        "liquidity_index": 1005000000000000000000000000,
                        "tx_id": "a1b2c3d4e5f6..."
                    }
                }
            }
        },
        400: {"description": "Invalid request (amount too small, invalid address, etc.)"},
        500: {"description": "Internal server error during supply processing"}
    },
    tags=["Supply & Withdraw"]
)
async def supply_assets(
    intent: SupplyIntent,
    session: AsyncSession = Depends(get_db_session),
) -> SupplyResponse:
    """Supply assets to lending pool and receive aTokens."""
    try:
        logger.info(
            f"Supply request: user={intent.user_address}, "
            f"asset={intent.asset_id[:8]}..., amount={intent.amount}"
        )
        
        # Create reserve service
        reserve_service = ReserveService(session)
        
        # Process supply
        position = await reserve_service.supply(
            user_address=intent.user_address,
            asset_id=intent.asset_id,
            amount=intent.amount,
        )
        
        # Get updated reserve state
        reserve = await reserve_service.get_reserve_state(intent.asset_id)
        
        return SupplyResponse(
            position_id=position.id,
            user_address=intent.user_address,
            asset_id=intent.asset_id,
            amount_supplied=intent.amount,
            atoken_amount=position.atoken_amount,
            liquidity_index=reserve.liquidity_index if reserve else 0,
            tx_id=None,  # TODO: Implement actual transaction broadcast
        )
    
    except ValueError as e:
        logger.warning(f"Supply validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except Exception as e:
        logger.error(f"Supply error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process supply"
        )


@router.post(
    "/withdraw",
    response_model=WithdrawResponse,
    status_code=status.HTTP_200_OK,
    summary="Withdraw Supplied Assets",
    description="""
    Withdraw supplied assets from the lending pool by burning aTokens.
    
    ## Process Flow
    1. Validates user has sufficient aToken balance
    2. Updates reserve interest indices
    3. Calculates withdrawal amount based on current liquidity index
    4. Burns aTokens from user's position
    5. Decreases reserve total liquidity
    6. Validates reserve remains solvent (borrowed ≤ liquidity)
    7. Returns withdrawal details
    
    ## Withdrawal Amount
    ```
    withdrawal_amount = aToken_amount * liquidity_index
    ```
    
    ## Full Withdrawal
    Set `amount` to 0 to withdraw your entire available balance.
    
    ## Constraints
    - Cannot withdraw more than supplied
    - Cannot reduce liquidity below total borrowed (solvency check)
    - Interest automatically included in withdrawal
    
    ## Example (Partial Withdrawal)
    ```json
    {
      "user_address": "lq1qq2xm7k0kz23r24h0v5s...",
      "asset_id": "6f0279e9ed041c3d710a9f...",
      "amount": 50000000
    }
    ```
    
    ## Example (Full Withdrawal)
    ```json
    {
      "user_address": "lq1qq2xm7k0kz23r24h0v5s...",
      "asset_id": "6f0279e9ed041c3d710a9f...",
      "amount": 0
    }
    ```
    """,
    responses={
        200: {
            "description": "Withdrawal successful",
            "content": {
                "application/json": {
                    "example": {
                        "user_address": "lq1qq2xm7k0kz23r24h0v5s...",
                        "asset_id": "6f0279e9ed041c3d710a9f...",
                        "amount_withdrawn": 50500000,
                        "atoken_burned": 50000000,
                        "liquidity_index": 1010000000000000000000000000,
                        "tx_id": "d4e5f6a1b2c3..."
                    }
                }
            }
        },
        400: {"description": "Invalid request (insufficient balance, would break solvency, etc.)"},
        500: {"description": "Internal server error during withdrawal"}
    },
    tags=["Supply & Withdraw"]
)
async def withdraw_assets(
    intent: WithdrawIntent,
    session: AsyncSession = Depends(get_db_session),
) -> WithdrawResponse:
    """Withdraw supplied assets by burning aTokens."""
    try:
        logger.info(
            f"Withdraw request: user={intent.user_address}, "
            f"asset={intent.asset_id[:8]}..., amount={intent.amount}"
        )

        reserve_service = ReserveService(session)
        amount_withdrawn, atoken_burned, liquidity_index = await reserve_service.withdraw(
            user_address=intent.user_address,
            asset_id=intent.asset_id,
            amount=intent.amount,
        )

        return WithdrawResponse(
            user_address=intent.user_address,
            asset_id=intent.asset_id,
            amount_withdrawn=amount_withdrawn,
            atoken_burned=atoken_burned,
            liquidity_index=liquidity_index,
            tx_id=None,
        )

    except ValueError as e:
        logger.warning(f"Withdraw validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Withdraw error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process withdraw"
        )
