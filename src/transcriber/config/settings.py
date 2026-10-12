from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Audio Transcription Service"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    hf_token: str
    MODEL_NAME: str = "large-v3"
    DEVICE: str = "cpu"
    COMPUTE_TYPE: str = "int8"
    BEAM_SIZE: int = 5

    MAX_FILE_SIZE_MB: int = 100
    CHUNK_DURATION_SECONDS: int = 60

    # Environment configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()