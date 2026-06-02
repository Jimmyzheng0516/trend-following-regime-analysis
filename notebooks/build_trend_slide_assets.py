"""Generate PPT-sized PNGs for trend_performance_intro (separate slides folder)."""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter

REPO = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = REPO / "Notebooks"
sys.path.insert(0, str(NOTEBOOK_DIR))

from trend_analysis.config import BENCHMARK_6040, BONDS, COMMODITY_TREND, EQUITY  # noqa: E402
from trend_analysis.data import (  # noqa: E402
    load_core_summary,
    load_drawdown_episodes,
    load_part5_calendar,
    load_part5_conditional,
    load_part6_conditional,
    load_part6_stress,
    prepare_core_and_strategy_returns,
)
from trend_analysis.original_style import (  # noqa: E402
    NEGATIVE_COLOR,
    POSITIVE_COLOR,
    STRATEGY_COLORS,
    _pct_axis,
    _style_axes,
    plot_drawdown_episode_timeline_original,
)

SLIDES_DIR = NOTEBOOK_DIR / "output" / "trend_performance_slides"
SLIDES_DIR.mkdir(parents=True, exist_ok=True)

DPI = 150
plt.rcParams.update({
    "font.size": 9,
    "axes.titlesize": 10,
    "axes.labelsize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "figure.dpi": DPI,
})

# White metrics table (matches notebook table styling on navy slide)
TABLE_BG_WHITE = "#FFFFFF"
TABLE_HEADER_LIGHT = "#F7F9FC"
TABLE_ROW_LIGHT = "#FFFFFF"
TABLE_ROW_ALT = "#F3F6FA"
TABLE_BORDER = "#E6EAF0"
TABLE_TEXT = "#1F2937"
TABLE_TEXT_MUTED = "#475569"
TABLE_TITLE = "#1F4E79"
CONDITIONAL_BAR = "#2A9D8F"
REFERENCE_BAR = "#94A3B8"
EQUITY_ACCENT = "#8E3B46"
BOND_ACCENT = "#4F6D7A"
STRESS_ESCALATION = ["#94A3B8", "#5BA4A4", "#2A9D8F"]

# Slide 1 annual strip: 1.75× original 2.55" placement width (overlays right edge of timeline)
SLIDE1_ANNUAL_W = 2.55 * 1.75
SLIDE1_ANNUAL_LEFT = 13.08 - SLIDE1_ANNUAL_W  # flush to right margin

METRIC_ROWS = [
    ("Annual return", "Annual rate of return", "{:.2%}"),
    ("Volatility", "Annualized volatility", "{:.2%}"),
    ("Sharpe (rf=0)", "Sharpe ratio, rf=0", "{:.2f}"),
    ("Max drawdown", "Maximum drawdown", "{:.2%}"),
    ("Ending NAV", "Ending NAV", "${:,.0f}"),
]


def _save(fig, name: str, *, facecolor: str | None = None) -> None:
    path = SLIDES_DIR / name
    kwargs = {"dpi": DPI, "bbox_inches": "tight", "pad_inches": 0.2}
    if facecolor:
        kwargs["facecolor"] = facecolor
        kwargs["edgecolor"] = "none"
    fig.savefig(path, **kwargs)
    plt.close(fig)
    print(" ", path.name)


def _episode_short_label(row: pd.Series) -> str:
    peak = pd.Timestamp(row["peak_date"])
    tags = {
        (2007, 10): "GFC '08",
        (2021, 12): "2022",
        (2020, 2): "COVID '20",
        (2002, 3): "2002",
        (2018, 9): "Q4 '18",
        (2025, 2): "2025",
        (2011, 7): "2011",
        (2015, 5): "2015",
        (2015, 12): "2015-16",
        (2018, 1): "Feb '18",
        (2020, 9): "Sep '20",
        (2026, 2): "2026",
        (2004, 3): "2004",
    }
    return tags.get((peak.year, peak.month), peak.strftime("%Y"))


