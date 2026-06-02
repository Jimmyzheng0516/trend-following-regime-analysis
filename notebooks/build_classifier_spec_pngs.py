"""Render classifier formulas + decision table — reference layout, white background."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "Notebooks" / "output" / "regime_classifier_slides"
OUT.mkdir(parents=True, exist_ok=True)

BG = "#FFFFFF"
TITLE = "#0F172A"
BODY = "#334155"
ACCENT = "#0891B2"  # cyan section headers (readable on white)
HEADER_FILL = "#E2E8F0"
ROW_FILL = "#F1F5F9"
ROW_ALT = "#FFFFFF"
GRID = "#CBD5E1"

DPI = 160

TABLE_ROWS = [
    ("$u^{(2)}$", "$u^{(10)}$", "$u^{(S)}$", "Regime"),
    ("$-1$", "$-1$", "$+1$", "Bull Steepener"),
    ("$-1$", "$-1$", "$-1$", "Bull Flattener"),
    ("$+1$", "$+1$", "$+1$", "Bear Steepener"),
    ("$+1$", "$+1$", "$-1$", "Bear Flattener"),
    ("$-1$", "$+1$", "$+1$ (forced)", "Steepener Twist"),
    ("$+1$", "$-1$", "$-1$ (forced)", "Flattener Twist"),
    ("$0$", "—", "—", "Unclassified"),
]

REGIME_COLORS = {
    "Bull Steepener": "#2E7D32",
    "Bull Flattener": "#81C784",
    "Bear Steepener": "#C62828",
    "Bear Flattener": "#EF9A9A",
    "Steepener Twist": "#1565C0",
    "Flattener Twist": "#64B5F6",
    "Unclassified": "#9E9E9E",
}

TABLE_FONT = 12
TABLE_HEADER_FONT = 13


def _save(fig: plt.Figure, name: str) -> None:
    path = OUT / name
    fig.savefig(path, dpi=DPI, facecolor=BG, edgecolor="none", bbox_inches="tight", pad_inches=0.12)
    plt.close(fig)
    print("Wrote", path)


def render_formulas() -> None:
    """Left-panel layout from reference: single-column vertical spec."""
    fig = plt.figure(figsize=(7.2, 4.6), facecolor=BG)
    ax = fig.add_axes([0.06, 0.04, 0.90, 0.92])
    ax.set_facecolor(BG)
    ax.axis("off")

    ax.text(
        0.0, 1.0,
        "Yield-curve regime classifier — specification",
        fontsize=13.5, color=TITLE, fontweight="bold", va="top", transform=ax.transAxes,
    )

    lines = [
        (0.90, r"Inputs: $y^{(2)}_t$, $y^{(10)}_t$ (FRED DGS2, DGS10);  spread  $S_t = y^{(10)}_t - y^{(2)}_t$", 11, BODY),
        (0.78, r"Trend differential ($i \in \{2,\,10\}$):", 10.5, ACCENT),
        (0.70, r"$d^{(i)}_t = \mathrm{SMA}_{21}(y^{(i)}_t) - \mathrm{SMA}_{200}(y^{(i)}_t)$", 11.5, BODY),
        (0.60, r"$d^{(S)}_t = d^{(10)}_t - d^{(2)}_t$  (spread trend by linearity)", 11, BODY),
        (0.48, r"Direction flags (dead-zone $\tau$):", 10.5, ACCENT),
        (0.38, r"$u^{(i)}_t = +1$ if $d^{(i)}_t > \tau^{(i)}$;  $-1$ if $d^{(i)}_t < -\tau^{(i)}$;  $0$ if $|d^{(i)}_t| \leq \tau^{(i)}$", 11, BODY),
        (0.28, r"Defaults:  $\tau^{(2)} = \tau^{(10)} = 10$ bp on yields;  $\tau^{(S)} = 5$ bp on spread", 10.5, BODY),
        (0.16, r"Persistence filter:", 10.5, ACCENT),
        (0.06, r"Commit filtered label only after $k = 5$ consecutive trading days of the same raw label", 11, BODY),
    ]

    for y, txt, size, color in lines:
        ax.text(0.0, y, txt, fontsize=size, color=color, va="top", transform=ax.transAxes)

    _save(fig, "slide1_classifier_formulas.png")


def render_decision_table() -> None:
    """Right-panel layout from reference: titled table, larger cell text."""
    nrows = len(TABLE_ROWS)
    fig = plt.figure(figsize=(7.0, 4.6), facecolor=BG)
    ax = fig.add_axes([0.04, 0.02, 0.92, 0.94])
    ax.set_facecolor(BG)
    ax.axis("off")

    ax.text(
        0.5, 0.98,
        "Decision table (raw label, before persistence)",
        fontsize=13, color=TITLE, fontweight="bold", ha="center", va="top",
        transform=ax.transAxes,
    )

    col_widths = [0.14, 0.14, 0.20, 0.52]
    table = ax.table(
        cellText=[list(r) for r in TABLE_ROWS],
        colLabels=None,
        cellLoc="center",
        loc="center",
        bbox=[0, 0.02, 1, 0.86],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(TABLE_FONT)

    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor(GRID)
        cell.set_linewidth(0.9)
        if row == 0:
            cell.set_facecolor(HEADER_FILL)
            cell.get_text().set_color(TITLE)
            cell.get_text().set_fontweight("bold")
            cell.get_text().set_fontsize(TABLE_HEADER_FONT)
        else:
            regime = TABLE_ROWS[row][3]
            cell.set_facecolor(ROW_FILL if row % 2 else ROW_ALT)
            if col == 3 and regime in REGIME_COLORS:
                cell.get_text().set_color(REGIME_COLORS[regime])
                cell.get_text().set_fontweight("bold")
                cell.get_text().set_fontsize(TABLE_FONT + 0.5)
            else:
                cell.get_text().set_color(BODY)
        cell.PAD = 0.10

    for j, w in enumerate(col_widths):
        for row in range(nrows):
            table[(row, j)].set_width(w)

    _save(fig, "slide1_classifier_decision_table.png")


def main() -> None:
    render_formulas()
    render_decision_table()


if __name__ == "__main__":
    main()
