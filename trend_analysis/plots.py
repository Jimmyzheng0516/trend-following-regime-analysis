import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.ticker import FuncFormatter, PercentFormatter

from .config import BENCHMARK_6040, BONDS, COMMODITY_TREND, DYNAMIC_MV, EQUITY, PRO_PALETTE, SLEEVE_9010, STATIC_MV
from .metrics import TRADING_DAYS, drawdown


def apply_theme():
    plt.rcParams.update(
        {
            "figure.figsize": (11.5, 6.2),
            "figure.dpi": 140,
            "axes.facecolor": "white",
            "axes.edgecolor": "#B8C0CC",
            "axes.grid": True,
            "axes.labelcolor": "#2F3640",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.titleweight": "600",
            "axes.titlesize": 14,
            "axes.labelsize": 10,
            "grid.color": "#E6EAF0",
            "grid.linewidth": 0.8,
            "legend.frameon": False,
            "legend.fontsize": 9,
            "lines.linewidth": 2.0,
            "xtick.color": "#4B5563",
            "ytick.color": "#4B5563",
            "font.family": "DejaVu Sans",
        }
    )


apply_theme()


def _color(name):
    return PRO_PALETTE.get(name, PRO_PALETTE["neutral"])


def _finalize(ax, title, xlabel="", ylabel="", legend=True):
    ax.set_title(title, loc="left", pad=12)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", alpha=0.9)
    ax.grid(axis="x", alpha=0.25)
    if legend:
        ax.legend(loc="best")
    plt.tight_layout()
    return ax


def _finalize_figure(fig):
    fig.tight_layout()
    return fig


def _percent_axis(ax, axis="y"):
    formatter = PercentFormatter(1.0)
    if axis == "x":
        ax.xaxis.set_major_formatter(formatter)
    else:
        ax.yaxis.set_major_formatter(formatter)


def _money_axis(ax):
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:,.1f}x"))


def _growth(returns):
    return (1 + returns.dropna(how="all")).cumprod()


def _annualized_return(series):
    returns = series.dropna()
    if returns.empty:
        return np.nan
    years = len(returns) / TRADING_DAYS
    return (1 + returns).prod() ** (1 / years) - 1


def _annualized_vol(series):
    return series.dropna().std() * np.sqrt(TRADING_DAYS)


def plot_cumulative_performance(returns, columns, title="Cumulative Performance"):
    fig, ax = plt.subplots()
    growth = _growth(returns[columns])
    for col in columns:
        ax.plot(growth.index, growth[col], label=col, color=_color(col), alpha=0.9)
    _money_axis(ax)
    return _finalize(ax, title, ylabel="Growth of $1")


def plot_daily_returns(returns, columns, title="Daily Returns"):
    fig, ax = plt.subplots()
    for col in columns:
        ax.plot(returns.index, returns[col], label=col, color=_color(col), alpha=0.48, linewidth=1.15)
    ax.axhline(0, color="#9AA4B2", linewidth=0.9)
    _percent_axis(ax)
    return _finalize(ax, title, ylabel="Daily Return")


def plot_drawdowns(returns, columns, title="Drawdowns"):
    fig, ax = plt.subplots()
    for col in columns:
        ax.plot(returns.index, drawdown(returns[col]), label=col, color=_color(col), alpha=0.82, linewidth=1.8)
    ax.axhline(0, color="#9AA4B2", linewidth=0.9)
    _percent_axis(ax)
    return _finalize(ax, title, ylabel="Drawdown")


def plot_annual_returns(return_series, title="60/40 Annual Returns"):
    annual = (1 + return_series.dropna()).resample("YE").prod() - 1
    fig, ax = plt.subplots(figsize=(11.5, 5.4))
    colors = [PRO_PALETTE["positive"] if value >= 0 else PRO_PALETTE["negative"] for value in annual]
    ax.bar(annual.index.year, annual.values, color=colors, alpha=0.86, width=0.72)
    ax.axhline(0, color="#4B5563", linewidth=0.9)
    _percent_axis(ax)
    return _finalize(ax, title, xlabel="Year", ylabel="Return", legend=False)