def _month_row(df: pd.DataFrame, **filters) -> pd.Series:
    sub = df[df["horizon"] == "month"]
    for col, val in filters.items():
        sub = sub[sub[col] == val]
    if sub.empty:
        raise ValueError(f"No monthly row for {filters}")
    return sub.iloc[0]


def _annotate_rate(ax, x: float, rate: float, *, extra: str = "", color: str = "#1F2937") -> None:
    ax.text(x, rate + 0.025, f"{rate:.1%}{extra}", ha="center", va="bottom",
            fontsize=8, fontweight="bold", color=color)


def _annotate_jump(ax, x0: float, x1: float, y0: float, y1: float, label: str) -> None:
    ax.annotate(
        "",
        xy=(x1, y1 + 0.01),
        xytext=(x0, y0 + 0.01),
        arrowprops=dict(arrowstyle="-|>", color="#64748B", lw=1.1, shrinkA=0, shrinkB=0),
    )
    xm = (x0 + x1) / 2
    ax.text(xm, max(y0, y1) + 0.09, label, ha="center", va="bottom",
            fontsize=7, color="#64748B", fontweight="bold")


def _annual_returns(return_series: pd.Series) -> pd.Series:
    return (1.0 + return_series.dropna()).resample("YE").prod() - 1.0


def slide1_drawdown_episodes_timeline() -> None:
    _, core_returns, _ = prepare_core_and_strategy_returns()
    episodes = load_drawdown_episodes()
    fig = plot_drawdown_episode_timeline_original(core_returns, episodes)
    fig.set_size_inches(5.35, 3.55)
    fig.subplots_adjust(hspace=0.22)
    _save(fig, "slide1_drawdown_episodes_timeline.png")


def slide1_annual_returns_stacked() -> None:
    """Tall narrow column: annual return bars for Trend (top) and 60/40 (bottom)."""
    _, core_returns, _ = prepare_core_and_strategy_returns()
    fig, (ax_trend, ax_bench) = plt.subplots(
        2, 1, figsize=(2.75 * 1.75, 5.15), sharex=True, gridspec_kw={"height_ratios": [1, 1], "hspace": 0.32}
    )
    panels = [
        (ax_trend, COMMODITY_TREND, COMMODITY_TREND),
        (ax_bench, BENCHMARK_6040, "60/40"),
    ]
    for ax, col, title in panels:
        annual = _annual_returns(core_returns[col])
        years = annual.index.year
        bar_colors = [POSITIVE_COLOR if v >= 0 else NEGATIVE_COLOR for v in annual.values]
        ax.bar(years, annual.values, color=bar_colors, width=0.82, edgecolor="white", linewidth=0.3)
        ax.axhline(0, color="#333333", linewidth=0.7)
        ax.set_title(title, fontsize=8.5, pad=2)
        _pct_axis(ax)
        _style_axes(ax, "y")
        ax.tick_params(axis="x", labelsize=7)
    ax_bench.set_xlabel("Year", fontsize=7.5)
    plt.setp(ax_trend.get_xticklabels(), visible=False)
    fig.suptitle("Annual returns", fontsize=9, y=0.995)
    fig.subplots_adjust(top=0.94, bottom=0.07, left=0.14, right=0.98)
    _save(fig, "slide1_annual_returns_stacked.png")


