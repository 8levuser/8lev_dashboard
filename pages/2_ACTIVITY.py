import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import streamlit.components.v1 as components

from utils.loaders import load_daily_summary, load_trade_log
from utils.parsers import get_latest_daily_summary, get_latest_activity_trades


# ============================================================
# DAILY SUMMARY CARD FONT CONTROLS
# Change these numbers until the Daily Summary card looks right.
# ============================================================

SUMMARY_TITLE_SIZE = 20          # "Daily Summary | 2026-04-23"
SUMMARY_LABEL_SIZE = 16          # Labels: Realized Profit, Asset Activity, etc.

REALIZED_PROFIT_SIZE = 26        # Realized Profit dollar amount
ASSET_ACTIVITY_SIZE = 26         # Asset Activity number
TOTAL_EQUITY_SIZE = 24           # Total Equity dollar amount
DEPLOYED_CAPITAL_SIZE = 24       # Deployed Capital dollar amount
UNSETTLED_FUNDS_SIZE = 22        # Unsettled Funds dollar amount

SUMMARY_CARD_PADDING = 20        # Inner padding inside the card
SUMMARY_GRID_GAP = 16            # Space between data blocks

# Desktop card can be shorter because the grid is 2 columns.
# Mobile card needs more height because the grid stacks into 1 column.
SUMMARY_CARD_HEIGHT_DESKTOP = 300
SUMMARY_CARD_HEIGHT_MOBILE = 430


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
    font-weight: 800 !important;
    letter-spacing: 0.2px;
}

[data-testid="stMetricLabel"] {
    color: #A5D6A7 !important;
    font-weight: 700 !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.3px;
}

[data-testid="stMetricValue"] {
    color: #FFFFFF !important;
    font-weight: 800 !important;
    font-size: 1.4rem !important;
    letter-spacing: -0.2px;
    line-height: 1.2 !important;
}

[data-testid="stMetric"] {
    background-color: #111814;
    padding: 12px 14px;
    border-radius: 18px;
    border: 1px solid rgba(212, 175, 55, 0.16);
}

[data-testid="stAlert"] {
    background-color: #111814 !important;
    color: #CFE8D2 !important;
    border: 1px solid rgba(212, 175, 55, 0.12) !important;
    border-radius: 14px;
}

/* ---------- MOBILE PAGE WIDTH / OVERFLOW CONTROL ---------- */
html, body {
    overflow-x: hidden !important;
    max-width: 100vw !important;
}

[data-testid="stAppViewContainer"],
[data-testid="stMain"],
.block-container {
    overflow-x: hidden !important;
    max-width: 100% !important;
}

iframe {
    max-width: 100% !important;
    margin-bottom: 0px !important;
}

@media (max-width: 700px) {
    .block-container {
        padding-left: 0.75rem !important;
        padding-right: 0.75rem !important;
        max-width: 100% !important;
    }
}
</style>
""", unsafe_allow_html=True)


def get_next_business_day(date_str: str) -> str:
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    next_day = dt + timedelta(days=1)

    while next_day.weekday() >= 5:
        next_day += timedelta(days=1)

    return next_day.strftime("%Y-%m-%d")


def fmt_signed_currency(value):
    if value is None or pd.isna(value):
        return "—"
    return f"+${abs(value):.2f}" if value >= 0 else f"-${abs(value):.2f}"


st.title("Activity")

# ---------- MOBILE DETECTION ----------
user_agent = st.context.headers.get("user-agent", "").lower()

is_mobile = (
    "mobile" in user_agent
    or "iphone" in user_agent
    or "android" in user_agent
)

SUMMARY_CARD_HEIGHT = (
    SUMMARY_CARD_HEIGHT_MOBILE
    if is_mobile
    else SUMMARY_CARD_HEIGHT_DESKTOP
)

# ---------- LOAD DATA ----------
daily_data = load_daily_summary()
trade_log = load_trade_log()

latest_summary = get_latest_daily_summary(daily_data)
latest_trades, latest_activity_date = get_latest_activity_trades(trade_log)

# ---------- LAST / NEXT UPDATE ----------
next_update = get_next_business_day(latest_summary["summary_date"])

info_html = f"""
<div style="
    color: #A5D6A7;
    font-size: 12px;
    font-weight: 700;
    margin-top: 20px;
    margin-bottom: -10px;
    line-height: 1.2;
