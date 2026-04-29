import streamlit as st
import pandas as pd
import altair as alt

from utils.loaders import load_daily_summary, load_open_positions_live
from utils.parsers import get_latest_daily_summary, prepare_equity_curve


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
    return f"{value * 100:+.2f}%"


def fmt_quantity(value):
    if value is None or pd.isna(value):
        return "—"
    x = float(value)
    return f"{int(x)}" if x.is_integer() else f"{x:.2f}"


st.title("Overview")

# ---------- LOAD DATA ----------
daily_data = load_daily_summary()
open_positions_payload = load_open_positions_live()

latest = get_latest_daily_summary(daily_data)
open_positions = open_positions_payload.get("positions", [])

# ---------- EQUITY STATUS CARD ----------
daily_df = pd.DataFrame(daily_data)
daily_df["summary_date_dt"] = pd.to_datetime(daily_df["summary_date"], errors="coerce")
daily_df["total_equity"] = pd.to_numeric(daily_df["total_equity"], errors="coerce")
daily_df = daily_df.dropna(subset=["summary_date_dt", "total_equity"])
daily_df = daily_df.sort_values("summary_date_dt").reset_index(drop=True)

live_total_equity = open_positions_payload.get("total_equity")
live_total_equity = pd.to_numeric(live_total_equity, errors="coerce")

if pd.isna(live_total_equity):
    live_total_equity = None

if len(daily_df) > 0:
    latest_daily_equity = daily_df["total_equity"].iloc[-1]
else:
    latest_daily_equity = None

if live_total_equity is not None:
    latest_equity = live_total_equity
    previous_equity = latest_daily_equity
else:
    latest_equity = latest_daily_equity
    previous_equity = daily_df["total_equity"].iloc[-2] if len(daily_df) > 1 else None

if latest_equity is not None and previous_equity is not None:
    equity_change = latest_equity - previous_equity
    equity_change_pct = equity_change / previous_equity if previous_equity != 0 else None
else:
    equity_change = None
    equity_change_pct = None

equity_change_text = fmt_signed_currency(equity_change)
equity_change_pct_text = (
    f"({equity_change_pct * 100:+.2f}%)"
    if equity_change_pct is not None else ""
)

change_color = "#4CAF50" if equity_change is not None and equity_change >= 0 else "#FF5C5C"

equity_card_html = f"""
<div style="
    background-color: #111814;
    border: 1px solid rgba(212, 175, 55, 0.20);
    border-radius: 22px;
    padding: 22px 24px;
    margin-bottom: 24px;
    max-width: 205px;
    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'SF Pro Text', 'Segoe UI', sans-serif;
">
    <div style="
        color: #A5D6A7;
        font-size: 16px;
        font-weight: 800;
        letter-spacing: 0.3px;
        margin-bottom: 6px;
    ">
        Total Equity
    </div>

    <div style="
        color: #FFFFFF;
        font-size: 32px;
        font-weight: 900;
        letter-spacing: -0.8px;
        line-height: 1.05;
        margin-bottom: 10px;
    ">
        {fmt_currency(latest_equity)}
    </div>

    <div style="
        color: {change_color};
        font-size: 16px;
        font-weight: 850;
    ">
        Today: {equity_change_text} {equity_change_pct_text}
    </div>
</div>
"""

st.html(equity_card_html)

# ---------- EQUITY CURVE ----------
st.subheader("Equity Curve")

dates, equity = prepare_equity_curve(daily_data)

full_equity_df = pd.DataFrame({
    "Date": pd.to_datetime(dates, errors="coerce"),
    "Equity": equity
}).dropna().sort_values("Date").reset_index(drop=True)

user_agent = st.context.headers.get("user-agent", "").lower()

is_mobile = (
    "mobile" in user_agent
    or "iphone" in user_agent
    or "android" in user_agent
)

# ---------- MOBILE RANGE SELECTOR STATE ----------
selected_range = st.session_state.get("mobile_equity_range", "MAX") if is_mobile else "MAX"

