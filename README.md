# Bitcoin Mining Difficulty and Revenue Forecast
This project analyzes and forecasts Bitcoin mining difficulty and miner revenue using public blockchain APIs and network data.  
The goal is to predict how mining difficulty and network hashrate evolve over time, and to estimate expected miner income (in USD) under different BTC price and electricity cost scenarios.  
The project combines time-series forecasting (ARIMA / Prophet) and machine learning models (LightGBM / XGBoost).

---

# Data sources

| Data source # | Name / short description                                                                                                    | Source URL | Type | List of fields (examples) | Format |           Accessed via Python?           | Estimated data size |
|:--:|:----------------------------------------------------------------------------------------------------------------------------|:--|:--|:--|:--:|:----------------------------------------:|:--:|
| 1 | CoinMetrics community network data (Bitcoin) — daily chain-level indicators such as difficulty, hashrate, fees, and prices. | [https://coinmetrics.io/community-network-data/](https://coinmetrics.io/community-network-data/) | File (CSV) | `time`, `DiffMean`, `HashRate`, `PriceUSD`, `FeeTotUSD`, `RevHashUSD` | CSV | No — I download it directly from website | ≥3,000 daily points |
| 2 | lockchain.com Explorer API — provides network charts and block-level stats (difficulty, hashrate, fees).                    | [https://www.blockchain.com/explorer/api](https://www.blockchain.com/explorer/api) | API (REST) | `difficulty`, `hash_rate`, `tx_count`, `fees` | JSON |       Yes — fetched via `requests`       | ≥1,000 time points |
| 3 | CoinGecko API — historical BTC price data in USD and market metrics.                                                        | [https://www.coingecko.com/en/api](https://www.coingecko.com/en/api) | API (REST) | `prices[timestamp, price_usd]`, `market_caps`, `total_volumes` | JSON |       Yes — fetched via `requests`       | ≥3,650 daily points |


---
# Results 
The project currently supports:
--Successful connection to Blockchain.com Query API for retrieving real-time blockchain metrics like difficulty and block height.
--Integration with CoinGecko API to obtain live BTC/USD price data.
--Verified sample data written to the data/ folder as proof of successful API connection.
Model-based forecasting and mining revenue analysis are under development.

# Installation
- No API keys are required for light usage of CoinGecko or Blockchain.com APIs.
- Python packages used:
requests — for HTTP requests
pandas — for data handling
matplotlib — for plotting (for future analysis)
python-dotenv — for reading environment variables
prophet — for time-series forecasting (not currently used)

# Running analysis
From `src/` directory run:

`tests.py `

This will:

Fetch real-time difficulty and price from APIs

Save small sample .json files to the data/ directory as a connection test