"""Generate PPT-sized PNGs for trend_regime_intro (commodity-trend × yield-curve regimes)."""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter, PercentFormatter

REPO = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = REPO / "Notebooks"
DATA = REPO / "data"
sys.path.insert(0, str(NOTEBOOK_DIR))

from trend_analysis.original_style import _style_axes  # noqa: E402

SLIDES_DIR = NOTEBOOK_DIR / "output" / "trend_regime_slides"
SLIDES_DIR.mkdir(parents=True, exist_ok=True)

DPI = 150
plt.rcParams.update({
    "font.size": 9,
    "axes.titlesize": 10,
    "axes.labelsize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 7.5,
    "figure.dpi": DPI,
})

TRADING_DAYS = 252
INITIAL_AUM = 100_000_000
W_STOCK = 0.6
W_BOND = 0.4
FAST_WINDOW = 20
SLOW_WINDOW = 63
WEIGHT_PER_SIGNAL = 0.25
ONSET_DAYS = 21

TREND = "Commodity-Trend"
BENCH_6040 = "60/40"

REGIME_ORDER = [
    "Bull Steepener",
    "Bull Flattener",
    "Bear Steepener",
    "Bear Flattener",
    "Steepener Twist",
    "Flattener Twist",
]
REGIME_COLORS = {
    "Bull Steepener": "#2E7D32",
    "Bull Flattener": "#81C784",
    "Bear Steepener": "#C62828",
    "Bear Flattener": "#EF9A9A",
    "Steepener Twist": "#1565C0",
    "Flattener Twist": "#64B5F6",
    "Unclassified": "#BDBDBD",
}
STRAT_COLORS = {
    TREND: "#2A9D8F",
    BENCH_6040: "#1F4E79",
}

BULL = {"Bull Steepener", "Bull Flattener"}
BEAR = {"Bear Steepener", "Bear Flattener"}

TABLE_BG_WHITE = "#FFFFFF"
TABLE_HEADER_LIGHT = "#F7F9FC"
TABLE_ROW_LIGHT = "#FFFFFF"
TABLE_ROW_ALT = "#F3F6FA"
TABLE_BORDER = "#E6EAF0"
TABLE_TEXT = "#1F2937"
TABLE_TEXT_MUTED = "#475569"
TABLE_TITLE = "#1F4E79"

BUCKET_ORDER = ["Bull", "Bear", "Twist"]
BUCKET_COLORS = {"Bull": "#2E7D32", "Bear": "#C62828", "Twist": "#1565C0"}


def _save(fig, name: str, *, facecolor: str | None = None) -> None:
    path = SLIDES_DIR / name
    kwargs = {"dpi": DPI, "bbox_inches": "tight", "pad_inches": 0.2}
    if facecolor:
        kwargs["facecolor"] = facecolor
        kwargs["edgecolor"] = "none"
    fig.savefig(path, **kwargs)
    plt.close(fig)
    print(" ", path.name)


def load_bloomberg_panel(path: Path) -> pd.DataFrame:
    raw = pd.read_excel(path, sheet_name="Sheet1")
    cols = list(raw.columns)
    date_positions = [i for i, c in enumerate(cols) if c == "Date" or c.startswith("Date.")]
    series_list = []
    for dc in date_positions:
        vc = cols[dc + 1]
        pair = raw[[cols[dc], vc]].copy()
        pair.columns = ["date", vc]
        pair["date"] = pd.to_datetime(pair["date"], errors="coerce")
        pair[vc] = pd.to_numeric(pair[vc], errors="coerce")
        pair = pair.dropna(subset=["date"]).set_index("date").sort_index()
        pair = pair[~pair.index.duplicated(keep="last")]
        series_list.append(pair[vc])
    panel = pd.concat(series_list, axis=1).sort_index()
    for c in panel.columns:
        first = panel[c].first_valid_index()
        if first is not None:
            panel.loc[first:, c] = panel.loc[first:, c].ffill()
    return panel


