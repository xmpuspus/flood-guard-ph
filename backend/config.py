from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str
    openai_api_key: str
    news_api_key: str = ""
    chroma_persist_dir: str = "./chroma_data"
    projects_csv: str = "./data/projects.csv"
    cors_origins: str = "http://localhost:3000,http://localhost:8000"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()