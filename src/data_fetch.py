from pathlib import Path
import json
import time
from typing import Any, Dict, Optional, Union

import requests

# ----------------------------
# Paths & constants
# ----------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"
DEFAULT_TIMEOUT = 15


# ----------------------------
# Small helpers
# ----------------------------
def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def write_json(obj: Any, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def http_get_text(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = DEFAULT_TIMEOUT,
    max_retries: int = 3,
    backoff_seconds: float = 1.5,
) -> str:
    """GET text with simple retries/backoff."""
    last = None
    for attempt in range(1, max_retries + 1):
        try:
            r = requests.get(url, params=params, headers=headers, timeout=timeout)
            r.raise_for_status()
            return r.text
        except Exception as e:
            last = e
            if attempt < max_retries:
                time.sleep(backoff_seconds * attempt)
            else:
                raise
    assert last
    raise last


def http_get_json(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: int = DEFAULT_TIMEOUT,
    max_retries: int = 3,
    backoff_seconds: float = 1.5,
) -> Union[Dict[str, Any], list]:
    """GET JSON with simple retries/backoff."""
    last = None
    for attempt in range(1, max_retries + 1):
        try:
            r = requests.get(url, params=params, headers=headers, timeout=timeout)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            last = e
            if attempt < max_retries:
                time.sleep(backoff_seconds * attempt)
            else:
                raise
    assert last
    raise last


# ----------------------------
# Blockchain.com Query API
# ----------------------------
def _coerce_number(s: str) -> Union[int, float, str]:
    """Try to parse numeric string to int/float. Return original if not numeric."""
    try:
        return float(s) if "." in s else int(s)
    except Exception:
        return s


def fetch_blockchain_metric(
    metric: str,
    base_url: str = "https://blockchain.info/q",
    timeout: int = DEFAULT_TIMEOUT,
) -> Union[int, float, str]:
    """
    Fetch a metric from Blockchain.com's Query API.

    Examples (doctest):
        >>> val = fetch_blockchain_metric("getdifficulty")  # doctest: +ELLIPSIS
        >>> isinstance(val, (int, float)) and val > 0
        True
        >>> h = fetch_blockchain_metric("getblockcount")  # doctest: +ELLIPSIS
        >>> isinstance(h, int) and h > 0
        True
    """
    url = f"{base_url}/{metric}"
    text = http_get_text(url, timeout=timeout)
    return _coerce_number(text.strip())


# ----------------------------
# CoinGecko (simple/price)
# ----------------------------
def fetch_coingecko_simple_price(
    ids: str = "bitcoin",
    vs_currencies: str = "usd",
    timeout: int = DEFAULT_TIMEOUT,
    max_retries: int = 3,
) -> Dict[str, Any]:
    """
    CoinGecko simple/price endpoint (no API key needed for light usage).

    Examples (doctest):
        >>> sp = fetch_coingecko_simple_price(ids="bitcoin", vs_currencies="usd")  # doctest: +ELLIPSIS
        >>> isinstance(sp, dict) and 'bitcoin' in sp
        True
    """
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": ids, "vs_currencies": vs_currencies}
    return http_get_json(url, params=params, timeout=timeout, max_retries=max_retries)


# ----------------------------
# Demo
# ----------------------------
def _demo() -> None:
    ensure_dirs()

    # 1) Blockchain.com
    try:
        diff = fetch_blockchain_metric("getdifficulty")
        height = fetch_blockchain_metric("getblockcount")
        write_json({"difficulty": diff, "height": height}, DATA_DIR / ".sample_blockchain_q.json")
        print("Blockchain.com Query API OK")
    except Exception as e:
        print("Blockchain.com Query API FAILED ->", e)

    # 2) CoinGecko
    try:
        sp = fetch_coingecko_simple_price(ids="bitcoin", vs_currencies="usd")
        write_json(sp, DATA_DIR / ".sample_coingecko_simple_price.json")
        print("CoinGecko API OK")
    except Exception as e:
        print("CoinGecko API FAILED ->", e)


if __name__ == "__main__":
    _demo()