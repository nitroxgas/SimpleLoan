"""
Configuration management using Pydantic settings.
"""

from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )
    
    # Elements/Liquid Network
    ELEMENTS_RPC_URL: str = "http://127.0.0.1:18884"
    ELEMENTS_RPC_USER: str = "liquiduser"
    ELEMENTS_RPC_PASSWORD: str = "liquidpass"
    NETWORK: str = "regtest"
    
    # Asset IDs (generated during setup)
    BTC_ASSET_ID: str = ""
    USDT_ASSET_ID: str = ""
    
    # Database
    DATABASE_URL: str = "sqlite:///./fantasma.db"
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Oracle
    ORACLE_URL: str = "http://localhost:8001"
    ORACLE_PUBKEYS: List[str] = []
    ORACLE_STALENESS_THRESHOLD: int = 600  # 10 minutes
    
    # Protocol Parameters (RAY precision)
    RAY: int = 10**27
    SECONDS_PER_YEAR: int = 31536000
    
    # Liquidation parameters
    LIQUIDATION_THRESHOLD: int = 800000000000000000000000000  # 0.8 * RAY (80%)
    LIQUIDATION_BONUS: int = 50000000000000000000000000  # 0.05 * RAY (5%)
    RESERVE_FACTOR: int = 100000000000000000000000000  # 0.1 * RAY (10%)
    
    # Interest Rate Model
    BASE_VARIABLE_BORROW_RATE: int = 20000000000000000000000000  # 0.02 * RAY (2%)
    OPTIMAL_UTILIZATION: int = 800000000000000000000000000  # 0.8 * RAY (80%)
    SLOPE_1: int = 40000000000000000000000000  # 0.04 * RAY (4%)
    SLOPE_2: int = 600000000000000000000000000  # 0.6 * RAY (60%)
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    
    # Development
    DEBUG: bool = False
    TEST_MODE: bool = False


# Global settings instance
settings = Settings()
