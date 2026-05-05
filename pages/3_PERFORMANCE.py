import json
from pathlib import Path
from html import escape

import pandas as pd
import streamlit as st

from utils.loaders import load_daily_summary, load_capital_flow_analysis


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
        ("Label", "Value", "tone", "note", True),
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
        background:
            radial-gradient(circle at top right, rgba(212, 175, 55, 0.10), transparent 34%),
            #111814;
        border-color: rgba(212, 175, 55, 0.36);
        box-shadow:
            0 18px 45px rgba(0, 0, 0, 0.18),
            0 0 0 1px rgba(212, 175, 55, 0.05);
    }}

    .metric-label {{
        color: #A5D6A7;
        font-size: 12.5px;
        font-weight: 850;
        line-height: 1.15;
        margin-bottom: 8px;
    }}

    .metric-card.highlight .metric-label {{
        color: #D4AF37;
    }}

    .metric-value {{
        font-weight: 950;
        letter-spacing: -0.4px;
        line-height: 1.18;
        padding-bottom: 2px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}

    .metric-note {{
        color: #CFE8D2;
        font-size: 11.5px;
        font-weight: 700;
        line-height: 1.2;
        margin-top: 10px;
        opacity: 0.82;
    }}

    @media (max-width: 700px) {{
        .metric-grid {{
            gap: 8px;
            margin-bottom: 11px;
        }}

        .metric-card {{
            border-radius: 12px;
            padding: 8px 9px;
            min-height: 53px;
        }}

        .metric-label {{
            font-size: 10.5px;
            margin-bottom: 4px;
            line-height: 1.05;
        }}

        .metric-value {{
            font-size: 18px !important;
            letter-spacing: -0.25px;
            line-height: 1.16;
            padding-bottom: 2px;
        }}

        .metric-note {{
            font-size: 9.5px;
            margin-top: 7px;
            line-height: 1.1;
        }}
    }}
    </style>

    <div class="metric-grid">
    """

    for idx, metric in enumerate(metrics):
        label = metric[0]
        value = metric[1]

        tone = metric[2] if len(metric) >= 3 else infer_tone(value)
        note = metric[3] if len(metric) >= 4 else ""
        highlight_this = metric[4] if len(metric) >= 5 else False

        value_color = tone_color(tone)
        value_size = metric_value_size(value)

        highlight_class = "highlight" if highlight_this or (highlight_last and idx == len(metrics) - 1) else ""

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

    @media (max-width: 700px) {
        .headline-grid {
            gap: 8px;
            margin-bottom: 12px;
        }

        .headline-card {
            border-radius: 14px;
            padding: 10px 10px;
            min-height: 63px;
        }

        .headline-label {
            font-size: 10.5px;
            margin-bottom: 5px;
        }

        .headline-value {
            font-size: 22px;
            letter-spacing: -0.35px;
        }
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


def narrative_card(title, text):
    safe_title = escape(str(title))
    safe_text = escape(str(text)).replace("\n", "<br>")

    card_html = f"""
    <style>
    .narrative-card {{
        background:
            radial-gradient(circle at top right, rgba(212, 175, 55, 0.08), transparent 34%),
            #111814;
        border: 1px solid rgba(212, 175, 55, 0.24);
        border-radius: 22px;
        padding: 17px 16px;
        margin-bottom: 18px;
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Segoe UI", sans-serif;
    }}

    .narrative-title {{
        color: #D4AF37;
        font-size: 14px;
        font-weight: 950;
        margin-bottom: 10px;
    }}

    .narrative-text {{
        color: #CFE8D2;
        font-size: 14.5px;
        font-weight: 750;
        line-height: 1.45;
    }}

    @media (max-width: 700px) {{
        .narrative-card {{
            border-radius: 14px;
            padding: 11px 10px;
            margin-bottom: 12px;
        }}

        .narrative-title {{
            font-size: 12px;
            margin-bottom: 7px;
        }}

        .narrative-text {{
            font-size: 12px;
            line-height: 1.35;
        }}
    }}
    </style>

    <div class="narrative-card">
        <div class="narrative-title">{safe_title}</div>
        <div class="narrative-text">{safe_text}</div>
    </div>
    """

    st.html(card_html)


def get_capital_display(capital_flow, group, key, default="—"):
    value = (
        capital_flow
        .get("group_summaries", {})
        .get(group, {})
        .get("display", {})
        .get(key)
    )

    if value in [None, "N/A"]:
        return default

    return value


def pressure_level_color(level):
    level = str(level).lower()

    if level == "minor":
        return "#A5D6A7"

    if level == "medium":
        return "#D4AF37"

    if level == "major":
        return "#FFB74D"

    return "#FFFFFF"


def capital_flow_cycle_table(cycles, max_rows=30):
    if not cycles:
        st.info("No completed downside pressure cycles found.")
        return

    display_cycles = list(reversed(cycles))[:max_rows]
    rows_html = ""

    for cycle in display_cycles:
        display = cycle.get("display", {})

        level = cycle.get("pressure_level", "—")
        level_display = display.get("pressure_level_display", str(level).title())
        level_color = pressure_level_color(level)

        rows_html += f"""
            <div class="cfs-row"
                data-cycle="{cycle.get("cycle_number", 0)}"
                data-level="{escape(str(level_display))}"
                data-peak="{escape(str(cycle.get("peak_date", "")))}"
                data-trough="{escape(str(cycle.get("trough_date", "")))}"
                data-restored="{escape(str(cycle.get("restored_date", "")))}"
                data-depth="{cycle.get("depth_pct", 0)}"
                data-pressure="{cycle.get("pressure_duration_days", 0)}"
                data-restore="{cycle.get("restoration_time_days", 0)}"
                data-cycledays="{cycle.get("total_cycle_days", 0)}"               
            >
                <div class="muted">{cycle.get("cycle_number", "—")}</div>
                <div class="level-pill" style="color:{level_color}; border-color:{level_color};">{escape(str(level_display))}</div>
                <div class="muted">{escape(str(cycle.get("peak_date", "—")))}</div>
                <div class="muted">{escape(str(cycle.get("trough_date", "—")))}</div>
                <div class="muted">{escape(str(cycle.get("restored_date", "—")))}</div>
                <div class="negative">{escape(str(display.get("depth_display", "—")))}</div>
                <div class="money">{escape(str(display.get("pressure_duration_display", "—")))}</div>
                <div class="money">{escape(str(display.get("restoration_time_display", "—")))}</div>
                <div class="money">{escape(str(display.get("total_cycle_display", "—")))}</div>
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

    .cfs-shell {{
        background-color: #111814;
        border: 1px solid rgba(212, 175, 55, 0.20);
        border-radius: 22px;
        padding: 14px;
        box-shadow: 0 18px 45px rgba(0, 0, 0, 0.22);
    }}

    .cfs-scroll {{
        max-height: 560px;
        overflow-x: auto;
        overflow-y: auto;
        border-radius: 14px;
    }}

    .cfs-grid {{
        width: 100%;
        min-width: 900px;
    }}

    .cfs-header,
    .cfs-row {{
        display: grid;
        grid-template-columns: 0.42fr 0.75fr 0.85fr 0.85fr 0.85fr 0.65fr 0.9fr 0.9fr 0.9fr;
        gap: 8px;
        align-items: center;
    }}

    .cfs-header {{
        padding: 10px 10px 12px 10px;
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

    .cfs-header div[data-key] {{
        cursor: pointer;
        user-select: none;
    }}

    .cfs-header div[data-key]:hover {{
        color: #FFE082;
    }}

    .sort-indicator {{
        opacity: 0.75;
        font-size: 11px;
        margin-left: 4px;
    }}

    .cfs-row {{
        padding: 11px 10px;
        color: #E8F5E9;
        font-weight: 750;
        font-size: 13px;
        border-bottom: 1px solid rgba(165, 214, 167, 0.08);
        border-radius: 12px;
    }}

    .cfs-row:hover {{
        background-color: rgba(212, 175, 55, 0.055);
    }}

    .level-pill {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        border: 1px solid;
        border-radius: 999px;
        padding: 3px 8px;
        font-size: 11px;
        font-weight: 950;
        text-transform: uppercase;
        width: fit-content;
    }}

    .money {{
        color: #F2FFF4;
        font-weight: 800;
    }}

    .muted {{
        color: #CFE8D2;
        font-weight: 750;
    }}

    .negative {{
        color: #FF5C5C;
        font-weight: 950;
    }}

    @media (max-width: 700px) {{
        .cfs-shell {{
            border-radius: 18px;
            padding: 10px;
        }}

        .cfs-scroll {{
            max-height: 520px;
            border-radius: 12px;
        }}

        .cfs-grid {{
            min-width: 850px;
        }}

        .cfs-header {{
            font-size: 11px;
        }}

        .cfs-row {{
            font-size: 12px;
        }}
    }}
    </style>

    <div class="cfs-shell">
        <div class="cfs-scroll">
            <div class="cfs-grid" id="capital-flow-table">
                <div class="cfs-header">
                    <div data-key="cycle" data-type="number">#<span class="sort-indicator"></span></div>
                    <div data-key="level" data-type="text">Level<span class="sort-indicator"></span></div>
                    <div data-key="peak" data-type="text">Peak<span class="sort-indicator"></span></div>
                    <div data-key="trough" data-type="text">Trough<span class="sort-indicator"></span></div>
                    <div data-key="restored" data-type="text">Restored<span class="sort-indicator"></span></div>
                    <div data-key="depth" data-type="number">Depth<span class="sort-indicator"></span></div>
                    <div data-key="pressure" data-type="number">Pressure<span class="sort-indicator"></span></div>
                    <div data-key="restore" data-type="number">Restore<span class="sort-indicator"></span></div>
                    <div data-key="cycledays" data-type="number">Cycle<span class="sort-indicator"></span></div>
                </div>

                {rows_html}
            </div>
        </div>
    </div>

    <script>
    const table = document.getElementById("capital-flow-table");
    const headers = table.querySelectorAll(".cfs-header div[data-key]");
    let currentSort = {{ key: "cycle", direction: "desc" }};

    headers.forEach(header => {{
        header.addEventListener("click", () => {{
            const key = header.dataset.key;
            const type = header.dataset.type;

            let direction = "asc";
            if (currentSort.key === key && currentSort.direction === "asc") {{
                direction = "desc";
            }}

            currentSort = {{ key, direction }};

            const rows = Array.from(table.querySelectorAll(".cfs-row"));

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

    st.iframe(table_html, height=650)


# ============================================================
# LOAD DATA
# ============================================================

snapshot = load_performance_snapshot()
capital_flow = load_capital_flow_analysis()
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
        infer_tone(get_display(snapshot, "trade_quality", "average_profit_per_move_display")),
        "",
        True,
    ),
    (
        "Average Moves per Day",
        get_display(snapshot, "trade_quality", "average_moves_per_day_display"),
        "neutral",
    ),
    (
        "Average Realized Profit per Day",
        get_display(snapshot, "trade_quality", "average_realized_profit_per_day_display"),
        infer_tone(get_display(snapshot, "trade_quality", "average_realized_profit_per_day_display")),
        "",
        True,
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
        infer_tone(get_display(snapshot, "monthly_consistency", "average_monthly_realized_profit_display")),
        "",
        True,
    ),
    (
        "Average Monthly Equity Growth",
        get_display(snapshot, "monthly_consistency", "average_monthly_equity_growth_display"),
        infer_tone(get_display(snapshot, "monthly_consistency", "average_monthly_equity_growth_display")),
        "",
        True,
    ),
], desktop_columns=2, mobile_columns=2)


# ============================================================
# DAILY CONSISTENCY
# ============================================================

st.subheader("Daily Consistency")
section_note("Realized profit/loss tracks completed moves.")

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
        "",
        True,
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
        "Return quality after volatility",
    ),
    (
        "Sortino Ratio",
        get_display(snapshot, "capital_behavior", "sortino_ratio_display"),
        "neutral",
        "Return quality after downside",
    ),
    (
        "Calmar Ratio",
        get_display(snapshot, "capital_behavior", "calmar_ratio_display"),
        "neutral",
        "Return quality after drawdown",
    ),
], desktop_columns=3, mobile_columns=2)

metric_cards([
    (
        "Capital Utilization",
        get_display(snapshot, "capital_behavior", "capital_utilization_display"),
        "neutral",
        "Average capital deployed",
        False,
    ),
    (
        "Return on Deployed Capital",
        get_display(snapshot, "capital_behavior", "return_on_deployed_capital_display"),
        infer_tone(get_display(snapshot, "capital_behavior", "return_on_deployed_capital_display")),
        "Return from deployed capital",
        True,
    ),
], desktop_columns=2, mobile_columns=1)


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
        True,
    ),
], desktop_columns=1, mobile_columns=1)