def plot_return_scatter(returns, title="Daily Return Relationship"):
    df = returns[[BENCHMARK_6040, COMMODITY_TREND]].dropna()
    fig, ax = plt.subplots(figsize=(7.2, 6.4))
    ax.scatter(
        df[BENCHMARK_6040],
        df[COMMODITY_TREND],
        s=14,
        alpha=0.28,
        color=_color(COMMODITY_TREND),
        edgecolors="none",
    )
    slope, intercept = np.polyfit(df[BENCHMARK_6040], df[COMMODITY_TREND], 1)
    x_vals = np.linspace(df[BENCHMARK_6040].min(), df[BENCHMARK_6040].max(), 100)
    ax.plot(x_vals, slope * x_vals + intercept, color=_color(BENCHMARK_6040), linewidth=1.8, label="Best Fit")
    ax.axhline(0, color="#9AA4B2", linewidth=0.8)
    ax.axvline(0, color="#9AA4B2", linewidth=0.8)
    _percent_axis(ax, "x")
    _percent_axis(ax)
    return _finalize(ax, title, xlabel="60/40 Daily Return", ylabel="Commodity-Trend Daily Return")


def plot_rolling_correlation(returns, window=252):
    corr = returns[BENCHMARK_6040].rolling(window).corr(returns[COMMODITY_TREND])
    fig, ax = plt.subplots()
    ax.plot(corr.index, corr, color=_color(COMMODITY_TREND), alpha=0.88, label=f"{window}D Correlation")
    ax.axhline(0, color="#4B5563", linewidth=0.9)
    return _finalize(ax, "Rolling Correlation", ylabel="Correlation")


def plot_correlation_panel(returns, windows=(21, 63), title="Correlation Profile"):
    df = returns[[BENCHMARK_6040, COMMODITY_TREND]].dropna()
    rolling = {window: df[BENCHMARK_6040].rolling(window).corr(df[COMMODITY_TREND]) for window in windows}
    annual = df[BENCHMARK_6040].groupby(df.index.year).corr(df[COMMODITY_TREND])

    fig, axes = plt.subplots(2, 1, figsize=(11.5, 7.4), sharex=False)
    for window, corr in rolling.items():
        axes[0].plot(corr.index, corr, label=f"{window}D", linewidth=1.8)
    axes[0].axhline(0, color="#4B5563", linewidth=0.9)
    axes[0].set_title("Rolling Correlation", loc="left", pad=10)
    axes[0].set_ylabel("Correlation")
    axes[0].legend(loc="best")

    colors = [PRO_PALETTE["positive"] if value >= 0 else PRO_PALETTE["negative"] for value in annual]
    axes[1].bar(annual.index.astype(int), annual.values, color=colors, alpha=0.82, width=0.72)
    axes[1].axhline(0, color="#4B5563", linewidth=0.9)
    axes[1].set_title("Calendar-Year Correlation", loc="left", pad=10)
    axes[1].set_xlabel("Year")
    axes[1].set_ylabel("Correlation")
    fig.suptitle(title, x=0.01, y=1.02, ha="left", fontsize=14, fontweight="600")
    return _finalize_figure(fig)


def plot_strategy_panel(strategy_returns, title="Five Strategies"):
    fig, ax = plt.subplots()
    growth = _growth(strategy_returns)
    for col in growth.columns:
        ax.plot(growth.index, growth[col], label=col, color=_color(col), alpha=0.78, linewidth=1.75)
    _money_axis(ax)
    return _finalize(ax, title, ylabel="Growth of $1")


def plot_mean_variance_frontier(strategy_returns=None, static_weights=None):
    if static_weights is not None:
        stats = static_weights.rename(columns={"ann_vol": "Ann. Vol", "ann_return": "Ann. Return"}).copy()
        if "Strategy" in stats.columns:
            stats = stats.set_index("Strategy")
    else:
        stats = pd.DataFrame(
            {
                "Ann. Vol": strategy_returns.apply(_annualized_vol),
                "Ann. Return": strategy_returns.apply(_annualized_return),
            }
        ).dropna()
    fig, ax = plt.subplots(figsize=(8.0, 6.4))
    for name, row in stats.iterrows():
        display_name = str(name).replace("100% trend", COMMODITY_TREND).replace("60/40 only", BENCHMARK_6040)
        ax.scatter(row["Ann. Vol"], row["Ann. Return"], s=90, color=_color(display_name), alpha=0.9)
        ax.annotate(display_name, (row["Ann. Vol"], row["Ann. Return"]), xytext=(7, 5), textcoords="offset points", fontsize=9)
    _percent_axis(ax, "x")
    _percent_axis(ax)
    return _finalize(ax, "Risk-Return Map", xlabel="Annualized Volatility", ylabel="Annualized Return", legend=False)