def slide1_core_metrics_table() -> None:
    summary = load_core_summary()
    trend_col = "Commodity-Trend Model" if "Commodity-Trend Model" in summary.columns else "Method 1 (trend)"
    bench_col = "60/40" if "60/40" in summary.columns else "60/40 benchmark"

    fig, ax = plt.subplots(figsize=(5.35, 1.55))
    fig.patch.set_facecolor(TABLE_BG_WHITE)
    ax.set_facecolor(TABLE_BG_WHITE)
    ax.axis("off")

    n_rows = len(METRIC_ROWS) + 1
    n_cols = 3
    cell_w, cell_h = 1.0 / n_cols, 1.0 / n_rows
    headers = ["Metric", COMMODITY_TREND, BENCHMARK_6040]

    for j, header in enumerate(headers):
        x = j * cell_w
        y = 1.0 - cell_h
        ax.add_patch(plt.Rectangle((x, y), cell_w, cell_h, transform=ax.transAxes,
                                     facecolor=TABLE_HEADER_LIGHT, edgecolor=TABLE_BORDER, linewidth=0.8))
        ax.text(x + cell_w / 2, y + cell_h / 2, header, ha="center", va="center",
                fontsize=8.5, color=TABLE_TEXT, fontweight="bold", transform=ax.transAxes)

    for i, (label, metric_key, fmt) in enumerate(METRIC_ROWS):
        row_y = 1.0 - (i + 2) * cell_h
        row_fill = TABLE_ROW_ALT if i % 2 else TABLE_ROW_LIGHT
        values = [label]
        for col in (trend_col, bench_col):
            raw = summary.loc[summary["Metric"] == metric_key, col].iloc[0]
            values.append(fmt.format(float(raw)))

        for j, val in enumerate(values):
            x = j * cell_w
            ax.add_patch(plt.Rectangle((x, row_y), cell_w, cell_h, transform=ax.transAxes,
                                         facecolor=row_fill, edgecolor=TABLE_BORDER, linewidth=0.8))
            ax.text(x + cell_w / 2, row_y + cell_h / 2, val, ha="center", va="center",
                    fontsize=8 if j else 8.5, color=TABLE_TEXT_MUTED if j else TABLE_TEXT,
                    fontweight="normal" if j else "bold", transform=ax.transAxes)

    ax.text(0.0, 1.02, "Core performance metrics", fontsize=9.5, color=TABLE_TITLE,
            fontweight="bold", transform=ax.transAxes)
    _save(fig, "slide1_core_metrics_table.png", facecolor=TABLE_BG_WHITE)


def slide2_deepest13_drawdown_bars() -> None:
    episodes = load_drawdown_episodes().sort_values("depth_60_40").head(13).copy()
    episodes["label"] = episodes.apply(_episode_short_label, axis=1)
    y = np.arange(len(episodes))

    fig, ax = plt.subplots(figsize=(6.8, 4.35))
    ax.barh(y - 0.18, episodes["bench_ret_peak_to_trough"], height=0.36,
            color=STRATEGY_COLORS[BENCHMARK_6040], label="60/40")
    ax.barh(y + 0.18, episodes["trend_ret_peak_to_trough"], height=0.36,
            color=STRATEGY_COLORS[COMMODITY_TREND], label=COMMODITY_TREND)
    ax.set_yticks(y)
    ax.set_yticklabels(episodes["label"])
    ax.invert_yaxis()
    ax.axvline(0, color="#333333", linewidth=0.8)
    ax.set_title("Deepest 13 drawdown episodes: peak-to-trough returns")
    ax.set_xlabel("Return")
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax.legend(loc="lower left")
    _style_axes(ax, "x")
    _save(fig, "slide2_deepest13_drawdown_bars.png")


def slide3_part5_sleeve_win_rates() -> None:
    """Part 5: outright vs down-sleeve monthly win rates (Trend vs equity / bonds)."""
    cal = load_part5_calendar()
    cond = load_part5_conditional()

    panels = [
        (EQUITY, EQUITY_ACCENT, "equity_return < 0", "Equity down"),
        (BONDS, BOND_ACCENT, "bond_return < 0", "Bond down"),
    ]

    fig, axes = plt.subplots(1, 2, figsize=(6.8, 2.45), sharey=True)
    fig.suptitle("Trend vs sleeves: outright vs conditional (monthly win rate)", fontsize=9.5, y=1.02)

    for ax, (comp, accent, cond_key, cond_label) in zip(axes, panels):
        outright = float(_month_row(cal, comparator=comp)["outright_win_rate"])
        cond_row = _month_row(cond, comparator=comp, condition=cond_key)
        conditional = float(cond_row["outright_win_rate"])
        active = float(cond_row["average_active_return"])

        x = np.array([0.0, 1.0])
        ax.bar(x[0], outright, width=0.52, color=REFERENCE_BAR, edgecolor="white", linewidth=0.6)
        ax.bar(x[1], conditional, width=0.52, color=CONDITIONAL_BAR, edgecolor="white", linewidth=0.6)
        ax.axhline(0.5, color="#CBD5E1", linestyle=":", linewidth=0.9, alpha=0.9)
        ax.set_xticks(x)
        ax.set_xticklabels(["All\nmonths", cond_label])
        ax.set_title(f"vs {comp}", fontsize=9, color=accent, fontweight="bold")
        ax.set_ylim(0, 1.02)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0%}"))
        _annotate_rate(ax, x[0], outright)
        _annotate_rate(ax, x[1], conditional, extra=f"\n({active:+.1%} avg active)")
        _annotate_jump(ax, x[0], x[1], outright, conditional, f"+{(conditional - outright) * 100:.0f}pp")
        _style_axes(ax, "y")

    axes[0].set_ylabel("Trend win rate")
    fig.subplots_adjust(wspace=0.22, top=0.82, bottom=0.16, left=0.09, right=0.98)
    _save(fig, "slide3_part5_sleeve_win_rates.png")


