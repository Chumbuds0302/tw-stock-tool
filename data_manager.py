"""
data_manager.py - Phase 1 DSS Data Layer

Handles:
- Universe building from tw_stocks.json (4-digit codes only)
- OHLCV disk caching in parquet format
- Stock data fetching with cache support
"""

import yfinance as yf
import pandas as pd
import json
import os
import re
from pathlib import Path

# --- Paths ---
DATA_DIR = Path("data")
OHLCV_DIR = DATA_DIR / "ohlcv"
UNIVERSE_PATH = DATA_DIR / "universe.parquet"
STOCK_MAP_FILE = "tw_stocks.json"

# --- Stock Map (Name -> Code) ---
stock_map = {}

def load_stock_map():
    """Load stock name to code mapping from JSON."""
    global stock_map
    if os.path.exists(STOCK_MAP_FILE):
        try:
            with open(STOCK_MAP_FILE, 'r', encoding='utf-8') as f:
                stock_map = json.load(f)
        except Exception as e:
            print(f"Error loading stock map: {e}")

load_stock_map()


# --- A) Universe Builder ---
def build_universe(json_path=STOCK_MAP_FILE, out_path=UNIVERSE_PATH):
    """
    Build universe.parquet from tw_stocks.json.
    Filters for 4-digit codes only, excludes derivatives/warrants.
    
    Returns:
        pd.DataFrame with schema: code, name_zh, ticker, market, is_etf, is_active
    """
    DATA_DIR.mkdir(exist_ok=True)
    
    # Load JSON
    with open(json_path, 'r', encoding='utf-8') as f:
        raw_map = json.load(f)
    
    # Filter for 4-digit codes only
    pattern = re.compile(r'^\d{4}$')
    records = []
    
    for name_zh, code in raw_map.items():
        if pattern.match(str(code)):
            records.append({
                "code": str(code),
                "name_zh": name_zh,
                "ticker": f"{code}.TW",
                "market": "AUTO",
                "is_etf": str(code).startswith("00"),
                "is_active": True
            })
    
    df = pd.DataFrame(records)
    df.to_parquet(out_path, index=False)
    print(f"[Universe] Built {len(df)} stocks -> {out_path}")
    return df


def load_universe(path=UNIVERSE_PATH):
    """Load universe from parquet. Returns None if not exists."""
    if path.exists():
        return pd.read_parquet(path)
    return None


# --- B) OHLCV Disk Caching ---
def get_cache_paths(ticker):
    """
    Get cache file paths for a ticker.
    
    Returns:
        dict with 'ohlcv' key pointing to parquet path
    """
    clean_ticker = ticker.replace(".", "_")
    return {
        "ohlcv": OHLCV_DIR / f"ticker={clean_ticker}.parquet"
    }


def fetch_stock_history(ticker, start=None, end=None, period="6mo", 
                        use_cache=True, force_refresh=False):
    """
    Fetch OHLCV data with disk caching.
    
    Args:
        ticker: Stock ticker (e.g., "2330" or "2330.TW")
        start: Start date (optional, overrides period)
        end: End date (optional)
        period: yfinance period string (default "6mo")
        use_cache: Whether to use disk cache
        force_refresh: Force re-download even if cached
        
    Returns:
        (df, stock_obj) - stock_obj may be None when loaded from cache
    """
    # Validate ticker
    ticker = validate_ticker(ticker)
    
    # Ensure cache directory exists
    OHLCV_DIR.mkdir(parents=True, exist_ok=True)
    
    cache_path = get_cache_paths(ticker)["ohlcv"]
    
    # Try cache first
    if use_cache and not force_refresh and cache_path.exists():
        try:
            df = pd.read_parquet(cache_path)
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()
            return df, None  # No stock_obj from cache
        except Exception as e:
            print(f"[Cache] Error reading {cache_path}: {e}")
    
    # Fetch from yfinance
    try:
        stock = yf.Ticker(ticker)
        
        if start:
            df = stock.history(start=start, end=end)
        else:
            df = stock.history(period=period)
        
        if df.empty:
            # Try .TWO suffix for OTC stocks
            if ticker.endswith(".TW"):
                ticker_otc = ticker.replace(".TW", ".TWO")
                stock = yf.Ticker(ticker_otc)
                if start:
                    df = stock.history(start=start, end=end)
                else:
                    df = stock.history(period=period)
        
        # Standardize columns
        required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
        for col in required_cols:
            if col not in df.columns:
                df[col] = 0
        
        df = df[required_cols].sort_index()
        
        # Save to cache
        if use_cache and not df.empty:
            df.to_parquet(cache_path)
        
        return df, stock
        
    except Exception as e:
        print(f"[Fetch] Error fetching {ticker}: {e}")
        return pd.DataFrame(), None