def plot_dynamic_weights(weights):
    fig, ax = plt.subplots()
    labels = {"w_T_tan": "Tangency Weight", "w_T_mv": "Min-Variance Weight"}
    colors = {"w_T_tan": _color(DYNAMIC_MV), "w_T_mv": _color(STATIC_MV)}
    for col, label in labels.items():
        if col in weights:
            ax.plot(weights.index, weights[col], label=label, color=colors[col], alpha=0.82, linewidth=1.8)
    _percent_axis(ax)
    return _finalize(ax, "Dynamic Commodity-Trend Weights", ylabel="Weight")


def plot_wealth_ratio(strategy_returns, numerator=DYNAMIC_MV, denominator=BENCHMARK_6040):
    growth = _growth(strategy_returns[[numerator, denominator]].dropna())
    ratio = growth[numerator] / growth[denominator]
    fig, ax = plt.subplots()
    ax.plot(ratio.index, ratio, color=_color(numerator), alpha=0.88, label=f"{numerator} / {denominator}")
    ax.axhline(1, color="#4B5563", linewidth=0.9)
    return _finalize(ax, "Relative Wealth", ylabel="Ratio")


def plot_strategy_drawdown_panel(strategy_returns):
    columns = [col for col in [BENCHMARK_6040, COMMODITY_TREND, SLEEVE_9010, STATIC_MV, DYNAMIC_MV] if col in strategy_returns]
    fig, axes = plt.subplots(len(columns), 1, figsize=(11.5, 1.65 * len(columns)), sharex=True)
    axes = np.atleast_1d(axes)
    for ax, col in zip(axes, columns):
        ax.fill_between(strategy_returns.index, drawdown(strategy_returns[col]), 0, color=_color(col), alpha=0.35)
        ax.plot(strategy_returns.index, drawdown(strategy_returns[col]), color=_color(col), linewidth=1.1)
        ax.set_ylabel(col)
        _percent_axis(ax)
        ax.axhline(0, color="#9AA4B2", linewidth=0.8)
    axes[0].set_title("Strategy Drawdowns", loc="left", pad=10)
    axes[-1].set_xlabel("Date")
    return _finalize_figure(fig)


def plot_strategy_annual_returns(strategy_returns):
    columns = [col for col in [BENCHMARK_6040, COMMODITY_TREND, SLEEVE_9010, STATIC_MV, DYNAMIC_MV] if col in strategy_returns]
    annual = (1 + strategy_returns[columns].dropna(how="all")).resample("YE").prod() - 1
    fig, axes = plt.subplots(len(columns), 1, figsize=(11.5, 1.75 * len(columns)), sharex=True)
    axes = np.atleast_1d(axes)
    for ax, col in zip(axes, columns):
        colors = [PRO_PALETTE["positive"] if value >= 0 else PRO_PALETTE["negative"] for value in annual[col]]
        ax.bar(annual.index.year, annual[col], color=colors, alpha=0.82, width=0.72)
        ax.axhline(0, color="#4B5563", linewidth=0.8)
        ax.set_ylabel(col)
        _percent_axis(ax)
    axes[0].set_title("Annual Returns", loc="left", pad=10)
    axes[-1].set_xlabel("Year")
    return _finalize_figure(fig)


def plot_drawdown_episode_timeline(returns, episodes):
    core = returns[[BENCHMARK_6040, COMMODITY_TREND]].dropna()
    growth = _growth(core)
    dd = core.apply(drawdown)
    large = episodes[episodes.get("large_ge_10pct", True)].copy()

    fig, axes = plt.subplots(2, 1, figsize=(11.5, 7.4), sharex=True)
    for col in [BENCHMARK_6040, COMMODITY_TREND]:
        axes[0].plot(growth.index, growth[col], label=col, color=_color(col), alpha=0.88)
        axes[1].plot(dd.index, dd[col], label=col, color=_color(col), alpha=0.88)
    for _, row in large.iterrows():
        for ax in axes:
            ax.axvspan(row["peak_date"], row["trough_date"], color=PRO_PALETTE["light"], alpha=0.42, linewidth=0)
    axes[0].set_title("Wealth During 60/40 Drawdowns", loc="left", pad=10)
    axes[0].set_ylabel("Growth of $1")
    axes[0].legend(loc="best")
    axes[1].set_title("Drawdown", loc="left", pad=10)
    axes[1].set_ylabel("Drawdown")
    _money_axis(axes[0])
    _percent_axis(axes[1])
    axes[1].set_xlabel("Date")
    return _finalize_figure(fig)


