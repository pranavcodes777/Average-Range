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
BG     = "#0e1117"
CARD   = "#161b27"
BORDER = "#232736"
ACCENT = "#5b6af0"
A2     = "#818cf8"
TEXT   = "#f0f2f8"
MUTED  = "#5a6178"
GRID   = "#1c2030"

ICE_BG     = "rgba(100,180,255,0.05)"
ICE_BORDER = "rgba(120,200,255,0.18)"
ICE_GLOW   = "rgba(100,180,255,0.08)"
ICE_ACTIVE = "rgba(100,180,255,0.15)"
ICE_TEXT   = "#a8d4ff"

TF_COLORS = ["#3730a3","#4338ca","#5b6af0","#818cf8","#a5b4fc","#c7d2fe","#e0e7ff"]

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, .stApp {{ background:{BG}; font-family:'Inter',sans-serif; }}
.block-container {{ padding:1.5rem 2.5rem 1rem; max-width:1320px; }}

/* ── Ice-blue glass KPI cards ─────────────────────────────────────────── */
div[data-testid="metric-container"] {{
  background: {ICE_BG};
  border: 1px solid {ICE_BORDER};
  border-radius: 14px;
  padding: 0.8rem 1.1rem;
  box-shadow: 0 0 24px {ICE_GLOW}, inset 0 1px 0 rgba(255,255,255,0.04);
  backdrop-filter: blur(12px);
}}
div[data-testid="metric-container"] label {{
  font-size: 0.65rem !important;
  color: {ICE_TEXT} !important;
  text-transform: uppercase;
  letter-spacing: .07em;
  font-weight: 600;
  opacity: 0.7;
}}
div[data-testid="metric-container"] [data-testid="stMetricValue"] {{
  font-size: 1.15rem !important;
  color: {TEXT} !important;
  font-weight: 700;
  line-height: 1.3;
}}
div[data-testid="stMetricDelta"] {{
  font-size: 0.7rem !important;
  color: {ICE_TEXT} !important;
  opacity: 0.65;
}}

/* ── Timeframe radio — single line, ice-blue pills ──────────────────────── */
div[role="radiogroup"] {{
  flex-wrap: nowrap !important;
  gap: 0.35rem !important;
  overflow-x: auto;
}}
div[role="radiogroup"] label {{
  background: {ICE_BG} !important;
  border: 1px solid {ICE_BORDER} !important;
  border-radius: 8px !important;
  padding: 0.28rem 0.85rem !important;
  white-space: nowrap !important;
  color: #6a88b8 !important;
  font-size: 0.76rem !important;
  font-weight: 500 !important;
  cursor: pointer !important;
  transition: all .15s ease !important;
}}
div[role="radiogroup"] label:hover {{
  border-color: rgba(140,200,255,0.45) !important;
  background: {ICE_ACTIVE} !important;
  color: {ICE_TEXT} !important;
}}
div[role="radiogroup"] label:has(input:checked) {{
  background: {ICE_ACTIVE} !important;
  border-color: rgba(140,210,255,0.55) !important;
  color: #cce8ff !important;
  box-shadow: 0 0 10px rgba(100,180,255,0.12) !important;
}}
div[role="radiogroup"] label span {{ display:none !important; }}

/* ── Inputs / Selectbox ──────────────────────────────────────────────────── */
.stTextInput>div>div, .stSelectbox>div>div {{
  background: {ICE_BG} !important;
  border: 1px solid {ICE_BORDER} !important;
  border-radius: 10px !important;
}}
.stTextInput input {{ color:{TEXT} !important; font-size:.88rem !important; }}
div[data-baseweb="select"] span {{ color:{TEXT} !important; }}
div[data-baseweb="select"] svg {{ color:{MUTED} !important; }}

