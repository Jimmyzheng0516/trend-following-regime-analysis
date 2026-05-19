import re

import pandas as pd

from .config import (
    BENCHMARK_6040,
    BONDS,
    COMMODITY_TREND,
    DISPLAY_NAME_MAP,
    DYNAMIC_MV,
    EQUITY,
    OUTPUT_DIR,
    PORTFOLIO_STRATEGIES,
    RETURN_COLUMN_MAP,
    SLEEVE_9010,
    STATIC_MV,
)


OUTPUT_FILES = [
    "merged_method1_vs_60_40_daily.csv",
    "merged_method1_vs_60_40_summary_compare.csv",
    "part3_sleeve_10_daily.csv",
    "part3_sleeve_10_summary.csv",
    "part3_dynamic_daily.csv",
    "part3_five_strategies_summary.csv",
    "part3_static_mv_weights.csv",
    "part3_dynamic_weights.csv",
    "part4_60_40_drawdown_episodes.csv",
    "part4_quantile_window_returns.csv",
    "part4_dd_depth_buckets.csv",
    "part5_calendar_horizon_outperformance.csv",
    "part5_conditional_outperformance.csv",
    "part6_stock_bond_corr_horizon_summary.csv",
    "part6_positive_corr_conditional_performance.csv",
    "part6_positive_corr_stress_lens.csv",
]


def expected_output_files():
    return [OUTPUT_DIR / file_name for file_name in OUTPUT_FILES]


def _read_output(file_name, **kwargs):
    return pd.read_csv(OUTPUT_DIR / file_name, **kwargs)


def _date_index(df):
    date_col = "Dates" if "Dates" in df.columns else "date" if "date" in df.columns else None
    if date_col is None:
        return df
    out = df.copy()
    out[date_col] = pd.to_datetime(out[date_col])
    return out.set_index(date_col).sort_index()


def _rename_display_value(value):
    if not isinstance(value, str):
        return value
    out = DISPLAY_NAME_MAP.get(value, value)
    out = re.sub(r"\btrend\b", COMMODITY_TREND, out, flags=re.IGNORECASE)
    out = out.replace("100% Commodity-Trend Model", COMMODITY_TREND)
    out = out.replace("90% 60/40 + 10% Commodity-Trend Model", SLEEVE_9010)
    return out


def clean_display_names(df):
    out = df.copy()
    out = out.rename(columns=DISPLAY_NAME_MAP)
    object_cols = out.select_dtypes(include="object").columns
    for col in object_cols:
        out[col] = out[col].map(_rename_display_value)
    return out


def load_strategy_returns():
    core = _date_index(_read_output("merged_method1_vs_60_40_daily.csv"))
    core_returns = core[[c for c in RETURN_COLUMN_MAP if c in core.columns]].rename(columns=RETURN_COLUMN_MAP)

    sleeve = _date_index(_read_output("part3_sleeve_10_daily.csv"))
    sleeve_returns = sleeve[[c for c in ["mix10_ret"] if c in sleeve.columns]].rename(columns=RETURN_COLUMN_MAP)

    mv = _date_index(_read_output("part3_dynamic_daily.csv"))
    mv_returns = mv[[c for c in ["ret_static_mv", "ret_dynamic_mv"] if c in mv.columns]].rename(columns=RETURN_COLUMN_MAP)

    returns = pd.concat([core_returns, sleeve_returns, mv_returns], axis=1)
    returns = returns.loc[:, ~returns.columns.duplicated()]
    ordered = [BENCHMARK_6040, COMMODITY_TREND, SLEEVE_9010, STATIC_MV, DYNAMIC_MV, EQUITY, BONDS]
    return returns[[col for col in ordered if col in returns.columns]].dropna(how="all")


def load_merged_daily():
    return _date_index(_read_output("merged_method1_vs_60_40_daily.csv"))


def prepare_core_and_strategy_returns():
    returns = load_strategy_returns()
    core_returns = returns[[BENCHMARK_6040, COMMODITY_TREND]].dropna()
    strategy_returns = returns[[col for col in PORTFOLIO_STRATEGIES if col in returns.columns]].dropna()
    return returns, core_returns, strategy_returns


def load_summary_table(file_name):
    return clean_display_names(_read_output(file_name))


def load_core_summary():
    return load_summary_table("merged_method1_vs_60_40_summary_compare.csv")


def load_sleeve_summary():
    return load_summary_table("part3_sleeve_10_summary.csv")


def load_five_strategy_summary():
    return load_summary_table("part3_five_strategies_summary.csv")


def load_static_mv_weights():
    return clean_display_names(_read_output("part3_static_mv_weights.csv"))


def load_dynamic_weights():
    return _date_index(_read_output("part3_dynamic_weights.csv"))


def load_drawdown_episodes():
    df = _read_output("part4_60_40_drawdown_episodes.csv", parse_dates=["peak_date", "trough_date", "recovery_date"])
    return clean_display_names(df)


def load_quantile_windows():
    return clean_display_names(_read_output("part4_quantile_window_returns.csv"))


def load_drawdown_buckets():
    return clean_display_names(_read_output("part4_dd_depth_buckets.csv"))


def load_part5_calendar():
    return clean_display_names(_read_output("part5_calendar_horizon_outperformance.csv"))


def load_part5_conditional():
    return clean_display_names(_read_output("part5_conditional_outperformance.csv"))


def load_part6_counts():
    return clean_display_names(_read_output("part6_stock_bond_corr_horizon_summary.csv"))


def load_part6_conditional():
    return clean_display_names(_read_output("part6_positive_corr_conditional_performance.csv"))


def load_part6_stress():
    return clean_display_names(_read_output("part6_positive_corr_stress_lens.csv"))

