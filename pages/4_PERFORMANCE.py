import streamlit as st
import pandas as pd
import altair as alt
import streamlit.components.v1 as components

from utils.loaders import load_daily_summary, load_monthly_log, load_trade_log


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


def fmt_pct(value):
    if value is None or pd.isna(value):
        return "—"
    return f"{value:.2f}%"


def metric_row(metrics):
    cols = st.columns(len(metrics))
    for col, (label, value) in zip(cols, metrics):
        col.metric(label, value)


def themed_chart(chart, height=320):
    return (
        chart
        .properties(
            height=height,
            background="#111814",
            padding={"left": 26, "right": 34, "top": 24, "bottom": 18}
        )
        .configure_view(strokeWidth=0)
        .configure_axis(
            labelFont="Segoe UI",
            titleFont="Segoe UI",
            labelFontSize=15,
            titleFontSize=20,
            labelFontWeight=700,
            titleFontWeight=800,
            labelColor="#E8F5E9",
            titleColor="#D4AF37",
            gridColor="#2E7D32",
            gridOpacity=0.14,
            domain=False,
            tickColor="#2E7D32",
            labelPadding=10,
        )
    )

def resettable_chart(chart, chart_key, height=340):
    reset_col, spacer = st.columns([0.25, 1.75])

    with reset_col:
        if st.button("Reset position", key=f"reset_{chart_key}"):
            st.session_state[f"{chart_key}_version"] = (
                st.session_state.get(f"{chart_key}_version", 0) + 1
            )

    version = st.session_state.get(f"{chart_key}_version", 0)

    st.altair_chart(
        themed_chart(chart.interactive(), height=height),
        width="stretch",
        key=f"{chart_key}_{version}"
    )
    
def add_snap_layers(base, df, x_field, tooltip_fields):
    hover = alt.selection_point(
        nearest=True,
        on="pointermove",
        encodings=["x"],
        empty=False
    )

    selectors = base.mark_point(
        opacity=0,
        size=220
    ).encode(
        tooltip=tooltip_fields
    ).add_params(hover)

    points = base.mark_circle(
        size=85,
        color="#4CAF50"
    ).encode(
        opacity=alt.condition(hover, alt.value(1), alt.value(0))
    )

    rules = alt.Chart(df).mark_rule(
        color="#777777"
    ).encode(
        x=f"{x_field}:T",
        opacity=alt.condition(hover, alt.value(0.45), alt.value(0))
    ).add_params(hover)

    return selectors, points, rules

def parse_money_string(value):
    if value is None or pd.isna(value):
        return None

    if isinstance(value, (int, float)):
        return float(value)

    cleaned = (
        str(value)
        .replace("$", "")
        .replace(",", "")
        .replace("+", "")
        .strip()
    )

    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_pct_string(value):
    if value is None or pd.isna(value):
        return None

    cleaned = str(value).replace("%", "").strip()

    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_period_start_date(start_label, end_label, year):
    start_dt = pd.to_datetime(
        f"{start_label} {year}",
        format="%B %d %Y",
        errors="coerce"
    )

    end_dt = pd.to_datetime(
        f"{end_label} {year}",
        format="%B %d %Y",
        errors="coerce"
    )

    if pd.isna(start_dt) or pd.isna(end_dt):
        return pd.NaT

    if start_dt.month > end_dt.month:
        start_dt = start_dt - pd.DateOffset(years=1)

    return start_dt

def metric_value_size(value_text):
    value_text = str(value_text)

    if len(value_text) >= 14:
        return "20px"
    elif len(value_text) >= 11:
        return "23px"
    elif len(value_text) >= 8:
        return "26px"
    else:
        return "30px"


def metric_cards(metrics, columns=3):
    cards_html = f"""
    <div style="
        display: grid;
        grid-template-columns: repeat({columns}, 1fr);
        gap: 14px;
        margin-bottom: 18px;
        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', 'Segoe UI', sans-serif;
    ">
    """

    for label, value in metrics:
        size = metric_value_size(value)

        cards_html += f"""
        <div style="
            background-color: #111814;
            border: 1px solid rgba(212, 175, 55, 0.16);
            border-radius: 18px;
            padding: 14px 16px;
            min-height: 86px;
        ">
            <div style="
                color: #A5D6A7;
                font-size: 13px;
                font-weight: 800;
                margin-bottom: 8px;
            ">
                {label}
            </div>

            <div style="
                color: #FFFFFF;
                font-size: {size};
                font-weight: 900;
                letter-spacing: -0.4px;
                line-height: 1.05;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            ">
                {value}
            </div>
        </div>
        """

    cards_html += "</div>"
    st.html(cards_html)