def build_trend_backtest(panel: pd.DataFrame, start: str | None = None) -> dict:
    signal_assets = {
        "BRL": "USDBRL Curncy",
        "AUD": "AUDUSD Curncy",
        "BCOM": "BCOM Index",
        "XAU": "XAU BGN Curncy",
    }
    trade_assets = {
        "BRL": "B1MLBRUS Index",
        "AUD": "B1MLAUUS Index",
        "BCOM": "BCOM Index",
        "XAU": "XAU BGN Curncy",
    }
    needed = sorted(set(signal_assets.values()) | set(trade_assets.values()))
    df = panel[needed].dropna()
    if start is not None:
        df = df.loc[start:]

    ma_fast = pd.DataFrame(index=df.index)
    ma_slow = pd.DataFrame(index=df.index)
    for asset, col in signal_assets.items():
        ma_fast[asset] = df[col].rolling(FAST_WINDOW, min_periods=FAST_WINDOW).mean()
        ma_slow[asset] = df[col].rolling(SLOW_WINDOW, min_periods=SLOW_WINDOW).mean()

    signals = pd.DataFrame(index=df.index, dtype=float)
    signals["BRL"] = (ma_fast["BRL"] < ma_slow["BRL"]).astype(float)
    signals["AUD"] = (ma_fast["AUD"] > ma_slow["AUD"]).astype(float)
    signals["BCOM"] = (ma_fast["BCOM"] > ma_slow["BCOM"]).astype(float)
    signals["XAU"] = (ma_fast["XAU"] > ma_slow["XAU"]).astype(float)

    valid = ma_fast.notna().all(axis=1) & ma_slow.notna().all(axis=1)
    signals = signals.where(valid, 0.0)
    positions = signals.shift(1).fillna(0.0)

    asset_returns = pd.DataFrame(index=df.index)
    for asset, col in trade_assets.items():
        asset_returns[asset] = df[col].pct_change()
    asset_returns = asset_returns.fillna(0.0)

    weights = positions * WEIGHT_PER_SIGNAL
    strategy_ret = (weights * asset_returns).sum(axis=1)
    nav = INITIAL_AUM * (1.0 + strategy_ret).cumprod()
    first_signal = (positions.sum(axis=1) > 0).idxmax()
    return {"strategy_return": strategy_ret, "nav": nav, "first_signal_date": first_signal}


def build_6040_backtest(panel: pd.DataFrame, start: str | None = None) -> dict:
    df = panel[["SPXT Index", "LUATTRUU Index"]].dropna()
    if start is not None:
        df = df.loc[start:]
    stock_ret = df["SPXT Index"].pct_change().fillna(0.0)
    bond_ret = df["LUATTRUU Index"].pct_change().fillna(0.0)
    strategy_ret = W_STOCK * stock_ret + W_BOND * bond_ret
    nav = INITIAL_AUM * (1.0 + strategy_ret).cumprod()
    return {"strategy_return": strategy_ret, "nav": nav}


def annualize_window(s: pd.Series) -> dict:
    s = s.dropna()
    if len(s) < 2:
        return dict(ann_return=np.nan, ann_vol=np.nan, sharpe=np.nan, max_dd=np.nan, hit=np.nan)
    growth = (1 + s).prod()
    ann_r = growth ** (TRADING_DAYS / len(s)) - 1
    ann_v = s.std() * np.sqrt(TRADING_DAYS)
    sharpe = ann_r / ann_v if ann_v else np.nan
    wealth = (1 + s).cumprod()
    mdd = (wealth / wealth.cummax() - 1).min()
    return dict(ann_return=ann_r, ann_vol=ann_v, sharpe=sharpe, max_dd=mdd, hit=(s > 0).mean())


def per_regime_compare(returns_df: pd.DataFrame, regimes_col: pd.Series) -> pd.DataFrame:
    df = pd.concat([returns_df[[TREND, BENCH_6040]], regimes_col.rename("regime")], axis=1).dropna()
    rows = []
    for regime in REGIME_ORDER:
        sub = df[df["regime"].eq(regime)]
        if sub.empty:
            continue
        sa = annualize_window(sub[TREND])
        sb = annualize_window(sub[BENCH_6040])
        active = sub[TREND] - sub[BENCH_6040]
        rows.append({
            "Regime": regime,
            "Days": len(sub),
            f"{TREND} Ann. Ret.": sa["ann_return"],
            f"{BENCH_6040} Ann. Ret.": sb["ann_return"],
            f"{TREND} Sharpe": sa["sharpe"],
            f"{BENCH_6040} Sharpe": sb["sharpe"],
            f"{TREND} Max DD": sa["max_dd"],
            f"{BENCH_6040} Max DD": sb["max_dd"],
            "Active mean (bps/day)": active.mean() * 1e4,
            "Corr": sub[TREND].corr(sub[BENCH_6040]),
        })
    return pd.DataFrame(rows)


