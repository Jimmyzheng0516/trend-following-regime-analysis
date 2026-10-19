# trend-following-regime-analysis

My part of the University of Chicago MSFM project lab with **Low Tide Capital Management**, spring 2026 (team: Daniil Garbuzov, Lucie Martin, Scarlett He, Andrew Yang and me). The team repository is private to the group; this repository contains the notebooks and the Python package I wrote or maintained, with notebook outputs cleared because the inputs (Bloomberg price data) are licensed.

## Question

Does a simple trend-following commodity model add value next to a 60/40 stock/bond portfolio, and does the answer depend on the interest-rate regime?

## What is here

| Path | Content |
|---|---|
| `trend_analysis/` | Package used by the analysis notebooks: data loading (`data.py`), performance metrics (`metrics.py`), tables (`tables.py`), plotting (`plots.py`, `original_style.py`), settings (`config.py`) |
| `notebooks/data_summary.ipynb` | Exploratory analysis of the cleaned trend-asset price file |
| `notebooks/60_40_construction.ipynb` | Daily-rebalanced 60/40 benchmark on the model's calendar |
| `notebooks/trend_model_method1_backtest_updated.ipynb` | Commodity trend backtest (moving-average crossover signals, volatility scaling) |
| `notebooks/build_interest_rate_regimes.ipynb` | Six-state yield-curve regime classifier from 2-year and 10-year Treasury yields (level and slope moving-average crossovers), with robustness checks on the smoothing windows |
| `notebooks/trend_vs_60_40_analysis.ipynb` | Six-part comparison: performance, correlation, mean-variance sleeves, drawdown episodes, conditional outperformance, stock-bond correlation horizons |
| `notebooks/trend_vs_60_40_regime_analysis.ipynb` | Performance conditional on regime, regime-change event studies, average weights by regime |
| `notebooks/trend_vs_60_40_presentation.ipynb`, `notebooks/build_*.py`, `fill_*.py`, `export_*.py` | Slide-ready charts and the scripts that assembled my section of the final presentation |
| `figures/regime/` | Regime figures from the final presentation |

## Running

Python 3.10+, `numpy`, `pandas`, `matplotlib`, `openpyxl`, Jupyter. Place the input files in `data/` (see `trend_analysis/config.py` for expected names); the notebooks run in the order listed above.

Files are committed on their last-modified date so the history reflects when the work was done.
