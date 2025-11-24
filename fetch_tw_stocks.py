import requests
import pandas as pd
import json
import io

def fetch_and_save_stocks():
    url = "https://isin.twse.com.tw/isin/C_public.jsp?strMode=2"
    print(f"Fetching data from {url}...")
    
    try:
        res = requests.get(url)
        # CP950 is the standard encoding for Traditional Chinese (Big5 extension) used in TW
        content = res.content.decode('cp950', errors='ignore')
        
        dfs = pd.read_html(io.StringIO(content))
        df = dfs[0]
        
        # Clean up dataframe
        df.columns = df.iloc[0]
        df = df.iloc[1:]
        
        stock_map = {}
        
        for index, row in df.iterrows():
            code_name = row.iloc[0]
            if isinstance(code_name, str):
                # Format is usually "2330　台積電" (Fullwidth space) or "2330 台積電"
                parts = code_name.split()
                if len(parts) >= 2:
                    code = parts[0]
                    name = parts[1]
                    
                    # Filter for 4-digit stock codes (Equities)
                    if len(code) == 4 and code.isdigit():
                        stock_map[name] = code
                        stock_map[code] = name # Also map code to name for reverse lookup if needed
        
        print(f"Found {len(stock_map) // 2} unique stocks.")
        
        # Save to JSON
        with open('tw_stocks.json', 'w', encoding='utf-8') as f:
            json.dump(stock_map, f, ensure_ascii=False, indent=4)
            
        print("Saved to tw_stocks.json")
        
        # Verify
        if "台積電" in stock_map:
            print(f"Verification: 台積電 -> {stock_map['台積電']}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fetch_and_save_stocks()
