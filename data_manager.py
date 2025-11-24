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
    Ensures the ticker ends with .TW for Taiwan stocks if it's a number.
    """
    if ticker.isdigit():
        return f"{ticker}.TW"
    return ticker

def get_stock_name(ticker):
    """
    Returns the Chinese name for a given ticker code.
    """
    code = ticker.replace(".TW", "")
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
    """
    ticker = validate_ticker(ticker)
    stock = yf.Ticker(ticker)
    df = stock.history(period=period)
    return df, stock

def fetch_stock_info(ticker):
    """
    Fetches fundamental info.
    """
    ticker = validate_ticker(ticker)
    stock = yf.Ticker(ticker)
    return stock.info

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