def slide3_part6_poscorr_stress() -> None:
    """Part 6: positive-corr months vs 60/40, then stress overlaps."""
    p6 = load_part6_conditional()
    stress = load_part6_stress()

    outright = float(_month_row(p6, regime="Positive stock-bond corr")["trend_win_rate_vs_60_40"])
    stress_6040 = _month_row(
        stress,
        regime="Positive stock-bond corr stress",
        condition="positive corr and 60/40_return < 0",
    )
    stress_both = _month_row(
        stress,
        regime="Positive stock-bond corr stress",
        condition="positive corr and equity_return < 0 and bond_return < 0",
    )

    rates = [
        outright,
        float(stress_6040["trend_win_rate_vs_60_40"]),
        float(stress_both["trend_win_rate_vs_60_40"]),
    ]
    actives = [
        float(_month_row(p6, regime="Positive stock-bond corr")["avg_active_return_t_minus_6040"]),
        float(stress_6040["avg_active_return_t_minus_6040"]),
        float(stress_both["avg_active_return_t_minus_6040"]),
    ]
    labels = ["All pos-corr\nmonths", "+ 60/40 down", "+ both sleeves\ndown"]

    fig, ax = plt.subplots(figsize=(6.8, 2.45))
    x = np.arange(len(labels))
    ax.bar(x, rates, width=0.58, color=STRESS_ESCALATION, edgecolor="white", linewidth=0.6)
    ax.axhline(outright, color=REFERENCE_BAR, linestyle="--", linewidth=1.0,
               label=f"Pos-corr baseline ({outright:.1%})")
    ax.axhline(0.5, color="#CBD5E1", linestyle=":", linewidth=0.9, alpha=0.9)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 1.02)
    ax.set_ylabel("Trend win rate vs 60/40")
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax.set_title("Positive stock-bond correlation: stress overlap (monthly)", fontsize=9.5)
    for i, (xi, rate, active) in enumerate(zip(x, rates, actives)):
        extra = f"\n({active:+.1%})" if i > 0 else ""
        _annotate_rate(ax, xi, rate, extra=extra)
        if i > 0:
            prev = rates[i - 1]
            _annotate_jump(ax, x[i - 1], xi, prev, rate, f"+{(rate - prev) * 100:.0f}pp")
    ax.legend(loc="upper left", fontsize=7.5)
    _style_axes(ax, "y")
    fig.subplots_adjust(top=0.84, bottom=0.18, left=0.11, right=0.98)
    _save(fig, "slide3_part6_poscorr_stress.png")


def main() -> None:
    print("Writing to", SLIDES_DIR)
    slide1_drawdown_episodes_timeline()
    slide1_annual_returns_stacked()
    slide1_core_metrics_table()
    slide2_deepest13_drawdown_bars()
    slide3_part5_sleeve_win_rates()
    slide3_part6_poscorr_stress()
    print("Done.")


if __name__ == "__main__":
    main()
