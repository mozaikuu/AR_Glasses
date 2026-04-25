from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    api_title: str = "NMU Smart Bus Tracking API"
    api_version: str = "0.1.0"
    api_description: str = (
        "Prototype MVP backend for Smart University Bus Tracking integrated with Cerebro."
    )
    database_url: str = Field(
        default="sqlite:///./data/bus_tracking.db",
        description="SQLAlchemy database URL. Replace with PostgreSQL URL in production.",
    )
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    simulation_tick_seconds: int = 3
    trip_fee_egp: float = 12.0
    monthly_subscription_fee_egp: float = 180.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
