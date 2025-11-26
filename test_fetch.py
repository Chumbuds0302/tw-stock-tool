# -*- coding: utf-8 -*-
"""
Test data fetching
"""
import yfinance as yf
import pandas as pd
from datetime import datetime

print("=" * 50)
print("Test 1: Testing yfinance basic functionality")
print("=" * 50)

try:
    # Test TSMC
    ticker = "2330.TW"
    print(f"\nFetching data for {ticker}...")
    
    stock = yf.Ticker(ticker)
    df = stock.history(period="1mo")
    
    if df.empty:
        print("[ERROR] Cannot fetch historical data, DataFrame is empty")
    else:
        print(f"[SUCCESS] Got {len(df)} days of data")
        print(f"Latest close price: {df['Close'].iloc[-1]:.2f}")
        print(f"Date range: {df.index[0].date()} to {df.index[-1].date()}")
    
    print("\nFetching stock info...")
    info = stock.info
    if info:
        print("[SUCCESS] Got stock info")
        print(f"  - Name: {info.get('longName', 'N/A')}")
        print(f"  - Current Price: {info.get('currentPrice', 'N/A')}")
        print(f"  - Market Cap: {info.get('marketCap', 'N/A')}")
    else:
        print("[ERROR] Cannot get stock info")
        
except Exception as e:
    print(f"[ERROR] Exception occurred: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 50)
print("Test 2: Testing network connection")
print("=" * 50)

try:
    import requests
    response = requests.get("https://query1.finance.yahoo.com/v8/finance/chart/2330.TW", timeout=10)
    print(f"[SUCCESS] Can connect to Yahoo Finance (status: {response.status_code})")
except Exception as e:
    print(f"[ERROR] Cannot connect to Yahoo Finance: {e}")

print("\n" + "=" * 50)
print("Test completed")
print("=" * 50)