def regime_changes(regime_series: pd.Series) -> pd.DataFrame:
    s = regime_series.dropna()
    changed = s.ne(s.shift())
    changed.iloc[0] = False
    dates = s.index[changed]
    return pd.DataFrame({
        "change_date": dates,
        "prev_regime": s.shift().loc[dates].values,
        "new_regime": s.loc[dates].values,
    })


def cumulative_event_paths(
    returns_col: pd.Series,
    change_df: pd.DataFrame,
    before: int = 21,
    after: int = 63,
) -> pd.DataFrame:
    paths = []
    idx = returns_col.index
    for _, row in change_df.iterrows():
        date = row["change_date"]
        if date not in idx:
            continue
        pos = idx.get_loc(date)
        lo = max(0, pos - before)
        hi = min(len(idx), pos + after + 1)
        if (pos - lo) < before or (hi - 1 - pos) < after:
            continue
        window = returns_col.iloc[lo:hi]
        offsets = np.arange(-before, after + 1)
        cum = (1 + window).cumprod().values
        anchor = cum[before]
        rel = cum / anchor - 1
        paths.append(pd.DataFrame({
            "offset": offsets,
            "cum_rel": rel,
            "new_regime": row["new_regime"],
            "prev_regime": row["prev_regime"],
            "change_date": date,
        }))
    if not paths:
        return pd.DataFrame()
    return pd.concat(paths, ignore_index=True)


def event_return_at_horizon(
    returns_df: pd.DataFrame,
    change_df: pd.DataFrame,
    horizon: int = 63,
    before: int = 21,
) -> pd.DataFrame:
    rows = []
    idx = returns_df.index
    for _, row in change_df.iterrows():
        date = row["change_date"]
        if date not in idx:
            continue
        pos = idx.get_loc(date)
        if (pos - before) < before or (len(idx) - 1 - pos) < horizon:
            continue
        trend_slice = returns_df[TREND].iloc[pos: pos + horizon + 1]
        bench_slice = returns_df[BENCH_6040].iloc[pos: pos + horizon + 1]
        trend_cum = (1 + trend_slice).prod() - 1
        active_cum = (1 + (trend_slice - bench_slice)).prod() - 1
        rows.append({
            **row.to_dict(),
            "trend_63d": trend_cum,
            "active_63d": active_cum,
        })
    return pd.DataFrame(rows)


def regime_to_bucket(label: str) -> str | None:
    if label in BULL:
        return "Bull"
    if label in BEAR:
        return "Bear"
    if label in {"Steepener Twist", "Flattener Twist"}:
        return "Twist"
    return None


def bull_bear_twist_table(returns_df: pd.DataFrame, regimes_col: pd.Series) -> pd.DataFrame:
    df = pd.concat([returns_df[[TREND, BENCH_6040]], regimes_col.rename("regime")], axis=1).dropna()
    df["bucket"] = df["regime"].map(regime_to_bucket)
    df = df.dropna(subset=["bucket"])
    rows = []
    for bucket in BUCKET_ORDER:
        sub = df[df["bucket"].eq(bucket)]
        sa = annualize_window(sub[TREND])
        sb = annualize_window(sub[BENCH_6040])
        active = sub[TREND] - sub[BENCH_6040]
        rows.append({
            "Bucket": bucket,
            "Days": len(sub),
            f"{TREND} Ann. Ret.": sa["ann_return"],
            f"{BENCH_6040} Ann. Ret.": sb["ann_return"],
            f"{TREND} Sharpe": sa["sharpe"],
            f"{BENCH_6040} Sharpe": sb["sharpe"],
            "Active mean (bps/day)": active.mean() * 1e4,
            "Active win rate": (active > 0).mean(),
            "Corr": sub[TREND].corr(sub[BENCH_6040]),
        })
    return pd.DataFrame(rows)


