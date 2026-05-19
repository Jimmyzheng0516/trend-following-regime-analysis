import numpy as np
import pandas as pd
from IPython.display import display
from matplotlib import pyplot as plt
from matplotlib.ticker import FuncFormatter

from .config import BENCHMARK_6040, BONDS, COMMODITY_TREND, DYNAMIC_MV, EQUITY, PRO_PALETTE, SLEEVE_9010, STATIC_MV
from .metrics import TRADING_DAYS, drawdown, monthly_returns, summary_frame


INITIAL_AUM = 100_000_000
STRATEGY_COLORS = {
    BENCHMARK_6040: "#C55A11",
    COMMODITY_TREND: "#1F4E79",
    SLEEVE_9010: "#70AD47",
    STATIC_MV: "#7030A0",
    DYNAMIC_MV: "#00838F",
}
POSITIVE_COLOR = "#70AD47"
NEGATIVE_COLOR = "#C00000"


def _pct_axis(ax):
    ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f"{y:.0%}"))


def _style_axes(ax, grid_axis=None):
    ax.grid(True, axis=grid_axis or "both", alpha=0.35)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def _growth(ret):
    return (1.0 + ret.dropna()).cumprod()


def format_metric_table(df):
    out = df.copy()
    if "Metric" not in out.columns:
        return out

    money_metrics = {"Initial AUM", "Ending NAV", "Gross profit", "Gross loss"}
    pct_metrics = {
        "Total return",
        "Annual rate of return",
        "Annualized volatility",
        "Maximum drawdown",
        "Win rate",
        "Average gross leverage",
    }
    number_metrics = {"Sharpe ratio, rf=0", "Total trade count", "Average holding period per trade", "Average active signals"}

    def fmt(metric, value):
        if pd.isna(value) or value == "":
            return ""
        if isinstance(value, str):
            return value.replace("Method 1 (trend)", COMMODITY_TREND).replace("100% trend", COMMODITY_TREND)
        try:
            value = float(value)
        except (TypeError, ValueError):
            return value
        if metric in money_metrics:
            return f"${value:,.0f}"
        if metric in pct_metrics:
            return f"{value:.2%}"
        if metric in number_metrics:
            return f"{value:,.2f}" if abs(value - round(value)) > 1e-9 else f"{value:,.0f}"
        return f"{value:,.4f}" if abs(value) < 10 else f"{value:,.2f}"

    for col in out.columns:
        if col != "Metric":
            out[col] = [fmt(metric, value) for metric, value in zip(out["Metric"], out[col])]
    return out


def display_metric_table(df):
    display(format_metric_table(df))


def plot_core_nav(merged):
    m1_idx = merged["method1_nav"] / merged["method1_nav"].iloc[0]
    b_idx = merged["benchmark_nav"] / merged["benchmark_nav"].iloc[0]
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(m1_idx.index, m1_idx.values, label=f"{COMMODITY_TREND}, NAV / $100M", color=STRATEGY_COLORS[COMMODITY_TREND], linewidth=1.8)
    ax.plot(b_idx.index, b_idx.values, label="60/40, NAV / $100M", color=STRATEGY_COLORS[BENCHMARK_6040], linewidth=1.8)
    ax.set_title("NAV Index")
    ax.set_ylabel("NAV / Initial NAV")
    ax.set_xlabel("")
    ax.legend(loc="upper left")
    _style_axes(ax)
    plt.tight_layout()
    return ax


def plot_core_daily_returns(core_returns):
    fig, ax = plt.subplots(figsize=(12, 4))
    ax.plot(core_returns.index, core_returns[COMMODITY_TREND], label=f"{COMMODITY_TREND} daily return", color=STRATEGY_COLORS[COMMODITY_TREND], linewidth=0.7, alpha=0.85)
    ax.plot(core_returns.index, core_returns[BENCHMARK_6040], label="60/40 daily return", color=STRATEGY_COLORS[BENCHMARK_6040], linewidth=0.7, alpha=0.85)
    ax.set_title("Daily Returns")
    ax.set_ylabel("Return")
    _pct_axis(ax)
    ax.legend(loc="upper left")
    _style_axes(ax)
    plt.tight_layout()
    return ax


