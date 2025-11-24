import pandas as pd

def get_fundamental_metrics(info):
    """
    Extracts key fundamental metrics from yfinance info dict.
    """
    metrics = {
        "Name": info.get("longName", "N/A"),
        "Symbol": info.get("symbol", "N/A"),
        "Sector": info.get("sector", "N/A"),
        "Industry": info.get("industry", "N/A"),
        "Market Cap": info.get("marketCap", "N/A"),
        "P/E Ratio": info.get("trailingPE", "N/A"),
        "Forward P/E": info.get("forwardPE", "N/A"),
        "Dividend Yield": info.get("dividendYield", info.get("trailingAnnualDividendYield", "N/A")),
        "Ex-Dividend Date": info.get("exDividendDate", "N/A"),
        "Trailing EPS": info.get("trailingEps", "N/A"),
        "Forward EPS": info.get("forwardEps", "N/A"),
        "ROE": info.get("returnOnEquity", "N/A"),
        "Profit Margin": info.get("profitMargins", "N/A"),
        "Price to Book": info.get("priceToBook", "N/A"),
    }
    
    # Format percentages
    for key in ["Dividend Yield", "ROE", "Profit Margin"]:
        val = metrics[key]
        if isinstance(val, (int, float)):
            metrics[key] = f"{val * 100:.2f}%"
            
    return metrics