def onset_vs_steady(returns_col: pd.Series, regimes_col: pd.Series, onset_days: int = ONSET_DAYS) -> pd.DataFrame:
    df = pd.concat([returns_col.rename("r"), regimes_col.rename("regime")], axis=1).dropna()
    block_id = (df["regime"].ne(df["regime"].shift())).cumsum()
    df["block"] = block_id
    rows = []
    for regime in REGIME_ORDER:
        sub = df[df["regime"].eq(regime)]
        if sub.empty:
            continue
        onset_parts, rest_parts = [], []
        for _, group in sub.groupby("block", sort=False):
            onset_parts.append(group["r"].iloc[:onset_days])
            rest_parts.append(group["r"].iloc[onset_days:])
        onset_s = pd.concat(onset_parts) if onset_parts else pd.Series(dtype=float)
        rest_s = pd.concat(rest_parts) if rest_parts else pd.Series(dtype=float)
        stats_on = annualize_window(onset_s)
        stats_re = annualize_window(rest_s)
        rows.append({
            "Regime": regime,
            "Onset days": len(onset_s),
            "Onset ann. ret.": stats_on["ann_return"],
            "Onset Sharpe": stats_on["sharpe"],
            "Steady days": len(rest_s),
            "Steady ann. ret.": stats_re["ann_return"],
            "Steady Sharpe": stats_re["sharpe"],
        })
    return pd.DataFrame(rows)


def prepare_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    panel = load_bloomberg_panel(DATA / "bloombergdata-uncleaned.xlsx")
    trend_pack = build_trend_backtest(panel, start="2001-01-01")
    b6040_pack = build_6040_backtest(panel, start="2001-01-01")

    returns = pd.DataFrame({
        TREND: trend_pack["strategy_return"],
        BENCH_6040: b6040_pack["strategy_return"],
    }).dropna(how="any")
    returns = returns.loc[trend_pack["first_signal_date"]:]

    regime_df = pd.read_excel(
        DATA / "interest_rate_regimes.xlsx",
        sheet_name="Regime Classification",
        parse_dates=["date"],
    ).set_index("date").sort_index()
    returns["regime"] = regime_df["regime_filtered"].reindex(returns.index, method="ffill")
    returns = returns.dropna(subset=["regime"])

    q2_table = per_regime_compare(returns, returns["regime"])
    bucket_table = bull_bear_twist_table(returns, returns["regime"])
    onset_table = onset_vs_steady(returns[TREND], returns["regime"], onset_days=ONSET_DAYS)
    change_all = regime_changes(returns["regime"])
    change_named = change_all[change_all["new_regime"].isin(REGIME_ORDER)].copy()
    paths = cumulative_event_paths(returns[TREND], change_named, before=21, after=63)
    horizon_df = event_return_at_horizon(returns, change_all, horizon=63, before=21)

    return returns, q2_table, bucket_table, onset_table, paths, horizon_df


def macro_pivot_summary(horizon_df: pd.DataFrame) -> pd.DataFrame:
    # Named regimes rarely jump directly Bull↔Bear; pivots usually route via Unclassified.
    pivots = [
        ("→ Bull Steepener", lambda r: r["new_regime"] == "Bull Steepener"),
        ("→ Bear Flattener", lambda r: r["new_regime"] == "Bear Flattener"),
        ("Unclassified → Bull", lambda r: r["prev_regime"] == "Unclassified" and r["new_regime"] in BULL),
        ("Unclassified → Bear", lambda r: r["prev_regime"] == "Unclassified" and r["new_regime"] in BEAR),
    ]
    rows = []
    for label, pred in pivots:
        sub = horizon_df[horizon_df.apply(pred, axis=1)]
        if sub.empty:
            continue
        rows.append({
            "Transition": label,
            "Events": len(sub),
            "Median 63d Commodity-Trend return": sub["trend_63d"].median(),
            "Median 63d Active return": sub["active_63d"].median(),
            "Win rate (Commodity-Trend > 0)": (sub["trend_63d"] > 0).mean(),
        })
    return pd.DataFrame(rows)