def monthly_return_heatmap_original(return_series):
    heatmap = monthly_returns(return_series)
    annual = (1.0 + return_series.dropna()).resample("YE").prod() - 1.0
    heatmap["Annual"] = annual.groupby(annual.index.year).first()
    return heatmap.style.format("{:.1%}", na_rep="-").map(_color_returns)


def _color_returns(value):
    if pd.isna(value):
        return ""
    if value > 0.06:
        return "background-color: #D9EAD3; color: #174A1A"
    if value < -0.02:
        return "background-color: #F4CCCC; color: #7F0000"
    return ""


def plot_benchmark_drawdown(core_returns):
    dd = drawdown(core_returns[BENCHMARK_6040])
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(dd.index, dd.values, color=STRATEGY_COLORS[BENCHMARK_6040], linewidth=1.6)
    ax.fill_between(dd.index, dd.values, 0.0, alpha=0.12, color=STRATEGY_COLORS[BENCHMARK_6040])
    ax.axhline(0, color="#333333", linewidth=0.8)
    ax.set_title("60/40 Drawdown")
    ax.set_ylabel("Drawdown")
    _pct_axis(ax)
    _style_axes(ax)
    plt.tight_layout()
    return ax


def plot_annual_return_bars(return_series, title):
    annual = (1.0 + return_series.dropna()).resample("YE").prod() - 1.0
    fig, ax = plt.subplots(figsize=(13, 5))
    colors = [POSITIVE_COLOR if x >= 0 else NEGATIVE_COLOR for x in annual.values]
    ax.bar(annual.index.year, annual.values, color=colors, width=0.8)
    ax.axhline(0, color="#333333", linewidth=0.8)
    ax.set_title(title)
    ax.set_ylabel("Return")
    ax.set_xlabel("")
    _pct_axis(ax)
    _style_axes(ax, "y")
    plt.tight_layout()
    return ax


def plot_return_scatter_original(core_returns):
    df = core_returns[[COMMODITY_TREND, BENCHMARK_6040]].dropna()
    rho = df[COMMODITY_TREND].corr(df[BENCHMARK_6040])
    fig, ax = plt.subplots(figsize=(7, 7))
    ax.scatter(df[BENCHMARK_6040], df[COMMODITY_TREND], s=8, alpha=0.25, color=STRATEGY_COLORS[COMMODITY_TREND])
    coef = np.polyfit(df[BENCHMARK_6040], df[COMMODITY_TREND], 1)
    xp = np.linspace(df[BENCHMARK_6040].min(), df[BENCHMARK_6040].max(), 100)
    ax.plot(xp, np.poly1d(coef)(xp), color=STRATEGY_COLORS[BENCHMARK_6040], linewidth=1.5, alpha=0.9, label=f"OLS slope = {coef[0]:.3f}")
    ax.set_xlabel("60/40 daily return")
    ax.set_ylabel("Commodity-Trend daily return")
    ax.set_title(f"Daily returns, full sample, rho = {rho:.3f}")
    ax.legend(loc="upper left", fontsize=9)
    ax.axhline(0, color="gray", linewidth=0.5)
    ax.axvline(0, color="gray", linewidth=0.5)
    _pct_axis(ax)
    ax.xaxis.set_major_formatter(FuncFormatter(lambda y, _: f"{y:.0%}"))
    _style_axes(ax)
    plt.tight_layout()
    return ax


