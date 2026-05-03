import json
from pathlib import Path

import pandas as pd
import streamlit as st

from utils.loaders import load_daily_summary


# ============================================================
# FILE PATHS
# ============================================================

CURRENT_FILE = Path(__file__).resolve()

# Handles both:
# - root-level performance.py
# - pages/performance.py
if (CURRENT_FILE.parent / "data").exists():
    BASE_DIR = CURRENT_FILE.parent
else:
    BASE_DIR = CURRENT_FILE.parent.parent

DATA_DIR = BASE_DIR / "data"
PERFORMANCE_SNAPSHOT_FILE = DATA_DIR / "performance_snapshot.json"


# ============================================================
# THEME
# ============================================================

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

@media (max-width: 700px) {
    .block-container {
        padding-left: 0.75rem !important;
        padding-right: 0.75rem !important;
        max-width: 100% !important;
    }
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# HELPERS
# ============================================================

def load_performance_snapshot():
    if not PERFORMANCE_SNAPSHOT_FILE.exists():
        return None

    with PERFORMANCE_SNAPSHOT_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_display(snapshot, section, key, default="—"):
    value = snapshot.get(section, {}).get(key)
    if value is None:
        return default
    return value


def fmt_currency(value):
    if value is None or pd.isna(value):
        return "—"
    return f"${value:,.2f}"


def fmt_signed_currency(value):
    if value is None or pd.isna(value):
        return "—"
    return f"+${abs(value):,.2f}" if value >= 0 else f"-${abs(value):,.2f}"


def metric_value_size(value_text):
    value_text = str(value_text)

    if len(value_text) >= 18:
        return "18px"
    elif len(value_text) >= 14:
        return "20px"
    elif len(value_text) >= 11:
        return "23px"
    elif len(value_text) >= 8:
        return "26px"
    else:
        return "30px"


def infer_tone(value_text):
    """
    Controls value color based on the display text.
    """
    value_text = str(value_text).strip()

    if value_text.startswith("-"):
        return "negative"

    if value_text.startswith("+"):
        return "positive"

    return "neutral"


def tone_color(tone):
    if tone == "positive":
        return "#4CAF50"
    if tone == "negative":
        return "#FF5C5C"
    if tone == "gold":
        return "#D4AF37"
    return "#FFFFFF"


def metric_cards(metrics, desktop_columns=3, mobile_columns=2, highlight_last=False):
    """
    Mobile-first metric card grid.

    metrics format:
    [
        ("Label", "Value"),
        ("Label", "Value", "tone"),
        ("Label", "Value", "tone", "note"),
    ]
    """

    cards_html = f"""
    <style>
    .metric-grid {{
        display: grid;
        grid-template-columns: repeat({mobile_columns}, minmax(0, 1fr));
        gap: 12px;
        margin-bottom: 18px;
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Segoe UI", sans-serif;
    }}

    @media (max-width: 430px) {{
        .metric-grid {{
            grid-template-columns: 1fr;
        }}
    }}

    @media (min-width: 900px) {{
        .metric-grid {{
            grid-template-columns: repeat({desktop_columns}, minmax(0, 1fr));
        }}
    }}

    .metric-card {{
        background-color: #111814;
        border: 1px solid rgba(212, 175, 55, 0.16);
        border-radius: 18px;
        padding: 14px 14px;
        min-height: 88px;
        overflow: hidden;
    }}

    .metric-card.highlight {{
        border-color: rgba(212, 175, 55, 0.42);
        box-shadow: 0 0 0 1px rgba(212, 175, 55, 0.06);
    }}

    .metric-label {{
        color: #A5D6A7;
        font-size: 12.5px;
        font-weight: 850;
        line-height: 1.15;
        margin-bottom: 8px;
    }}

    .metric-value {{
        font-weight: 950;
        letter-spacing: -0.4px;
        line-height: 1.05;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}

    .metric-note {{
        color: #CFE8D2;
        font-size: 11.5px;
        font-weight: 700;
        line-height: 1.2;
        margin-top: 7px;
        opacity: 0.82;
    }}
    </style>

    <div class="metric-grid">
    """

    for idx, metric in enumerate(metrics):
        label = metric[0]
        value = metric[1]

        tone = metric[2] if len(metric) >= 3 else infer_tone(value)
        note = metric[3] if len(metric) >= 4 else ""

        value_color = tone_color(tone)
        value_size = metric_value_size(value)

        highlight_class = "highlight" if highlight_last and idx == len(metrics) - 1 else ""

        cards_html += f"""
        <div class="metric-card {highlight_class}">
            <div class="metric-label">{label}</div>
            <div class="metric-value" style="color:{value_color}; font-size:{value_size};">
                {value}
            </div>
            {f'<div class="metric-note">{note}</div>' if note else ''}
        </div>
        """

    cards_html += "</div>"

    st.html(cards_html)


def headline_cards(metrics):
    """
    Larger top-level mobile-first cards.
    """

    cards_html = """
    <style>
    .headline-grid {
        display: grid;
        grid-template-columns: 1fr;
        gap: 13px;
        margin-bottom: 20px;
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Segoe UI", sans-serif;
    }

    @media (min-width: 900px) {
        .headline-grid {
            grid-template-columns: repeat(3, minmax(0, 1fr));
        }
    }

    .headline-card {
        background:
            radial-gradient(circle at top right, rgba(212, 175, 55, 0.08), transparent 36%),
            #111814;
        border: 1px solid rgba(212, 175, 55, 0.25);
        border-radius: 22px;
        padding: 18px 16px;
        min-height: 105px;
    }

    .headline-label {
        color: #A5D6A7;
        font-size: 13px;
        font-weight: 850;
        margin-bottom: 10px;
    }

    .headline-value {
        font-size: 32px;
        font-weight: 950;
        letter-spacing: -0.7px;
        line-height: 1.0;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    </style>

    <div class="headline-grid">
    """

    for label, value, tone in metrics:
        cards_html += f"""
        <div class="headline-card">
            <div class="headline-label">{label}</div>
            <div class="headline-value" style="color:{tone_color(tone)};">
                {value}
            </div>
        </div>
        """

    cards_html += "</div>"

    st.html(cards_html)


def section_note(text):
    st.markdown(
        f"""
        <div style="
            color: #A5D6A7;
            font-size: 12.5px;
            font-weight: 750;
            margin-top: -8px;
            margin-bottom: 12px;
            line-height: 1.25;
        ">
            {text}
        </div>
        """,
        unsafe_allow_html=True
    )


def context_card(title, main_text, sub_text=None):
    sub_html = ""

    if sub_text:
        sub_html = f"""
        <div style="
            color: #CFE8D2;
            font-size: 15px;
            font-weight: 750;
            line-height: 1.3;
            margin-top: 8px;
        ">
            {sub_text}
        </div>
        """

    card_html = f"""
    <style>
    .context-card {{
        background:
            radial-gradient(circle at top right, rgba(255, 92, 92, 0.10), transparent 34%),
            #111814;
        border: 1px solid rgba(212, 175, 55, 0.32);
        border-radius: 22px;
        padding: 17px 16px;
        margin-bottom: 20px;
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Segoe UI", sans-serif;
    }}

    .context-title {{
        color: #D4AF37;
        font-size: 14px;
        font-weight: 950;
        margin-bottom: 10px;
    }}

    .context-main {{
        color: #FF5C5C;
        font-size: 24px;
        font-weight: 950;
        letter-spacing: -0.4px;
        line-height: 1.1;
    }}
    </style>

    <div class="context-card">
        <div class="context-title">{title}</div>
        <div class="context-main">{main_text}</div>
        {sub_html}
    </div>
    """

    st.html(card_html)

# ============================================================
# LOAD DATA
# ============================================================

snapshot = load_performance_snapshot()
daily_data = load_daily_summary()

daily_df = pd.DataFrame(daily_data)

if not daily_df.empty:
    daily_df["summary_date_dt"] = pd.to_datetime(
        daily_df["summary_date"],
        errors="coerce"
    )

    daily_df["realized_profit"] = pd.to_numeric(
        daily_df["realized_profit"],
        errors="coerce"
    )

    daily_df["total_equity"] = pd.to_numeric(
        daily_df["total_equity"],
        errors="coerce"
    )

    daily_df["deployed_capital"] = pd.to_numeric(
        daily_df.get("deployed_capital"),
        errors="coerce"
    )

    daily_df["unsettled_funds"] = pd.to_numeric(
        daily_df.get("unsettled_funds"),
        errors="coerce"
    )

    daily_df = (
        daily_df
        .dropna(subset=["summary_date_dt"])
        .sort_values("summary_date_dt")
        .reset_index(drop=True)
    )


# ============================================================
# PAGE
# ============================================================

st.title("Performance")

if snapshot is None:
    st.info("No performance snapshot found. Run performance_snapshot.py first.")
    st.stop()

if daily_df.empty:
    st.info("No daily summary data found.")
    st.stop()


# ============================================================
# PERFORMANCE SNAPSHOT
# ============================================================

st.subheader("Performance Snapshot")

headline_cards([
    (
        "Net Realized Gain",
        get_display(snapshot, "performance_snapshot", "net_realized_gain_display"),
        infer_tone(get_display(snapshot, "performance_snapshot", "net_realized_gain_display")),
    ),
    (
        "Total Equity Return",
        get_display(snapshot, "performance_snapshot", "total_equity_return_display"),
        infer_tone(get_display(snapshot, "performance_snapshot", "total_equity_return_display")),
    ),
    (
        "Business Days Since Inception",
        get_display(snapshot, "performance_snapshot", "business_days_since_inception_display"),
        "neutral",
    ),
])


# ============================================================
# TRADE QUALITY
# ============================================================

st.subheader("Trade Quality")

profit_factor = get_display(snapshot, "trade_quality", "profit_factor_display")

metric_cards([
    (
        "Total Realized Moves",
        get_display(snapshot, "trade_quality", "total_realized_moves_display"),
        "neutral",
    ),
    (
        "Win Rate",
        get_display(snapshot, "trade_quality", "win_rate_display"),
        "neutral",
    ),
    (
        "Profit Factor",
        profit_factor,
        "neutral",
        "Profit vs loss strength",
    ),
    (
        "Average Profit per Move",
        get_display(snapshot, "trade_quality", "average_profit_per_move_display"),
    ),
    (
        "Average Moves per Day",
        get_display(snapshot, "trade_quality", "average_moves_per_day_display"),
        "neutral",
    ),
    (
        "Average Realized Profit per Day",
        get_display(snapshot, "trade_quality", "average_realized_profit_per_day_display"),
    ),
], desktop_columns=3, mobile_columns=2)


# ============================================================
# MONTHLY CONSISTENCY
# ============================================================

st.subheader("Monthly Consistency")
section_note("Realized = closed positions. Equity = total account value.")

metric_cards([
    (
        "Realized Profitable Months",
        get_display(snapshot, "monthly_consistency", "realized_profitable_months_display"),
        "neutral",
    ),
    (
        "Average Monthly Realized Profit",
        get_display(snapshot, "monthly_consistency", "average_monthly_realized_profit_display"),
    ),
    (
        "Average Monthly Equity Growth",
        get_display(snapshot, "monthly_consistency", "average_monthly_equity_growth_display"),
    ),
], desktop_columns=2, mobile_columns=2)


# ============================================================
# DAILY CONSISTENCY
# ============================================================

st.subheader("Daily Consistency")
section_note("Realized profit/loss tracks closed moves.")

metric_cards([
    (
        "Realized Profitable Days",
        get_display(snapshot, "daily_consistency", "realized_profitable_days_display"),
        "neutral",
    ),
], desktop_columns=2, mobile_columns=2)

metric_cards([
    (
        "Best Realized Day",
        get_display(snapshot, "daily_consistency", "best_realized_day_display"),
        "positive",
    ),
    (
        "Largest Realized Loss Day",
        get_display(snapshot, "daily_consistency", "largest_realized_loss_day_display"),
        "negative",
    ),
], desktop_columns=2, mobile_columns=2)

metric_cards([
    (
        "Total Realized Profit",
        get_display(snapshot, "daily_consistency", "total_realized_profit_display"),
        "positive",
    ),
    (
        "Total Realized Loss",
        get_display(snapshot, "daily_consistency", "total_realized_loss_display"),
        "negative",
    ),
    (
        "Total Net Gain",
        get_display(snapshot, "daily_consistency", "total_net_gain_display"),
        infer_tone(get_display(snapshot, "daily_consistency", "total_net_gain_display")),
    ),
], desktop_columns=3, mobile_columns=1, highlight_last=True)


# ============================================================
# LARGEST REALIZED LOSS CONTEXT
# ============================================================

loss_context = snapshot.get("largest_realized_loss_context") or {}

context_text = loss_context.get("context_text", "—")
realized_loss_display = get_display(
    snapshot,
    "daily_consistency",
    "largest_realized_loss_day_display"
)

if " while " in context_text:
    main_text, sub_text = context_text.split(" while ", 1)
    sub_text = "while " + sub_text
else:
    main_text = realized_loss_display
    sub_text = context_text

context_card(
    "Largest Realized Loss Context",
    main_text,
    sub_text,
)


# ============================================================
# CAPITAL BEHAVIOR
# ============================================================

st.subheader("Capital Behavior")

metric_cards([
    (
        "Max Drawdown",
        get_display(snapshot, "capital_behavior", "max_drawdown_display"),
        "negative",
    ),
    (
        "Current Drawdown",
        get_display(snapshot, "capital_behavior", "current_drawdown_display"),
        infer_tone(get_display(snapshot, "capital_behavior", "current_drawdown_display")),
    ),
    (
        "Drawdown Recovery",
        get_display(snapshot, "capital_behavior", "drawdown_recovery_display"),
        "neutral",
    ),
    (
        "Sharpe Ratio",
        get_display(snapshot, "capital_behavior", "sharpe_ratio_display"),
        "neutral",
    ),
    (
        "Sortino Ratio",
        get_display(snapshot, "capital_behavior", "sortino_ratio_display"),
        "neutral",
    ),
    (
        "Calmar Ratio",
        get_display(snapshot, "capital_behavior", "calmar_ratio_display"),
        "neutral",
    ),
], desktop_columns=3, mobile_columns=2)

metric_cards([
    (
        "Return on Deployed Capital",
        get_display(snapshot, "capital_behavior", "return_on_deployed_capital_display"),
        infer_tone(get_display(snapshot, "capital_behavior", "return_on_deployed_capital_display")),
    ),
], desktop_columns=1, mobile_columns=1)


# ============================================================
# POSITION BEHAVIOR
# ============================================================

st.subheader("Position Behavior")

metric_cards([
    (
        "Typical Holding Time",
        get_display(snapshot, "position_behavior", "typical_holding_time_display"),
        "neutral",
    ),
    (
        "Long Holds Over 30 Days",
        get_display(snapshot, "position_behavior", "long_holds_over_30_days_display"),
        "neutral",
    ),
], desktop_columns=4, mobile_columns=2)

metric_cards([
    (
        "Daily Realized Profit Rate",
        get_display(snapshot, "position_behavior", "daily_realized_profit_rate_display"),
        infer_tone(get_display(snapshot, "position_behavior", "daily_realized_profit_rate_display")),
        "Average daily realized profit / average equity",
    ),
], desktop_columns=1, mobile_columns=1)


# ============================================================
# DAILY SUMMARY LOG
# ============================================================

st.subheader("Daily Summary Log")

DAILY_ROWS_PER_PAGE_OPTIONS = [25, 50, 100, 150, "All"]
DEFAULT_DAILY_ROWS_PER_PAGE_INDEX = 1  # 0=25, 1=50, 2=100, 3=150, 4=All

daily_display_df = daily_df.copy()

daily_display_df = daily_display_df.rename(columns={
    "summary_date": "Date",
    "asset_activity": "Asset Activity",
    "realized_profit": "Realized Profit",
    "total_equity": "Total Equity",
    "deployed_capital": "Deployed Capital",
    "unsettled_funds": "Unsettled Funds",
})

daily_display_df = daily_display_df.sort_values("Date", ascending=False).reset_index(drop=True)

# ---------- DAILY LOG PAGINATION ----------
daily_page_col1, daily_page_col2, daily_page_col3 = st.columns([0.7, 0.7, 2.0])

with daily_page_col1:
    daily_rows_per_page = st.selectbox(
        "Rows per page",
        options=DAILY_ROWS_PER_PAGE_OPTIONS,
        index=DEFAULT_DAILY_ROWS_PER_PAGE_INDEX,
        key="daily_summary_rows_per_page",
    )

if daily_rows_per_page == "All":
    daily_table_df = daily_display_df.copy()
    daily_total_pages = 1
    daily_page_number = 1
else:
    daily_total_pages = max(
        1,
        (len(daily_display_df) + daily_rows_per_page - 1) // daily_rows_per_page
    )

    with daily_page_col2:
        daily_page_number = st.number_input(
            "Page",
            min_value=1,
            max_value=daily_total_pages,
            value=1,
            step=1,
            key="daily_summary_page_number",
        )

    daily_start_idx = (daily_page_number - 1) * daily_rows_per_page
    daily_end_idx = daily_start_idx + daily_rows_per_page
    daily_table_df = daily_display_df.iloc[daily_start_idx:daily_end_idx].copy()

st.markdown(
    f"""
    <div style="
        color: #A5D6A7;
        font-size: 12px;
        font-weight: 700;
        margin-top: -6px;
        margin-bottom: 10px;
    ">
        Showing {len(daily_table_df)} of {len(daily_display_df)} daily summaries
        {f"| Page {daily_page_number} of {daily_total_pages}" if daily_rows_per_page != "All" else ""}
    </div>
    """,
    unsafe_allow_html=True
)

# ---------- CUSTOM DAILY SUMMARY TABLE ----------
daily_rows_html = ""

for _, row in daily_table_df.iterrows():
    realized = row.get("Realized Profit")
    realized_color = "#4CAF50" if pd.notna(realized) and realized >= 0 else "#FF5C5C"

    daily_rows_html += f"""
            <div class="table-row"
                data-date="{row.get("Date", "—")}"
                data-activity="{row.get("Asset Activity", 0)}"
                data-realized="{realized}"
                data-equity="{row.get("Total Equity", 0)}"
                data-deployed="{row.get("Deployed Capital", 0)}"
                data-unsettled="{row.get("Unsettled Funds", 0)}"
            >
                <div class="muted">{row.get("Date", "—")}</div>
                <div class="muted">{row.get("Asset Activity", "—")}</div>
                <div class="pl" style="color:{realized_color};">{fmt_signed_currency(realized)}</div>
                <div class="money">{fmt_currency(row.get("Total Equity"))}</div>
                <div class="money">{fmt_currency(row.get("Deployed Capital"))}</div>
                <div class="money">{fmt_currency(row.get("Unsettled Funds"))}</div>
            </div>
    """

daily_table_html = f"""
<style>
* {{
    box-sizing: border-box;
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Segoe UI", sans-serif;
}}

html, body {{
    margin: 0;
    padding: 0;
    background: transparent;
}}

::-webkit-scrollbar {{
    width: 6px;
    height: 6px;
}}

::-webkit-scrollbar-track {{
    background: transparent;
}}

::-webkit-scrollbar-thumb {{
    background: rgba(212, 175, 55, 0.35);
    border-radius: 999px;
}}

::-webkit-scrollbar-thumb:hover {{
    background: rgba(212, 175, 55, 0.6);
}}

.table-shell {{
    background-color: #111814;
    border: 1px solid rgba(212, 175, 55, 0.20);
    border-radius: 22px;
    padding: 14px;
    box-shadow: 0 18px 45px rgba(0, 0, 0, 0.22);
}}

.table-scroll {{
    max-height: 650px;
    overflow-x: auto;
    overflow-y: auto;
    border-radius: 14px;
}}

.table-grid {{
    width: 100%;
    min-width: 660px;
}}

.table-row,
.table-header {{
    display: grid;
    grid-template-columns: 1fr 0.8fr 1fr 1fr 1.15fr 1.15fr;
    gap: 8px;
    align-items: center;
}}

.table-header {{
    padding: 10px 10px 12px 10px;
    color: #D4AF37;
    font-weight: 900;
    font-size: 13px;
    letter-spacing: 0.45px;
    text-transform: uppercase;
    border-bottom: 1px solid rgba(212, 175, 55, 0.22);
    position: sticky;
    top: 0;
    background: #111814;
    z-index: 3;
}}

.table-header div {{
    cursor: pointer;
    user-select: none;
}}

.table-header div:hover {{
    color: #FFE082;
}}

.sort-indicator {{
    opacity: 0.75;
    font-size: 11px;
    margin-left: 4px;
}}

.table-row {{
    padding: 11px 10px;
    color: #E8F5E9;
    font-weight: 700;
    font-size: 14px;
    border-bottom: 1px solid rgba(165, 214, 167, 0.08);
    border-radius: 12px;
    transition: background-color 0.12s ease;
}}

.table-row:hover {{
    background-color: rgba(212, 175, 55, 0.055);
}}

.money {{
    color: #F2FFF4;
    font-weight: 750;
}}

.muted {{
    color: #CFE8D2;
    font-weight: 750;
}}

.pl {{
    font-weight: 900;
}}

@media (max-width: 700px) {{
    .table-shell {{
        border-radius: 18px;
        padding: 10px;
    }}

    .table-scroll {{
        max-height: 620px;
        border-radius: 12px;
    }}

    .table-grid {{
        width: 100%;
        min-width: 620px;
    }}

    .table-row,
    .table-header {{
        grid-template-columns: 1fr 0.75fr 1fr 1fr 1.1fr 1.1fr;
        gap: 6px;
    }}

    .table-header {{
        font-size: 12px;
    }}

    .table-row {{
        font-size: 13px;
    }}
}}
</style>

<div class="table-shell">
    <div class="table-scroll">
        <div class="table-grid" id="daily-summary-table">
            <div class="table-header">
                <div data-key="date" data-type="text">Date<span class="sort-indicator"></span></div>
                <div data-key="activity" data-type="number">Activity<span class="sort-indicator"></span></div>
                <div data-key="realized" data-type="number">Realized<span class="sort-indicator"></span></div>
                <div data-key="equity" data-type="number">Equity<span class="sort-indicator"></span></div>
                <div data-key="deployed" data-type="number">Deployed<span class="sort-indicator"></span></div>
                <div data-key="unsettled" data-type="number">Unsettled<span class="sort-indicator"></span></div>
            </div>

            {daily_rows_html}
        </div>
    </div>
</div>

<script>
const table = document.getElementById("daily-summary-table");
const headers = table.querySelectorAll(".table-header div[data-key]");
let currentSort = {{ key: null, direction: "asc" }};

headers.forEach(header => {{
    header.addEventListener("click", () => {{
        const key = header.dataset.key;
        const type = header.dataset.type;

        let direction = "asc";
        if (currentSort.key === key && currentSort.direction === "asc") {{
            direction = "desc";
        }}

        currentSort = {{ key, direction }};

        const rows = Array.from(table.querySelectorAll(".table-row"));

        rows.sort((a, b) => {{
            let aVal = a.dataset[key];
            let bVal = b.dataset[key];

            if (type === "number") {{
                aVal = parseFloat(aVal || 0);
                bVal = parseFloat(bVal || 0);
            }} else {{
                aVal = String(aVal).toUpperCase();
                bVal = String(bVal).toUpperCase();
            }}

            if (aVal < bVal) return direction === "asc" ? -1 : 1;
            if (aVal > bVal) return direction === "asc" ? 1 : -1;
            return 0;
        }});

        rows.forEach(row => table.appendChild(row));

        headers.forEach(h => {{
            const indicator = h.querySelector(".sort-indicator");
            if (indicator) indicator.textContent = "";
        }});

        const activeIndicator = header.querySelector(".sort-indicator");
        if (activeIndicator) {{
            activeIndicator.textContent = direction === "asc" ? "▲" : "▼";
        }}
    }});
}});
</script>
"""

st.iframe(daily_table_html, height=740)