# ---------- LOAD DATA ----------
daily_data = load_daily_summary()
monthly_data = load_monthly_log()
trade_log = load_trade_log()

daily_df = pd.DataFrame(daily_data)

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

daily_df = (
    daily_df
    .dropna(subset=["summary_date_dt"])
    .sort_values("summary_date_dt")
    .reset_index(drop=True)
)

daily_df["cumulative_realized_profit"] = daily_df["realized_profit"].cumsum()

trade_df = pd.DataFrame(list(trade_log.values())) if trade_log else pd.DataFrame()

if not trade_df.empty:
    trade_df["buy_date_dt"] = pd.to_datetime(trade_df["buy_date"], errors="coerce")
    trade_df["sell_date_dt"] = pd.to_datetime(trade_df["sell_date"], errors="coerce")
    trade_df["profit"] = pd.to_numeric(trade_df["profit"], errors="coerce")
    trade_df["trade_percentage"] = pd.to_numeric(
        trade_df["trade_percentage"],
        errors="coerce"
    )

    trade_df = (
        trade_df
        .dropna(subset=["sell_date_dt", "profit"])
        .sort_values("sell_date_dt")
        .reset_index(drop=True)
    )


# ---------- PAGE ----------
st.title("Performance")

if trade_df.empty:
    st.info("No closed position data found.")
    st.stop()


# ---------- PERFORMANCE SNAPSHOT ----------
st.subheader("Performance Snapshot")

total_net_profit = trade_df["profit"].sum()
total_moves = len(trade_df)
avg_profit_per_move = trade_df["profit"].mean()

total_days = len(daily_df) if not daily_df.empty else 0

avg_moves_per_day = total_moves / total_days if total_days > 0 else None
avg_profit_per_day = total_net_profit / total_days if total_days > 0 else None

metric_cards([
    ("Total Net Realized Profit", fmt_signed_currency(total_net_profit)),
    ("Total Realized Moves", f"{total_moves:,}"),
    ("Average Profit per Move", fmt_signed_currency(avg_profit_per_move)),
], columns=3)

metric_cards([
    ("Average Moves per Day", f"{avg_moves_per_day:.2f}" if avg_moves_per_day else "—"),
    ("Average Profit per Day", fmt_signed_currency(avg_profit_per_day)),
], columns=3)


# ---------- CUMULATIVE REALIZED PROFIT ----------
st.subheader("Cumulative Realized Profit")

cumulative_base = alt.Chart(daily_df).encode(
    x=alt.X("summary_date_dt:T", title=None),
    y=alt.Y(
        "cumulative_realized_profit:Q",
        title="Cumulative Realized Profit"
    )
)

cumulative_area = cumulative_base.mark_area(
    interpolate="monotone",
    opacity=0.18,
    color="#4CAF50"
)

cumulative_line = cumulative_base.mark_line(
    interpolate="monotone",
    strokeWidth=3,
    color="#4CAF50"
)

cumulative_selectors, cumulative_points, cumulative_rules = add_snap_layers(
    cumulative_base,
    daily_df,
    "summary_date_dt",
    [
        alt.Tooltip("summary_date_dt:T", title="Date", format="%b %d, %Y"),
        alt.Tooltip("realized_profit:Q", title="Daily Realized", format="$,.2f"),
        alt.Tooltip("cumulative_realized_profit:Q", title="Cumulative", format="$,.2f"),
    ]
)

st.altair_chart(
    themed_chart(
        alt.layer(
            cumulative_area,
            cumulative_line,
            cumulative_selectors,
            cumulative_points,
            cumulative_rules
        ),
        height=340
    ),
    width="stretch"
)
# ---------- EQUITY PROGRESSION ----------
st.subheader("Equity Progression")

equity_base = alt.Chart(daily_df).encode(
    x=alt.X("summary_date_dt:T", title=None),
    y=alt.Y(
        "total_equity:Q",
        title="Equity",
        scale=alt.Scale(zero=False)
    )
)

