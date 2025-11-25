# Bitcoin Mining Pool Concentration and Price Forecast
This project analyzes the decentralization of Bitcoin mining over time, using Herfindahl-Hirschman Index (HHI) and daily mining pool shares. It also explores the relationship between mining concentration and BTC/USD price using historical time series data and XGBoost forecasting.

The goal is to measure how centralized or decentralized mining has become over time and to forecast future trends in HHI and Bitcoin price.

---

# Data sources

| Data source # | Name / short description                                                                                                    | Source URL | Type | List of fields (examples) | Format |           Accessed via Python?           | Estimated data size |
|:--:|:----------------------------------------------------------------------------------------------------------------------------|:--|:--|:--|:--:|:----------------------------------------:|:--:|
| 1 | CoinMetrics community network data (Bitcoin) — daily chain-level indicators such as difficulty, hashrate, fees, and prices. | [https://coinmetrics.io/community-network-data/](https://coinmetrics.io/community-network-data/) | File (CSV) | `time`, `DiffMean`, `HashRate`, `PriceUSD`, `FeeTotUSD`, `RevHashUSD` | CSV | No — I download it directly from website | ≥3,000 daily points |
| 2 | lockchain.com Explorer API — provides network charts and block-level stats (difficulty, hashrate, fees).                    | [https://www.blockchain.com/explorer/api](https://www.blockchain.com/explorer/api) | API (REST) | `difficulty`, `hash_rate`, `tx_count`, `fees` | JSON |       Yes — fetched via `requests`       | ≥1,000 time points |
| 3 | CoinGecko API — historical BTC price data in USD and market metrics.                                                        | [https://www.coingecko.com/en/api](https://www.coingecko.com/en/api) | API (REST) | `prices[timestamp, price_usd]`, `market_caps`, `total_volumes` | JSON |       Yes — fetched via `requests`       | ≥3,650 daily points |


---
# Results 
This project generates the following analyses and visualizations in the results/ folder:

1. pool_distribution.png: Daily stacked bar chart of blocks mined by each pool.

2. hhi_over_time.png: HHI trend chart measuring mining concentration.

3. market_price.png: Daily BTC/USD price chart.

4. hhi_forecast.png: Forecasted HHI values using XGBoost.

5. price_forecast.png: Forecasted Bitcoin price using XGBoost.

# Installation
No API keys are required.

Python dependencies

1. pandas — data manipulation

2. matplotlib — plotting

3. requests — optional for API access

4. xgboost — machine learning regression model

# Running analysis
From the src/ directory, run:

python main.py

This will:
Load JSON data from data/pools-timeseries.json.

Generate mining pool share breakdown and compute daily HHI.

Train XGBoost models to forecast HHI and BTC price until 2026.

Save all results and plots to the results/ folder.