def plot_correlation_combo_original(core_returns):
    df = core_returns[[COMMODITY_TREND, BENCHMARK_6040]].dropna()
    roll_m = df[COMMODITY_TREND].rolling(21, min_periods=10).corr(df[BENCHMARK_6040])
    roll_q = df[COMMODITY_TREND].rolling(63, min_periods=31).corr(df[BENCHMARK_6040])
    annual = df.groupby(df.index.year).apply(lambda g: g[COMMODITY_TREND].corr(g[BENCHMARK_6040]))

    fig, (ax_top, ax_bot) = plt.subplots(2, 1, figsize=(12, 7), gridspec_kw={"height_ratios": [2, 1], "hspace": 0.25})
    ax_top.plot(roll_m.index, roll_m.values, color=STRATEGY_COLORS[COMMODITY_TREND], linewidth=1.2, label="21-day rolling rho")
    ax_top.plot(roll_q.index, roll_q.values, color=STRATEGY_COLORS[BENCHMARK_6040], linewidth=1.2, label="63-day rolling rho")
    ax_top.set_ylabel("Rolling correlation")
    ax_top.set_title("Commodity-Trend vs 60/40: rolling and calendar-year correlation")
    ax_top.legend(loc="upper right")
    _style_axes(ax_top)

    ax_bot.bar(annual.index.to_numpy(), annual.to_numpy(), color="#2E75B6", alpha=0.85, width=0.7)
    ax_bot.set_ylabel("Calendar-year correlation")
    ax_bot.set_xlabel("Year")
    ax_bot.axhline(0, color="gray", linewidth=0.6)
    _style_axes(ax_bot, "y")
    plt.tight_layout()
    return fig


def plot_nav_original(return_map, title, colors=None):
    fig, ax = plt.subplots(figsize=(12, 6))
    for label, ret in return_map.items():
        nav = INITIAL_AUM * _growth(ret)
        ax.plot(nav.index, (nav / INITIAL_AUM).values, label=label, linewidth=2.0, color=(colors or {}).get(label, STRATEGY_COLORS.get(label)))
    ax.set_title(title)
    ax.set_ylabel("NAV / Initial AUM")
    ax.set_xlabel("")
    ax.legend(loc="upper left")
    _style_axes(ax)
    plt.tight_layout()
    return ax


def plot_drawdown_original(return_map, title, colors=None):
    fig, ax = plt.subplots(figsize=(12, 5))
    for label, ret in return_map.items():
        dd = drawdown(ret)
        c = (colors or {}).get(label, STRATEGY_COLORS.get(label, "#7F7F7F"))
        ax.plot(dd.index, dd.values, label=label, linewidth=1.6, color=c)
        ax.fill_between(dd.index, dd.values, 0.0, alpha=0.12, color=c)
    ax.axhline(0, color="#333333", linewidth=0.8)
    ax.set_title(title)
    ax.set_ylabel("Drawdown")
    _pct_axis(ax)
    ax.legend(loc="lower left")
    _style_axes(ax)
    plt.tight_layout()
    return ax


def display_evaluation_block(name, daily_ret, weight=None):
    summary = summary_frame(daily_ret.to_frame(name), [name])
    if weight is not None:
        summary["Weights (w_T / w_B)"] = f"{weight:.0%} / {1.0 - weight:.0%}"
    display(format_metric_table(summary.T.reset_index().rename(columns={"index": "Metric", 0: name})))
    plot_nav_original({name: daily_ret}, f"{name}: NAV index", colors={name: STRATEGY_COLORS.get(name)})
    plot_drawdown_original({name: daily_ret}, f"{name}: Drawdown", colors={name: "#7F7F7F"})
    display(monthly_return_heatmap_original(daily_ret))
    plot_annual_return_bars(daily_ret, f"{name}: Annual returns")


