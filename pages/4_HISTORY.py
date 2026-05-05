import streamlit as st
import pandas as pd
from html import escape

from utils.loaders import load_trade_log, load_daily_summary

# ---------- TABLE CONTROLS ----------
ROWS_PER_PAGE_OPTIONS = [50, 100, 150, 250, "All"]
DEFAULT_ROWS_PER_PAGE_INDEX = 2


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

/* Inputs/select boxes */
[data-testid="stSelectbox"] label,
[data-testid="stNumberInput"] label,
[data-testid="stMultiSelect"] label {
    color: #A5D6A7 !important;
    font-weight: 700 !important;
    font-size: 0.85rem !important;
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
        padding-top: 1rem !important;
        max-width: 100% !important;
    }

    h2, h3 {
        margin-top: 0.65rem !important;
        margin-bottom: 0.35rem !important;
    }
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# HELPERS
# ============================================================

def fmt_currency(value):
    if value is None or pd.isna(value):
        return "—"
    return f"${value:.2f}"


def fmt_signed_currency(value):
    if value is None or pd.isna(value):
        return "—"
    return f"+${abs(value):.2f}" if value >= 0 else f"-${abs(value):.2f}"


def fmt_pct_from_decimal(value):
    if value is None or pd.isna(value):
        return "—"
    return f"{value * 100:+.2f}%"


def fmt_quantity(value):
    if value is None or pd.isna(value):
        return "—"

    x = float(value)
    return f"{int(x)}" if x.is_integer() else f"{x:.2f}"


def value_color(value):
    if value is None or pd.isna(value):
        return "#E8F5E9"

    return "#4CAF50" if value >= 0 else "#FF5C5C"


def compute_business_days_since_first_move(df: pd.DataFrame) -> str:
    if df.empty:
        return "—"

    first_move = df["buy_date_dt"].min()
    latest_exit = df["sell_date_dt"].max()

    if pd.isna(first_move) or pd.isna(latest_exit):
        return "—"

    business_days = pd.bdate_range(start=first_move.date(), end=latest_exit.date())
    return f"{len(business_days)} days"


# ============================================================
# PAGE
# ============================================================

st.title("Investment History")


# ============================================================
# LOAD DATA
# ============================================================

trade_log = load_trade_log()
positions = list(trade_log.values())

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

if not positions:
    st.info("No investment history found.")
    st.stop()



# ============================================================
# DAILY SUMMARY LOG
# ============================================================

st.subheader("Daily Summary Log")

if daily_df.empty:
    st.info("No daily summary data found.")
