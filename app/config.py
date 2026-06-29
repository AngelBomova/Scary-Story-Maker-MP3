from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str = ""
    openai_text_model: str = "gpt-4.1-mini"
    openai_tts_model: str = "gpt-4o-mini-tts"
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = ""
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    output_dir: str = "generated"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def output_path(self) -> Path:
        return Path(self.output_dir)


@lru_cache
def get_settings() -> Settings:
    return Settings()