def plot_mean_variance_frontier_original(core_returns, static_weights):
    df = core_returns[[COMMODITY_TREND, BENCHMARK_6040]].dropna()
    mu = df.mean() * TRADING_DAYS
    cov = df.cov() * TRADING_DAYS

    def stats(w_t):
        w = np.array([w_t, 1 - w_t])
        ann_return = float(w @ mu.values)
        ann_vol = float(np.sqrt(w @ cov.values @ w))
        return ann_return, ann_vol

    grid = np.linspace(0, 1, 101)
    frontier = pd.DataFrame([stats(w) for w in grid], columns=["return", "vol"])
    tan_row = static_weights[static_weights["Strategy"].str.contains("Tangency", case=False, na=False)].iloc[0]
    mv_row = static_weights[static_weights["Strategy"].str.contains("Min", case=False, na=False)].iloc[0]
    sleeve_row = static_weights[static_weights["Strategy"].str.contains("90/10", case=False, na=False)].iloc[0]

    fig, ax = plt.subplots(figsize=(9.6, 6.2))
    ax.plot(frontier["vol"], frontier["return"], color="#404040", linewidth=1.6, label="Long-only efficient frontier")
    for label, w_t, marker, color in [
        ("60/40 only (w_T = 0)", 0.0, "o", STRATEGY_COLORS[BENCHMARK_6040]),
        ("Commodity-Trend only (w_T = 100%)", 1.0, "o", STRATEGY_COLORS[COMMODITY_TREND]),
        (f"Min. variance (w_T = {mv_row['w_T']:.0%})", float(mv_row["w_T"]), "s", STATIC_MV and STRATEGY_COLORS[STATIC_MV]),
        (f"Tangency, long-only (w_T = {tan_row['w_T']:.0%})", float(tan_row["w_T"]), "*", STRATEGY_COLORS[STATIC_MV]),
        ("90/10 blend", float(sleeve_row["w_T"]), "D", STRATEGY_COLORS[SLEEVE_9010]),
    ]:
        r, v = stats(w_t)
        ax.scatter([v], [r], s=110, color=color, marker=marker, label=label, edgecolor="white", linewidth=0.7, zorder=3)
    ax.set_title("Mean-Variance Frontier")
    ax.set_xlabel("Annualized volatility")
    ax.set_ylabel("Annualized return")
    ax.xaxis.set_major_formatter(FuncFormatter(lambda y, _: f"{y:.0%}"))
    _pct_axis(ax)
    ax.legend(loc="best", fontsize=8)
    _style_axes(ax)
    plt.tight_layout()
    return ax


def plot_dynamic_weight_step(dynamic_weights):
    fig, ax = plt.subplots(figsize=(12, 4.2))
    ax.step(dynamic_weights.index, dynamic_weights["w_T_tan"], where="post", color=STRATEGY_COLORS[DYNAMIC_MV], linewidth=1.65)
    ax.set_title("Dynamic MV: tangency w_T at month-ends")
    ax.set_ylabel("w_T")
    ax.set_xlabel("Month-end")
    _pct_axis(ax)
    _style_axes(ax)
    plt.tight_layout()
    return ax


def plot_stacked_drawdowns_original(strategy_returns):
    columns = [c for c in [BENCHMARK_6040, COMMODITY_TREND, SLEEVE_9010, STATIC_MV, DYNAMIC_MV] if c in strategy_returns]
    fig, axes = plt.subplots(len(columns), 1, figsize=(12, 2.65 * len(columns)), sharex=True)
    axes = np.atleast_1d(axes)
    for ax, name in zip(axes, columns):
        dd = drawdown(strategy_returns[name])
        c = STRATEGY_COLORS.get(name, "#7F7F7F")
        ax.fill_between(dd.index, dd.values, 0.0, alpha=0.16, color=c)
        ax.plot(dd.index, dd.values, color=c, linewidth=1.15)
        ax.axhline(0, color="#333333", linewidth=0.65)
        ax.set_title(name, loc="left", fontsize=10)
        ax.set_ylabel("Drawdown")
        _pct_axis(ax)
        _style_axes(ax)
    axes[-1].set_xlabel("Date")
    fig.suptitle("Five strategies: drawdown", fontsize=12, y=1.005)
    plt.tight_layout()
    return fig


