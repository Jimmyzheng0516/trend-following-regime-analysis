import numpy as np
import pandas as pd


TRADING_DAYS = 252


def drawdown(return_series):
    returns = return_series.dropna()
    wealth = (1 + returns).cumprod()
    return wealth / wealth.cummax() - 1


def monthly_returns(return_series):
    monthly = (1 + return_series.dropna()).resample("ME").prod() - 1
    heatmap = monthly.to_frame("return")
    heatmap["Year"] = heatmap.index.year
    heatmap["Month"] = heatmap.index.strftime("%b")
    month_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    return heatmap.pivot(index="Year", columns="Month", values="return").reindex(columns=month_order)


def summary_stats(name, return_series):
    returns = return_series.dropna()
    if returns.empty:
        return {"Strategy": name}

    wealth = (1 + returns).cumprod()
    total_return = wealth.iloc[-1] - 1
    years = len(returns) / TRADING_DAYS
    annual_return = wealth.iloc[-1] ** (1 / years) - 1 if years > 0 else np.nan
    annual_vol = returns.std() * np.sqrt(TRADING_DAYS)
    sharpe = annual_return / annual_vol if annual_vol else np.nan
    max_dd = drawdown(returns).min()

    return {
        "Strategy": name,
        "Start": returns.index.min().date(),
        "End": returns.index.max().date(),
        "Total Return": total_return,
        "Ann. Return": annual_return,
        "Ann. Vol": annual_vol,
        "Sharpe": sharpe,
        "Max Drawdown": max_dd,
    }


def summary_frame(returns, columns):
    return pd.DataFrame([summary_stats(col, returns[col]) for col in columns])

