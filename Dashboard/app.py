import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="NSE500 · Average Range",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
  .block-container { padding-top: 2rem; padding-bottom: 1rem; max-width: 1200px; }
  div[data-testid="metric-container"] { background: #f8f9fa; border-radius: 8px; padding: 0.5rem 1rem; }
  div[data-testid="metric-container"] label { font-size: 0.75rem !important; color: #666; }
  h1 { font-size: 1.6rem !important; font-weight: 700; }
  h3 { font-size: 1rem !important; font-weight: 600; color: #333; }
  .stDataFrame { font-size: 0.85rem; }
</style>
""", unsafe_allow_html=True)

BASE_DIR = Path(__file__).parent.parent
DB_DIR = BASE_DIR / "Database"

TIMEFRAMES = {
    "Daily":      ("daily_range_pct",      "daily_range_abs",      "D"),
    "Weekly":     ("weekly_range_pct",     "weekly_range_abs",     "W"),
    "Monthly":    ("monthly_range_pct",    "monthly_range_abs",    "ME"),
    "3-Monthly":  ("quarterly_range_pct",  "quarterly_range_abs",  "QE"),
    "6-Monthly":  ("halfyearly_range_pct", "halfyearly_range_abs", "6ME"),
    "Yearly":     ("yearly_range_pct",     "yearly_range_abs",     "YE"),
    "5-Yearly":   ("fiveyearly_range_pct", "fiveyearly_range_abs", "5YE"),
}

TF_LABELS = list(TIMEFRAMES.keys())


@st.cache_data(show_spinner=False)
def load_summary() -> pd.DataFrame:
    return pd.read_parquet(DB_DIR / "avg_range_summary.parquet")


@st.cache_data(show_spinner=False)
def load_daily(symbol: str) -> pd.DataFrame:
    df = pd.read_parquet(DB_DIR / "daily_ranges.parquet")
    df["date"] = pd.to_datetime(df["date"])
    return df[df["symbol"] == symbol].set_index("date").sort_index()


def range_bar_chart(values: dict, title: str = "") -> go.Figure:
    labels = list(values.keys())
    vals = list(values.values())
    colors = px.colors.sequential.Blues[2:]
    colors = (colors * 10)[:len(labels)]
    fig = go.Figure(go.Bar(
        x=labels, y=vals,
        marker_color=colors,
        text=[f"{v:.2f}%" for v in vals],
        textposition="outside",
    ))
    fig.update_layout(
        title=title,
        height=280,
        margin=dict(t=40, b=10, l=10, r=10),
        yaxis=dict(title="Avg Range %", gridcolor="#eee"),
        xaxis=dict(tickfont=dict(size=11)),
        plot_bgcolor="white",
        paper_bgcolor="white",
        showlegend=False,
    )
    return fig


def rolling_range_chart(daily_df: pd.DataFrame, symbol: str, company: str) -> go.Figure:
    roll = daily_df["range_pct"].rolling(20, min_periods=5).mean()
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=daily_df.index, y=daily_df["range_pct"],
        mode="lines", name="Daily Range %",
        line=dict(color="#d0d8e4", width=1),
        opacity=0.6,
    ))
    fig.add_trace(go.Scatter(
        x=roll.index, y=roll,
        mode="lines", name="20-day Rolling Avg",
        line=dict(color="#2563eb", width=2),
    ))
    fig.update_layout(
        title=f"{symbol} — Daily Range % (since 2015)",
        height=300,
        margin=dict(t=40, b=10, l=10, r=10),
        yaxis=dict(title="Range %", gridcolor="#eee"),
        plot_bgcolor="white",
        paper_bgcolor="white",
        legend=dict(orientation="h", y=1.1),
    )
    return fig


def sector_chart(summary: pd.DataFrame, col: str) -> go.Figure:
    sector_avg = (
        summary.groupby("industry")[col].mean()
        .dropna()
        .sort_values(ascending=True)
    )
    fig = go.Figure(go.Bar(
        y=sector_avg.index,
        x=sector_avg.values,
        orientation="h",
        marker_color="#2563eb",
        text=[f"{v:.2f}%" for v in sector_avg.values],
        textposition="outside",
    ))
    fig.update_layout(
        height=max(300, len(sector_avg) * 28),
        margin=dict(t=10, b=10, l=10, r=60),
        xaxis=dict(title="Avg Range %", gridcolor="#eee"),
        plot_bgcolor="white",
        paper_bgcolor="white",
        showlegend=False,
    )
    return fig


# ─── LOAD DATA ────────────────────────────────────────────────────────────────
summary = load_summary()
all_sectors = ["All"] + sorted(summary["industry"].dropna().unique().tolist())

# ─── HEADER ───────────────────────────────────────────────────────────────────
st.markdown("## NSE500 · Average Range")
st.markdown("<p style='color:#666;margin-top:-12px;font-size:0.9rem;'>Price movement analysis across timeframes — NSE500 equities since 2015</p>", unsafe_allow_html=True)

# ─── CONTROLS ROW ─────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns([2, 2, 1])
with c1:
    search = st.text_input("🔍  Search equity", placeholder="Symbol or company name...", label_visibility="collapsed")
with c2:
    tf_label = st.selectbox("Timeframe", TF_LABELS, index=2, label_visibility="collapsed")
with c3:
    sector_filter = st.selectbox("Sector", all_sectors, label_visibility="collapsed")

st.markdown("---")

pct_col, abs_col, _ = TIMEFRAMES[tf_label]

# ─── FILTER SUMMARY ───────────────────────────────────────────────────────────
filtered = summary.copy()
if sector_filter != "All":
    filtered = filtered[filtered["industry"] == sector_filter]
if search.strip():
    q = search.strip().upper()
    mask = (
        filtered["symbol"].str.upper().str.contains(q, na=False) |
        filtered["company_name"].str.upper().str.contains(q, na=False)
    )
    filtered = filtered[mask]

# ─── STOCK DETAIL VIEW ────────────────────────────────────────────────────────
if len(filtered) == 1 or (search.strip() and len(filtered) <= 5 and len(filtered) >= 1):
    # If search narrows to a single stock, show detail
    if len(filtered) == 1:
        stock = filtered.iloc[0]
    else:
        # Let user pick from small result set
        pick = st.selectbox("Select stock", filtered["symbol"].tolist())
        stock = filtered[filtered["symbol"] == pick].iloc[0]

    st.markdown(f"### {stock['symbol']}  ·  {stock['company_name']}")
    st.markdown(f"<span style='color:#666;font-size:0.85rem'>{stock['industry']}  ·  Last close ₹{stock['last_close']:,.2f}  ·  Data: {stock['data_start']} → {stock['data_end']}</span>", unsafe_allow_html=True)
    st.markdown("")

    # Metrics row — all timeframes
    cols = st.columns(len(TIMEFRAMES))
    for col, (tf_name, (p_col, a_col, _)) in zip(cols, TIMEFRAMES.items()):
        val = stock.get(p_col)
        col.metric(tf_name, f"{val:.2f}%" if pd.notna(val) else "—")

    st.markdown("")

    # Bar chart + rolling chart side by side
    tf_vals = {}
    for tf_name, (p_col, _, _) in TIMEFRAMES.items():
        v = stock.get(p_col)
        if pd.notna(v):
            tf_vals[tf_name] = v

    left, right = st.columns(2)
    with left:
        st.plotly_chart(range_bar_chart(tf_vals, "Avg Range % by Timeframe"), use_container_width=True)
    with right:
        try:
            daily_df = load_daily(stock["symbol"])
            if len(daily_df) > 5:
                st.plotly_chart(rolling_range_chart(daily_df, stock["symbol"], stock["company_name"]), use_container_width=True)
        except Exception:
            st.info("Historical chart not available.")

    st.markdown("---")
    if st.button("← Back to full list"):
        st.query_params.clear()
        st.rerun()

# ─── OVERVIEW MODE ────────────────────────────────────────────────────────────
else:
    # Top stats
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Stocks shown", len(filtered))
    m2.metric("Avg Range (selected TF)", f"{filtered[pct_col].mean():.2f}%" if pct_col in filtered else "—")
    m3.metric("Highest", f"{filtered[pct_col].max():.2f}%  ({filtered.loc[filtered[pct_col].idxmax(), 'symbol'] if filtered[pct_col].notna().any() else '—'})" if filtered[pct_col].notna().any() else "—")
    m4.metric("Lowest", f"{filtered[pct_col].min():.2f}%  ({filtered.loc[filtered[pct_col].idxmin(), 'symbol'] if filtered[pct_col].notna().any() else '—'})" if filtered[pct_col].notna().any() else "—")

    st.markdown("")

    tab1, tab2 = st.tabs(["📋  Stock Table", "🏭  Sector View"])

    with tab1:
        display = (
            filtered[["symbol", "company_name", "industry", "last_close", pct_col, abs_col]]
            .rename(columns={
                "symbol": "Symbol",
                "company_name": "Company",
                "industry": "Sector",
                "last_close": "Last Close (₹)",
                pct_col: f"Avg Range % ({tf_label})",
                abs_col: f"Avg Range ₹ ({tf_label})",
            })
            .sort_values(f"Avg Range % ({tf_label})", ascending=False)
            .reset_index(drop=True)
        )
        display.index += 1
        st.dataframe(
            display.style.format({
                "Last Close (₹)": "{:,.2f}",
                f"Avg Range % ({tf_label})": "{:.2f}%",
                f"Avg Range ₹ ({tf_label})": "{:.2f}",
            }),
            use_container_width=True,
            height=500,
        )

    with tab2:
        st.markdown(f"**Average {tf_label} Range % by Sector**")
        st.plotly_chart(sector_chart(filtered, pct_col), use_container_width=True)

        sector_tbl = (
            filtered.groupby("industry")
            .agg(
                stocks=("symbol", "count"),
                avg_range_pct=(pct_col, "mean"),
                median_range_pct=(pct_col, "median"),
                max_range_pct=(pct_col, "max"),
            )
            .round(2)
            .sort_values("avg_range_pct", ascending=False)
            .rename(columns={
                "stocks": "# Stocks",
                "avg_range_pct": f"Avg Range % ({tf_label})",
                "median_range_pct": f"Median Range % ({tf_label})",
                "max_range_pct": f"Max Range % ({tf_label})",
            })
        )
        st.dataframe(sector_tbl, use_container_width=True)