def plot_stacked_annual_returns_original(strategy_returns):
    columns = [c for c in [BENCHMARK_6040, COMMODITY_TREND, SLEEVE_9010, STATIC_MV, DYNAMIC_MV] if c in strategy_returns]
    fig, axes = plt.subplots(len(columns), 1, figsize=(12, 2.5 * len(columns)), sharex=False)
    axes = np.atleast_1d(axes)
    for ax, name in zip(axes, columns):
        annual = (1.0 + strategy_returns[name].dropna()).resample("YE").prod() - 1.0
        colors = [POSITIVE_COLOR if x >= 0 else NEGATIVE_COLOR for x in annual.values]
        ax.bar(annual.index.year, annual.values, color=colors, width=0.82)
        ax.axhline(0, color="#333333", linewidth=0.75)
        ax.set_title(name, loc="left", fontsize=10)
        ax.set_ylabel("Return")
        _pct_axis(ax)
        _style_axes(ax, "y")
    axes[-1].set_xlabel("Calendar year")
    fig.suptitle("Five strategies: annual returns", fontsize=12, y=1.005)
    plt.tight_layout()
    return fig


def plot_relative_wealth_original(strategy_returns):
    ratio = _growth(strategy_returns[DYNAMIC_MV]) / _growth(strategy_returns[BENCHMARK_6040])
    fig, ax = plt.subplots(figsize=(12, 3.2))
    ax.plot(ratio.index, ratio.values, color=STRATEGY_COLORS[DYNAMIC_MV], linewidth=1.75)
    ax.axhline(1.0, color="#333333", linewidth=0.8)
    ax.set_title("Dynamic MV relative wealth vs 60/40")
    ax.set_ylabel("Ratio")
    _style_axes(ax)
    plt.tight_layout()
    return ax


def plot_drawdown_episode_timeline_original(core_returns, episodes):
    growth = core_returns[[BENCHMARK_6040, COMMODITY_TREND]].dropna().apply(_growth)
    dds = core_returns[[BENCHMARK_6040, COMMODITY_TREND]].dropna().apply(drawdown)
    large = episodes[episodes["large_ge_10pct"].astype(bool)]
    fig, (ax_top, ax_bot) = plt.subplots(2, 1, figsize=(12, 7.2), sharex=True, gridspec_kw={"height_ratios": [2, 1]})
    for name in [BENCHMARK_6040, COMMODITY_TREND]:
        ax_top.plot(growth.index, growth[name], label=name, color=STRATEGY_COLORS[name], linewidth=1.55)
        ax_bot.plot(dds.index, dds[name], label=name, color=STRATEGY_COLORS[name], linewidth=1.2)
    for _, row in large.iterrows():
        ax_top.axvspan(row["peak_date"], row["trough_date"], color="#D9E2F3", alpha=0.45)
        ax_bot.axvspan(row["peak_date"], row["trough_date"], color="#D9E2F3", alpha=0.45)
    ax_top.set_title("NAV index: shaded bands = 60/40 drawdown episodes >=10% depth")
    ax_top.set_ylabel("NAV index")
    ax_top.legend(loc="upper left")
    ax_bot.set_ylabel("Drawdown")
    _pct_axis(ax_bot)
    _style_axes(ax_top)
    _style_axes(ax_bot)
    plt.tight_layout()
    return fig


def plot_drawdown_episode_bars_original(episodes, top_n=13):
    sub = episodes.sort_values("depth_60_40").head(top_n).copy()
    labels = sub["peak_date"].dt.strftime("%Y-%m-%d") + " to " + sub["trough_date"].dt.strftime("%Y-%m-%d")
    y = np.arange(len(sub))
    fig, ax = plt.subplots(figsize=(10, max(4.0, 0.42 * len(sub))))
    ax.barh(y - 0.18, sub["bench_ret_peak_to_trough"], height=0.36, color=STRATEGY_COLORS[BENCHMARK_6040], label="60/40")
    ax.barh(y + 0.18, sub["trend_ret_peak_to_trough"], height=0.36, color=STRATEGY_COLORS[COMMODITY_TREND], label=COMMODITY_TREND)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.axvline(0, color="#333333", linewidth=0.8)
    ax.set_title(f"Deepest {top_n} drawdown episodes: peak-to-trough returns")
    ax.set_xlabel("Return")
    ax.xaxis.set_major_formatter(FuncFormatter(lambda y, _: f"{y:.0%}"))
    ax.legend(loc="best")
    _style_axes(ax, "x")
    plt.tight_layout()
    return ax