else:
    DAILY_ROWS_PER_PAGE_OPTIONS = [25, 50, 100, 150, "All"]
    DEFAULT_DAILY_ROWS_PER_PAGE_INDEX = 1

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

    daily_page_col1, daily_page_col2, daily_page_col3 = st.columns([0.7, 0.7, 2.0])

    with daily_page_col1:
        daily_rows_per_page = st.selectbox(
            "Rows per page",
            options=DAILY_ROWS_PER_PAGE_OPTIONS,
            index=DEFAULT_DAILY_ROWS_PER_PAGE_INDEX,
            key="history_daily_summary_rows_per_page",
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
                key="history_daily_summary_page_number",
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

    daily_rows_html = ""

    for _, row in daily_table_df.iterrows():
        realized = row.get("Realized Profit")
        realized_color = "#4CAF50" if pd.notna(realized) and realized >= 0 else "#FF5C5C"

        daily_rows_html += f"""
                <div class="daily-table-row"
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

    .daily-table-shell {{
        background-color: #111814;
        border: 1px solid rgba(212, 175, 55, 0.20);
        border-radius: 22px;
        padding: 14px;
        box-shadow: 0 18px 45px rgba(0, 0, 0, 0.22);
    }}

    .daily-table-scroll {{
        max-height: 650px;
        overflow-x: auto;
        overflow-y: auto;
        border-radius: 14px;
    }}

    .daily-table-grid {{
        width: 100%;
        min-width: 660px;
    }}

    .daily-table-row,
    .daily-table-header {{
        display: grid;
        grid-template-columns: 1fr 0.8fr 1fr 1fr 1.15fr 1.15fr;
        gap: 8px;
        align-items: center;
    }}

    .daily-table-header {{
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

    .daily-table-header div {{
        cursor: pointer;
        user-select: none;
    }}

    .daily-table-header div:hover {{
        color: #FFE082;
    }}

    .sort-indicator {{
        opacity: 0.75;
        font-size: 11px;
        margin-left: 4px;
    }}

    .daily-table-row {{
        padding: 11px 10px;
        color: #E8F5E9;
        font-weight: 700;
        font-size: 14px;
        border-bottom: 1px solid rgba(165, 214, 167, 0.08);
        border-radius: 12px;
        transition: background-color 0.12s ease;
    }}

    .daily-table-row:hover {{
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
        .daily-table-shell {{
            border-radius: 18px;
            padding: 10px;
        }}

        .daily-table-scroll {{
            max-height: 620px;
            border-radius: 12px;
        }}

        .daily-table-grid {{
            width: 100%;
            min-width: 620px;
        }}

        .daily-table-row,
        .daily-table-header {{
            grid-template-columns: 1fr 0.75fr 1fr 1fr 1.1fr 1.1fr;
            gap: 6px;
        }}

        .daily-table-header {{
            font-size: 12px;
        }}

        .daily-table-row {{
            font-size: 13px;
        }}
    }}
    </style>

    <div class="daily-table-shell">
        <div class="daily-table-scroll">
            <div class="daily-table-grid" id="daily-summary-table">
                <div class="daily-table-header">
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
    const dailyTable = document.getElementById("daily-summary-table");
    const dailyHeaders = dailyTable.querySelectorAll(".daily-table-header div[data-key]");
    let dailyCurrentSort = {{ key: null, direction: "asc" }};

    dailyHeaders.forEach(header => {{
        header.addEventListener("click", () => {{
            const key = header.dataset.key;
            const type = header.dataset.type;

            let direction = "asc";
            if (dailyCurrentSort.key === key && dailyCurrentSort.direction === "asc") {{
                direction = "desc";
            }}

            dailyCurrentSort = {{ key, direction }};

            const rows = Array.from(dailyTable.querySelectorAll(".daily-table-row"));

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

            rows.forEach(row => dailyTable.appendChild(row));

            dailyHeaders.forEach(h => {{
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

# ============================================================
# DATAFRAME PREP
# ============================================================

df = pd.DataFrame(positions)

df["sell_date_dt"] = pd.to_datetime(df["sell_date"], errors="coerce")
df["buy_date_dt"] = pd.to_datetime(df["buy_date"], errors="coerce")

df = df.sort_values("sell_date_dt", ascending=False).reset_index(drop=True)


# ============================================================
# CLOSED POSITIONS LOG
# ============================================================

st.subheader("Closed Positions Log")

symbol_options = sorted(df["symbol"].dropna().unique().tolist())

selected_symbols = st.multiselect(
    label="Select Symbol(s)",
    options=symbol_options,
    default=[],
    placeholder="Select Symbol(s)",
    label_visibility="collapsed",
)

if selected_symbols:
    filtered_df = df[df["symbol"].isin(selected_symbols)].copy()
else:
    filtered_df = df.copy()


# ============================================================
# PAGINATION
# ============================================================

page_col1, page_col2, page_col3 = st.columns([0.7, 0.7, 2.0])

with page_col1:
    rows_per_page = st.selectbox(
        "Rows per page",
        options=ROWS_PER_PAGE_OPTIONS,
        index=DEFAULT_ROWS_PER_PAGE_INDEX,
        key="history_rows_per_page",
    )

if rows_per_page == "All":
    table_df = filtered_df.copy()
    total_pages = 1
    page_number = 1
else:
    total_pages = max(
        1,
        (len(filtered_df) + rows_per_page - 1) // rows_per_page
    )

    with page_col2:
        page_number = st.number_input(
            "Page",
            min_value=1,
            max_value=total_pages,
            value=1,
            step=1,
            key="history_page_number",
        )

    start_idx = (page_number - 1) * rows_per_page
    end_idx = start_idx + rows_per_page
    table_df = filtered_df.iloc[start_idx:end_idx].copy()

st.markdown(
    f"""
    <div style="
        color: #A5D6A7;
        font-size: 12px;
        font-weight: 700;
        margin-top: -6px;
        margin-bottom: 10px;
    ">
        Showing {len(table_df)} of {len(filtered_df)} closed positions
        {f"| Page {page_number} of {total_pages}" if rows_per_page != "All" else ""}
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# CUSTOM TABLE
# ============================================================

rows_html = ""

for _, row in table_df.iterrows():
    symbol = row.get("symbol", "—")
    quantity = row.get("quantity")
    buy_price = row.get("buy_price")
    sell_price = row.get("sell_price")
    profit = row.get("profit")
    trade_pct = row.get("trade_percentage")
    buy_date = row.get("buy_date", "—")
    sell_date = row.get("sell_date", "—")

    profit_color = value_color(profit)
    pct_color = value_color(trade_pct)

    safe_symbol = escape(str(symbol))
    safe_buy_date = escape(str(buy_date))
    safe_sell_date = escape(str(sell_date))

    rows_html += f"""
            <div class="table-row"
                data-symbol="{safe_symbol}"
                data-shares="{quantity}"
                data-entry="{buy_price}"
                data-exit="{sell_price}"
                data-profit="{profit}"
                data-return="{trade_pct}"
                data-entrydate="{safe_buy_date}"
                data-exitdate="{safe_sell_date}"
            >
                <div class="symbol">{safe_symbol}</div>
                <div class="muted">{fmt_quantity(quantity)}</div>
                <div class="money">{fmt_currency(buy_price)}</div>
                <div class="money">{fmt_currency(sell_price)}</div>
                <div class="pl" style="color:{profit_color};">{fmt_signed_currency(profit)}</div>
                <div class="pl" style="color:{pct_color};">{fmt_pct_from_decimal(trade_pct)}</div>
                <div class="muted">{safe_buy_date}</div>
                <div class="muted">{safe_sell_date}</div>
            </div>
    """

table_html = f"""
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
    min-width: 760px;
}}

.table-row,
.table-header {{
    display: grid;
    grid-template-columns:
        0.65fr
        0.45fr
        0.7fr
        0.7fr
        0.8fr
        0.8fr
        0.95fr
        0.95fr;
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

.symbol {{
    color: #FFFFFF;
    font-weight: 900;
    letter-spacing: 0.2px;
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
        min-width: 740px;
    }}

    .table-row,
    .table-header {{
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
        <div class="table-grid" id="history-table">
            <div class="table-header">
                <div data-key="symbol" data-type="text">Symbol<span class="sort-indicator"></span></div>
                <div data-key="shares" data-type="number">Shares<span class="sort-indicator"></span></div>
                <div data-key="entry" data-type="number">Entry<span class="sort-indicator"></span></div>
                <div data-key="exit" data-type="number">Exit<span class="sort-indicator"></span></div>
                <div data-key="profit" data-type="number">Profit<span class="sort-indicator"></span></div>
                <div data-key="return" data-type="number">Return %<span class="sort-indicator"></span></div>
                <div data-key="entrydate" data-type="text">Entry Date<span class="sort-indicator"></span></div>
                <div data-key="exitdate" data-type="text">Exit Date<span class="sort-indicator"></span></div>
            </div>

            {rows_html}
        </div>
    </div>
</div>

<script>
const table = document.getElementById("history-table");
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

st.iframe(table_html, height=740)