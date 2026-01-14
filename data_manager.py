import yfinance as yf
import pandas as pd
import json
import os
import requests
import datetime

# Load stock map
STOCK_MAP_FILE = 'tw_stocks.json'
stock_map = {}

def load_stock_map():
    global stock_map
    if os.path.exists(STOCK_MAP_FILE):
        try:
            with open(STOCK_MAP_FILE, 'r', encoding='utf-8') as f:
                stock_map = json.load(f)
        except Exception as e:
            print(f"Error loading stock map: {e}")

load_stock_map()

def search_stock_by_name(query):
    """
    Search for a stock ticker by Chinese name or code.
    Returns the ticker with .TW suffix if found, else returns the original query.
    """
    query = query.strip()
    
    # If it's already a number, assume it's a code
    if query.isdigit():
        return f"{query}.TW"
        
    # Search in loaded stock map
    if query in stock_map:
        return f"{stock_map[query]}.TW"
            
    # Partial match
    for name, code in stock_map.items():
        if query in name and code.isdigit(): 
            return f"{code}.TW"

    return query

def validate_ticker(ticker):
    """
    Ensures the ticker ends with .TW or .TWO for Taiwan stocks.
    If input is not a number, try to search by name first.
    """
    ticker = ticker.strip()
    
    # If it already has .TW or .TWO suffix, return as is
    if ticker.endswith(".TW") or ticker.endswith(".TWO"):
        return ticker
    
    # If it's a number, we'll try .TW first (will be handled in fetch_stock_history)
    if ticker.isdigit():
        return f"{ticker}.TW"
    
    # Try to search by name (Chinese or partial match)
    return search_stock_by_name(ticker)

def get_stock_name(ticker):
    """
    Returns the Chinese name for a given ticker code.
    """
    code = ticker.replace(".TW", "").replace(".TWO", "")
    # Create reverse map if needed, or just search
    # Since map is Name -> Code, we search for value == code
    for name, c in stock_map.items():
        if c == code:
            return name
    return ticker # Return ticker if name not found
    if not ticker.endswith(".TW") and ticker[:-3].isdigit(): # Handle case where user might input 2330.TW manually
         pass # It is already fine
    elif not ticker.endswith(".TW") and ticker.isdigit() == False:
         # Try to search if it's a name
         return search_stock_by_name(ticker)
         
    return ticker

def fetch_stock_history(ticker, period="1y"):
    """
    Fetches historical stock data.
    Automatically tries .TWO suffix if .TW returns no data (for OTC stocks).
    """
    ticker = validate_ticker(ticker)
    stock = yf.Ticker(ticker)
    df = stock.history(period=period)
    
    # If no data and ticker ends with .TW, try .TWO (OTC market)
    if df.empty and ticker.endswith(".TW"):
        ticker_otc = ticker.replace(".TW", ".TWO")
        stock = yf.Ticker(ticker_otc)
        df = stock.history(period=period)
        if not df.empty:
            # Successfully found data with .TWO suffix
            ticker = ticker_otc
    
    return df, stock

def fetch_stock_info(ticker):
    """
    Fetches fundamental info.
    Automatically tries .TWO suffix if .TW returns no data (for OTC stocks).
    """
    ticker = validate_ticker(ticker)
    stock = yf.Ticker(ticker)
    info = stock.info
    
    # If no useful info and ticker ends with .TW, try .TWO (OTC market)
    if (not info or info.get('regularMarketPrice') is None) and ticker.endswith(".TW"):
        ticker_otc = ticker.replace(".TW", ".TWO")
        stock = yf.Ticker(ticker_otc)
        info_otc = stock.info
        if info_otc and info_otc.get('regularMarketPrice') is not None:
            info = info_otc
    
    return info

def get_daily_inst_data(date_str):
    """
    Fetches the entire institutional investor data for a specific date from TWSE.
    Returns a dictionary mapping stock code to data, or None if failed/no data.
    """
    url = f"https://www.twse.com.tw/rwd/zh/fund/T86?response=json&selectType=ALL&date={date_str}"
    try:
        # Add a small delay to be polite to the server
        # time.sleep(0.1) 
        res = requests.get(url, timeout=10)
        data = res.json()
        
        if data.get('stat') == 'OK':
            daily_data = {}
            for row in data['data']:
                # row[0] is code
                code = row[0]
                daily_data[code] = {
                    "Foreign": int(row[4].replace(',', '')),
                    "Trust": int(row[10].replace(',', '')),
                    "Dealer": int(row[11].replace(',', ''))
                }
            return daily_data
    except Exception as e:
        print(f"Error fetching institutional data for {date_str}: {e}")
    return None

def fetch_institutional_data_history(ticker, days=5):
    """
    This function is now a wrapper that logic will be moved to app.py to utilize st.cache_data.
    However, for compatibility, we keep a version here but it won't be efficient without caching.
    The app.py should call fetch_daily_institutional_data directly with caching.
    """
    pass # Logic moved to app.py for caching control

def fetch_eps_data(stock_obj):
    """
    Fetches quarterly EPS data from yfinance stock object (last 2 years = 8 quarters).
    """
    try:
        # Use quarterly_financials instead of annual financials
        fin = stock_obj.quarterly_financials
        if not fin.empty and 'Basic EPS' in fin.index:
            eps_series = fin.loc['Basic EPS']
            # Convert to dataframe and limit to 8 quarters (2 years)
            eps_df = eps_series.reset_index().rename(columns={'index': 'Date', 'Basic EPS': 'EPS'})
            # Sort by date descending and take first 8
            eps_df = eps_df.sort_values('Date', ascending=False).head(8)
            # Reverse to show chronologically
            return eps_df.sort_values('Date', ascending=True)
    except Exception as e:
        print(f"Error fetching EPS: {e}")
    return None

def fetch_news(stock_obj):
    """
    Fetches news from yfinance stock object.
    """
    news_list = []
    try:
        raw_news = stock_obj.news
        for item in raw_news:
            content = item.get('content', {})
            if not content: # Sometimes it's directly in item
                 content = item
            
            title = content.get('title')
            link = content.get('clickThroughUrl', {}).get('url')
            
            # Fallback for different yfinance versions/structures
            if not title:
                title = item.get('title')
            if not link:
                link = item.get('link')

            if title and link:
                news_list.append({"title": title, "link": link})
    except Exception as e:
        print(f"Error fetching news: {e}")
    return news_list
