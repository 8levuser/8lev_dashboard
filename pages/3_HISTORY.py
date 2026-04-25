import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

from utils.loaders import load_trade_log


# ---------- TABLE CONTROLS ----------
ROWS_PER_PAGE_OPTIONS = [50, 100, 150, 250, "All"]  # adjust available options here
DEFAULT_ROWS_PER_PAGE_INDEX = 2  # 0=50, 1=100, 2=150, 3=250, 4=All


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

/* Inputs/select boxes */
[data-testid="stSelectbox"] label,
[data-testid="stNumberInput"] label {
    color: #A5D6A7 !important;
    font-weight: 700 !important;
    font-size: 0.85rem !important;
}
</style>
""", unsafe_allow_html=True)


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


st.title("Investment History")

# ---------- LOAD DATA ----------
trade_log = load_trade_log()
positions = list(trade_log.values())

if not positions:
    st.info("No investment history found.")
    st.stop()

# ---------- DATAFRAME PREP ----------
df = pd.DataFrame(positions)

df["sell_date_dt"] = pd.to_datetime(df["sell_date"], errors="coerce")
df["buy_date_dt"] = pd.to_datetime(df["buy_date"], errors="coerce")

df = df.sort_values("sell_date_dt", ascending=False).reset_index(drop=True)

# ---------- FILTERS ----------
st.subheader("Filters")

symbol_options = sorted(df["symbol"].dropna().unique().tolist())
selected_symbols = st.multiselect(
    label="Select Symbol(s)",
    options=symbol_options,
    default=[],
    placeholder="Select Symbol(s)",
    label_visibility="collapsed"
)

if selected_symbols:
    filtered_df = df[df["symbol"].isin(selected_symbols)].copy()
else:
    filtered_df = df.copy()

# ---------- STATS ----------
closed_positions = len(filtered_df)
total_realized_profit = filtered_df["profit"].sum()
days_since_first_move = compute_business_days_since_first_move(filtered_df)

st.subheader("History Snapshot")

col1, col2, col3 = st.columns(3)

col1.metric("Closed Positions", closed_positions)
col2.metric("Total Realized Profit", fmt_signed_currency(total_realized_profit))
col3.metric("Days Since First Move", days_since_first_move)

# ---------- PAGINATION ----------
st.subheader("Closed Positions Log")

page_col1, page_col2, page_col3 = st.columns([0.7, 0.7, 2.0])

with page_col1:
    rows_per_page = st.selectbox(
        "Rows per page",
        options=ROWS_PER_PAGE_OPTIONS,
        index=DEFAULT_ROWS_PER_PAGE_INDEX,
    )

if rows_per_page == "All":
    table_df = filtered_df.copy()
    total_pages = 1
    page_number = 1
else:
    total_pages = max(1, (len(filtered_df) + rows_per_page - 1) // rows_per_page)

    with page_col2:
        page_number = st.number_input(
            "Page",
            min_value=1,
            max_value=total_pages,
            value=1,
            step=1,
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

# ---------- CUSTOM TABLE ----------
cards_html = """
<style>
* {
    box-sizing: border-box;
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Segoe UI", sans-serif;
}

html, body {
    margin: 0;
    padding: 0;
    background: transparent;
}

::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}

::-webkit-scrollbar-track {
    background: transparent;
}

::-webkit-scrollbar-thumb {
    background: rgba(212, 175, 55, 0.35);
    border-radius: 999px;
}

::-webkit-scrollbar-thumb:hover {
    background: rgba(212, 175, 55, 0.6);
}

.table-shell {
    background-color: #111814;
    border: 1px solid rgba(212, 175, 55, 0.20);
    border-radius: 22px;
    padding: 14px;
    box-shadow: 0 18px 45px rgba(0, 0, 0, 0.22);
}

.table-scroll {
    max-height: 650px;
    overflow-y: auto;
    overflow-x: hidden;
    border-radius: 14px;
}

.table-grid {
    width: 100%;
    min-width: 0;
}