/* ── Tabs ──────────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {{
  gap:0; border-bottom:1px solid {BORDER}; background:transparent;
}}
.stTabs [data-baseweb="tab"] {{
  background:transparent; color:{MUTED}; border:none;
  border-bottom:2px solid transparent;
  padding:.55rem 1.2rem; font-size:.82rem; font-weight:500; border-radius:0;
}}
.stTabs [aria-selected="true"] {{
  color:{ICE_TEXT} !important;
  border-bottom:2px solid {ICE_TEXT} !important;
  background:transparent !important;
}}
.stTabs [data-baseweb="tab-panel"] {{ padding-top:1.2rem; }}

/* ── Card containers ─────────────────────────────────────────────────── */
.card {{
  background:{CARD}; border:1px solid {BORDER};
  border-radius:14px; padding:1.1rem 1.4rem; margin-bottom:.9rem;
}}
.card-accent {{
  background:{ICE_BG}; border:1px solid {ICE_BORDER};
  border-left:3px solid {ACCENT}; border-radius:12px;
  padding:1rem 1.4rem; margin-bottom:1rem;
  box-shadow:0 0 20px {ICE_GLOW};
}}

/* ── Table ──────────────────────────────────────────────────────────── */
.stDataFrame {{ border-radius:12px; overflow:hidden; }}

/* ── Buttons ─────────────────────────────────────────────────────────── */
.stButton button {{
  background:{ICE_BG}; border:1px solid {ICE_BORDER};
  color:{ICE_TEXT}; border-radius:9px;
  font-size:.8rem; padding:.35rem 1rem;
  transition:all .15s;
}}
.stButton button:hover {{
  background:{ICE_ACTIVE}; border-color:rgba(140,210,255,.5);
  color:#cce8ff;
}}

/* ── Toggle ──────────────────────────────────────────────────────────── */
.stToggle span {{ color:{MUTED} !important; font-size:.8rem !important; }}

hr {{ border-color:{BORDER} !important; margin:.6rem 0 1rem; }}
h1,h2,h3,h4 {{ color:{TEXT} !important; }}
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

def chart_base(height=290, t=40, b=20, l=8, r=20):
    return dict(
        height=height,
        plot_bgcolor=CARD, paper_bgcolor=CARD,
        margin=dict(t=t, b=b, l=l, r=r),
        font=dict(color=TEXT, family="Inter, sans-serif", size=11),
        xaxis=dict(gridcolor=GRID, linecolor=BORDER,
                   tickfont=dict(color=MUTED, size=10), zeroline=False),
        yaxis=dict(gridcolor=GRID, linecolor=BORDER,
                   tickfont=dict(color=MUTED, size=10), zeroline=False),
        hoverlabel=dict(bgcolor="#1a2038", bordercolor=BORDER,
                        font=dict(color=TEXT, size=12)),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=MUTED, size=10)),
    )

# ── CHARTS ────────────────────────────────────────────────────────────────────
def tf_bar_chart(values: dict) -> go.Figure:
    labels, vals = list(values.keys()), list(values.values())
    norm = [(v - min(vals)) / max(max(vals) - min(vals), 0.01) for v in vals]
    colors = [TF_COLORS[min(int(n * (len(TF_COLORS)-1)), len(TF_COLORS)-1)] for n in norm]
    fig = go.Figure(go.Bar(
        x=labels, y=vals,
        marker=dict(color=colors, line=dict(width=0),
                    opacity=0.85),
        text=[f"{v:.2f}%" for v in vals],
        textposition="outside",
        textfont=dict(color=TEXT, size=11),
        hovertemplate="<b>%{x}</b><br>Avg Range: %{y:.2f}%<extra></extra>",
    ))
    kw = chart_base(height=280, t=36)
    fig.update_layout(
        title=dict(text="Avg Range % · All Timeframes",
                   font=dict(color=MUTED, size=11), x=0),
        yaxis_ticksuffix="%",
        **{k: v for k, v in kw.items()},
    )
    return fig

def rolling_chart(daily_df: pd.DataFrame, symbol: str) -> go.Figure:
    raw  = daily_df["range_pct"]
    roll = raw.rolling(20, min_periods=5).mean()
    fig  = go.Figure()
    fig.add_trace(go.Scatter(
        x=raw.index, y=raw, mode="lines", name="Daily",
        line=dict(color=ACCENT + "44", width=1),
        hovertemplate="%{x|%d %b %Y} · %{y:.2f}%<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=roll.index, y=roll, mode="lines", name="20-day avg",
        line=dict(color=ICE_TEXT, width=2),
        hovertemplate="%{x|%d %b %Y} · rolling avg %{y:.2f}%<extra></extra>",
    ))
    kw = chart_base(height=280, t=36)
    fig.update_layout(
        title=dict(text=f"{symbol} · Daily Range History",
                   font=dict(color=MUTED, size=11), x=0),
        yaxis_ticksuffix="%",
        **{k: v for k, v in kw.items()},
    )
    return fig

