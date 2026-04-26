import streamlit as st
import pandas as pd

from utils.loaders import load_daily_summary, load_open_positions_live, load_trade_log
from utils.parsers import get_latest_daily_summary


# ---------- PAGE PATHS ----------
PAGE_OVERVIEW = "pages/1_OVERVIEW.py"
PAGE_ACTIVITY = "pages/2_ACTIVITY.py"
PAGE_PERFORMANCE = "pages/3_PERFORMANCE.py"
PAGE_HISTORY = "pages/4_HISTORY.py"

# ---------- THEME ----------
st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
    background-color: #0B0F0C;
}

[data-testid="stSidebar"] {
    background-color: #111814;
}

/* Mobile/sidebar navigation text */
[data-testid="stSidebar"] * {
    color: #E8F5E9 !important;
}

[data-testid="stSidebar"] a {
    color: #E8F5E9 !important;
}

[data-testid="stSidebar"] a p {
    color: #E8F5E9 !important;
    font-weight: 800 !important;
}

[data-testid="stSidebar"] a[aria-current="page"] {
    background-color: rgba(212, 175, 55, 0.16) !important;
    border-radius: 10px;
}

[data-testid="stSidebar"] a[aria-current="page"] p {
    color: #D4AF37 !important;
}

html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Segoe UI", sans-serif !important;
    color: #E8F5E9;
    font-weight: 500;
}

h1, h2, h3 {
    color: #D4AF37 !important;
    font-weight: 850 !important;
    letter-spacing: 0.2px;
}

[data-testid="stPageLink"] {
    background-color: #111814;
    border: 1px solid rgba(212, 175, 55, 0.18);
    border-radius: 18px;
    padding: 10px 12px;
    margin-bottom: 8px;
}

[data-testid="stPageLink"]:hover {
    border-color: rgba(212, 175, 55, 0.38);
    background-color: rgba(212, 175, 55, 0.04);
}

[data-testid="stPageLink"] p {
    color: #D4AF37 !important;
    font-weight: 900 !important;
    font-size: 16px !important;
}
</style>
""", unsafe_allow_html=True)


# ---------- HELPERS ----------
def fmt_currency(value):
    if value is None or pd.isna(value):
        return "—"
    return f"${value:.2f}"


def fmt_signed_currency(value):
    if value is None or pd.isna(value):
        return "—"
    return f"+${abs(value):.2f}" if value >= 0 else f"-${abs(value):.2f}"


def preview_card(description, label_1, value_1, label_2, value_2, value_2_style=None):
    value_2_style = value_2_style or "color:#FFFFFF; font-size:18px; font-weight:900;"

    st.html(f"""
    <div style="
        background-color: #111814;
        border: 1px solid rgba(212, 175, 55, 0.18);
        border-radius: 18px;
        padding: 14px 15px;
        min-height: 150px;
        margin-bottom: 22px;
    ">
        <div style="
            color: #CFE8D2;
            font-size: 13px;
            line-height: 1.45;
            font-weight: 650;
            margin-bottom: 14px;
        ">
            {description}
        </div>

        <div style="
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        ">
            <div>
                <div style="color:#A5D6A7; font-size:11px; font-weight:800;">{label_1}</div>
                <div style="color:#FFFFFF; font-size:18px; font-weight:900;">{value_1}</div>
            </div>

            <div>
                <div style="color:#A5D6A7; font-size:11px; font-weight:800;">{label_2}</div>
                <div style="{value_2_style}">{value_2}</div>
            </div>
        </div>
    </div>
    """)


# ---------- LOAD PREVIEW DATA ----------
daily_data = load_daily_summary()
open_positions_payload = load_open_positions_live()
trade_log = load_trade_log()

latest = get_latest_daily_summary(daily_data) if daily_data else {}

daily_df = pd.DataFrame(daily_data) if daily_data else pd.DataFrame()
trade_df = pd.DataFrame(list(trade_log.values())) if trade_log else pd.DataFrame()

open_positions = open_positions_payload.get("positions", []) if open_positions_payload else []

latest_equity = latest.get("total_equity")
latest_realized = latest.get("realized_profit")
latest_activity = latest.get("asset_activity")

closed_positions = len(trade_df) if not trade_df.empty else 0
total_profit = (
    trade_df["profit"].sum()
    if not trade_df.empty and "profit" in trade_df.columns
    else 0
)

# ---------- DAYS SINCE FIRST MOVE ----------
if not trade_df.empty and "buy_date" in trade_df.columns and "sell_date" in trade_df.columns:
    trade_df["buy_date_dt"] = pd.to_datetime(trade_df["buy_date"], errors="coerce")
    trade_df["sell_date_dt"] = pd.to_datetime(trade_df["sell_date"], errors="coerce")

    first_move = trade_df["buy_date_dt"].min()
    latest_exit = trade_df["sell_date_dt"].max()

    if pd.notna(first_move) and pd.notna(latest_exit):
        performance_days = len(
            pd.bdate_range(start=first_move.date(), end=latest_exit.date())
        )
    else:
        performance_days = "—"
else:
    performance_days = "—"

if not daily_df.empty and "summary_date" in daily_df.columns:
    latest_date = daily_df["summary_date"].iloc[-1]
else:
    latest_date = "—"

# ---------- HERO ----------
hero_html = """
<div style="
    background:
        radial-gradient(circle at top right, rgba(76, 175, 80, 0.13), transparent 34%),
        #111814;
    border: 1px solid rgba(212, 175, 55, 0.22);
    border-radius: 26px;
    padding: 30px 32px;
    margin-bottom: 30px;
    box-shadow: 0 18px 45px rgba(0, 0, 0, 0.22);