def regime_entry_summary(paths: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for regime in REGIME_ORDER:
        sub = paths[paths["new_regime"].eq(regime) & paths["offset"].eq(63)]
        if sub.empty:
            continue
        rows.append({
            "Destination regime": regime,
            "Events": int(sub["change_date"].nunique()),
            "Median 63d Commodity-Trend return": sub["cum_rel"].median(),
            "Win rate (Commodity-Trend > 0 at +63d)": (sub["cum_rel"] > 0).mean(),
        })
    return pd.DataFrame(rows)


def slide1_regime_performance(q2_table: pd.DataFrame) -> None:
    """Single slide-1 figure: metrics table + stacked Sharpe / max-DD bars (readable at slide scale)."""
    plot_df = q2_table.set_index("Regime").loc[[r for r in REGIME_ORDER if r in q2_table["Regime"].values]]
    regime_short = {
        "Bull Steepener": "Bull Stp",
        "Bull Flattener": "Bull Flt",
        "Bear Steepener": "Bear Stp",
        "Bear Flattener": "Bear Flt",
        "Steepener Twist": "Stp Twist",
        "Flattener Twist": "Flt Twist",
    }
    x_labels = [regime_short.get(r, r) for r in plot_df.index]

    fig = plt.figure(figsize=(7.4, 6.4))
    gs = fig.add_gridspec(3, 1, height_ratios=[1.15, 1.0, 1.0], hspace=0.42)

    # --- table (returns + Sharpe only; drawdown in charts below) ---
    ax_t = fig.add_subplot(gs[0])
    ax_t.axis("off")
    headers = ["Regime", "Days", "Commodity-\nTrend ret.", "60/40\nret.",
               "Commodity-\nTrend Sharpe", "60/40\nSharpe"]
    n_data_rows = len(q2_table)
    n_cols = len(headers)
    cell_w = 1.0 / n_cols

    table_top = 0.90
    table_bottom = 0.0
    table_height = table_top - table_bottom
    header_h = table_height * 0.26
    data_h = (table_height - header_h) / n_data_rows

    for j, header in enumerate(headers):
        x = j * cell_w
        y = table_top - header_h
        ax_t.add_patch(plt.Rectangle((x, y), cell_w, header_h, transform=ax_t.transAxes,
                                     facecolor=TABLE_HEADER_LIGHT, edgecolor=TABLE_BORDER, linewidth=0.8))
        ax_t.text(x + cell_w / 2, y + header_h / 2, header, ha="center", va="center",
                  fontsize=8, color=TABLE_TEXT, fontweight="bold", transform=ax_t.transAxes,
                  linespacing=1.25)
    for i, (_, row) in enumerate(q2_table.iterrows()):
        row_y = table_top - header_h - (i + 1) * data_h
        row_fill = TABLE_ROW_ALT if i % 2 else TABLE_ROW_LIGHT
        values = [
            regime_short.get(row["Regime"], row["Regime"]),
            f"{int(row['Days']):,}",
            f"{row[f'{TREND} Ann. Ret.']:.1%}",
            f"{row[f'{BENCH_6040} Ann. Ret.']:.1%}",
            f"{row[f'{TREND} Sharpe']:.2f}",
            f"{row[f'{BENCH_6040} Sharpe']:.2f}",
        ]
        for j, val in enumerate(values):
            x = j * cell_w
            ax_t.add_patch(plt.Rectangle((x, row_y), cell_w, data_h, transform=ax_t.transAxes,
                                         facecolor=row_fill, edgecolor=TABLE_BORDER, linewidth=0.8))
            ax_t.text(x + cell_w / 2, row_y + data_h / 2, val, ha="center", va="center",
                      fontsize=7.5 if j else 8, color=TABLE_TEXT_MUTED if j else TABLE_TEXT,
                      fontweight="normal" if j else "bold", transform=ax_t.transAxes)
    ax_t.text(0.0, 1.02, "In-regime performance (named regimes)", fontsize=10, color=TABLE_TITLE,
              fontweight="bold", transform=ax_t.transAxes, va="bottom")

    x = np.arange(len(plot_df))
    width = 0.36

    ax_sh = fig.add_subplot(gs[1])
    ax_sh.bar(x - width / 2, plot_df[f"{TREND} Sharpe"], width=width,
              color=STRAT_COLORS[TREND], label="Commodity-Trend")
    ax_sh.bar(x + width / 2, plot_df[f"{BENCH_6040} Sharpe"], width=width,
              color=STRAT_COLORS[BENCH_6040], label="60/40")
    ax_sh.axhline(0, color="#333", linewidth=0.6)
    ax_sh.set_xticks(x)
    ax_sh.set_xticklabels(x_labels, fontsize=8)
    ax_sh.set_title("Sharpe by regime", loc="left", fontsize=9.5)
    ax_sh.legend(loc="upper right", fontsize=7.5, ncol=2)
    _style_axes(ax_sh, "y")

    ax_dd = fig.add_subplot(gs[2])
    ax_dd.bar(x - width / 2, plot_df[f"{TREND} Max DD"], width=width,
              color=STRAT_COLORS[TREND], label="Commodity-Trend")
    ax_dd.bar(x + width / 2, plot_df[f"{BENCH_6040} Max DD"], width=width,
              color=STRAT_COLORS[BENCH_6040], label="60/40")
    ax_dd.axhline(0, color="#333", linewidth=0.6)
    ax_dd.set_xticks(x)
    ax_dd.set_xticklabels(x_labels, fontsize=8)
    ax_dd.set_title("Max drawdown while in regime", loc="left", fontsize=9.5)
    ax_dd.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax_dd.legend(loc="lower left", fontsize=7.5, ncol=2)
    _style_axes(ax_dd, "y")

    _save(fig, "slide1_regime_performance.png", facecolor=TABLE_BG_WHITE)


def slide2_bull_bear_twist_rollup(bucket_table: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.55))
    x = np.arange(len(bucket_table))
    width = 0.36
    colors = [BUCKET_COLORS[b] for b in bucket_table["Bucket"]]

    ax = axes[0]
    ax.bar(x - width / 2, bucket_table[f"{TREND} Sharpe"], width=width,
           color=STRAT_COLORS[TREND], label="Commodity-Trend")
    ax.bar(x + width / 2, bucket_table[f"{BENCH_6040} Sharpe"], width=width,
           color=STRAT_COLORS[BENCH_6040], label="60/40")
    ax.axhline(0, color="#333", linewidth=0.6)
    ax.set_xticks(x)
    ax.set_xticklabels(bucket_table["Bucket"], fontsize=8.5)
    ax.set_title("Sharpe by curve bucket", loc="left", fontsize=9.5)
    ax.legend(loc="best", fontsize=7.5)
    _style_axes(ax, "y")

    ax2 = axes[1]
    bps_vals = bucket_table["Active mean (bps/day)"].values
    bars = ax2.bar(x, bps_vals, width=0.52, color=colors, edgecolor="white", linewidth=0.6)
    ax2.axhline(0, color="#333", linewidth=0.6)
    ax2.set_xticks(x)
    ax2.set_xticklabels(bucket_table["Bucket"], fontsize=8.5)
    ax2.set_ylabel("bps / day", fontsize=8)
    ax2.set_title("Daily active return vs 60/40", loc="left", fontsize=9.5)

    y_min, y_max = float(bps_vals.min()), float(bps_vals.max())
    y_span = max(y_max - y_min, 1.0)
    y_pad = y_span * 0.55
    ax2.set_ylim(y_min - y_pad, y_max + y_pad)

    for bar, (_, row) in zip(bars, bucket_table.iterrows()):
        h = float(row["Active mean (bps/day)"])
        win = float(row["Active win rate"])
        cx = bar.get_x() + bar.get_width() / 2
        if h >= 0:
            ax2.text(cx, h + y_pad * 0.06, f"{h:+.1f}", ha="center", va="bottom",
                     fontsize=7.5, fontweight="bold", color=TABLE_TEXT)
            ax2.text(cx, h + y_pad * 0.22, f"{win:.0%} win", ha="center", va="bottom",
                     fontsize=7, color=TABLE_TEXT_MUTED)
        else:
            ax2.text(cx, h - y_pad * 0.06, f"{h:+.1f}", ha="center", va="top",
                     fontsize=7.5, fontweight="bold", color=TABLE_TEXT)
            ax2.text(cx, h - y_pad * 0.22, f"{win:.0%} win", ha="center", va="top",
                     fontsize=7, color=TABLE_TEXT_MUTED)

    _style_axes(ax2, "y")
    fig.subplots_adjust(wspace=0.38, left=0.07, right=0.98, top=0.88, bottom=0.14)
    _save(fig, "slide2_bull_bear_twist_rollup.png")