def plot_stress_matched_panels_original(quantile_windows, q_use=0.10):
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    for ax, horizon, title in zip(axes, ["21d_trailing", "63d_trailing"], ["21-Day Windows", "63-Day Windows"]):
        sub = quantile_windows[(quantile_windows["horizon"] == horizon) & (quantile_windows["quantile_cutoff_q"].round(4) == round(q_use, 4))]
        sub = sub.set_index("bucket").reindex([f"worst {q_use:.0%}", "rest"])
        x = np.arange(len(sub))
        ax.bar(x - 0.18, sub["bench_window_mean"], width=0.36, color=STRATEGY_COLORS[BENCHMARK_6040], label="60/40")
        ax.bar(x + 0.18, sub["trend_window_mean"], width=0.36, color=STRATEGY_COLORS[COMMODITY_TREND], label=COMMODITY_TREND)
        ax.set_xticks(x)
        ax.set_xticklabels(sub.index)
        ax.axhline(0, color="#333333", linewidth=0.75)
        ax.set_title(title)
        ax.set_ylabel("Average window return")
        _pct_axis(ax)
        _style_axes(ax, "y")
    axes[0].legend(loc="best")
    fig.suptitle("Commodity-Trend Performance in Worst 60/40 Windows", fontsize=11, y=1.03)
    plt.tight_layout()
    return fig


def plot_quintile_matched_bars_original(core_returns):
    def q_table(window):
        bench = (1.0 + core_returns[BENCHMARK_6040]).rolling(window).apply(np.prod, raw=True) - 1.0
        trend = (1.0 + core_returns[COMMODITY_TREND]).rolling(window).apply(np.prod, raw=True) - 1.0
        df = pd.concat({"bench": bench, "trend": trend}, axis=1).dropna()
        df["quintile"] = pd.qcut(df["bench"], 5, labels=["Q1", "Q2", "Q3", "Q4", "Q5"])
        return df.groupby("quintile", observed=False)[["bench", "trend"]].mean()

    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(12, 4.8))
    for ax, tbl, title in [(ax_a, q_table(21), "21-Day Windows"), (ax_b, q_table(63), "63-Day Windows")]:
        x = np.arange(len(tbl))
        ax.bar(x - 0.18, tbl["bench"], width=0.36, color=STRATEGY_COLORS[BENCHMARK_6040], label="60/40")
        ax.bar(x + 0.18, tbl["trend"], width=0.36, color=STRATEGY_COLORS[COMMODITY_TREND], label=COMMODITY_TREND)
        ax.set_xticks(x)
        ax.set_xticklabels(tbl.index)
        ax.axhline(0, color="#333333", linewidth=0.75)
        ax.set_title(title)
        ax.set_ylabel("Average window return")
        _pct_axis(ax)
        _style_axes(ax, "y")
    ax_a.legend(loc="best")
    fig.suptitle("Commodity-Trend Performance by 60/40 Return Quintile", fontsize=11, y=1.03)
    plt.tight_layout()
    return fig


