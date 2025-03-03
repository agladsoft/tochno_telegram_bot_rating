import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    TELEGRAM_BOT_TOKEN: str | None = os.getenv("TELEGRAM_BOT_TOKEN")
    URL_TOP: str | None = os.getenv("URL_TOP")
    URL_VOTE: str | None = os.getenv("URL_VOTE")
    COMPARE_RATING: float | None = os.getenv("COMPARE_RATING")
    DELTA_THRESHOLD: int | None = os.getenv("DELTA_THRESHOLD")
    PROXY: str | None = os.getenv("PROXY")
    USER_ID: int | None = os.getenv("USER_ID")
    REDIS_URL: str | None = os.getenv("REDIS_URL")


def get_settings():
    load_dotenv(override=True)
    return Settings()