def slide2_onset_vs_steady(onset_table: pd.DataFrame) -> None:
    plot_regimes = ["Bear Flattener", "Bull Steepener", "Flattener Twist", "Bull Flattener"]
    plot_df = onset_table.set_index("Regime").loc[plot_regimes]
    x = np.arange(len(plot_df))
    width = 0.36

    fig, ax = plt.subplots(figsize=(6.8, 3.0))
    ax.bar(x - width / 2, plot_df["Onset ann. ret."], width=width,
           color="#94A3B8", label=f"First {ONSET_DAYS}d (onset)")
    ax.bar(x + width / 2, plot_df["Steady ann. ret."], width=width,
           color="#2A9D8F", label="Remainder (steady)")
    ax.axhline(0, color="#333", linewidth=0.6)
    ax.set_xticks(x)
    ax.set_xticklabels([r.replace(" ", "\n") for r in plot_df.index], fontsize=7)
    ax.set_ylabel("Annualized return")
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax.set_title("Transition vs persistence: onset vs steady-state within each regime", loc="left")
    ax.legend(loc="upper right", fontsize=7)
    _style_axes(ax, "y")
    fig.subplots_adjust(bottom=0.22)
    _save(fig, "slide2_onset_vs_steady.png")


REGIME_SHORT = {
    "Bull Steepener": "Bull Stp",
    "Bull Flattener": "Bull Flt",
    "Bear Steepener": "Bear Stp",
    "Bear Flattener": "Bear Flt",
    "Steepener Twist": "Stp Twist",
    "Flattener Twist": "Flt Twist",
}
SLIDE3_MACRO = ["Bull Steepener", "Bear Flattener"]
SLIDE3_OTHER = ["Bull Flattener", "Bear Steepener", "Steepener Twist", "Flattener Twist"]


