# src/main.py
# -*- coding: utf-8 -*-
"""
Mini analysis demo:
- Load CoinMetrics CSV from data/btc.csv
- Auto-detect column names (difficulty/hashrate/price/fees)
- Plot difficulty (if available)
- Compute expected miner revenue (USD/day) for an example miner hashrate
Outputs -> results/ directory
"""

import os
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

CSV_PATH = DATA_DIR / "btc.csv"  # 你的 CoinMetrics 文件名
MINER_HASHRATE_TH = 100          # 示例矿工算力（TH/s），可自行修改
BLOCKS_PER_DAY = 144
# 记得按历史时间段改补贴（这里只做示例；真实项目可按日期自动判断）
BLOCK_SUBSIDY_BTC = 3.125        # 比特币当前补贴（2024/04 之后）

def pick_col(cols, candidates):
    """从列名列表中选出第一个存在的候选名；找不到返回 None。"""
    low = {c.lower(): c for c in cols}
    for name in candidates:
        if name.lower() in low:
            return low[name.lower()]
    return None

def main():
    if not CSV_PATH.exists():
        print(f"CSV not found: {CSV_PATH}")
        return

    df = pd.read_csv(CSV_PATH, low_memory=False)
    print(f"Loaded CSV: shape={df.shape}")
    # 看看有哪些列，方便你核对
    # print(sorted(df.columns.tolist()))

    # ---- 解析时间索引 ----
    time_col = pick_col(df.columns, ["time", "Date", "date"])
    if time_col is None:
        print("No time column found; trying to continue without index.")
    else:
        df[time_col] = pd.to_datetime(df[time_col], errors="coerce", utc=True)
        df = df.sort_values(time_col).reset_index(drop=True).set_index(time_col)

    # ---- 自动匹配关键列 ----
    col_difficulty = pick_col(df.columns, ["DiffMean", "DiffLast", "Difficulty"])
    col_hashrate   = pick_col(df.columns, ["HashRate", "HashRateMean", "HashRate7d", "HashRate30d"])
    col_price_usd  = pick_col(df.columns, ["PriceUSD", "Price(USD)", "price_usd", "PriceUsd"])
    col_fee_usd    = pick_col(df.columns, ["FeeTotUSD", "FeesUSD", "FeeUSD"])
    col_fee_btc    = pick_col(df.columns, ["FeeTotNtv", "FeesNtv", "FeeTotBTC", "FeesBTC"])

    # ---- 画难度曲线（若有）----
    if col_difficulty is not None:
        plt.figure()
        df[col_difficulty].astype(float).plot(title=f"Bitcoin Difficulty ({col_difficulty})")
        plt.tight_layout()
        out_png = RESULTS_DIR / "difficulty.png"
        plt.savefig(out_png, dpi=140)
        plt.close()
        print(f"Difficulty plot saved -> {out_png}")
    else:
        print("No difficulty column (DiffMean/DiffLast/Difficulty) found — skip difficulty plot.")

    # ---- 计算示例矿工收益（USD/day）----
    # 需要：网络算力、价格、美金手续费或比特币手续费（二选一）
    missing_reqs = []
    if col_hashrate is None:  missing_reqs.append("HashRate")
    if col_price_usd is None: missing_reqs.append("PriceUSD")
    if (col_fee_usd is None) and (col_fee_btc is None):
        missing_reqs.append("Fees (FeeTotUSD or FeeTotNtv)")

    if missing_reqs:
        print("Skip revenue calculation — missing:", ", ".join(missing_reqs))
        return

    # 将手续费换算成“每区块的 BTC 手续费”
    if col_fee_btc is not None:
        fees_per_block_btc = (df[col_fee_btc].astype(float) / BLOCKS_PER_DAY)
    else:
        # 用 USD 手续费 / 当日均价 转成 BTC
        price = df[col_price_usd].astype(float).replace(0, np.nan)
        fees_per_block_btc = (df[col_fee_usd].astype(float) / price) / BLOCKS_PER_DAY

    # 估算网络算力（单位假定：H/s）。CoinMetrics 的 HashRate 常为 H/s。
    net_hash = df[col_hashrate].astype(float)

    # 矿工算力（H/s）
    miner_hash_hs = MINER_HASHRATE_TH * 1e12

    # 预期 BTC/天 = (miner_hr / net_hr) * blocks_per_day * (block_subsidy + avg_fees_per_block_btc)
    exp_btc_day = (miner_hash_hs / net_hash) * BLOCKS_PER_DAY * (BLOCK_SUBSIDY_BTC + fees_per_block_btc)

    # 转 USD
    price_usd = df[col_price_usd].astype(float)
    exp_usd_day = exp_btc_day * price_usd

    out = pd.DataFrame({
        "price_usd": price_usd,
        "net_hashrate_Hs": net_hash,
        "fees_per_block_btc": fees_per_block_btc,
        "exp_btc_day": exp_btc_day,
        "exp_usd_day": exp_usd_day,
    })
    # 丢掉不合法/inf
    out = out.replace([np.inf, -np.inf], np.nan).dropna(how="any")

    # 导出 CSV 与图
    out_csv = RESULTS_DIR / "revenue_estimate.csv"
    out.to_csv(out_csv, index=True)
    print(f"Revenue table saved -> {out_csv}")

    plt.figure()
    out["exp_usd_day"].tail(365).plot(title=f"Expected USD/day for {MINER_HASHRATE_TH} TH/s (last 365 days)")
    plt.tight_layout()
    out_png2 = RESULTS_DIR / "revenue_usd_per_day.png"
    plt.savefig(out_png2, dpi=140)
    plt.close()
    print(f"Revenue plot saved -> {out_png2}")

    # 给出最近一天的示例输出
    last = out.iloc[-1]
    print(f"Latest (example miner {MINER_HASHRATE_TH} TH/s): USD/day ≈ {last['exp_usd_day']:.2f}")

if __name__ == "__main__":
    main()
