# vnstock_puller
Personal Vietnam stock tracker built with Python. Fetches market data via vnstock, stores history in SQLite, computes indicators (returns, volatility, MA, RSI) with pandas/NumPy, and visualizes them in a Streamlit dashboard.
# VN Stock Tracker

A personal Python project for tracking and analyzing the Vietnam stock market.

> Status: under development (v1.0 in progress). This is a learning project.

## Planned features (v1.0)
- Fetch historical price data with `vnstock` and store it in SQLite
- Analytics: daily returns, volatility, moving averages (MA), RSI using pandas and NumPy
- Charts and a simple Streamlit dashboard
- Small portfolio tracker

## Tech stack
Python, pandas, NumPy, SQLite, matplotlib, Streamlit

## Notes
- Market data comes from third-party sources through `vnstock`, so it may be delayed
  or inaccurate. Verify against official sources. This project is not investment advice.
- Not affiliated with vnstock or any data source.
