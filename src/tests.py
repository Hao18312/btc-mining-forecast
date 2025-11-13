import time
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
    assert isinstance(val, (int, float)), f"getdifficulty not numeric: {val!r}"
    assert val > 0, f"getdifficulty <= 0: {val}"

    out = DATA_DIR / ".sample_blockchain_q_ok.json"
    write_json({"ok": True, "difficulty": float(val)}, out)
    print(f"Blockchain.com Query API test: OK -> {out.name}")

def test_coingecko_simple_price():
    """Test CoinGecko simple/price endpoint."""
    ensure_dirs()
    sp = fetch_coingecko_simple_price(ids="bitcoin", vs_currencies="usd")
    assert isinstance(sp, dict) and "bitcoin" in sp, f"Unexpected payload: {sp}"
    btc = sp["bitcoin"]
    assert isinstance(btc, dict) and "usd" in btc and float(btc["usd"]) > 0, f"Bad price: {btc}"

    out = DATA_DIR / ".sample_coingecko_price_ok.json"
    write_json({"ok": True, "usd_price": float(btc["usd"])}, out)
    print(f"CoinGecko simple/price test: OK -> {out.name}")

if __name__ == "__main__":
    test_blockchain_query_api()
    time.sleep(2)
    test_coingecko_simple_price()
    print("All tests ran successfully.")
