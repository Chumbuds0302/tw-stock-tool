import yfinance as yf
import twstock
import json

def test_yfinance_news(ticker):
    print(f"--- News for {ticker} ---")
    stock = yf.Ticker(ticker)
    try:
        news = stock.news
        print(json.dumps(news[:3], indent=2)) # Print first 3 news items
    except Exception as e:
        print(f"Error fetching news: {e}")

def test_twstock_search():
    print("\n--- twstock Search Test ---")
    # twstock.codes is a dict of all codes
    # We can search by name
    target_name = "台積電"
    found = False
    for code, info in twstock.codes.items():
        if info.name == target_name:
            print(f"Found {target_name}: {code} ({info.type})")
            found = True
            break
    if not found:
        print(f"Could not find {target_name}")

def test_twstock_institutional(ticker_code):
    print(f"\n--- Institutional Data for {ticker_code} ---")
    try:
        stock = twstock.Stock(ticker_code)
        # twstock might fetch recent trading data including institutional?
        # Actually twstock.Stock mainly fetches price data.
        # Let's check 'moving_average' or similar, but institutional data might be in 'bfp' (Buy/Sell by Foreign Investors, etc.) if available.
        # Looking at docs (or common usage), twstock usually fetches from TWSE.
        # Let's just print what we can get easily.
        print("Fetching recent data...")
        data = stock.fetch_31() # Fetch this month
        print(f"Data points fetched: {len(data)}")
        if len(data) > 0:
            print(f"Sample data: {data[-1]}")
    except Exception as e:
        print(f"Error with twstock: {e}")

if __name__ == "__main__":
    test_yfinance_news("2330.TW")
    test_twstock_search()
    test_twstock_institutional("2330")