def plot_drawdown_episode_bars(episodes):
    df = episodes.copy()
    df["episode"] = df["peak_date"].dt.year.astype(str) + " to " + df["trough_date"].dt.year.astype(str)
    fig, ax = plt.subplots(figsize=(11.5, 6.8))
    y = np.arange(len(df))
    width = 0.38
    ax.barh(y - width / 2, df["bench_ret_peak_to_trough"], height=width, color=_color(BENCHMARK_6040), alpha=0.82, label="60/40")
    ax.barh(y + width / 2, df["trend_ret_peak_to_trough"], height=width, color=_color(COMMODITY_TREND), alpha=0.82, label=COMMODITY_TREND)
    ax.set_yticks(y)
    ax.set_yticklabels(df["episode"])
    ax.invert_yaxis()
    ax.axvline(0, color="#4B5563", linewidth=0.9)
    _percent_axis(ax, "x")
    return _finalize(ax, "60/40 Drawdown Episodes", xlabel="Peak-to-Trough Return", ylabel="")


def plot_quantile_windows(windows, quantile=0.10):
    df = windows[windows["quantile_cutoff_q"].round(4).eq(round(quantile, 4))].copy()
    df["label"] = df["horizon"].str.replace("_", " ").str.replace("trailing", "", regex=False).str.strip() + " | " + df["bucket"]
    fig, ax = plt.subplots(figsize=(11.5, 6.4))
    x = np.arange(len(df))
    width = 0.36
    ax.bar(x - width / 2, df["bench_window_mean"], width, label="60/40", color=_color(BENCHMARK_6040), alpha=0.84)
    ax.bar(x + width / 2, df["trend_window_mean"], width, label=COMMODITY_TREND, color=_color(COMMODITY_TREND), alpha=0.84)
    ax.set_xticks(x)
    ax.set_xticklabels(df["label"], rotation=30, ha="right")
    ax.axhline(0, color="#4B5563", linewidth=0.9)
    _percent_axis(ax)
    return _finalize(ax, "Worst-Window Performance", ylabel="Average Return")


def plot_all_quantile_windows(windows):
    df = windows.copy()
    df["label"] = (
        df["horizon"].str.replace("_", " ").str.replace("trailing", "", regex=False).str.strip()
        + " | q="
        + (df["quantile_cutoff_q"] * 100).round(0).astype(int).astype(str)
        + "% | "
        + df["bucket"]
    )
    fig, ax = plt.subplots(figsize=(12.6, 6.6))
    x = np.arange(len(df))
    width = 0.36
    ax.bar(x - width / 2, df["bench_window_mean"], width, label=BENCHMARK_6040, color=_color(BENCHMARK_6040), alpha=0.84)
    ax.bar(x + width / 2, df["trend_window_mean"], width, label=COMMODITY_TREND, color=_color(COMMODITY_TREND), alpha=0.84)
    ax.set_xticks(x)
    ax.set_xticklabels(df["label"], rotation=35, ha="right")
    ax.axhline(0, color="#4B5563", linewidth=0.9)
    _percent_axis(ax)
    return _finalize(ax, "Matched Stress Windows", ylabel="Average Return")


def plot_stress_hit_rate(windows):
    df = windows.copy()
    df["label"] = (
        df["horizon"].str.replace("_", " ").str.replace("trailing", "", regex=False).str.strip()
        + " | q="
        + (df["quantile_cutoff_q"] * 100).round(0).astype(int).astype(str)
        + "% | "
        + df["bucket"]
    )
    fig, ax = plt.subplots(figsize=(12.2, 5.4))
    ax.bar(df["label"], df["trend_window_hit_rate_pos"], color=_color(COMMODITY_TREND), alpha=0.78)
    ax.axhline(0.5, color="#4B5563", linewidth=0.9)
    ax.tick_params(axis="x", rotation=35)
    _percent_axis(ax)
    return _finalize(ax, "Positive Hit Rate in Stress Windows", ylabel="Hit Rate", legend=False)