def sector_bar_chart(sector_avg: pd.Series, tf_label: str) -> go.Figure:
    lo, hi = sector_avg.min(), sector_avg.max()
    alphas = [0.35 + 0.65 * (v - lo) / max(hi - lo, 0.01) for v in sector_avg.values]
    colors = [f"rgba(100,180,255,{a:.2f})" for a in alphas]
    fig = go.Figure(go.Bar(
        y=sector_avg.index, x=sector_avg.values, orientation="h",
        marker=dict(color=colors, line=dict(width=0)),
        text=[f"  {v:.2f}%" for v in sector_avg.values],
        textposition="outside",
        textfont=dict(color=TEXT, size=11),
        hovertemplate="<b>%{y}</b><br>Avg Range: %{x:.2f}%<extra></extra>",
    ))
    kw = chart_base(height=max(320, len(sector_avg)*30), t=40, b=20, l=8, r=55)
    fig.update_layout(
        title=dict(text=f"Sector Avg Range % · {tf_label}",
                   font=dict(color=MUTED, size=11), x=0),
        xaxis_ticksuffix="%",
        yaxis=dict(gridcolor="rgba(0,0,0,0)", tickfont=dict(color=TEXT, size=11)),
        **{k: v for k, v in kw.items() if k not in ("yaxis",)},
    )
    return fig

# ── SESSION STATE ─────────────────────────────────────────────────────────────
if "sk" not in st.session_state:
    st.session_state.sk = 0

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown(
    f"<h1 style='margin-bottom:2px;font-size:1.4rem;font-weight:700;'>"
    f"NSE500 &nbsp;·&nbsp; Average Range</h1>"
    f"<p style='color:{MUTED};font-size:.78rem;margin:0 0 1.1rem;'>"
    f"Price movement analysis across timeframes &nbsp;·&nbsp; "
    f"501 equities &nbsp;·&nbsp; 2015 → 2026</p>",
    unsafe_allow_html=True,
)

# ── LOAD DATA ─────────────────────────────────────────────────────────────────
summary     = load_summary()
all_sectors = ["All"] + sorted(summary["industry"].dropna().unique().tolist())

# Build autocomplete options: "SYMBOL  ·  Company Name"
search_opts = sorted(
    f"{r['symbol']}  ·  {r['company_name']}"
    for _, r in summary.iterrows()
)

# ── CONTROLS ROW ──────────────────────────────────────────────────────────────
c_search, c_tf, c_sector = st.columns([2.2, 4.5, 1.5])

with c_search:
    search_val = st.selectbox(
        "",
        options=search_opts,
        index=None,
        placeholder="🔍  Symbol or company…",
        label_visibility="collapsed",
        key=f"search_{st.session_state.sk}",
    )

with c_tf:
    tf_label = st.radio("", TF_LABELS, index=2, horizontal=True,
                        label_visibility="collapsed")

with c_sector:
    sector_filter = st.selectbox("", all_sectors, label_visibility="collapsed")

st.markdown(f"<hr>", unsafe_allow_html=True)

pct_col, abs_col = TIMEFRAMES[tf_label]

# ── FILTER FOR OVERVIEW ───────────────────────────────────────────────────────
filtered = summary.copy()
if sector_filter != "All":
    filtered = filtered[filtered["industry"] == sector_filter]