def plot_drawdown_buckets_original(bucket_tbl):
    fig, ax = plt.subplots(figsize=(10, 4.5))
    x = np.arange(len(bucket_tbl))
    bars = ax.bar(x, bucket_tbl["trend_ann_mean_from_daily"].values, color=STRATEGY_COLORS[COMMODITY_TREND], alpha=0.88)
    ax.set_xticks(x)
    ax.set_xticklabels(bucket_tbl["bucket"].tolist(), rotation=15, ha="right")
    ax.axhline(0, color="#333333", linewidth=0.8)
    ax.set_ylabel("Annualized trend return")
    ax.set_title("Commodity-Trend performance vs current 60/40 drawdown depth")
    _pct_axis(ax)
    for bar, (_, row) in zip(bars, bucket_tbl.iterrows()):
        if pd.notna(row.get("trend_hit_rate_pos")):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f"n={int(row['n_days'])}\nhit={row['trend_hit_rate_pos']:.0%}", ha="center", va="bottom" if bar.get_height() >= 0 else "top", fontsize=8)
    _style_axes(ax, "y")
    plt.tight_layout()
    return ax


def dual_beta_regression_table(core_returns):
    pair = core_returns[[BENCHMARK_6040, COMMODITY_TREND]].dropna()
    y = pair[COMMODITY_TREND].to_numpy(dtype=float)
    b = pair[BENCHMARK_6040].to_numpy(dtype=float)
    pos = (b > 0).astype(float)
    neg = (b < 0).astype(float)
    x = np.column_stack([np.ones_like(b), b * pos, b * neg])
    beta_hat, *_ = np.linalg.lstsq(x, y, rcond=None)
    n_obs, n_params = x.shape
    resid = y - x @ beta_hat
    xtx_inv = np.linalg.pinv(x.T @ x)
    meat = np.zeros((n_params, n_params))
    for i in range(n_obs):
        xi = x[i]
        meat += (resid[i] ** 2) * np.outer(xi, xi)
    cov = xtx_inv @ meat @ xtx_inv * (n_obs / (n_obs - n_params))
    se = np.sqrt(np.clip(np.diag(cov), 0.0, np.inf))

    out = pd.DataFrame(
        {
            "Term": ["Alpha", "Beta up", "Beta down"],
            "Formula term": ["1", "r_60/40 * 1{r_60/40 > 0}", "r_60/40 * 1{r_60/40 < 0}"],
            "Estimate": beta_hat,
            "HC1 SE": se,
            "t-stat": beta_hat / se,
        }
    )
    out["N"] = n_obs
    return out


def style_regression_table(df):
    return (
        df.style.format({"Estimate": "{:.6f}", "HC1 SE": "{:.6f}", "t-stat": "{:.2f}", "N": "{:,.0f}"})
        .set_properties(**{"text-align": "center"})
        .set_table_styles([{"selector": "th", "props": [("text-align", "center"), ("font-weight", "600")]}])
        .hide(axis="index")
    )


def plot_part5_active_return_boxplots_original(returns):
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), sharey=True)
    freqs = {"month": "ME", "quarter": "QE", "year": "YE"}
    labels = {"month": "Month", "quarter": "Quarter", "year": "Year"}
    for ax, comp, title in zip(axes, [EQUITY, BONDS], ["vs Equity", "vs Bonds"]):
        plot_data = []
        for freq in freqs.values():
            windows = (1.0 + returns[[COMMODITY_TREND, comp]].dropna()).resample(freq).prod() - 1.0
            plot_data.append((windows[COMMODITY_TREND] - windows[comp]).dropna())
        bp = ax.boxplot(plot_data, tick_labels=[labels[h] for h in freqs], patch_artist=True, showfliers=False)
        for patch in bp["boxes"]:
            patch.set_facecolor(STRATEGY_COLORS[COMMODITY_TREND])
            patch.set_alpha(0.35)
        ax.axhline(0, color="#333333", linewidth=0.8)
        ax.set_title(f"Commodity-Trend active return {title}")
        ax.set_ylabel("Active return")
        _pct_axis(ax)
        _style_axes(ax, "y")
    plt.tight_layout()
    return fig


