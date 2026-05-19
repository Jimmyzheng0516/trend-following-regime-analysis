from pathlib import Path


NOTEBOOK_DIR = Path(__file__).resolve().parents[1]
OUTPUT_DIR = NOTEBOOK_DIR / "output"

BENCHMARK_6040 = "60/40"
COMMODITY_TREND = "Commodity-Trend Model"
COMMODITY_TREND_MODEL = COMMODITY_TREND
SLEEVE_9010 = "90/10 Blend"
STATIC_MV = "Static MV"
DYNAMIC_MV = "Dynamic MV"
EQUITY = "Equity"
BONDS = "Bonds"

CORE_STRATEGIES = [BENCHMARK_6040, COMMODITY_TREND]
PORTFOLIO_STRATEGIES = [BENCHMARK_6040, COMMODITY_TREND, SLEEVE_9010, STATIC_MV, DYNAMIC_MV]
STRATEGY_ORDER = PORTFOLIO_STRATEGIES

PRO_PALETTE = {
    BENCHMARK_6040: "#1F4E79",
    COMMODITY_TREND: "#2A9D8F",
    SLEEVE_9010: "#6C757D",
    STATIC_MV: "#B08D57",
    DYNAMIC_MV: "#6A4C93",
    EQUITY: "#8E3B46",
    BONDS: "#4F6D7A",
    "positive": "#2A9D8F",
    "negative": "#8E3B46",
    "neutral": "#6C757D",
    "light": "#D9DEE7",
}

DISPLAY_NAME_MAP = {
    "Method 1 (trend)": COMMODITY_TREND,
    "Method 1": COMMODITY_TREND,
    "60/40 benchmark": BENCHMARK_6040,
    "100% 60/40": BENCHMARK_6040,
    "100% trend": COMMODITY_TREND,
    "100% Trend": COMMODITY_TREND,
    "trend": COMMODITY_TREND,
    "Trend": COMMODITY_TREND,
    "90% 60/40 + 10% trend": SLEEVE_9010,
    "static MV": STATIC_MV,
    "dynamic MV": DYNAMIC_MV,
    "equity": EQUITY,
    "bond": BONDS,
    "bonds": BONDS,
}

RETURN_COLUMN_MAP = {
    "method1_strategy_return": COMMODITY_TREND,
    "benchmark_strategy_return": BENCHMARK_6040,
    "spxt_return": EQUITY,
    "luattruu_return": BONDS,
    "trend_ret": COMMODITY_TREND,
    "bench_ret": BENCHMARK_6040,
    "mix10_ret": SLEEVE_9010,
    "ret_100pct_60_40": BENCHMARK_6040,
    "ret_static_mv": STATIC_MV,
    "ret_dynamic_mv": DYNAMIC_MV,
}


def apply_theme():
    from .plots import apply_theme as _apply_theme

    return _apply_theme()

