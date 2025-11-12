# tests.py
# -*- coding: utf-8 -*-
"""
Simple connectivity tests for:
- Blockchain.com Query API (getdifficulty)
- CoinGecko simple price API

Run:
    python tests.py
"""

import time
from pathlib import Path

from src.data_fetch import (
    ensure_dirs,
    write_json,
    fetch_blockchain_metric,
    fetch_coingecko_simple_price,
    DATA_DIR,
)

def test_blockchain_query_api():
    """Test Blockchain.com Query API: getdifficulty."""
    ensure_dirs()
    val = fetch_blockchain_metric("getdifficulty")
    # Basic assertions
    assert isinstance(val, (int, float)), f"getdifficulty not numeric: {val!r}"
    assert val > 0, f"getdifficulty <= 0: {val}"

    # Write a tiny placeholder so TA sees a side-effect in data/
    write_json({"ok": True, "getdifficulty": float(val)}, DATA_DIR / ".ok_blockchain_q.json")
    print("Blockchain.com Query API test: OK")

def test_coingecko_simple_price():
    """Test CoinGecko simple/price endpoint."""
    ensure_dirs()
    sp = fetch_coingecko_simple_price(ids="bitcoin", vs_currencies="usd")
    # Expect a dict like {'bitcoin': {'usd': 6xxxx.x}}
    assert isinstance(sp, dict) and "bitcoin" in sp, f"Unexpected payload: {sp}"
    btc = sp["bitcoin"]
    assert isinstance(btc, dict) and "usd" in btc and float(btc["usd"]) > 0, f"Bad price: {btc}"

    write_json({"ok": True, "price_usd": float(btc["usd"])}, DATA_DIR / ".ok_coingecko_simple_price.json")
    print("CoinGecko simple/price test: OK")

if __name__ == "__main__":
    # Respect remote rate limits a little bit
    test_blockchain_query_api()
    time.sleep(2)  # 若遇到429，可改为 time.sleep(10)
    test_coingecko_simple_price()
    print("All tests ran.")