">
    <div style="
        display: inline-block;
        color: #A5D6A7;
        border: 1px solid rgba(165, 214, 167, 0.18);
        border-radius: 999px;
        padding: 6px 12px;
        font-size: 12px;
        font-weight: 850;
        letter-spacing: 0.35px;
        margin-bottom: 18px;
    ">
        AUTOMATED INVESTMENT DASHBOARD
    </div>

    <div style="
        color: #D4AF37;
        font-size: 44px;
        line-height: 1.02;
        font-weight: 950;
        letter-spacing: -1px;
        margin-bottom: 12px;
    ">
        8Leverage Investments
    </div>

    <div style="
        color: #D4AF37;
        font-size: 24px;
        font-weight: 850;
        margin-bottom: 18px;
    ">
        A system for structured capital movement
    </div>

    <div style="
        color: #E8F5E9;
        font-size: 16px;
        line-height: 1.65;
        max-width: 820px;
        font-weight: 650;
    ">
        This dashboard presents the performance, activity, and historical record of an automated investment system designed to compound ongoing realized returns through structured position management.
    </div>
</div>
"""

st.html(hero_html)


# ---------- NAVIGATION ----------
st.markdown("## How To Navigate")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.page_link(PAGE_OVERVIEW, label="Overview")
    preview_card(
        "Current equity, daily change, and open positions.",
        "Equity",
        fmt_currency(latest_equity),
        "Open",
        len(open_positions),
    )

with col2:
    st.page_link(PAGE_ACTIVITY, label="Activity")
    preview_card(
        "Daily summaries and latest realized activity.",
        "Realized",
        fmt_signed_currency(latest_realized),
        "Moves",
        latest_activity if latest_activity is not None else "—",
    )

with col3:
    st.page_link(PAGE_PERFORMANCE, label="Performance")
    preview_card(
        "Capital progression and long-term realized metrics.",
        "Net Profit",
        fmt_signed_currency(total_profit),
        "Days",
        performance_days,
    )

with col4:
    st.page_link(PAGE_HISTORY, label="History")
    preview_card(
        "Complete closed-position record and filters.",
        "Closed",
        f"{closed_positions:,}",
        "Latest",
        latest_date,
        value_2_style="color:#CFE8D2; font-size:10px; font-weight:800; line-height:1.25;"
    )


# ---------- CONCEPT CARD ----------
concept_html = """
<div style="
    background-color: #111814;
    border: 1px solid rgba(212, 175, 55, 0.20);
    border-radius: 24px;
    padding: 24px 26px;
    margin-top: 10px;
">
    <div style="
        color: #D4AF37;
        font-size: 24px;
        font-weight: 900;
        margin-bottom: 12px;
    ">
        What you’re looking at
    </div>

    <div style="
        color: #E8F5E9;
        font-size: 15px;
        line-height: 1.7;
        font-weight: 650;
        max-width: 820px;
    ">
        This is not a traditional trading interface. It is a system that continuously reallocates capital, realizes gains incrementally, and operates across a broad universe of assets.
    </div>

    <div style="
        margin-top: 18px;
        padding: 16px 18px;
        border-left: 3px solid #D4AF37;
        background-color: rgba(212, 175, 55, 0.045);
        border-radius: 14px;
        color: #FFFFFF;
        font-size: 17px;
        font-weight: 850;
    ">
        The goal is not prediction — but structured participation over time.
    </div>
</div>
"""

st.html(concept_html)