equity_area = equity_base.mark_area(
    interpolate="monotone",
    opacity=0.16,
    color="#4CAF50"
)

equity_line = equity_base.mark_line(
    interpolate="monotone",
    strokeWidth=3,
    color="#4CAF50"
)

equity_selectors, equity_points, equity_rules = add_snap_layers(
    equity_base,
    daily_df,
    "summary_date_dt",
    [
        alt.Tooltip("summary_date_dt:T", title="Date", format="%b %d, %Y"),
        alt.Tooltip("total_equity:Q", title="Equity", format="$,.2f"),
    ]
)

st.altair_chart(
    themed_chart(
        alt.layer(
            equity_area,
            equity_line,
            equity_selectors,
            equity_points,
            equity_rules
        ),
        height=340
    ),
    width="stretch"
)

# ---------- DAILY REALIZED PROFIT ----------
st.subheader("Daily Realized Profit")

daily_profit_base = alt.Chart(daily_df).encode(
    x=alt.X("summary_date_dt:T", title=None),
    y=alt.Y("realized_profit:Q", title="Realized Profit")
)

daily_profit_bars = daily_profit_base.mark_bar(
    color="#4CAF50",
    opacity=0.75
)

daily_profit_hover = alt.selection_point(
    nearest=True,
    on="pointermove",
    encodings=["x"],
    empty=False
)

daily_profit_selectors = daily_profit_base.mark_point(
    opacity=0,
    size=220
).encode(
    tooltip=[
        alt.Tooltip("summary_date_dt:T", title="Date", format="%b %d, %Y"),
        alt.Tooltip("realized_profit:Q", title="Realized Profit", format="$,.2f"),
    ]
).add_params(daily_profit_hover)

daily_profit_points = daily_profit_base.mark_circle(
    size=85,
    color="#4CAF50"
).encode(
    opacity=alt.condition(daily_profit_hover, alt.value(1), alt.value(0))
)

daily_profit_rules = alt.Chart(daily_df).mark_rule(
    color="#777777"
).encode(
    x="summary_date_dt:T",
    opacity=alt.condition(daily_profit_hover, alt.value(0.45), alt.value(0))
).add_params(daily_profit_hover)

daily_profit_chart = alt.layer(
    daily_profit_bars,
    daily_profit_selectors,
    daily_profit_points,
    daily_profit_rules
)

st.altair_chart(
    themed_chart(daily_profit_chart, height=300),
    width="stretch"
)
# ---------- MONTHLY DATA ----------
if monthly_data:
    monthly_df = pd.DataFrame(monthly_data)

    monthly_df["monthly_realized_profit_num"] = (
        monthly_df["monthly_realized_profit"].apply(parse_money_string)
    )
    monthly_df["growth_value_num"] = (
        monthly_df["growth_value"].apply(parse_money_string)
    )
    monthly_df["equity_growth_pct_num"] = (
        monthly_df["equity_growth_%"].apply(parse_pct_string)
    )
    monthly_df["end_amount"] = pd.to_numeric(
        monthly_df["end_amount"],
        errors="coerce"
    )

    monthly_df["period_start_dt"] = monthly_df.apply(
        lambda row: parse_period_start_date(
            row["start_label"],
            row["end_label"],
            row["year"]
        ),
        axis=1
    )

    monthly_df = (
        monthly_df
        .sort_values("period_start_dt")
        .reset_index(drop=True)
    )

    monthly_df["period_label"] = (
        monthly_df["start_label"].astype(str)
        + " → "
        + monthly_df["end_label"].astype(str)
        + ", "
        + monthly_df["year"].astype(str)
    )

    st.subheader("Monthly Progression")

    latest_month_realized = monthly_df["monthly_realized_profit_num"].iloc[-1]
    latest_month_growth = monthly_df["equity_growth_pct_num"].iloc[-1]

    metric_row([
        ("Latest Monthly Realized Profit", fmt_signed_currency(latest_month_realized)),
        ("Latest Monthly Equity Growth", fmt_pct(latest_month_growth)),
    ])

# ---------- MONTHLY REALIZED PROFIT ----------
st.subheader("Monthly Realized Profit")

# Equal monthly slots, but chronologically sorted
monthly_df = monthly_df.sort_values("period_start_dt").reset_index(drop=True)
monthly_df["month_axis_label"] = monthly_df["period_start_dt"].dt.strftime("%b %Y")