">
    <div>Last updated: 08:00PM ET {latest_summary['summary_date']}</div>
    <div>Next update: 08:00PM ET {next_update}</div>
</div>
"""

st.markdown(info_html, unsafe_allow_html=True)

# ---------- DAILY SUMMARY CARD ----------
st.subheader("Daily Summary")

daily_options = sorted(
    [entry["summary_date"] for entry in daily_data],
    reverse=True
)

if "day_index" not in st.session_state:
    st.session_state.day_index = 0

if st.session_state.day_index >= len(daily_options):
    st.session_state.day_index = 0

if st.session_state.day_index < 0:
    st.session_state.day_index = 0


# ---------- DATE NAVIGATION CONTROLS ----------

NAV_BUTTON_HEIGHT = 32
NAV_BUTTON_FONT_SIZE = 13
NAV_BUTTON_RADIUS = 6

NAV_MOBILE_BREAKPOINT = 760
NAV_MOBILE_BUTTON_HEIGHT = 32
NAV_MOBILE_BUTTON_FONT_SIZE = 12

# Controls button spacing.
# Smaller first three numbers = tighter/narrower buttons.
# Larger first three numbers = wider/more rectangular buttons.
NAV_COLUMN_LAYOUT = [0.052, 0.052, 0.0452, 0.86]

# Controls button spacing below the summary card.
# Since the buttons are below an iframe, SUMMARY_CARD_HEIGHT is still the main control.
NAV_TOP_MARGIN = 0
NAV_BOTTOM_MARGIN = 12


st.markdown(f"""
<style>
/* ============================================================
   DATE NAVIGATION BUTTONS
   Applies to the real Streamlit buttons.
   ============================================================ */

div[data-testid="stButton"] button {{
    background-color: #111814 !important;
    border: 1px solid rgba(212, 175, 55, 0.25) !important;
    color: #D4AF37 !important;
    border-radius: {NAV_BUTTON_RADIUS}px !important;
    font-weight: 900 !important;

    padding: 0px 0px !important;
    font-size: {NAV_BUTTON_FONT_SIZE}px !important;
    height: {NAV_BUTTON_HEIGHT}px !important;
    min-height: {NAV_BUTTON_HEIGHT}px !important;
    line-height: 1 !important;

    display: flex !important;
    align-items: center !important;
    justify-content: center !important;

    width: 100% !important;
}}

div[data-testid="stButton"] button:hover {{
    border-color: rgba(212, 175, 55, 0.55) !important;
    background-color: rgba(212, 175, 55, 0.07) !important;
    color: #FFE082 !important;
}}

div[data-testid="stButton"] button:active {{
    background-color: rgba(212, 175, 55, 0.12) !important;
}}

/* Scoped nav spacing below the Daily Summary card */
.st-key-summary_nav_below {{
    margin-top: {NAV_TOP_MARGIN}px !important;
    padding-top: 0px !important;
    margin-bottom: {NAV_BOTTOM_MARGIN}px !important;
}}

.st-key-summary_nav_below div[data-testid="stHorizontalBlock"] {{
    margin-top: 0px !important;
    padding-top: 0px !important;
}}

.st-key-summary_nav_below div[data-testid="stButton"] {{
    margin-top: 0px !important;
    margin-bottom: 0px !important;
    padding-top: 0px !important;
}}

@media (max-width: {NAV_MOBILE_BREAKPOINT}px) {{

    div[data-testid="stButton"] button {{
        height: {NAV_MOBILE_BUTTON_HEIGHT}px !important;
        min-height: {NAV_MOBILE_BUTTON_HEIGHT}px !important;
        font-size: {NAV_MOBILE_BUTTON_FONT_SIZE}px !important;
        padding: 0px !important;
    }}

    .st-key-summary_nav_below {{
        margin-top: {NAV_TOP_MARGIN}px !important;
        margin-bottom: {NAV_BOTTOM_MARGIN}px !important;
    }}
}}
</style>
""", unsafe_allow_html=True)


# ---------- SELECT SUMMARY BASED ON CURRENT INDEX ----------
selected_date = daily_options[st.session_state.day_index]

selected_summary = next(
    entry for entry in daily_data
    if entry["summary_date"] == selected_date
)

profit = selected_summary["realized_profit"]
profit_text = fmt_signed_currency(profit)
profit_color = "#4CAF50" if profit >= 0 else "#FF5C5C"


# ---------- SUMMARY CARD ----------
summary_html = f"""
<style>
* {{
    box-sizing: border-box;
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Segoe UI", sans-serif;
}}