# ═══════════════════════════════════════════════════════════════════════════════
# STOCK DETAIL VIEW
# ═══════════════════════════════════════════════════════════════════════════════
if search_val:
    symbol = search_val.split("  ·  ")[0].strip()
    row    = summary[summary["symbol"] == symbol]
    if len(row) == 0:
        st.warning("Stock not found.")
        st.stop()
    stock = row.iloc[0]

    # Header card
    st.markdown(f"""
    <div class="card-accent">
      <div style="font-size:1.15rem;font-weight:700;color:{TEXT};">
        {stock['symbol']} &nbsp;<span style="color:{MUTED};font-weight:400;">·</span>&nbsp; {stock['company_name']}
      </div>
      <div style="margin-top:.4rem;font-size:.78rem;color:{MUTED};display:flex;gap:1rem;align-items:center;flex-wrap:wrap;">
        <span style="background:{ICE_BG};color:{ICE_TEXT};border:1px solid {ICE_BORDER};
              border-radius:6px;padding:.15rem .7rem;font-weight:500;font-size:.72rem;">
          {stock['industry']}
        </span>
        <span>Last Close &nbsp;<strong style="color:{TEXT};">₹{stock['last_close']:,.2f}</strong></span>
        <span>Data &nbsp;<strong style="color:{TEXT};">{stock['data_start']} → {stock['data_end']}</strong></span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # 7 metric cards
    mcols = st.columns(7)
    for col, (tf_name, (p_col, a_col)) in zip(mcols, TIMEFRAMES.items()):
        val     = stock.get(p_col)
        abs_val = stock.get(a_col)
        col.metric(
            tf_name,
            f"{val:.2f}%" if pd.notna(val) else "—",
            delta=f"₹{abs_val:.2f}" if pd.notna(abs_val) else None,
            delta_color="off",
        )

    st.markdown("")

    tf_vals = {k: stock.get(v[0]) for k, v in TIMEFRAMES.items()
               if pd.notna(stock.get(v[0]))}

    left, right = st.columns(2)
    with left:
        st.markdown(f"<div class='card' style='padding:.6rem;'>", unsafe_allow_html=True)
        st.plotly_chart(tf_bar_chart(tf_vals), use_container_width=True,
                        config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.markdown(f"<div class='card' style='padding:.6rem;'>", unsafe_allow_html=True)
        try:
            daily_df = load_stock_daily(symbol)
            if len(daily_df) > 5:
                st.plotly_chart(rolling_chart(daily_df, symbol),
                                use_container_width=True,
                                config={"displayModeBar": False})
        except Exception:
            st.info("Historical data not available.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("")
    if st.button("← Back to overview"):
        st.session_state.sk += 1
        st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# OVERVIEW MODE
# ═══════════════════════════════════════════════════════════════════════════════
else:
    valid = filtered[pct_col].dropna()

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

    with tab1:
        _, tcol = st.columns([5, 1])
        with tcol:
            show_abs = st.toggle("Show ₹", value=False)

        dcols = ["symbol", "company_name", "industry", "last_close", pct_col]
        crename = {
            "symbol": "Symbol", "company_name": "Company",
            "industry": "Sector", "last_close": "Close (₹)",
            pct_col: f"Avg Range % · {tf_label}",
        }
        if show_abs:
            dcols.append(abs_col)
            crename[abs_col] = f"Avg Range ₹ · {tf_label}"

        display = (
            filtered[dcols].rename(columns=crename)
            .sort_values(f"Avg Range % · {tf_label}", ascending=False)
            .reset_index(drop=True)
        )
        display.index += 1

        fmt = {"Close (₹)": "{:,.2f}", f"Avg Range % · {tf_label}": "{:.2f}%"}
        if show_abs:
            fmt[f"Avg Range ₹ · {tf_label}"] = "{:.2f}"

        st.dataframe(
            display.style
                .format(fmt)
                .background_gradient(subset=[f"Avg Range % · {tf_label}"], cmap="Blues"),
            use_container_width=True,
            height=510,
        )

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

        st.markdown(f"<p style='color:{MUTED};font-size:.76rem;margin-bottom:.4rem;'>Sector breakdown</p>",
                    unsafe_allow_html=True)
        stbl = (
            filtered.groupby("industry")
            .agg(
                Stocks=(  "symbol", "count"),
                **{f"Avg %":    (pct_col, "mean")},
                **{f"Median %": (pct_col, "median")},
                **{f"Max %":    (pct_col, "max")},
                **{f"Min %":    (pct_col, "min")},
            )
            .round(2)
            .sort_values("Avg %", ascending=False)
        )
        st.dataframe(
            stbl.style.background_gradient(subset=["Avg %"], cmap="Blues"),
            use_container_width=True,
        )
