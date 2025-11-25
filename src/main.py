from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import xgboost as xgb
from datetime import datetime, timedelta

# Path settings
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
start_date = pd.to_datetime("2023-01-01")

# Reading JSON data
json_path = DATA_DIR / "pools-timeseries.json"
with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)
pools_ts = data["pools-timeseries"]
market_price = data["market-price"]

# Constructing the mining pool DataFrame & HHI
records = []
for date_str, pools in pools_ts.items():
    date = pd.to_datetime(date_str).tz_localize(None)
    for pool_name, blocks in pools.items():
        records.append({"date": date, "pool": pool_name, "blocks": blocks})
pools_df = pd.DataFrame(records)
pools_df = pools_df[pools_df["date"] >= start_date]

# Main mining pools
major_pools = ["Unknown", "AntPool", "ViaBTC", "F2Pool", "Mara Pool", "SBI Crypto"]

pivot = pools_df.pivot_table(
    index="date", columns="pool", values="blocks", fill_value=0
)

# Group other mining pools together as "Others".
other_cols = [c for c in pivot.columns if c not in major_pools]
pivot["Others"] = pivot[other_cols].sum(axis=1)
distribution_df = pivot[major_pools + ["Others"]]

# Calculate HHI
shares = distribution_df.div(distribution_df.sum(axis=1), axis=0)
hhi_series = (shares**2).sum(axis=1)
hhi_daily = hhi_series.resample("D").mean().ffill()

# Constructing a price series
price_df = pd.DataFrame(market_price)
price_df["date"] = pd.to_datetime(price_df["x"], unit="ms").dt.tz_localize(None)
price_df.set_index("date", inplace=True)
price_df = price_df[price_df.index >= start_date]

price_daily = (
    price_df["y"]
    .asfreq("D")
    .interpolate("time")
)

# --------------------------------
# 1. Mining Pool Stacked Bar Chart
fig1, ax1 = plt.subplots(figsize=(16, 8))

colors = [
    "steelblue",  # Unknown
    "orange",  # AntPool
    "green",  # ViaBTC
    "red",  # F2Pool
    "purple",  # Mara Pool
    "brown",  # SBI Crypto
    "pink",  # Others
]

bottom = pd.Series(0, index=distribution_df.index)
for pool, color in zip(distribution_df.columns, colors):
    ax1.bar(
        distribution_df.index,
        distribution_df[pool],
        bottom=bottom,
        label=pool,
        color=color,
        width=1.0,
    )
    bottom += distribution_df[pool]

ax1.set_title(
    f"Mining Pool Blocks Distribution ({start_date.date()} to {distribution_df.index.max().date()})"
)
ax1.set_xlabel("Date")
ax1.set_ylabel("Blocks")
ax1.legend(title="Mining Pools", loc="upper right")

ax1.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
ax1.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
plt.xticks(rotation=45)
fig1.tight_layout()
fig1.savefig(RESULTS_DIR / "pool_distribution.png")

# ------------------
# 2. HHI curve graph
fig2, ax2 = plt.subplots(figsize=(14, 5))
ax2.plot(hhi_series.index, hhi_series.values)
ax2.set_title("Herfindahl-Hirschman Index (HHI) Over Time")
ax2.set_xlabel("Date")
ax2.set_ylabel("HHI")
fig2.tight_layout()
fig2.savefig(RESULTS_DIR / "hhi_over_time.png")


# ---------------------
# 3. Market Price Chart
fig3, ax3 = plt.subplots(figsize=(14, 5))
ax3.plot(price_daily.index, price_daily.values)
ax3.set_title("Market Price Over Time")
ax3.set_xlabel("Date")
ax3.set_ylabel("Price (USD)")
fig3.tight_layout()
fig3.savefig(RESULTS_DIR / "market_price.png")


# =================================================
# XGBoost time series forecasting (for HHI & Price)
def create_features(series: pd.Series) -> pd.DataFrame:
    """Given a daily time series, generate lagged features and date features."""
    df = pd.DataFrame({"target": series})
    df["lag1"] = series.shift(1)
    df["lag7"] = series.shift(7)
    df["lag30"] = series.shift(30)
    df["month"] = series.index.month
    df["dayofyear"] = series.index.dayofyear
    df["dayofweek"] = series.index.dayofweek
    return df


