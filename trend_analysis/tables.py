import pandas as pd

from .config import DISPLAY_NAME_MAP


PERCENT_HINTS = (
    "return",
    "rate",
    "vol",
    "drawdown",
    "win_rate",
    "hit_rate",
    "share",
    "corr",
    "active",
    "weight",
)


def presentation_table(df):
    out = df.copy()
    out = out.rename(columns=DISPLAY_NAME_MAP)
    out.columns = [DISPLAY_NAME_MAP.get(str(col), str(col).replace("_", " ").title()) for col in out.columns]
    return out


def _formatters(df):
    formatters = {}
    for col in df.columns:
        lower = str(col).lower()
        if pd.api.types.is_float_dtype(df[col]):
            if any(hint in lower for hint in PERCENT_HINTS):
                formatters[col] = "{:.1%}"
            else:
                formatters[col] = "{:.2f}"
    return formatters


def style_summary_table(df):
    styler = df.style.format(_formatters(df), na_rep="")
    return (
        styler.set_properties(**{"text-align": "center"})
        .set_table_styles(
            [
                {"selector": "th", "props": [("text-align", "center"), ("font-weight", "600")]},
                {"selector": "caption", "props": [("caption-side", "top"), ("font-weight", "600")]},
            ]
        )
        .hide(axis="index")
    )


def style_return_heatmap(df):
    return (
        df.style.format("{:.1%}", na_rep="")
        .background_gradient(cmap="RdYlGn", axis=None, vmin=-0.08, vmax=0.08)
        .set_properties(**{"text-align": "center"})
        .set_table_styles([{"selector": "th", "props": [("text-align", "center"), ("font-weight", "600")]}])
    )