def _median_path_series(paths: pd.DataFrame, regime: str) -> pd.Series | None:
    sub = paths[paths["new_regime"].eq(regime)]
    if sub.empty:
        return None
    return sub.groupby("offset")["cum_rel"].median()


def _style_event_path_ax(ax, *, title: str, show_xlabel: bool = True) -> None:
    ax.axhline(0, color="#333", linewidth=0.6)
    ax.axvline(0, color="#333", linewidth=0.6, linestyle="--", alpha=0.6)
    if show_xlabel:
        ax.set_xlabel("Trading days from label change")
    ax.set_ylabel("Cumulative return vs day 0")
    ax.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax.set_title(title, loc="left", fontsize=9.5)
    _style_axes(ax, "y")


def slide3_regime_entry_bars(entry_df: pd.DataFrame) -> None:
    """Slide 3 top: setup note + 63d bars for all six named entries."""
    emphasize = set(SLIDE3_MACRO)
    plot_df = entry_df.set_index("Destination regime").loc[REGIME_ORDER].reset_index()
    win_col = "Win rate (Commodity-Trend > 0 at +63d)"
    ret_col = "Median 63d Commodity-Trend return"

    fig = plt.figure(figsize=(7.2, 4.05))
    gs = fig.add_gridspec(2, 1, height_ratios=[0.18, 1.0], hspace=0.20)

    ax_note = fig.add_subplot(gs[0])
    ax_note.axis("off")
    ax_note.text(0.0, 0.78, "Event study setup",
                 fontsize=9.5, fontweight="bold", color=TABLE_TITLE, transform=ax_note.transAxes)
    ax_note.text(
        0.0, 0.0,
        "Day 0 = filtered label change · Commodity-Trend return rebased to day 0 · "
        "Window: −21 to +63 trading days",
        fontsize=8, color=TABLE_TEXT_MUTED, transform=ax_note.transAxes, va="bottom",
    )

    ax_bar = fig.add_subplot(gs[1])
    x = np.arange(len(plot_df))
    colors = [REGIME_COLORS[r] for r in plot_df["Destination regime"]]
    vals = plot_df[ret_col].astype(float).values
    bars = ax_bar.bar(x, vals, width=0.54, color=colors, edgecolor="white", linewidth=0.5)
    for i, regime in enumerate(plot_df["Destination regime"]):
        if regime in emphasize:
            bars[i].set_edgecolor(TABLE_TITLE)
            bars[i].set_linewidth(1.6)
    ax_bar.axhline(0, color="#333", linewidth=0.6)
    ax_bar.set_xticks(x)
    ax_bar.set_xticklabels(
        [REGIME_SHORT.get(r, r) for r in plot_df["Destination regime"]],
        fontsize=8,
    )
    ax_bar.set_ylabel("Median return at day +63")
    ax_bar.yaxis.set_major_formatter(PercentFormatter(1.0))
    ax_bar.set_title("Return 63 days after each named regime entry", loc="left", fontsize=9.5)
    _style_axes(ax_bar, "y")

    y_data_lo, y_data_hi = float(vals.min()), float(vals.max())
    y_span_data = max(y_data_hi - y_data_lo, 0.01)
    y_lo = min(y_data_lo, 0.0) - y_span_data * 0.50
    y_hi = max(y_data_hi, 0.0) + y_span_data * 0.95
    ax_bar.set_ylim(y_lo, y_hi)
    y_span = y_hi - y_lo
    val_pad = y_span * 0.04
    meta_gap = y_span * 0.055
    for i, (_, row) in enumerate(plot_df.iterrows()):
        val = float(row[ret_col])
        bar_top = max(val, 0.0)
        meta = f"N={int(row['Events'])} · {row[win_col]:.0%} win"
        if abs(val) < 0.0005:
            ret_label, ret_y = "0.0%", val_pad
        elif val > 0:
            ret_label, ret_y = f"{val:+.1%}", val + val_pad
        else:
            ret_label, ret_y = f"{val:.1%}", val - val_pad
        ret_va = "bottom" if val >= 0 else "top"
        ax_bar.text(i, ret_y, ret_label, ha="center", va=ret_va, fontsize=8,
                    fontweight="bold", color=TABLE_TEXT, clip_on=True)
        meta_y = ret_y + meta_gap if val >= 0 else bar_top + val_pad
        ax_bar.text(i, meta_y, meta, ha="center", va="bottom", fontsize=7,
                    color=TABLE_TEXT_MUTED, clip_on=True)

    fig.subplots_adjust(top=0.96, bottom=0.14, left=0.10, right=0.98)
    _save(fig, "slide3_regime_entry_bars.png")


