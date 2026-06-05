from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "QuantCore AI"
    APP_ENV: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://quantcore:quantcore@localhost:5432/quantcore"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Auth
    SECRET_KEY: str = "changeme-in-production-use-vault"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    # Brokers (loaded from Vault/Secrets Manager in prod)
    ALPACA_API_KEY: str = ""
    ALPACA_API_SECRET: str = ""
    ALPACA_BASE_URL: str = "https://paper-api.alpaca.markets"

    OANDA_ACCOUNT_ID: str = ""
    OANDA_ACCESS_TOKEN: str = ""
    OANDA_ENVIRONMENT: Literal["practice", "live"] = "practice"

    IB_HOST: str = "127.0.0.1"
    IB_PORT: int = 7497
    IB_CLIENT_ID: int = 1

    # Data APIs
    ALPHA_VANTAGE_KEY: str = ""
    FRED_API_KEY: str = ""
    NEWS_API_KEY: str = ""
    UNUSUAL_WHALES_KEY: str = ""
    SIMFIN_API_KEY: str = ""

    # AI / LLM
    ANTHROPIC_API_KEY: str = ""

    # Notifications
    SENDGRID_API_KEY: str = ""
    SENDGRID_FROM_EMAIL: str = "reports@quantcore.ai"
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_FROM_NUMBER: str = ""

    # AWS
    AWS_REGION: str = "us-east-1"
    S3_BUCKET_REPORTS: str = "quantcore-reports"
    S3_BUCKET_MODELS: str = "quantcore-models"

    # Risk defaults
    MAX_RISK_PER_TRADE_PCT: float = 1.0
    MAX_DAILY_DRAWDOWN_PCT: float = 3.0
    MAX_WEEKLY_DRAWDOWN_PCT: float = 5.0
    MAX_OPEN_POSITIONS: int = 8
    MARGIN_CAP_PCT: float = 20.0
    CIRCUIT_BREAKER_PCT: float = 7.0

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"


settings = Settings()
