import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(
    page_title="Average Range · NSE500",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── PALETTE ───────────────────────────────────────────────────────────────────
BG        = "#0e1117"
CARD      = "#161b27"
BORDER    = "#232736"
ACCENT    = "#5b6af0"
ACCENT2   = "#818cf8"
TEXT      = "#f0f2f8"
MUTED     = "#5a6178"
SUCCESS   = "#34d399"
WARN      = "#f59e0b"
GRID      = "#1c2030"

TF_COLORS = ["#3730a3","#4338ca","#5b6af0","#818cf8","#a5b4fc","#c7d2fe","#e0e7ff"]
SECTOR_COLORSCALE = [[0,"#1e2a4a"],[0.5,"#5b6af0"],[1.0,"#a5b4fc"]]

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, .stApp {{ background-color:{BG}; font-family:'Inter',sans-serif; }}
.block-container {{ padding:1.75rem 2.5rem 1rem; max-width:1280px; }}

/* ── Cards ── */
.card {{
  background:{CARD}; border:1px solid {BORDER};
  border-radius:14px; padding:1.25rem 1.5rem; margin-bottom:1rem;
}}
.card-sm {{
  background:{CARD}; border:1px solid {BORDER};
  border-radius:10px; padding:0.9rem 1.1rem;
}}

/* ── Metrics ── */
div[data-testid="metric-container"] {{
  background:{CARD}; border:1px solid {BORDER};
  border-radius:10px; padding:0.8rem 1rem;
}}
div[data-testid="metric-container"] label {{
  font-size:0.68rem !important; color:{MUTED} !important;
  text-transform:uppercase; letter-spacing:.06em; font-weight:600;
}}
div[data-testid="metric-container"] [data-testid="stMetricValue"] {{
  font-size:1.45rem !important; color:{TEXT} !important; font-weight:700;
}}
div[data-testid="stMetricDelta"] {{ font-size:0.75rem !important; }}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {{ gap:0; border-bottom:1px solid {BORDER}; background:transparent; }}
.stTabs [data-baseweb="tab"] {{
  background:transparent; color:{MUTED}; border:none;
  border-bottom:2px solid transparent; padding:.6rem 1.2rem;
  font-size:.83rem; font-weight:500; border-radius:0;
}}
.stTabs [aria-selected="true"] {{
  color:{ACCENT2} !important; border-bottom:2px solid {ACCENT2} !important;
  background:transparent !important;
}}
.stTabs [data-baseweb="tab-panel"] {{ padding-top:1.25rem; }}

/* ── Inputs ── */
.stTextInput>div>div {{ background:{CARD} !important; border:1px solid {BORDER} !important; border-radius:9px !important; }}
.stTextInput input {{ color:{TEXT} !important; font-size:.9rem !important; }}
.stSelectbox>div>div {{ background:{CARD} !important; border:1px solid {BORDER} !important; border-radius:9px !important; }}
div[data-baseweb="select"] span {{ color:{TEXT} !important; }}

/* ── Radio (timeframe pills) ── */
div[data-testid="stHorizontalBlock"] .stRadio label {{
  background:{CARD}; border:1px solid {BORDER}; border-radius:8px;
  padding:.3rem .9rem; margin-right:.4rem; font-size:.8rem; color:{MUTED};
  cursor:pointer; transition:all .15s;
}}
div[data-testid="stHorizontalBlock"] .stRadio label:hover {{ border-color:{ACCENT}; color:{ACCENT2}; }}
.stRadio [aria-checked="true"] label {{ background:{ACCENT}22; border-color:{ACCENT}; color:{TEXT}; font-weight:600; }}

/* ── Table ── */
.stDataFrame {{ border-radius:10px; overflow:hidden; }}
.stDataFrame thead tr th {{ background:{CARD} !important; color:{MUTED} !important; font-size:.75rem !important; text-transform:uppercase; letter-spacing:.05em; }}
.stDataFrame tbody tr:hover {{ background:#1e2438 !important; }}

/* ── Misc ── */
hr {{ border-color:{BORDER} !important; margin:.75rem 0; }}
h1,h2,h3,h4 {{ color:{TEXT} !important; }}
.stButton button {{
  background:{CARD}; border:1px solid {BORDER}; color:{MUTED};
  border-radius:8px; font-size:.82rem; padding:.35rem 1rem;
}}
.stButton button:hover {{ border-color:{ACCENT}; color:{TEXT}; }}
p {{ color:{TEXT}; }}
</style>
""", unsafe_allow_html=True)

# ── DATA ──────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
DB_DIR   = BASE_DIR / "Database"

TIMEFRAMES = {
    "Daily":      ("daily_range_pct",      "daily_range_abs"),
    "Weekly":     ("weekly_range_pct",     "weekly_range_abs"),
    "Monthly":    ("monthly_range_pct",    "monthly_range_abs"),
    "3-Monthly":  ("quarterly_range_pct",  "quarterly_range_abs"),
    "6-Monthly":  ("halfyearly_range_pct", "halfyearly_range_abs"),
    "Yearly":     ("yearly_range_pct",     "yearly_range_abs"),
    "5-Yearly":   ("fiveyearly_range_pct", "fiveyearly_range_abs"),
}
TF_LABELS = list(TIMEFRAMES.keys())

@st.cache_data(show_spinner=False)
def load_summary():
    return pd.read_parquet(DB_DIR / "avg_range_summary.parquet")

@st.cache_data(show_spinner=False)
def load_stock_daily(symbol: str):
    df = pd.read_parquet(DB_DIR / "daily_ranges.parquet")
    df["date"] = pd.to_datetime(df["date"])
    return df[df["symbol"] == symbol].set_index("date").sort_index()

def chart_defaults(height=300, t=36, b=20, l=10, r=20):
    return dict(
        height=height,
        plot_bgcolor=CARD, paper_bgcolor=CARD,
        margin=dict(t=t, b=b, l=l, r=r),
        font=dict(color=TEXT, family="Inter, sans-serif", size=11),
        xaxis=dict(gridcolor=GRID, linecolor=BORDER, tickfont=dict(color=MUTED, size=10), zeroline=False),
        yaxis=dict(gridcolor=GRID, linecolor=BORDER, tickfont=dict(color=MUTED, size=10), zeroline=False),
        hoverlabel=dict(bgcolor="#1e2438", bordercolor=BORDER, font=dict(color=TEXT, size=12)),
        legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="rgba(0,0,0,0)", font=dict(color=MUTED, size=10)),
    )

# ── CHARTS ────────────────────────────────────────────────────────────────────

def tf_bar_chart(values: dict) -> go.Figure:
    labels = list(values.keys())
    vals   = list(values.values())
    fig = go.Figure(go.Bar(
        x=labels, y=vals,
        marker=dict(
            color=vals,
            colorscale=[[0, TF_COLORS[0]], [1, TF_COLORS[-1]]],
            showscale=False,
            line=dict(width=0),
        ),
        text=[f"{v:.2f}%" for v in vals],
        textposition="outside",
        textfont=dict(color=TEXT, size=11),
        hovertemplate="<b>%{x}</b><br>Avg Range: %{y:.2f}%<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text="Avg Range % · All Timeframes", font=dict(color=TEXT, size=13), x=0),
        yaxis_title="Avg Range %",
        yaxis=dict(ticksuffix="%", gridcolor=GRID, tickfont=dict(color=MUTED, size=10)),
        **{k: v for k, v in chart_defaults(height=290, t=44).items() if k not in ("yaxis",)},
    )
    return fig


def rolling_chart(daily_df: pd.DataFrame, symbol: str) -> go.Figure:
    raw  = daily_df["range_pct"]
    roll = raw.rolling(20, min_periods=5).mean()
    fig  = go.Figure()
    fig.add_trace(go.Scatter(
        x=raw.index, y=raw,
        mode="lines", name="Daily",
        line=dict(color=ACCENT+"55", width=1),
        hovertemplate="%{x|%b %d, %Y}<br>Range: %{y:.2f}%<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=roll.index, y=roll,
        mode="lines", name="20-day avg",
        line=dict(color=ACCENT2, width=2),
        hovertemplate="%{x|%b %d, %Y}<br>Rolling avg: %{y:.2f}%<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text=f"{symbol} · Daily Range % History", font=dict(color=TEXT, size=13), x=0),
        yaxis=dict(ticksuffix="%", gridcolor=GRID, tickfont=dict(color=MUTED, size=10)),
        **{k: v for k, v in chart_defaults(height=290, t=44).items() if k not in ("yaxis",)},
    )
    return fig


def sector_bar_chart(sector_avg: pd.Series, tf_label: str) -> go.Figure:
    colors = [
        f"rgba(91,106,240,{0.45 + 0.55 * (v - sector_avg.min()) / max(sector_avg.max() - sector_avg.min(), 0.01)})"
        for v in sector_avg.values
    ]
    fig = go.Figure(go.Bar(
        y=sector_avg.index,
        x=sector_avg.values,
        orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=[f"  {v:.2f}%" for v in sector_avg.values],
        textposition="outside",
        textfont=dict(color=TEXT, size=11),
        hovertemplate="<b>%{y}</b><br>Avg Range: %{x:.2f}%<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text=f"Sector Avg Range % · {tf_label}", font=dict(color=TEXT, size=13), x=0),
        xaxis=dict(ticksuffix="%", gridcolor=GRID, tickfont=dict(color=MUTED, size=10)),
        yaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(color=TEXT, size=11)),
        height=max(320, len(sector_avg) * 30),
        **{k: v for k, v in chart_defaults(t=44, b=20, l=10, r=60).items()
           if k not in ("height", "xaxis", "yaxis")},
    )
    return fig


# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown(
    f"<h1 style='margin-bottom:2px;font-size:1.5rem;font-weight:700;'>NSE500 · Average Range</h1>"
    f"<p style='color:{MUTED};font-size:.83rem;margin-top:0;margin-bottom:1.2rem;'>"
    f"Price movement analysis across timeframes — 501 equities · 2015 → 2026</p>",
    unsafe_allow_html=True,
)

# ── CONTROLS ──────────────────────────────────────────────────────────────────
summary     = load_summary()
all_sectors = ["All"] + sorted(summary["industry"].dropna().unique().tolist())

ctrl1, ctrl2, ctrl3 = st.columns([2.4, 3, 1.6])
with ctrl1:
    search = st.text_input("", placeholder="🔍  Search by symbol or company…", label_visibility="collapsed")
with ctrl2:
    tf_label = st.radio("", TF_LABELS, index=2, horizontal=True, label_visibility="collapsed")
with ctrl3:
    sector_filter = st.selectbox("", all_sectors, label_visibility="collapsed")

st.markdown(f"<hr style='border-color:{BORDER};margin:.5rem 0 1.2rem;'>", unsafe_allow_html=True)

pct_col, abs_col = TIMEFRAMES[tf_label]

# ── FILTER ────────────────────────────────────────────────────────────────────
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

# ═══════════════════════════════════════════════════════════════════════════════
# STOCK DETAIL VIEW
# ═══════════════════════════════════════════════════════════════════════════════
if search.strip() and 1 <= len(filtered) <= 10:
    if len(filtered) == 1:
        stock = filtered.iloc[0]
    else:
        sym_options = filtered["symbol"].tolist()
        pick = st.selectbox(
            f"{len(filtered)} matches — select one:",
            sym_options,
            format_func=lambda s: f"{s}  ·  {filtered.loc[filtered['symbol']==s,'company_name'].values[0]}",
        )
        stock = filtered[filtered["symbol"] == pick].iloc[0]

    # Stock header card
    sector_color = ACCENT2
    st.markdown(f"""
    <div class="card" style="border-left:3px solid {ACCENT};padding-left:1.4rem;">
      <div style="font-size:1.2rem;font-weight:700;color:{TEXT};">{stock['symbol']} &nbsp;·&nbsp; {stock['company_name']}</div>
      <div style="margin-top:.35rem;font-size:.8rem;color:{MUTED};">
        <span style="background:{ACCENT}22;color:{ACCENT2};border-radius:5px;padding:.15rem .6rem;font-weight:500;">{stock['industry']}</span>
        &nbsp;&nbsp;Last Close <span style="color:{TEXT};font-weight:600;">₹{stock['last_close']:,.2f}</span>
        &nbsp;&nbsp;Data <span style="color:{TEXT};">{stock['data_start']} → {stock['data_end']}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Metrics row — all 7 timeframes
    mcols = st.columns(7)
    for col, (tf_name, (p_col, a_col)) in zip(mcols, TIMEFRAMES.items()):
        val = stock.get(p_col)
        abs_val = stock.get(a_col)
        col.metric(
            tf_name,
            f"{val:.2f}%" if pd.notna(val) else "—",
            delta=f"₹{abs_val:.2f}" if pd.notna(abs_val) else None,
            delta_color="off",
        )

    st.markdown("")

    # Charts
    tf_vals = {k: stock.get(v[0]) for k, v in TIMEFRAMES.items() if pd.notna(stock.get(v[0]))}
    left, right = st.columns(2)
    with left:
        st.markdown(f"<div class='card' style='padding:.75rem;'>", unsafe_allow_html=True)
        st.plotly_chart(tf_bar_chart(tf_vals), use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.markdown(f"<div class='card' style='padding:.75rem;'>", unsafe_allow_html=True)
        try:
            daily_df = load_stock_daily(stock["symbol"])
            if len(daily_df) > 5:
                st.plotly_chart(rolling_chart(daily_df, stock["symbol"]), use_container_width=True, config={"displayModeBar": False})
        except Exception:
            st.info("Historical data not available.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("")
    if st.button("← Back to full list"):
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# OVERVIEW MODE
# ═══════════════════════════════════════════════════════════════════════════════
else:
    valid = filtered[pct_col].dropna()

    # KPI cards
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Equities", f"{len(filtered)}")
    k2.metric("Avg Range", f"{valid.mean():.2f}%" if len(valid) else "—")
    k3.metric("Median",    f"{valid.median():.2f}%" if len(valid) else "—")
    if len(valid):
        hi_sym = filtered.loc[valid.idxmax(), "symbol"]
        lo_sym = filtered.loc[valid.idxmin(), "symbol"]
        k4.metric("Highest", f"{valid.max():.2f}%", delta=hi_sym, delta_color="off")
        k5.metric("Lowest",  f"{valid.min():.2f}%",  delta=lo_sym,  delta_color="off")

    st.markdown("")

    tab1, tab2 = st.tabs(["  Stock Table  ", "  Sector View  "])

    # ── TABLE TAB ──────────────────────────────────────────────────────────────
    with tab1:
        col_a, col_b = st.columns([3, 1])
        with col_b:
            show_abs = st.toggle("Show ₹ absolute", value=False)

        display_cols = ["symbol", "company_name", "industry", "last_close", pct_col]
        col_rename   = {
            "symbol":       "Symbol",
            "company_name": "Company",
            "industry":     "Sector",
            "last_close":   "Last Close (₹)",
            pct_col:        f"Avg Range % · {tf_label}",
        }
        if show_abs:
            display_cols.append(abs_col)
            col_rename[abs_col] = f"Avg Range ₹ · {tf_label}"

        display = (
            filtered[display_cols]
            .rename(columns=col_rename)
            .sort_values(f"Avg Range % · {tf_label}", ascending=False)
            .reset_index(drop=True)
        )
        display.index += 1

        fmt = {
            "Last Close (₹)": "{:,.2f}",
            f"Avg Range % · {tf_label}": "{:.2f}%",
        }
        if show_abs:
            fmt[f"Avg Range ₹ · {tf_label}"] = "{:.2f}"

        st.dataframe(
            display.style
                .format(fmt)
                .background_gradient(subset=[f"Avg Range % · {tf_label}"], cmap="Blues"),
            use_container_width=True,
            height=520,
        )

    # ── SECTOR TAB ────────────────────────────────────────────────────────────
    with tab2:
        sector_avg = (
            filtered.groupby("industry")[pct_col].mean()
            .dropna().sort_values(ascending=True)
        )

        st.plotly_chart(
            sector_bar_chart(sector_avg, tf_label),
            use_container_width=True,
            config={"displayModeBar": False},
        )

        st.markdown(f"<p style='color:{MUTED};font-size:.8rem;margin-top:.5rem;'>Sector breakdown</p>", unsafe_allow_html=True)
        sector_tbl = (
            filtered.groupby("industry")
            .agg(
                Stocks   =("symbol",  "count"),
                **{f"Avg % · {tf_label}":    (pct_col, "mean")},
                **{f"Median % · {tf_label}": (pct_col, "median")},
                **{f"Max % · {tf_label}":    (pct_col, "max")},
                **{f"Min % · {tf_label}":    (pct_col, "min")},
            )
            .round(2)
            .sort_values(f"Avg % · {tf_label}", ascending=False)
        )
        st.dataframe(
            sector_tbl.style.background_gradient(subset=[f"Avg % · {tf_label}"], cmap="Blues"),
            use_container_width=True,
        )