def slide3_regime_paths(paths: pd.DataFrame, regimes: list[str], filename: str, title: str) -> None:
    """Slide 3 path panel: median paths for a subset of named entries."""
    fig, ax = plt.subplots(figsize=(7.2, 2.35))
    for regime in regimes:
        med = _median_path_series(paths, regime)
        if med is None:
            continue
        lw = 2.4 if regime in SLIDE3_MACRO else 2.0
        ax.plot(med.index, med.values, color=REGIME_COLORS[regime], linewidth=lw,
                label=REGIME_SHORT.get(regime, regime))
    _style_event_path_ax(ax, title=title)
    ax.legend(loc="best", fontsize=7.5, ncol=2 if len(regimes) > 2 else 1, framealpha=0.92)
    fig.subplots_adjust(bottom=0.18)
    _save(fig, filename)


def slide3_regime_change_focus(paths: pd.DataFrame, entry_df: pd.DataFrame) -> None:
    """Slide 3: bars + two separate path charts (macro pair vs other four)."""
    slide3_regime_entry_bars(entry_df)
    slide3_regime_paths(
        paths, SLIDE3_MACRO, "slide3_regime_paths_macro.png",
        "Median path: Bull Steepener & Bear Flattener (Fed easing vs hiking entry)",
    )
    slide3_regime_paths(
        paths, SLIDE3_OTHER, "slide3_regime_paths_other.png",
        "Median path: other four named regime entries",
    )


def main() -> None:
    print("Writing to", SLIDES_DIR)
    _returns, q2_table, bucket_table, onset_table, paths, horizon_df = prepare_data()

    entry_summary = regime_entry_summary(paths)
    pivot_df = macro_pivot_summary(horizon_df)

    entry_summary.to_csv(SLIDES_DIR / "regime_entry_summary.csv", index=False)
    pivot_df.to_csv(SLIDES_DIR / "macro_pivot_transitions.csv", index=False)
    bucket_table.to_csv(SLIDES_DIR / "bull_bear_twist_rollup.csv", index=False)
    onset_table.to_csv(SLIDES_DIR / "onset_vs_steady.csv", index=False)

    slide1_regime_performance(q2_table)
    slide2_bull_bear_twist_rollup(bucket_table)
    slide2_onset_vs_steady(onset_table)
    slide3_regime_change_focus(paths, entry_summary)
    print("Done.")


if __name__ == "__main__":
    main()
