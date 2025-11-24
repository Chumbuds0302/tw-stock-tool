import twstock
import yfinance as yf
import pandas as pd

def test_data_sources():
    ticker = "2330"
    print(f"Testing data for {ticker}...")

    # 1. Test yfinance for EPS and News
    print("\n[yfinance] Fetching info...")
    stock = yf.Ticker(f"{ticker}.TW")
    
    print("News:")
    try:
        for news in stock.news[:2]:
            print(f"- {news['title']} ({news['link']})")
    except Exception as e:
        print(f"Error fetching news: {e}")

    print("\nFinancials (EPS):")
    try:
        fin = stock.financials
        if not fin.empty:
            print(fin.loc['Basic EPS'])
        else:
            print("No financials found.")
    except Exception as e:
        print(f"Error fetching financials: {e}")

    # 2. Test twstock for Institutional Data (3 major investors)
    print("\n[twstock] Fetching institutional data...")
    try:
        # twstock.Stock('2330').moving_average(...) 
        # twstock doesn't directly give institutional data easily in the basic API, 
        # usually it's for price. Let's check if there's a specific module or if we need to scrape.
        # Actually twstock has `ThreeInstitutional` but it might be deprecated or require specific calls.
        # Let's try a simple fetch to see what we get.
        s = twstock.Stock(ticker)
        print(f"Price: {s.price[-1]}")
        
        # If twstock doesn't have easy institutional data, we might need to scrape TWSE directly.
        # URL: https://www.twse.com.tw/rwd/en/fund/T86?date=20231122&selectType=ALLBUT0999
        pass
    except Exception as e:
        print(f"Error with twstock: {e}")

if __name__ == "__main__":
    test_data_sources()
