import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    TELEGRAM_BOT_TOKEN: str | None = os.getenv("TELEGRAM_BOT_TOKEN")
    URL_TOP: str | None = os.getenv("URL_TOP")
    URL_VOTE: str | None = os.getenv("URL_VOTE")
    COMPARE_RATING: float | None = os.getenv("COMPARE_RATING")


def get_settings():
    return Settings()


setting = get_settings()