def build_ohlcv_dataset(universe_path=UNIVERSE_PATH, start="2018-01-01", 
                        end=None, max_tickers=None, force_refresh=False):
    """
    Batch download and cache OHLCV for universe.
    Resumable - skips already cached tickers unless force_refresh.
    
    Args:
        universe_path: Path to universe.parquet
        start: Start date for historical data
        end: End date (None = today)
        max_tickers: Limit number of tickers (for testing)
        force_refresh: Re-download even if cached
        
    Returns:
        dict with 'success', 'failed', 'skipped' counts
    """
    universe = load_universe(universe_path)
    if universe is None:
        print("[OHLCV] No universe found. Run build_universe() first.")
        return {"success": 0, "failed": 0, "skipped": 0}
    
    tickers = universe['ticker'].tolist()
    if max_tickers:
        tickers = tickers[:max_tickers]
    
    results = {"success": 0, "failed": 0, "skipped": 0}
    
    for i, ticker in enumerate(tickers):
        cache_path = get_cache_paths(ticker)["ohlcv"]
        
        # Skip if cached and not forcing refresh
        if cache_path.exists() and not force_refresh:
            results["skipped"] += 1
            continue
        
        try:
            df, _ = fetch_stock_history(ticker, start=start, end=end, 
                                        use_cache=True, force_refresh=force_refresh)
            if not df.empty:
                results["success"] += 1
            else:
                results["failed"] += 1
        except Exception as e:
            print(f"[OHLCV] Failed {ticker}: {e}")
            results["failed"] += 1
        
        # Progress
        if (i + 1) % 50 == 0:
            print(f"[OHLCV] Progress: {i+1}/{len(tickers)}")
    
    print(f"[OHLCV] Done: {results}")
    return results


# --- Utility Functions ---
def validate_ticker(ticker):
    """Ensure ticker has proper suffix."""
    ticker = ticker.strip()
    
    if ticker.endswith(".TW") or ticker.endswith(".TWO"):
        return ticker
    
    if ticker.isdigit():
        return f"{ticker}.TW"
    
    # Search by name
    return search_stock_by_name(ticker)


def search_stock_by_name(query):
    """Search for ticker by Chinese name or code."""
    query = query.strip()
    
    if query.isdigit():
        return f"{query}.TW"
    
    if query in stock_map:
        return f"{stock_map[query]}.TW"
    
    # Partial match
    for name, code in stock_map.items():
        if query in name and str(code).isdigit():
            return f"{code}.TW"
    
    return query


def get_stock_name(ticker):
    """Get Chinese name for a ticker."""
    code = ticker.replace(".TW", "").replace(".TWO", "")
    for name, c in stock_map.items():
        if str(c) == code:
            return name
    return ticker


def fetch_stock_info(ticker):
    """Fetch basic stock info from yfinance."""
    ticker = validate_ticker(ticker)
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Try .TWO if .TW fails
        if (not info or info.get('regularMarketPrice') is None) and ticker.endswith(".TW"):
            ticker_otc = ticker.replace(".TW", ".TWO")
            stock = yf.Ticker(ticker_otc)
            info = stock.info
        
        return info
    except Exception as e:
        print(f"[Info] Error: {e}")
        return {}
