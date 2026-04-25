import json
from pathlib import Path


# Project root = folder where INTRODUCTION.py lives
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

DAILY_SUMMARY_FILE = DATA_DIR / "daily_summary_log.json"
MONTHLY_LOG_FILE = DATA_DIR / "monthly_log.json"
TRADE_LOG_FILE = DATA_DIR / "trade_log.json"
OPEN_POSITIONS_FILE = DATA_DIR / "open_positions_live.json"


def load_json_file(file_path, default):
    if not file_path.exists():
        print(f"[Missing file] {file_path}")
        return default

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_daily_summary():
    return load_json_file(DAILY_SUMMARY_FILE, [])


def load_monthly_log():
    return load_json_file(MONTHLY_LOG_FILE, [])


def load_trade_log():
    return load_json_file(TRADE_LOG_FILE, {})


def load_open_positions_live():
    return load_json_file(OPEN_POSITIONS_FILE, {"positions": []})