def plot_drawdown_buckets(buckets):
    df = buckets.dropna(subset=["trend_ann_mean_from_daily"]).copy()
    fig, axes = plt.subplots(1, 2, figsize=(12.2, 5.2))
    axes[0].bar(df["bucket"], df["trend_ann_mean_from_daily"], color=_color(COMMODITY_TREND), alpha=0.84)
    axes[0].axhline(0, color="#4B5563", linewidth=0.9)
    _percent_axis(axes[0])
    _finalize(axes[0], "Return by 60/40 Drawdown", ylabel="Annualized Return", legend=False)

    axes[1].bar(df["bucket"], df["trend_hit_rate_pos"], color=_color(COMMODITY_TREND), alpha=0.72)
    axes[1].axhline(0.5, color="#4B5563", linewidth=0.9)
    _percent_axis(axes[1])
    _finalize(axes[1], "Positive Day Hit Rate", ylabel="Hit Rate", legend=False)
    for ax in axes:
        ax.tick_params(axis="x", rotation=25)
    plt.tight_layout()
    return axes


def plot_part5_calendar(calendar):
    df = calendar.copy()
    df["label"] = df["horizon"].str.title() + " vs. " + df["comparator"].str.title()
    fig, axes = plt.subplots(1, 2, figsize=(12.2, 5.4))
    axes[0].bar(df["label"], df["outright_win_rate"], color=_color(COMMODITY_TREND), alpha=0.82)
    axes[0].axhline(0.5, color="#4B5563", linewidth=0.9)
    _percent_axis(axes[0])
    _finalize(axes[0], "Outperformance Rate", ylabel="Win Rate", legend=False)

    colors = [PRO_PALETTE["positive"] if value >= 0 else PRO_PALETTE["negative"] for value in df["average_active_return"]]
    axes[1].bar(df["label"], df["average_active_return"], color=colors, alpha=0.82)
    axes[1].axhline(0, color="#4B5563", linewidth=0.9)
    _percent_axis(axes[1])
    _finalize(axes[1], "Average Active Return", ylabel="Active Return", legend=False)
    for ax in axes:
        ax.tick_params(axis="x", rotation=35)
    plt.tight_layout()
    return axes


def plot_stock_bond_correlation(returns, window=252):
    corr = returns[EQUITY].rolling(window).corr(returns[BONDS])
    fig, ax = plt.subplots()
    ax.plot(corr.index, corr, color=_color(BONDS), alpha=0.85, label=f"{window}D Correlation")
    ax.axhline(0, color="#4B5563", linewidth=0.9)
    return _finalize(ax, "Stock-Bond Correlation", ylabel="Correlation")


def plot_stock_bond_correlation_regimes(returns, window=252):
    corr = returns[EQUITY].rolling(window).corr(returns[BONDS])
    fig, ax = plt.subplots()
    ax.plot(corr.index, corr, color=_color(BONDS), alpha=0.9, label=f"{window}D Correlation")
    ax.fill_between(corr.index, 0, corr, where=corr.gt(0), color=PRO_PALETTE["positive"], alpha=0.18, linewidth=0)
    ax.axhline(0, color="#4B5563", linewidth=0.9)
    return _finalize(ax, "Stock-Bond Correlation Regimes", ylabel="Correlation")


def plot_part6_conditional(conditional):
    df = conditional[conditional["regime"].str.contains("Positive", case=False, na=False)].copy()
    if df.empty:
        df = conditional.copy()
    df["horizon"] = df["horizon"].str.title()
    fig, axes = plt.subplots(1, 2, figsize=(12.2, 5.4))
    axes[0].bar(df["horizon"], df["avg_active_return_t_minus_6040"], color=_color(COMMODITY_TREND), alpha=0.82)
    axes[0].axhline(0, color="#4B5563", linewidth=0.9)
    _percent_axis(axes[0])
    _finalize(axes[0], "Active Return in Positive-Corr Regimes", ylabel="Active Return", legend=False)

    axes[1].bar(df["horizon"], df["trend_win_rate_vs_60_40"], color=_color(COMMODITY_TREND), alpha=0.72)
    axes[1].axhline(0.5, color="#4B5563", linewidth=0.9)
    _percent_axis(axes[1])
    _finalize(axes[1], "Win Rate vs. 60/40", ylabel="Win Rate", legend=False)
    plt.tight_layout()
    return axes


