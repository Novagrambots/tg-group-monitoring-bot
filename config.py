from dataclasses import dataclass
import os
from dotenv import load_dotenv
load_dotenv()


@dataclass
class Config:

    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

    ADMIN_ID: int = int(os.getenv("ADMIN_ID", 0))

    DB_URL: str = "sqlite+aiosqlite:///monitor.db"  # Решил использовать SQLite для простоты

    REPORT_TIME: str = "01:00"

    TIMEZONE: str = "Asia/Tashkent"


config = Config()
