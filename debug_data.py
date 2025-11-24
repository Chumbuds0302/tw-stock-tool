import yfinance as yf
import requests
import pandas as pd
import time

def debug_news():
    print("Debugging News...")
    ticker = "2330.TW"
    stock = yf.Ticker(ticker)
    news = stock.news
    if news:
        print(f"First news item keys: {news[0].keys()}")
        print(news[0])
    else:
        print("No news found.")

def scrape_twse_institutional(stock_code):
    print(f"\nScraping TWSE for {stock_code}...")
    # TWSE T86 URL for daily institutional investors
    # https://www.twse.com.tw/rwd/en/fund/T86?date=20231122&selectType=ALLBUT0999&response=json
    
    # We need the latest trading date. For now, let's try to fetch today or yesterday.
    # Actually, let's just fetch the latest available data.
    # The API usually takes a date.
    
    url = "https://www.twse.com.tw/rwd/zh/fund/T86?response=json&selectType=ALL"
    
    try:
        res = requests.get(url)
        data = res.json()
        
        if data.get('stat') == 'OK':
            fields = data['fields']
            # Find the index for stock code, name, and investors
            # Usually: Code, Name, Foreign Buy, Foreign Sell, Foreign Net, ...
            # We need to parse 'data' list.
            
            for row in data['data']:
                if row[0] == stock_code:
                    print("Found data:")
                    print(f"Foreign Net: {row[4]}") # Foreign Investment Net
                    print(f"Trust Net: {row[10]}")   # Investment Trust Net
                    print(f"Dealer Net: {row[11]}")  # Dealer Net (Total)
                    return {
                        "Foreign": row[4],
                        "Trust": row[10],
                        "Dealer": row[11]
                    }
            print("Stock code not found in today's data (maybe not a trading day or wrong code).")
        else:
            print(f"TWSE Error: {data.get('stat')}")
            
    except Exception as e:
        print(f"Scraping Error: {e}")

if __name__ == "__main__":
    debug_news()
    scrape_twse_institutional("2330")
