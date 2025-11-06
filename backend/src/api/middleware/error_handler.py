"""
Error handling middleware for FastAPI.
"""

from typing import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from loguru import logger


class FantasmaException(Exception):
    """Base exception for Fantasma protocol errors."""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_ERROR",
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)


class InsufficientLiquidityError(FantasmaException):
    """Raised when reserve has insufficient liquidity."""
    
    def __init__(self, message: str = "Insufficient liquidity in reserve"):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="INSUFFICIENT_LIQUIDITY",
        )


class UnhealthyPositionError(FantasmaException):
    """Raised when position health factor is too low."""
    
    def __init__(self, message: str = "Position health factor below threshold"):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="UNHEALTHY_POSITION",
        )


class InvalidCollateralError(FantasmaException):
    """Raised when collateral is invalid or insufficient."""
    
    def __init__(self, message: str = "Invalid or insufficient collateral"):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="INVALID_COLLATERAL",
        )


class StaleOraclePriceError(FantasmaException):
    """Raised when oracle price is stale."""
    
    def __init__(self, message: str = "Oracle price is stale"):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="STALE_ORACLE_PRICE",
        )


class UTXORaceConditionError(FantasmaException):
    """Raised when UTXO race condition detected."""
    
    def __init__(self, message: str = "UTXO already spent, retry with updated state"):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            error_code="UTXO_RACE_CONDITION",
        )


class PositionNotFoundError(FantasmaException):
    """Raised when position not found."""
    
    def __init__(self, message: str = "Position not found"):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="POSITION_NOT_FOUND",
        )


async def error_handler_middleware(
    request: Request,
    call_next: Callable
) -> Response:
    """
    Global error handling middleware.
    
    Catches all exceptions and returns structured JSON responses.
    """
    try:
        response = await call_next(request)
        return response
    
    except FantasmaException as e:
        logger.warning(
            f"Fantasma error: {e.error_code} - {e.message} "
            f"(path: {request.url.path})"
        )
        return JSONResponse(
            status_code=e.status_code,
            content={
                "error": {
                    "code": e.error_code,
                    "message": e.message,
                }
            },
        )
    
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)} (path: {request.url.path})")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": str(e),
                }
            },
        )
    
    except Exception as e:
        logger.error(
            f"Unhandled exception: {type(e).__name__}: {str(e)} "
            f"(path: {request.url.path})",
            exc_info=True,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An internal error occurred",
                }
            },
        )