def plot_stock_bond_corr_original(returns):
    corr63 = returns[EQUITY].rolling(63, min_periods=31).corr(returns[BONDS])
    corr252 = returns[EQUITY].rolling(252, min_periods=126).corr(returns[BONDS])
    fig, ax = plt.subplots(figsize=(14, 5))
    ax.plot(returns.index, corr63, color=STRATEGY_COLORS[COMMODITY_TREND], linewidth=1.15, label="63-day equity-bond corr")
    ax.plot(returns.index, corr252, color=STRATEGY_COLORS[BENCHMARK_6040], linewidth=1.35, label="252-day equity-bond corr")
    ax.fill_between(returns.index, 0, corr63, where=corr63.gt(0), color="#D9EAD3", alpha=0.45)
    ax.axhline(0, color="#333333", linewidth=0.8)
    ax.set_title("Rolling Stock-Bond Correlation")
    ax.set_ylabel("Correlation")
    ax.legend(loc="upper right")
    _style_axes(ax)
    plt.tight_layout()
    return ax


def plot_part6_metric_panel_original(part6_conditional):
    pos = part6_conditional[part6_conditional["regime"] == "Positive stock-bond corr"].copy()
    pos["horizon"] = pos["horizon"].str.title()
    fig, axes = plt.subplots(1, 3, figsize=(16, 4.8))
    specs = [
        ("avg_trend_return", "avg_60_40_return", "Avg return"),
        ("avg_trend_sharpe", "avg_60_40_sharpe", "Avg Sharpe"),
        ("avg_trend_max_dd", "avg_60_40_max_dd", "Avg max drawdown"),
    ]
    for ax, (trend_col, bench_col, title) in zip(axes, specs):
        x = np.arange(len(pos))
        ax.bar(x - 0.18, pos[bench_col], width=0.36, color=STRATEGY_COLORS[BENCHMARK_6040], label="60/40")
        ax.bar(x + 0.18, pos[trend_col], width=0.36, color=STRATEGY_COLORS[COMMODITY_TREND], label=COMMODITY_TREND)
        ax.set_xticks(x)
        ax.set_xticklabels(pos["horizon"])
        ax.axhline(0, color="#333333", linewidth=0.8)
        ax.set_title(title)
        if "return" in trend_col or "dd" in trend_col:
            _pct_axis(ax)
        _style_axes(ax, "y")
    axes[0].legend(loc="best")
    plt.tight_layout()
    return fig


def plot_part6_active_return_boxplots_original(returns):
    frames = []
    for horizon, freq in {"Month": "ME", "Quarter": "QE", "Year": "YE"}.items():
        windows = (1.0 + returns[[COMMODITY_TREND, BENCHMARK_6040, EQUITY, BONDS]].dropna()).resample(freq).prod() - 1.0
        corr = returns[[EQUITY, BONDS]].dropna().resample(freq).apply(lambda frame: frame[EQUITY].corr(frame[BONDS])).reindex(windows.index)
        frames.append(
            pd.DataFrame(
                {
                    "horizon": horizon,
                    "regime": np.where(corr.gt(0), "Positive", "Non-positive"),
                    "active": windows[COMMODITY_TREND] - windows[BENCHMARK_6040],
                }
            )
        )
    df = pd.concat(frames).dropna()
    box_data, box_labels = [], []
    for horizon in ["Month", "Quarter", "Year"]:
        for regime in ["Positive", "Non-positive"]:
            box_data.append(df.loc[(df["horizon"] == horizon) & (df["regime"] == regime), "active"])
            box_labels.append(f"{horizon}\n{regime}")
    fig, ax = plt.subplots(figsize=(12, 5.5))
    bp = ax.boxplot(box_data, tick_labels=box_labels, showfliers=False, patch_artist=True)
    for patch in bp["boxes"]:
        patch.set_facecolor(STRATEGY_COLORS[COMMODITY_TREND])
        patch.set_alpha(0.30)
    ax.axhline(0, color="#333333", linewidth=0.8)
    ax.set_title("Commodity-Trend active return vs 60/40 by stock-bond correlation regime")
    ax.set_ylabel("Active return")
    _pct_axis(ax)
    _style_axes(ax, "y")
    plt.tight_layout()
    return ax
