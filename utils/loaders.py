import json
from pathlib import Path

import streamlit as st


# Project root = folder where INTRODUCTION.py lives
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

DAILY_SUMMARY_FILE = DATA_DIR / "daily_summary_log.json"
MONTHLY_LOG_FILE = DATA_DIR / "monthly_log.json"
TRADE_LOG_FILE = DATA_DIR / "trade_log.json"
OPEN_POSITIONS_FILE = DATA_DIR / "open_positions_live.json"


def get_file_modified_time(file_path):
    """
    Returns the file's last modified time.

    This is used as part of the cache key so Streamlit reloads the file
    when the JSON file actually changes.
    """
    if not file_path.exists():
        return None

    return file_path.stat().st_mtime


@st.cache_data(show_spinner=False)
def load_json_file_cached(file_path_str, default, modified_time):
    """
    Cached JSON loader.

    file_path_str is used instead of Path because Streamlit caching handles
    simple strings more reliably.
    
    modified_time is intentionally included so the cache refreshes whenever
    the file changes.
    """
    file_path = Path(file_path_str)

    if not file_path.exists():
        print(f"[Missing file] {file_path}")
        return default

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_json_file(file_path, default):
    modified_time = get_file_modified_time(file_path)

    return load_json_file_cached(
        str(file_path),
        default,
        modified_time
    )


def load_daily_summary():
    return load_json_file(DAILY_SUMMARY_FILE, [])


def load_monthly_log():
    return load_json_file(MONTHLY_LOG_FILE, [])


def load_trade_log():
    return load_json_file(TRADE_LOG_FILE, {})


def load_open_positions_live():
    return load_json_file(OPEN_POSITIONS_FILE, {"positions": []})