def mobile_range_selector(options, default="MAX", key="mobile_equity_range"):
    if key not in st.session_state:
        st.session_state[key] = default

    st.markdown("""
    <style>
    div[data-testid="stPills"] {
        max-width: 100% !important;
        overflow-x: hidden !important;
        margin-top: 4px !important;
        margin-bottom: 8px !important;
    }

    div[data-testid="stPills"] button {
        padding: 2px 6px !important;
        min-height: 24px !important;
        font-size: 10px !important;
        font-weight: 900 !important;
        border-radius: 999px !important;
        color: #A5D6A7 !important;
        background-color: #111814 !important;
        border: 1px solid rgba(76, 175, 80, 0.35) !important;
        white-space: nowrap !important;
    }

    div[data-testid="stPills"] button[aria-pressed="true"] {
        color: #E8F5E9 !important;
        background-color: rgba(46, 125, 50, 0.35) !important;
        border: 1px solid #4CAF50 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    selected = st.pills(
        "Equity range",
        options,
        default=st.session_state[key],
        selection_mode="single",
        label_visibility="collapsed",
        key=key,
    )

    if selected is None:
        selected = default

    return selected

def filter_equity_range(df, selected):
    if df.empty:
        return df

    latest_date = df["Date"].max()

    if selected == "1D":
        return df.tail(1)

    if selected == "1W":
        cutoff = latest_date - pd.Timedelta(days=7)
        return df[df["Date"] >= cutoff]

    if selected == "1M":
        cutoff = latest_date - pd.DateOffset(months=1)
        return df[df["Date"] >= cutoff]

    if selected == "3M":
        cutoff = latest_date - pd.DateOffset(months=3)
        return df[df["Date"] >= cutoff]

    if selected == "YTD":
        year_start = pd.Timestamp(year=latest_date.year, month=1, day=1)
        return df[df["Date"] >= year_start]

    if selected == "1Y":
        cutoff = latest_date - pd.DateOffset(years=1)
        return df[df["Date"] >= cutoff]

    return df


equity_df = filter_equity_range(full_equity_df, selected_range).copy()

# Fallback if a short range returns too little data
if len(equity_df) < 2 and len(full_equity_df) >= 2:
    equity_df = full_equity_df.tail(2).copy()

# ---------- RANGE PERFORMANCE LABEL ----------
if is_mobile and len(equity_df) >= 2:
    start_equity = equity_df["Equity"].iloc[0]
    end_equity = equity_df["Equity"].iloc[-1]

    range_change = end_equity - start_equity
    range_change_pct = range_change / start_equity if start_equity != 0 else None

    range_color = "#4CAF50" if range_change >= 0 else "#FF5C5C"

    range_change_text = fmt_signed_currency(range_change)
    range_pct_text = (
        f"({range_change_pct * 100:+.2f}%)"
        if range_change_pct is not None
        else ""
    )

    st.html(f"""
    <div style="
        color: {range_color};
        font-size: 14px;
        font-weight: 850;
        margin-top: -2px;
        margin-bottom: 8px;
        text-align: center;
    ">
        {range_change_text} {range_pct_text} · {selected_range}
    </div>
    """)

y_min = equity_df["Equity"].min()
y_max = equity_df["Equity"].max()
y_padding = max((y_max - y_min) * 0.25, 25)

y_floor = y_min - y_padding
y_ceiling = y_max + y_padding

equity_df["Baseline"] = y_floor

x_min = equity_df["Date"].min()
x_max = equity_df["Date"].max() + pd.Timedelta(days=3)

base = alt.Chart(equity_df).encode(
    x=alt.X(
        "Date:T",
        title=None,
        scale=alt.Scale(domain=[x_min, x_max]),
        axis=alt.Axis(labelAngle=0, grid=False)
    ),
    y=alt.Y(
        "Equity:Q",
        title=None,
        scale=alt.Scale(domain=[y_floor, y_ceiling], zero=False),
        axis=alt.Axis(grid=False)
    )
)

area = base.mark_area(
    opacity=0.16,
    interpolate="monotone",
    color="#4CAF50"
).encode(
    y=alt.Y(
        "Equity:Q",
        title=None,
        scale=alt.Scale(domain=[y_floor, y_ceiling], zero=False)
    ),
    y2=alt.Y2("Baseline:Q")
)

line = base.mark_line(
    strokeWidth=3,
    interpolate="monotone",
    color="#4CAF50"
)

if is_mobile:
    latest_point_df = equity_df.tail(1).copy()
    latest_point_df["Label"] = latest_point_df["Equity"].apply(lambda x: f"${x:,.2f}")

    latest_point = alt.Chart(latest_point_df).mark_circle(
        size=85,
        color="#4CAF50"
    ).encode(
        x="Date:T",
        y="Equity:Q"
    )

    latest_label = alt.Chart(latest_point_df).mark_text(
        align="left",
        dx=8,
        dy=-8,
        fontSize=12,
        fontWeight=800,
        color="#E8F5E9"
    ).encode(
        x="Date:T",
        y="Equity:Q",
        text="Label:N"
    )

    chart = (
        alt.layer(area, line, latest_point, latest_label)
        .properties(
            height=300,
            background="#111814",
            padding={"left": 0, "right": 0, "top": -5, "bottom": 7}
        )
    )

else:
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
        tooltip=[
            alt.Tooltip("Date:T", title="Date", format="%b %d, %Y"),
            alt.Tooltip("Equity:Q", title="Equity", format="$,.2f"),
        ]
    ).add_params(hover)

    points = base.mark_circle(
        size=85,
        color="#4CAF50"
    ).encode(
        opacity=alt.condition(hover, alt.value(1), alt.value(0))
    )

    rules = alt.Chart(equity_df).mark_rule(
        color="#777777"
    ).encode(
        x="Date:T",
        opacity=alt.condition(hover, alt.value(0.45), alt.value(0))
    ).add_params(hover)

    chart = (
        alt.layer(area, line, selectors, points, rules)
        .properties(
            height=400,
            background="#111814",
            padding={"left": 5, "right": -7, "top": -5, "bottom": 7}
        )
    )

chart = (
    chart
    .configure_view(strokeWidth=0)
    .configure_axis(
        labelFont="Segoe UI",
        titleFont="Segoe UI",
        labelFontSize=10,
        titleFontSize=15,
        labelFontWeight=600,
        titleFontWeight=800,
        labelColor="#E8F5E9",
        titleColor="#D4AF37",
        gridColor="#2E7D32",
        gridOpacity=0.16,
        domain=False,
        tickColor="#2E7D32",
        labelPadding=12
    )
)

st.altair_chart(chart, width="stretch")
if is_mobile:
    selected_range = mobile_range_selector(
        ["1D", "1W", "1M", "3M", "YTD", "1Y", "MAX"],
        default="MAX",
        key="mobile_equity_range"
    )

# ---------- OPEN POSITIONS ----------
st.subheader("Open Positions")

if not open_positions:
    st.info("No open positions found.")
else:
    positions_df = pd.DataFrame(open_positions)

    def value_color(value):
        if value is None or pd.isna(value):
            return "#E8F5E9"
        return "#4CAF50" if value >= 0 else "#FF5C5C"

    def sort_value(value):
        if value is None or pd.isna(value):
            return ""
        return value

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
        overflow-x: auto;
        overflow-y: auto;
        border-radius: 14px;
    }

    .table-grid {
        width: 100%;
        min-width: 660px;
    }

    .table-row,
    .table-header {
        display: grid;
        grid-template-columns: 0.75fr 1fr 0.5fr 1fr 1.15fr 1.15fr;
        gap: 8px;
        align-items: center;
    }

    .table-header {
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
            min-width: 620px;
        }

        .table-row,
        .table-header {
            grid-template-columns: 0.75fr 1fr 0.5fr 1fr 1.15fr 1.15fr;
            gap: 6px;
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
            <div class="table-grid" id="positions-table">
                <div class="table-header">
                    <div data-key="symbol" data-type="text">Symbol<span class="sort-indicator"></span></div>
                    <div data-key="entry" data-type="number">Entry<span class="sort-indicator"></span></div>
                    <div data-key="qty" data-type="number">Qty<span class="sort-indicator"></span></div>
                    <div data-key="close" data-type="number">Close<span class="sort-indicator"></span></div>
                    <div data-key="pl" data-type="number">Unrealized $<span class="sort-indicator"></span></div>
                    <div data-key="pct" data-type="number">Unrealized %<span class="sort-indicator"></span></div>
                </div>
    """

    for _, row in positions_df.iterrows():
        symbol = row.get("symbol", "—")
        entry_price = row.get("entry_price")
        quantity = row.get("quantity")
        last_close = row.get("last_close")
        unrealized_pl = row.get("unrealized_pl")
        unrealized_pl_pct = row.get("unrealized_pl_pct")

        entry_text = fmt_currency(entry_price)
        qty_text = fmt_quantity(quantity)
        close_text = fmt_currency(last_close)
        pl_text = fmt_signed_currency(unrealized_pl)
        pct_text = fmt_pct(unrealized_pl_pct)
        pl_color = value_color(unrealized_pl)
        pct_color = value_color(unrealized_pl_pct)

        cards_html += f"""
                <div class="table-row"
                    data-symbol="{symbol}"
                    data-entry="{sort_value(entry_price)}"
                    data-qty="{sort_value(quantity)}"
                    data-close="{sort_value(last_close)}"
                    data-pl="{sort_value(unrealized_pl)}"
                    data-pct="{sort_value(unrealized_pl_pct)}"
                >
                    <div class="symbol">{symbol}</div>
                    <div class="money">{entry_text}</div>
                    <div class="muted">{qty_text}</div>
                    <div class="money">{close_text}</div>
                    <div class="pl" style="color:{pl_color};">{pl_text}</div>
                    <div class="pl" style="color:{pct_color};">{pct_text}</div>
                </div>
        """

    cards_html += """
            </div>
        </div>
    </div>

    <script>
    const table = document.getElementById("positions-table");
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

    st.iframe(cards_html, height=740)