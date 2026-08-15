from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