def train_xgb_model(series: pd.Series) -> xgb.Booster:
    """Use XGBoost to fit the given time series."""
    feat_df = create_features(series).dropna()
    X = feat_df[["lag1", "lag7", "lag30", "month", "dayofyear", "dayofweek"]].values
    y = feat_df["target"].values

    dtrain = xgb.DMatrix(X, label=y)

    params = {
        "objective": "reg:squarederror",
        "eta": 0.05,
        "max_depth": 4,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "seed": 42,
    }

    num_boost_round = 300
    model = xgb.train(params, dtrain, num_boost_round=num_boost_round)
    return model


def forecast_with_xgb(series: pd.Series, model: xgb.Booster, end_date: pd.Timestamp) -> pd.Series:
    """
    Use the trained XGBoost model to make recursive predictions up to the end_date.
    Return: The complete sequence including historical data and predictions (with the same index).
    """
    forecast_series = series.copy()
    last_date = forecast_series.index[-1]
    forecast_days = (end_date - last_date).days
    if forecast_days <= 0:
        return forecast_series

    for i in range(forecast_days):
        next_date = last_date + timedelta(days=i + 1)

        lag1 = forecast_series.iloc[-1]
        lag7 = forecast_series.iloc[-7] if len(forecast_series) >= 7 else lag1
        lag30 = forecast_series.iloc[-30] if len(forecast_series) >= 30 else lag1

        month = next_date.month
        dayofyear = next_date.dayofyear
        dayofweek = next_date.dayofweek

        features = np.array([[lag1, lag7, lag30, month, dayofyear, dayofweek]])
        dtest = xgb.DMatrix(features)
        pred = float(model.predict(dtest)[0])

        forecast_series.loc[next_date] = pred

    return forecast_series

forecast_end = pd.to_datetime("2026-12-31")


# ---------------
# 4. HHI forecast
hhi_model = train_xgb_model(hhi_daily)
hhi_full = forecast_with_xgb(hhi_daily, hhi_model, forecast_end)
hhi_forecast_only = hhi_full[hhi_daily.index[-1] + timedelta(days=1):]

fig4, ax4 = plt.subplots(figsize=(14, 6))
ax4.plot(hhi_daily.index, hhi_daily.values, label="Actual HHI")
ax4.plot(
    hhi_forecast_only.index,
    hhi_forecast_only.values,
    linestyle="--",
    label="Forecasted HHI (XGBoost)",
)
ax4.set_title("HHI Forecast using XGBoost until 2026-12-31")
ax4.set_xlabel("Date")
ax4.set_ylabel("HHI")
ax4.legend()
ax4.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
ax4.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
plt.xticks(rotation=45)
fig4.tight_layout()
fig4.savefig(RESULTS_DIR / "hhi_forecast.png")


# -------------------
# 5. Price prediction
price_model = train_xgb_model(price_daily)
price_full = forecast_with_xgb(price_daily, price_model, forecast_end)
price_forecast_only = price_full[price_daily.index[-1] + timedelta(days=1):]

fig5, ax5 = plt.subplots(figsize=(14, 6))
ax5.plot(price_daily.index, price_daily.values, label="Actual Price")
ax5.plot(
    price_forecast_only.index,
    price_forecast_only.values,
    linestyle="--",
    label="Forecasted Price (XGBoost)",
)
ax5.set_title("BTC Price Forecast using XGBoost until 2026-12-31")
ax5.set_xlabel("Date")
ax5.set_ylabel("Price (USD)")
ax5.legend()
ax5.xaxis.set_major_locator(mdates.MonthLocator(interval=6))
ax5.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
plt.xticks(rotation=45)
fig5.tight_layout()
fig5.savefig(RESULTS_DIR / "price_forecast.png")

print("All plots saved to:", RESULTS_DIR)