body {{
    margin: 0;
    background: transparent;
}}

.summary-card {{
    background-color: #111814;
    border: 1px solid rgba(212, 175, 55, 0.22);
    border-radius: 22px;
    padding: {SUMMARY_CARD_PADDING}px;
    color: #E8F5E9;
}}

.summary-title {{
    color: #D4AF37;
    font-size: {SUMMARY_TITLE_SIZE}px;
    font-weight: 900;
    margin-bottom: 16px;
}}

.summary-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: {SUMMARY_GRID_GAP}px;
}}

.label {{
    color: #A5D6A7;
    font-size: {SUMMARY_LABEL_SIZE}px;
    font-weight: 700;
    margin-bottom: 4px;
}}

.realized-profit-value {{
    color: {profit_color};
    font-size: {REALIZED_PROFIT_SIZE}px;
    font-weight: 900;
}}

.asset-activity-value {{
    color: #FFFFFF;
    font-size: {ASSET_ACTIVITY_SIZE}px;
    font-weight: 900;
}}

.total-equity-value {{
    color: #FFFFFF;
    font-size: {TOTAL_EQUITY_SIZE}px;
    font-weight: 850;
}}

.deployed-capital-value {{
    color: #FFFFFF;
    font-size: {DEPLOYED_CAPITAL_SIZE}px;
    font-weight: 850;
}}

.unsettled-funds-value {{
    color: #FFFFFF;
    font-size: {UNSETTLED_FUNDS_SIZE}px;
    font-weight: 850;
}}

@media (max-width: 600px) {{
    .summary-grid {{
        grid-template-columns: 1fr;
    }}
}}
</style>

<div class="summary-card">
    <div class="summary-title">Daily Summary | {selected_summary["summary_date"]}</div>

    <div class="summary-grid">
        <div>
            <div class="label">Realized Profit</div>
            <div class="realized-profit-value">{profit_text}</div>
        </div>

        <div>
            <div class="label">Asset Activity</div>
            <div class="asset-activity-value">{selected_summary["asset_activity"]}</div>
        </div>

        <div>
            <div class="label">Total Equity</div>
            <div class="total-equity-value">${selected_summary["total_equity"]:.2f}</div>
        </div>

        <div>
            <div class="label">Deployed Capital</div>
            <div class="deployed-capital-value">${selected_summary["deployed_capital"]:.2f}</div>
        </div>

        <div>
            <div class="label">Unsettled Funds</div>
            <div class="unsettled-funds-value">${selected_summary["unsettled_funds"]:.2f}</div>
        </div>
    </div>