.table-row,
.table-header {
    display: grid;

    /* 🔧 MAIN CONTROL: column widths */
    grid-template-columns:
        0.65fr  /* Symbol */
        0.45fr  /* Shares */
        0.7fr   /* Entry */
        0.7fr   /* Exit */
        0.8fr   /* Profit */
        0.8fr   /* Return % */
        0.95fr  /* Entry Date */
        0.95fr; /* Exit Date */

    gap: 4px;
    align-items: center;
}

.table-header {
    padding: 8px 8px 10px 8px;
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
}

.table-header div {
    cursor: pointer;
    user-select: none;
}

.table-header div:hover {
    color: #FFE082;
}

.sort-indicator {
    opacity: 0.75;
    font-size: 11px;
    margin-left: 4px;
}

.table-row {
    padding: 11px 10px;
    color: #E8F5E9;
    font-weight: 700;
    font-size: 14px;
    border-bottom: 1px solid rgba(165, 214, 167, 0.08);
    border-radius: 12px;
    transition: background-color 0.12s ease;
}

.table-row:hover {
    background-color: rgba(212, 175, 55, 0.055);
}

.symbol {
    color: #FFFFFF;
    font-weight: 900;
    letter-spacing: 0.2px;
}

.money {
    color: #F2FFF4;
    font-weight: 750;
}

.muted {
    color: #CFE8D2;
    font-weight: 750;
}

.pl {
    font-weight: 900;
}

@media (max-width: 700px) {
    .table-shell {
        border-radius: 18px;
        padding: 10px;
    }

    .table-scroll {
        max-height: 620px;
        border-radius: 12px;
    }

    .table-grid {
        width: 100%;
        min-width: 760px; /* 🔧 mobile minimum width */
    }

    .table-row,
    .table-header {
        gap: 5px;
    }

    .table-header {
        font-size: 12px;
    }

    .table-row {
        font-size: 13px;
    }
}
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
"""

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

    cards_html += f"""
            <div class="table-row"
                data-symbol="{symbol}"
                data-shares="{quantity}"
                data-entry="{buy_price}"
                data-exit="{sell_price}"
                data-profit="{profit}"
                data-return="{trade_pct}"
                data-entrydate="{buy_date}"
                data-exitdate="{sell_date}"
            >
                <div class="symbol">{symbol}</div>
                <div class="muted">{fmt_quantity(quantity)}</div>
                <div class="money">{fmt_currency(buy_price)}</div>
                <div class="money">{fmt_currency(sell_price)}</div>
                <div class="pl" style="color:{profit_color};">{fmt_signed_currency(profit)}</div>
                <div class="pl" style="color:{pct_color};">{fmt_pct_from_decimal(trade_pct)}</div>
                <div class="muted">{buy_date}</div>
                <div class="muted">{sell_date}</div>
            </div>
    """

cards_html += """
        </div>
    </div>
</div>

<script>
const table = document.getElementById("history-table");
const headers = table.querySelectorAll(".table-header div[data-key]");
let currentSort = { key: null, direction: "asc" };

headers.forEach(header => {
    header.addEventListener("click", () => {
        const key = header.dataset.key;
        const type = header.dataset.type;

        let direction = "asc";
        if (currentSort.key === key && currentSort.direction === "asc") {
            direction = "desc";
        }

        currentSort = { key, direction };

        const rows = Array.from(table.querySelectorAll(".table-row"));

        rows.sort((a, b) => {
            let aVal = a.dataset[key];
            let bVal = b.dataset[key];

            if (type === "number") {
                aVal = parseFloat(aVal || 0);
                bVal = parseFloat(bVal || 0);
            } else {
                aVal = String(aVal).toUpperCase();
                bVal = String(bVal).toUpperCase();
            }

            if (aVal < bVal) return direction === "asc" ? -1 : 1;
            if (aVal > bVal) return direction === "asc" ? 1 : -1;
            return 0;
        });

        rows.forEach(row => table.appendChild(row));

        headers.forEach(h => {
            const indicator = h.querySelector(".sort-indicator");
            if (indicator) indicator.textContent = "";
        });

        const activeIndicator = header.querySelector(".sort-indicator");
        if (activeIndicator) {
            activeIndicator.textContent = direction === "asc" ? "▲" : "▼";
        }
    });
});
</script>
"""

components.html(cards_html, height=740, scrolling=False)