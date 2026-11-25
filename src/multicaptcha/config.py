from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    api_key: str = ""
    log_level: str = "INFO"
    browser_headless: bool = False
    max_concurrent_solves: int = 2
    solve_timeout_seconds: float = 120
    whisper_model: str = "small"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