</div>
"""

components.html(summary_html, height=SUMMARY_CARD_HEIGHT, scrolling=False)


# ---------- SUMMARY CARD NAVIGATION BUTTONS ----------
# Buttons are rendered below the Daily Summary card.
# When clicked, they update day_index and rerun the page.

with st.container(key="summary_nav_below"):
    b1, b2, b3, spacer = st.columns(NAV_COLUMN_LAYOUT, gap=None)

    with b1:
        if st.button("◀", key="prev_day_btn", help="Older summary", use_container_width=True):
            if st.session_state.day_index < len(daily_options) - 1:
                st.session_state.day_index += 1
                st.rerun()

    with b2:
        if st.button("▶", key="next_day_btn", help="Newer summary", use_container_width=True):
            if st.session_state.day_index > 0:
                st.session_state.day_index -= 1
                st.rerun()

    with b3:
        if st.button("⟳", key="latest_day_btn", help="Jump to latest summary", use_container_width=True):
            st.session_state.day_index = 0
            st.rerun()


# ---------- LATEST ACTIVITY ----------
st.subheader("Latest Activity")

if latest_activity_date:
    closed_count = len(latest_trades)
    position_word = "position" if closed_count == 1 else "positions"

    st.markdown(
        f"""
        <div style="
            color: #A5D6A7;
            font-size: 12px;
            font-weight: 700;
            margin-top: -4px;
            margin-bottom: 8px;
            line-height: 1.2;
        ">
            Showing {closed_count} closed {position_word} from: {latest_activity_date}
        </div>
        """,
        unsafe_allow_html=True
    )

if not latest_trades:
    st.info("No realized activity found for the latest available date.")
else:
    activity_html = """
    <style>
    * {
        box-sizing: border-box;
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Segoe UI", sans-serif;
    }

    body {
        margin: 0;
        background: transparent;
    }

    .activity-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 16px;
        padding: 2px;
    }

    .activity-card {
        background:
            radial-gradient(circle at top right, rgba(76, 175, 80, 0.12), transparent 34%),
            #111814;
        border: 1px solid rgba(212, 175, 55, 0.18);
        border-radius: 20px;
        padding: 16px;
        min-height: 150px;
        color: #E8F5E9;
        transition: transform 0.14s ease, border-color 0.14s ease, box-shadow 0.14s ease;
    }

    .activity-card:hover {
        transform: translateY(-2px);
        border-color: rgba(212, 175, 55, 0.38);
        box-shadow: 0 14px 34px rgba(0, 0, 0, 0.22);
    }

    .activity-top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 10px;
        margin-bottom: 12px;
    }

    .symbol {
        color: #FFFFFF;
        font-size: 20px;
        font-weight: 950;
        letter-spacing: 0.3px;
    }

    .return-pill {
        border: 1px solid rgba(76, 175, 80, 0.38);
        background-color: rgba(76, 175, 80, 0.10);
        color: #4CAF50;
        padding: 4px 8px;
        border-radius: 999px;
        font-size: 14.5px;
        font-weight: 900;
        white-space: nowrap;
    }

    .profit {
        color: #4CAF50;
        font-size: 26px;
        font-weight: 950;
        letter-spacing: -0.4px;
        margin-bottom: 12px;
    }

    .details {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px 14px;
        margin-top: 6px;
    }

    .detail-box {
        background-color: rgba(255, 255, 255, 0.025);
        border: 1px solid rgba(165, 214, 167, 0.08);
        border-radius: 12px;
        padding: 8px 10px;
    }

    .detail-label {
        color: #A5D6A7;
        font-size: 11px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.35px;
        margin-bottom: 3px;
    }

    .detail-value {
        color: #FFFFFF;
        font-size: 14px;
        font-weight: 850;
    }

    @media (max-width: 760px) {
        .activity-grid {
            grid-template-columns: 1fr;
        }

        .activity-card {
            min-height: auto;
        }
    }
    </style>

    <div class="activity-grid">
    """

    for trade in latest_trades:
        symbol = trade["symbol"]
        profit = trade["profit"]
        pct = trade["trade_percentage"] * 100
        sell_price = trade["sell_price"]
        buy_price = trade["buy_price"]
        qty = int(trade["quantity"])
        sell_time = trade["sell_date"].split(" ")[1]

        pct_text = f"{pct:+.2f}%"
        profit_text = fmt_signed_currency(profit)

        activity_html += f"""
        <div class="activity-card">
            <div class="activity-top">
                <div class="symbol">{symbol}</div>
                <div class="return-pill">{pct_text}</div>
            </div>

            <div class="profit">{profit_text} realized</div>

            <div class="details">
                <div class="detail-box">
                    <div class="detail-label">Entry</div>
                    <div class="detail-value">${buy_price:.2f}</div>
                </div>

                <div class="detail-box">
                    <div class="detail-label">Exit</div>
                    <div class="detail-value">${sell_price:.2f}</div>
                </div>

                <div class="detail-box">
                    <div class="detail-label">Shares</div>
                    <div class="detail-value">{qty}</div>
                </div>

                <div class="detail-box">
                    <div class="detail-label">Closed</div>
                    <div class="detail-value">{sell_time}</div>
                </div>
            </div>
        </div>
        """

    activity_html += """
    </div>
    """

    st.html(activity_html)