monthly_profit_base = alt.Chart(monthly_df).encode(
    x=alt.X(
        "month_axis_label:O",
        title=None,
        sort=alt.SortField(field="period_start_dt", order="ascending"),
        axis=alt.Axis(labelAngle=0)
    ),
    y=alt.Y(
        "monthly_realized_profit_num:Q",
        title="Monthly Realized Profit"
    )
)

monthly_profit_bars = monthly_profit_base.mark_bar(
    size=34,
    color="#4CAF50",
    opacity=0.85,
    cornerRadiusTopLeft=5,
    cornerRadiusTopRight=5,
)

monthly_profit_hover = alt.selection_point(
    nearest=True,
    on="pointermove",
    encodings=["x"],
    empty=False
)

monthly_profit_selectors = monthly_profit_base.mark_point(
    opacity=0,
    size=220
).encode(
    tooltip=[
        alt.Tooltip("period_label:N", title="Period"),
        alt.Tooltip(
            "monthly_realized_profit_num:Q",
            title="Monthly Realized Profit",
            format="$,.2f"
        ),
    ]
).add_params(monthly_profit_hover)

monthly_profit_points = monthly_profit_base.mark_circle(
    size=85,
    color="#4CAF50"
).encode(
    opacity=alt.condition(monthly_profit_hover, alt.value(1), alt.value(0))
)

monthly_profit_rules = alt.Chart(monthly_df).mark_rule(
    color="#777777"
).encode(
    x=alt.X(
        "month_axis_label:O",
        sort=alt.SortField(field="period_start_dt", order="ascending")
    ),
    opacity=alt.condition(monthly_profit_hover, alt.value(0.45), alt.value(0))
).add_params(monthly_profit_hover)

monthly_profit_chart = alt.layer(
    monthly_profit_bars,
    monthly_profit_selectors,
    monthly_profit_points,
    monthly_profit_rules
)

st.altair_chart(
    themed_chart(monthly_profit_chart, height=300),
    width="stretch"
)

# ---------- DAILY SUMMARY LOG ----------
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
    realized_color = "#4CAF50" if realized >= 0 else "#FF5C5C"

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

/* Custom Scrollbar */
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

html, body {{
    margin: 0;
    padding: 0;
    background: transparent;
}}

html, body {{
    margin: 0;
    padding: 0;
    background: transparent;
}}

.table-shell {{
    background-color: #111814;
    border: 1px solid rgba(212, 175, 55, 0.20);
    border-radius: 22px;
    padding: 12px;
    box-shadow: 0 18px 45px rgba(0, 0, 0, 0.22);
}}

.table-scroll {{
    max-height: 650px;
    overflow-y: auto;
    border-radius: 14px;
}}

.table-grid {{
    width: 100%;
    min-width: 0;  /* 🔥 removes forced horizontal scroll */
}}

.table-row,
.table-header {{
    display: grid;

    /* 🔥 TIGHT COLUMN CONTROL */
    grid-template-columns:
        0.80fr   /* Date */
        0.7fr   /* Activity */
        0.9fr    /* Realized */
        1fr      /* Equity */
        1fr      /* Deployed */
        1fr;     /* Unsettled */

    gap: 4px;   /* 🔥 tighter spacing */
    align-items: center;
}}

.table-header {{
    padding: 8px 8px 10px 8px;
    color: #D4AF37;
    font-weight: 900;
    font-size: 12px;
    letter-spacing: 0.4px;
    text-transform: uppercase;
    border-bottom: 1px solid rgba(212, 175, 55, 0.22);
    position: sticky;
    top: 0;
    background: #111814;
    z-index: 3;
}}

.table-header div:hover {{
    color: #FFE082;
}}

.table-row {{
    padding: 8px 8px;
    color: #E8F5E9;
    font-weight: 700;
    font-size: 13px;   /* 🔥 slightly smaller */
    border-bottom: 1px solid rgba(165, 214, 167, 0.08);
    border-radius: 10px;
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
</style>

<div class="table-shell">
    <div class="table-scroll">
        <div class="table-grid" id="daily-summary-table">

            <div class="table-header">
                <div>Date</div>
                <div>Activity</div>
                <div>Realized</div>
                <div>Equity</div>
                <div>Deploy</div>
                <div>Unsettled</div>
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

components.html(daily_table_html, height=740, scrolling=False)