def plot_part6_metric_panel(conditional):
    df = conditional[conditional["regime"].str.contains("Positive", case=False, na=False)].copy()
    if df.empty:
        df = conditional.copy()
    df["horizon"] = df["horizon"].str.title()
    metrics = [
        ("avg_trend_return", "avg_60_40_return", "Return"),
        ("avg_trend_sharpe", "avg_60_40_sharpe", "Sharpe"),
        ("avg_trend_max_dd", "avg_60_40_max_dd", "Max Drawdown"),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.8))
    for ax, (trend_col, bench_col, title) in zip(axes, metrics):
        x = np.arange(len(df))
        width = 0.36
        ax.bar(x - width / 2, df[bench_col], width, label=BENCHMARK_6040, color=_color(BENCHMARK_6040), alpha=0.84)
        ax.bar(x + width / 2, df[trend_col], width, label=COMMODITY_TREND, color=_color(COMMODITY_TREND), alpha=0.84)
        ax.set_xticks(x)
        ax.set_xticklabels(df["horizon"])
        ax.axhline(0, color="#4B5563", linewidth=0.8)
        ax.set_title(title, loc="left", pad=10)
        if "return" in trend_col or "dd" in trend_col:
            _percent_axis(ax)
    axes[0].legend(loc="best")
    return _finalize_figure(fig)


def _calendar_window_returns(returns, freq):
    grouped = (1 + returns.dropna(how="all")).resample(freq).prod() - 1
    return grouped.dropna(how="any")


def plot_part5_active_return_boxplots(returns):
    frames = []
    for label, freq in [("Month", "ME"), ("Quarter", "QE"), ("Year", "YE")]:
        windows = _calendar_window_returns(returns[[COMMODITY_TREND, EQUITY, BONDS]], freq)
        for comparator in [EQUITY, BONDS]:
            active = windows[COMMODITY_TREND] - windows[comparator]
            frames.append(pd.DataFrame({"Horizon": label, "Comparator": comparator, "Active Return": active.values}))
    df = pd.concat(frames, ignore_index=True)
    fig, axes = plt.subplots(1, 2, figsize=(12.2, 5.4), sharey=True)
    for ax, comparator in zip(axes, [EQUITY, BONDS]):
        sub = df[df["Comparator"].eq(comparator)]
        groups = [sub.loc[sub["Horizon"].eq(h), "Active Return"].dropna() for h in ["Month", "Quarter", "Year"]]
        ax.boxplot(groups, labels=["Month", "Quarter", "Year"], showfliers=False, patch_artist=True)
        for patch in ax.patches:
            patch.set_facecolor(_color(COMMODITY_TREND))
            patch.set_alpha(0.45)
        ax.axhline(0, color="#4B5563", linewidth=0.9)
        ax.set_title(f"vs. {comparator}", loc="left", pad=10)
        ax.set_ylabel("Active Return")
        _percent_axis(ax)
    fig.suptitle("Active Return Distribution", x=0.01, y=1.02, ha="left", fontsize=14, fontweight="600")
    return _finalize_figure(fig)


def plot_part6_active_return_boxplots(returns):
    frames = []
    for label, freq in [("Month", "ME"), ("Quarter", "QE"), ("Year", "YE")]:
        windows = _calendar_window_returns(returns[[COMMODITY_TREND, BENCHMARK_6040, EQUITY, BONDS]], freq)
        corr = returns[[EQUITY, BONDS]].dropna().resample(freq).apply(lambda frame: frame[EQUITY].corr(frame[BONDS]))
        corr = corr.reindex(windows.index)
        regime = np.where(corr.gt(0), "Positive", "Non-Positive")
        frames.append(
            pd.DataFrame(
                {
                    "Horizon": label,
                    "Regime": regime,
                    "Active Return": windows[COMMODITY_TREND] - windows[BENCHMARK_6040],
                }
            )
        )
    df = pd.concat(frames, ignore_index=True).dropna()
    labels = []
    groups = []
    for horizon in ["Month", "Quarter", "Year"]:
        for regime in ["Positive", "Non-Positive"]:
            labels.append(f"{horizon}\n{regime}")
            groups.append(df.loc[df["Horizon"].eq(horizon) & df["Regime"].eq(regime), "Active Return"])
    fig, ax = plt.subplots(figsize=(12.4, 5.6))
    bp = ax.boxplot(groups, labels=labels, showfliers=False, patch_artist=True)
    for patch, label in zip(bp["boxes"], labels):
        patch.set_facecolor(PRO_PALETTE["positive"] if "Positive" in label and "Non" not in label else PRO_PALETTE["neutral"])
        patch.set_alpha(0.45)
    ax.axhline(0, color="#4B5563", linewidth=0.9)
    _percent_axis(ax)
    return _finalize(ax, "Active Return by Correlation Regime", ylabel="Active Return", legend=False)

