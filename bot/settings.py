import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN пустой в .env")

raw_ids = os.getenv("ALLOWED_USER_IDS")
if not raw_ids:
    raise RuntimeError("ALLOWED_USER_IDS пустой в .env")

ALLOWED_USER_IDS = set(int(user_id) for user_id in raw_ids.split(",") if user_id != "")
MAX_VIDEO_SIZE = 100 * 1024 * 1024
MAX_VIDEO_DURATION = 60
BASE_DIR = Path(__file__).resolve().parent.parent
JOBS_DIR = BASE_DIR / "data" / "jobs"