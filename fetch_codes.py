import pandas as pd
import requests
import io

import json
import os

def fetch_twse_codes():
    url = "https://isin.twse.com.tw/isin/C_public.jsp?strMode=2"
    try:
        res = requests.get(url)
        # Try cp950 first, then big5 with replace
        try:
            content = res.content.decode('cp950')
        except:
            content = res.content.decode('big5', errors='replace')
            
        dfs = pd.read_html(io.StringIO(content))
        df = dfs[0]
        
        # The first row is usually header, and columns need adjustment
        df.columns = df.iloc[0]
        df = df.iloc[1:]
        
        # Filter for equities
        # Column 0 is "有價證券代號及名稱" (Code and Name)
        # Format is "2330　台積電"
        
        stock_dict = {}
        for index, row in df.iterrows():
            code_name = row.iloc[0]
            if isinstance(code_name, str):
                parts = code_name.split()
                if len(parts) >= 2:
                    code = parts[0]
                    name = parts[1]
                    if len(code) in [4, 5, 6] and code.isdigit(): # Include ETFs (5-6 digits)
                        stock_dict[name] = code
                        
        print(f"Fetched {len(stock_dict)} stocks.")
        
        # Save to JSON
        with open('tw_stocks.json', 'w', encoding='utf-8') as f:
            json.dump(stock_dict, f, ensure_ascii=False, indent=4)
        print("Saved to tw_stocks.json")
            
        return stock_dict
    except Exception as e:
        print(f"Error: {e}")
        return {}

if __name__ == "__main__":
    fetch_twse_codes()
