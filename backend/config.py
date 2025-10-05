from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str = "dummy"  # Users provide their own keys
    openai_api_key: str = "dummy"  # Users provide their own keys
    news_api_key: str = ""
    chroma_persist_dir: str = "./chroma_data"
    projects_csv: str = "./data/flood_control__floodcontrol_data__0__20251004_233415.csv"
    cors_origins: str = "*"  # Allow all origins for deployed app
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra env vars from Render


settings = Settings()