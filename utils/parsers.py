from datetime import datetime

def get_latest_daily_summary(daily_data):
    return sorted(daily_data, key=lambda x: x["summary_date"])[-1]

def prepare_equity_curve(daily_data):
    sorted_data = sorted(daily_data, key=lambda x: x["summary_date"])
    dates = [d["summary_date"] for d in sorted_data]
    equity = [d["total_equity"] for d in sorted_data]
    return dates, equity

def get_latest_activity_trades(trade_log):
    trades = list(trade_log.values())
    if not trades:
        return [], None

    valid_trades = []
    for trade in trades:
        sell_date = trade.get("sell_date")
        if not sell_date:
            continue
        try:
            sell_dt = datetime.strptime(sell_date, "%Y-%m-%d %H:%M")
            valid_trades.append((sell_dt, trade))
        except ValueError:
            continue

    if not valid_trades:
        return [], None

    latest_date = max(dt.date() for dt, _ in valid_trades)

    latest_trades = [
        trade for dt, trade in valid_trades
        if dt.date() == latest_date
    ]

    latest_trades = sorted(
        latest_trades,
        key=lambda x: x["sell_date"],
        reverse=True
    )

    return latest_trades, latest_date.strftime("%Y-%m-%d")

def parse_path_data(path_data):
    """
    Converts path.json into a cleaner list of open positions.
    Example raw value:
    'bollex1 6.48 2026-03-24, '
    """
    positions = []

    for symbol, raw_value in path_data.items():
        cleaned = raw_value.replace(",", "").strip()
        parts = cleaned.split()

        if len(parts) < 3:
            continue

        strategy_stage = parts[0]
        entry_price = float(parts[1])
        entry_date = parts[2]

        positions.append({
            "symbol": symbol,
            "strategy_stage": strategy_stage,
            "entry_price": entry_price,
            "entry_date": entry_date,
        })

    return sorted(positions, key=lambda x: x["symbol"])

def get_latest_1300_close_for_symbol(symbol, data_center):
    """
    For a given symbol, find the most recent available 13:00 row.
    This is better than forcing today's date only, because it still works
    if today's 13:00 bar isn't present yet.
    """
    rows = data_center.get(symbol, [])
    if not rows:
        return None

    thirteen_rows = []
    for row in rows:
        date_str = row.get("Date")
        close_val = row.get("Close")

        if not date_str or close_val is None:
            continue

        try:
            dt = datetime.strptime(date_str, "%Y/%m/%d %H:%M")
        except ValueError:
            continue

        if dt.hour == 13 and dt.minute == 0:
            thirteen_rows.append({
                "datetime": dt,
                "close": float(close_val),
                "date_str": date_str,
            })

    if not thirteen_rows:
        return None

    latest = max(thirteen_rows, key=lambda x: x["datetime"])
    return latest

def build_open_positions_snapshot(path_data, data_center):
    """
    Builds dashboard-friendly open positions data including current price
    and unrealized P/L based on latest available 13:00 close.
    """
    positions = parse_path_data(path_data)
    snapshot = []

    for pos in positions:
        symbol = pos["symbol"]
        entry_price = pos["entry_price"]

        latest_close_row = get_latest_1300_close_for_symbol(symbol, data_center)

        current_price = None
        price_timestamp = None
        unrealized_pl = None
        unrealized_pl_pct = None

        if latest_close_row is not None:
            current_price = latest_close_row["close"]
            price_timestamp = latest_close_row["date_str"]
            unrealized_pl = current_price - entry_price
            unrealized_pl_pct = (unrealized_pl / entry_price) if entry_price else None

        snapshot.append({
            "symbol": symbol,
            "entry_price": entry_price,
            "entry_date": pos["entry_date"],
            "current_price": current_price,
            "unrealized_pl": unrealized_pl,
            "unrealized_pl_pct": unrealized_pl_pct,
            "price_timestamp": price_timestamp,
        })

    return snapshot