"""
Fantasma Protocol - Main FastAPI Application

AAVE-inspired lending protocol on Liquid Network with formal verification.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings

# Create FastAPI app
app = FastAPI(
    title="Fantasma Protocol API",
    description="UTXO-based lending protocol on Liquid Network",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint - API health check."""
    return {
        "name": "Fantasma Protocol API",
        "version": "0.1.0",
        "status": "operational",
        "network": settings.NETWORK,
    }


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


# Import and include routers
from .api.routes import supply, positions, borrow, liquidate, reserves

app.include_router(supply.router, prefix="/api/v1", tags=["supply"])
app.include_router(positions.router, prefix="/api/v1", tags=["positions"])
app.include_router(borrow.router, prefix="/api/v1", tags=["borrow"])
app.include_router(liquidate.router, prefix="/api/v1", tags=["liquidation"])
app.include_router(reserves.router, prefix="/api/v1", tags=["reserves"])

# TODO: Add remaining routers as user stories are implemented
# from .api.routes import borrow, liquidate, reserves
# app.include_router(borrow.router, prefix="/api/v1", tags=["borrow"])
# app.include_router(liquidate.router, prefix="/api/v1", tags=["liquidate"])
# app.include_router(reserves.router, prefix="/api/v1", tags=["reserves"])