# ============================================================
# CAPITAL FLOW STABILITY
# ============================================================

st.subheader("Capital Flow Stability")

if not capital_flow:
    st.info("No capital flow analysis found. Run capital_flow_stability.py first.")
else:
    narrative_card(
        "Downside Pressure Handling",
        capital_flow.get(
            "interpretation",
            "Capital Flow Stability analysis is available."
        )
    )

    summary_display = capital_flow.get("summary", {}).get("display", {})

    metric_cards([
        (
            "Completed Pressure Cycles",
            summary_display.get("completed_cycles_display", "—"),
            "neutral",
        ),
        (
            "Avg Pressure Depth",
            summary_display.get("avg_depth_display", "—"),
            "neutral",
        ),
        (
            "Max Pressure Depth",
            summary_display.get("max_depth_display", "—"),
            "negative",
        ),
        (
            "Avg Restoration Time",
            summary_display.get("avg_restoration_time_display", "—"),
            "neutral",
        ),
        (
            "Max Restoration Time",
            summary_display.get("max_restoration_time_display", "—"),
            "neutral",
        ),
    ], desktop_columns=3, mobile_columns=2)

    metric_cards([
        (
            "Depth vs Restoration",
            summary_display.get("depth_vs_restoration_slope_display", "—"),
            "neutral",
            "Days added per 1% pressure",
            True,
        ),
    ], desktop_columns=1, mobile_columns=1)

    section_note(
        "Most recent cycles shown first. Click a column header to sort."
    )

    metric_cards([
        (
            "Minor Pressure",
            get_capital_display(capital_flow, "minor", "completed_cycles_display"),
            "neutral",
            f"Avg depth {get_capital_display(capital_flow, 'minor', 'avg_depth_display')} | restored {get_capital_display(capital_flow, 'minor', 'avg_restoration_time_display')}",
        ),
        (
            "Medium Pressure",
            get_capital_display(capital_flow, "medium", "completed_cycles_display"),
            "gold",
            f"Avg depth {get_capital_display(capital_flow, 'medium', 'avg_depth_display')} | restored {get_capital_display(capital_flow, 'medium', 'avg_restoration_time_display')}",
            True,
        ),
        (
            "Major Pressure",
            get_capital_display(capital_flow, "major", "completed_cycles_display"),
            "neutral",
            f"Avg depth {get_capital_display(capital_flow, 'major', 'avg_depth_display')} | restored {get_capital_display(capital_flow, 'major', 'avg_restoration_time_display')}",
        ),
    ], desktop_columns=3, mobile_columns=1)

    unresolved = capital_flow.get("current_unresolved_pressure")

    if unresolved:
        unresolved_display = unresolved.get("display", {})

        context_card(
            "Current Downside Pressure",
            unresolved_display.get("current_depth_display", "—"),
            (
                f"Current equity is below the latest high by "
                f"{unresolved_display.get('current_depth_display', '—')}. "
                f"Peak date: {unresolved.get('peak_date', '—')}. "
                f"Business days since peak: "
                f"{unresolved_display.get('business_days_since_peak_display', '—')}."
            ),
        )

    st.markdown("### Completed Pressure Cycle Breakdown")
    section_note(
        "Most recent cycles shown first. Click a column header to sort. RDR = restoration dominance ratio."
    )

    capital_flow_cycle_table(
        capital_flow.get("cycles", []),
        max_rows=30
    )