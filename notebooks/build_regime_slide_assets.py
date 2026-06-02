"""Generate PPT-sized PNGs for regime_classifier_intro (separate slides folder)."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "data"
REGIME_DATA = REPO / "Notebooks" / "output" / "regime"
SLIDES_DIR = REPO / "Notebooks" / "output" / "regime_classifier_slides"
SLIDES_DIR.mkdir(parents=True, exist_ok=True)

# Commodity-trend / 60-40 joint analysis window (see trend_vs_60_40_regime_analysis.ipynb)
TREND_PANEL_START = "2001-05-04"

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

REGIME_ORDER = [
    "Bull Steepener", "Bull Flattener", "Bear Steepener", "Bear Flattener",
    "Steepener Twist", "Flattener Twist", "Unclassified",
]
REGIME_COLORS = {
    "Bull Steepener": "#2E7D32", "Bull Flattener": "#81C784",
    "Bear Steepener": "#C62828", "Bear Flattener": "#EF9A9A",
    "Steepener Twist": "#1565C0", "Flattener Twist": "#64B5F6",
    "Unclassified": "#BDBDBD",
}
NAMED = [r for r in REGIME_ORDER if r != "Unclassified"]
Y2_COLOR = "#1565C0"   # blue
Y10_COLOR = "#E65100"  # amber


def load_panel() -> pd.DataFrame:
    return pd.read_excel(
        DATA / "interest_rate_regimes.xlsx",
        sheet_name="Regime Classification",
        parse_dates=["date"],
    ).set_index("date")


def _save(fig, name: str) -> None:
    path = SLIDES_DIR / name
    fig.savefig(path, dpi=DPI, bbox_inches="tight", pad_inches=0.2)
    plt.close(fig)
    print(" ", path.name)


def _episode_label(ax, ts: str, text: str, y_frac: float) -> None:
    """Place episode callout on yield panel; stagger y_frac to avoid legend overlap."""
    ax.axvline(pd.Timestamp(ts), color="#9E9E9E", ls=":", lw=0.75, zorder=0)
    ax.text(
        pd.Timestamp(ts), y_frac, text,
        transform=ax.get_xaxis_transform(),
        fontsize=7.5, ha="center", va="top", color="#212121",
        bbox=dict(boxstyle="round,pad=0.25", facecolor="white",
                  edgecolor="#BDBDBD", alpha=0.95),
        clip_on=False,
        zorder=5,
    )


def slide1_timeseries(df: pd.DataFrame) -> None:
    plot = df.loc["2019":].dropna(subset=["regime_filtered"])
    fig = plt.figure(figsize=(6.8, 4.35))
    gs = fig.add_gridspec(3, 1, height_ratios=[1.5, 0.48, 0.38], hspace=0.18)
    ax0 = fig.add_subplot(gs[0])
    ax1 = fig.add_subplot(gs[1], sharex=ax0)
    ax_leg = fig.add_subplot(gs[2])
    ax_leg.axis("off")

    ax0.plot(plot.index, plot["y2"], color=Y2_COLOR, lw=1.2, label="2Y")
    ax0.plot(plot.index, plot["y10"], color=Y10_COLOR, lw=1.2, label="10Y")
    ax0.set_ylabel("Yield (%)")
    ax0.legend(loc="lower right", frameon=True, fancybox=True, framealpha=0.95,
               edgecolor="#E0E0E0", ncol=1, fontsize=8)
    ax0.set_title("Yields and committed regimes (2019–present)", pad=8)
    ax0.margins(x=0.01)

    runs = (plot["regime_filtered"] != plot["regime_filtered"].shift()).cumsum()
    for _, block in plot.groupby(runs):
        reg = block["regime_filtered"].iloc[0]
        ax1.axvspan(block.index[0], block.index[-1],
                    color=REGIME_COLORS.get(reg, "#CCC"), alpha=0.95, lw=0)
    ax1.set_yticks([])
    ax1.set_ylim(0, 1)

    episodes = [
        ("2019-09", "Pre-COVID chop", 0.98),
        ("2020-03", "COVID easing", 0.90),
        ("2022-06", "2022 hikes", 0.98),
        ("2023-10", "Higher for longer", 0.90),
        ("2024-09", "Soft landing", 0.98),
        ("2026-04", "Bear flatter now", 0.90),
    ]
    for ts, lab, yf in episodes:
        _episode_label(ax0, ts, lab, yf)

    handles = [mpatches.Patch(color=REGIME_COLORS[r], label=r)
               for r in REGIME_ORDER if r in plot["regime_filtered"].unique()]
    ax_leg.legend(handles=handles, loc="center", ncol=4, frameon=False, fontsize=7.5)
    plt.setp(ax0.get_xticklabels(), visible=False)
    fig.subplots_adjust(top=0.94, bottom=0.06)
    _save(fig, "slide1_timeseries_regimes.png")


def slide1_named_mix_bar(df: pd.DataFrame) -> None:
    plot = df.loc[TREND_PANEL_START:].dropna(subset=["regime_filtered"])
    freq = plot["regime_filtered"].value_counts(normalize=True).reindex(REGIME_ORDER).fillna(0)
    freq = freq[freq > 0].sort_values()

    fig, ax = plt.subplots(figsize=(6.8, 3.0))
    labels = list(freq.index)
    vals = freq.values * 100
    ypos = np.arange(len(labels))
    ax.barh(ypos, vals, color=[REGIME_COLORS[r] for r in labels], height=0.58)
    ax.set_yticks(ypos)
    ax.set_yticklabels(labels, fontsize=8.5)
    ax.set_xlabel(f"% of all days ({TREND_PANEL_START}+, trend/60-40 panel)")
    ax.set_xlim(0, max(vals) * 1.18 + 4)
    for y, v in zip(ypos, vals):
        ax.text(v + 0.8, y, f"{v:.0f}%", va="center", fontsize=8, color="#424242")
    fig.subplots_adjust(left=0.34, right=0.96, top=0.96, bottom=0.18)
    _save(fig, "slide1_named_regime_mix.png")


def slide2_robustness() -> None:
    robust = pd.read_csv(REGIME_DATA / "regime_robustness_grid.csv")
    fig, axes = plt.subplots(1, 2, figsize=(6.8, 3.5))

    k = robust[robust["scenario"] == "persist_k"]
    axes[0].plot(k["param"], k["pct_unclassified_filtered"] * 100, "o-",
                 color="#1565C0", lw=2, markersize=7)
    axes[0].set_ylim(50, 54)
    axes[0].set_xlabel("k (consecutive days to commit label)")
    axes[0].set_ylabel("% Unclassified")
    axes[0].set_title(
        "Persistence k\n(days same raw label before filter commits)",
        pad=8, fontsize=9,
    )
    axes[0].set_xticks(k["param"])
    axes[0].text(0.04, 0.06, "Median block 22d → 36d", transform=axes[0].transAxes,
                 fontsize=7.5, color="#424242")

    tau = robust[robust["scenario"] == "tau_level"].copy()
    tau["param"] = pd.to_numeric(tau["param"], errors="coerce")
    xlabels = [f"{p * 100:.0f}" for p in tau["param"]]
    axes[1].bar(xlabels, tau["pct_unclassified_filtered"] * 100,
                color="#C62828", width=0.5, alpha=0.9)
    axes[1].axhline(51.5, color="#424242", ls=":", lw=1, label="baseline 10 bp")
    axes[1].set_xlabel("τ_level (bp on 2Y/10Y trend diff.)")
    axes[1].set_ylabel("% Unclassified")
    axes[1].set_title(
        "τ_level dead-zone\n(|d| ≤ τ → yield leg unclassified)",
        pad=8, fontsize=9,
    )
    axes[1].legend(loc="upper left", frameon=False, fontsize=7)

    fig.subplots_adjust(wspace=0.40, top=0.88, bottom=0.14, left=0.10, right=0.98)
    _save(fig, "slide2_robustness_k_tau.png")


def slide3_historical(df: pd.DataFrame) -> None:
    sub = df.loc["2008":].dropna(subset=["regime_filtered"])
    rows = []
    for yr, g in sub.groupby(sub.index.year):
        named = g.loc[g["regime_filtered"] != "Unclassified", "regime_filtered"]
        if len(named) == 0:
            continue
        top = named.value_counts().idxmax()
        share = named.value_counts(normalize=True).max()
        rows.append((yr, top, share, len(named)))
    ann = pd.DataFrame(rows, columns=["year", "regime", "share", "named_days"])

    fig = plt.figure(figsize=(6.8, 4.2))
    gs = fig.add_gridspec(2, 1, height_ratios=[1.0, 0.38], hspace=0.35)
    ax = fig.add_subplot(gs[0])
    ax_leg = fig.add_subplot(gs[1])
    ax_leg.axis("off")

    x = np.arange(len(ann))
    colors = [REGIME_COLORS.get(r, "#BDBDBD") for r in ann["regime"]]
    ax.bar(x, ann["share"] * 100, color=colors, width=0.72, edgecolor="white")
    ax.set_xticks(x)
    ax.set_xticklabels(ann["year"].astype(str), rotation=45, ha="right", fontsize=7.5)
    ax.set_ylabel("% of year's named-regime days")
    ax.set_title("Dominant named regime by year (2008+)", pad=8)
    ax.set_ylim(0, 105)
    ax.margins(y=0.08)

    handles = [mpatches.Patch(color=REGIME_COLORS[r], label=r) for r in NAMED]
    ax_leg.legend(handles=handles, loc="center", ncol=3, frameon=False, fontsize=7.5)
    fig.subplots_adjust(top=0.90, bottom=0.08, left=0.10, right=0.98)
    _save(fig, "slide3_dominant_regime_by_year.png")


def main():
    df = load_panel()
    print("Writing to", SLIDES_DIR)
    slide1_timeseries(df)
    slide1_named_mix_bar(df)
    slide2_robustness()
    slide3_historical(df)
    print("Done.")


if __name__ == "__main__":
    main()
