import json
from config import (
    DAILY_SUMMARY_FILE,
    MONTHLY_LOG_FILE,
    PATH_FILE,
    TRADE_LOG_FILE,
    DATA_CENTER_FILE,
    OPEN_POSITIONS_LIVE_FILE,
)

def load_daily_summary():
    with open(DAILY_SUMMARY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def load_monthly_log():
    with open(MONTHLY_LOG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def load_path_data():
    with open(PATH_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def load_trade_log():
    with open(TRADE_LOG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def load_data_center():
    with open(DATA_CENTER_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
    
def load_open_positions_live():
    with open(OPEN_POSITIONS_LIVE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)    