import pandas as pd
import yfinance as yf
import technical_analysis
import data_manager
import datetime

# --- Constants ---
TOP_STOCKS = [
    # Tech Giants
    "2330.TW", "2317.TW", "2454.TW", "2308.TW", "2382.TW", "2412.TW", "3711.TW",
    # Financials
    "2881.TW", "2882.TW", "2891.TW", "2886.TW", "2884.TW", "2892.TW", "5880.TW", "2883.TW",
    # Traditional
    "1301.TW", "1303.TW", "2002.TW", "1101.TW", "1216.TW", "2207.TW", "1326.TW",
    # Shipping
    "2603.TW", "2609.TW", "2615.TW", "2618.TW", "2610.TW", "2606.TW", "5608.TW",
    # Others
    "3008.TW", "3045.TW", "2357.TW", "3231.TW", "2353.TW", "2324.TW", "2303.TW", "6669.TW",
    "2356.TW", "2408.TW", "2344.TW", "2327.TW",
    # ETFs (Market/High Dividend)
    "0050.TW", "0056.TW", "00878.TW", "00929.TW", "00919.TW", "006208.TW", "00713.TW", "00940.TW",
    "00692.TW", "00881.TW"
]

# Sector-based grouping for filtering
SECTOR_MAP = {
    "全部 (All)": TOP_STOCKS,
    "ETF": ["0050.TW", "0056.TW", "00878.TW", "00929.TW", "00919.TW", "006208.TW", "00713.TW", "00940.TW", "00692.TW", "00881.TW", "00900.TW", "00895.TW"],
    "半導體 (Semi)": ["2330.TW", "2454.TW", "2303.TW", "3711.TW", "3034.TW", "2308.TW", "2379.TW", "3443.TW", "6446.TW"],
    "AI 伺服器 (AI)": ["2382.TW", "3231.TW", "2356.TW", "6669.TW", "2317.TW", "3706.TW", "2324.TW", "4958.TW"],
    "記憶體 (Memory)": ["2408.TW", "8299.TW", "3260.TW", "2344.TW", "2337.TW", "3450.TW"],
    "封測 (Packaging)": ["2311.TW", "3711.TW", "6239.TW", "8150.TW", "2369.TW", "6121.TW", "3711.TW"],
    "航運 (Shipping)": ["2603.TW", "2609.TW", "2615.TW", "2618.TW", "2610.TW", "2606.TW", "5608.TW", "2634.TW"],
    "傳統產業 (Traditional)": ["1101.TW", "1301.TW", "1303.TW", "2002.TW", "1216.TW", "2207.TW", "1326.TW", "1402.TW"],
    "金融 (Finance)": ["2881.TW", "2882.TW", "2886.TW", "2891.TW", "5880.TW", "2892.TW", "2883.TW", "2884.TW", "2885.TW"]
}


def process_ticker(ticker, mode):
    """
    Helper function to process a single ticker for recommendation.
    """
    try:
        # Basic check to skip if data fails
        # Always fetch history now for trend check
        df, stock_obj = data_manager.fetch_stock_history(ticker, period="6mo")
        if df.empty: return None
        
        # Get Chinese Name
        ch_name = data_manager.get_stock_name(ticker)
        is_etf = ticker.startswith("00")
        
        if mode == "Short-term":
            df = technical_analysis.add_technical_indicators(df)
            inst_df = data_manager.fetch_institutional_data_history(ticker, days=3) 
            
            signal, details, score, style = analyze_short_term(df, inst_df)
            
            # ETF Adjustment for Short-term: They are less volatile, so lower threshold slightly
            threshold = 3
            if is_etf: threshold = 2
            
            # Convert details to simple reasons list for the card view
            reasons = [f"{d['metric']}: {d['reason']}" for d in details if d['signal'] in ['Bullish', 'Warning']]
            
            if score >= threshold: 
                return {
                    "ticker": ticker,
                    "name": ch_name, # Use Chinese name
                    "signal": signal,
                    "score": score,
                    "reasons": reasons,
                    "price": df['Close'].iloc[-1],
                    "style": style
                }
                
        elif mode == "Long-term":
            info = data_manager.fetch_stock_info(ticker)
            if not info: return None
            
            inst_df = data_manager.fetch_institutional_data_history(ticker, days=10)
            
            # Pass stock_obj for financial data AND df for trend check
            signal, details, score, style = analyze_long_term(info, None, inst_df, stock_obj=stock_obj, df=df)
            
            # ETF Adjustment for Long-term: 
            # ETFs often don't have "Moat" (ROE/Cap) or "Financials" in the same way.
            # We prioritize Yield and Stability (Beta).
            threshold = 4
            if is_etf: 
                threshold = 2 # Much lower threshold for ETFs to ensure they appear
                # Add bonus for ETF stability if not already counted
                score += 1 
            
            reasons = [f"{d['metric']}: {d['reason']}" for d in details if d['signal'] in ['Bullish', 'Warning']]
            
            if score >= threshold:
                return {
                    "ticker": ticker,
                    "name": ch_name, # Use Chinese name
                    "signal": signal,
                    "score": score,
                    "reasons": reasons,
                    "price": info.get('currentPrice', 0),
                    "style": style
                }

                
    except Exception as e:
        print(f"Skipping {ticker}: {e}")
        return None
    return None

def get_stock_recommendations(mode, sector="全部 (All)"):
    """
    Scans stocks based on selected sector and returns top picks AND warnings.
    Uses parallel processing for speed.
    """
    recommendations = []
    
    # Get target list based on sector
    target_list = SECTOR_MAP.get(sector, TOP_STOCKS)
    
    # Use ThreadPoolExecutor for parallel fetching with increased workers
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        future_to_ticker = {executor.submit(process_ticker, ticker, mode): ticker for ticker in target_list}
        
        for future in concurrent.futures.as_completed(future_to_ticker):
            result = future.result()
            if result:
                recommendations.append(result)
                
    # Sort by score
    recommendations.sort(key=lambda x: x['score'], reverse=True)
    
    # Return both top picks and warnings
    top_picks = [r for r in recommendations if r['score'] >= 3][:10]  # Top 10 good stocks
    
    # Warnings: low score (<=1) OR sell/wait signals
    warnings = [r for r in recommendations if r['score'] <= 1 or 'Sell' in r.get('signal', '') or 'Wait' in r.get('signal', '')]
    warnings.sort(key=lambda x: x['score'])  # Sort worst first
    warnings = warnings[:5]  # Top 5 warnings
    
    return {'top_picks': top_picks, 'warnings': warnings}

def analyze_short_term(df, inst_df):
    """
    Analyzes stock for short-term trading signals.
    Returns: (Signal, Details_List, Score, Style)
    Details_List: List of dicts {'metric': '...', 'value': '...', 'signal': '...', 'reason': '...'}
    """
    score = 0
    details = []
    
    if df is None or df.empty:
        return "Neutral", [], 0, "N/A"

    # 1. Moving Average Trend
    current_price = df['Close'].iloc[-1]
    ma5 = df['MA5'].iloc[-1]
    ma20 = df['MA20'].iloc[-1]
    ma60 = df['MA60'].iloc[-1]
    
    ma_signal = "Neutral"
    if ma5 > ma20 > ma60:
        score += 2
        ma_signal = "Bullish"
        reason = "均線多頭排列"
    elif ma5 > ma20:
        score += 1
        ma_signal = "Bullish"
        reason = "短期均線翻多"
    elif ma5 < ma20:
        score -= 1
        ma_signal = "Bearish"
        reason = "短期均線偏空"
    else:
        reason = "均線糾結"
        
    details.append({
        "metric": "均線趨勢 (MA Trend)",
        "value": f"Price: {current_price:.1f} > MA20: {ma20:.1f}",
        "signal": ma_signal,
        "reason": reason
    })
        
    # 2. Momentum (RSI)
    rsi = df['RSI'].iloc[-1]
    rsi_signal = "Neutral"
    if 50 < rsi < 70:
        score += 1
        rsi_signal = "Bullish"
        reason = "強勢區"
    elif rsi > 80:
        score -= 1
        rsi_signal = "Warning"
        reason = "過熱恐回檔"
    elif rsi < 30:
        score += 1
        rsi_signal = "Bullish" # Oversold bounce
        reason = "超賣醞釀反彈"
    else:
        reason = "盤整區"
        
    details.append({
        "metric": "RSI 指標",
        "value": f"{rsi:.1f}",
        "signal": rsi_signal,
        "reason": reason
    })
        
    # 3. MACD
    macd = df['MACD'].iloc[-1]
    signal_line = df['MACD_Signal'].iloc[-1]
    macd_signal = "Neutral"
    if macd > signal_line:
        score += 1
        macd_signal = "Bullish"
        reason = "黃金交叉"
    else:
        reason = "無特殊訊號"
        
    details.append({
        "metric": "MACD 指標",
        "value": f"DIF: {macd:.2f} > DEM: {signal_line:.2f}" if macd > signal_line else "Bearish/Neutral",
        "signal": macd_signal,
        "reason": reason
    })
        
    # 4. Institutional (Chips)
    inst_val = "N/A"
    inst_signal = "Neutral"
    inst_reason = "無資料"
    if inst_df is not None and not inst_df.empty:
        recent_inst = inst_df.head(3)
        total_buy = recent_inst['Foreign'].sum() + recent_inst['Trust'].sum()
        inst_val = f"{total_buy:,}"
        if total_buy > 0:
            score += 1
            inst_signal = "Bullish"
            inst_reason = "近三日法人買超"
        else:
            inst_signal = "Bearish"
            inst_reason = "近三日法人賣超"
            
    details.append({
        "metric": "法人籌碼 (Chips)",
        "value": inst_val,
        "signal": inst_signal,
        "reason": inst_reason
    })

    # 5. Volume Analysis
    vol_today = df['Volume'].iloc[-1]
    vol_avg = df['Volume'].rolling(5).mean().iloc[-1]
    vol_signal = "Neutral"
    vol_reason = "量能正常"
    
    if vol_today > vol_avg * 2:
        score += 1
        vol_signal = "Bullish"
        vol_reason = "爆量攻擊 ( > 2x Avg)"
    elif vol_today < vol_avg * 0.5:
        vol_reason = "量縮觀望"
        
    details.append({
        "metric": "成交量 (Volume)",
        "value": f"{int(vol_today):,} (Avg: {int(vol_avg):,})",
        "signal": vol_signal,
        "reason": vol_reason
    })
            
    # 6. KD Indicator (Timing)
    k = df['K'].iloc[-1]
    d = df['D'].iloc[-1]
    prev_k = df['K'].iloc[-2]
    prev_d = df['D'].iloc[-2]
    
    kd_signal = "Neutral"
    kd_reason = "無特殊訊號"
    
    # Gold Cross in Oversold Zone (K < 20)
    if k < 20 and k > d and prev_k < prev_d:
        score += 2
        kd_signal = "Bullish"
        kd_reason = "KD 低檔黃金交叉 (絕佳買點)"
    # Overbought Zone
    elif k > 80:
        if k < d and prev_k > prev_d:
            score -= 1
            kd_signal = "Bearish"
            kd_reason = "KD 高檔死亡交叉 (獲利了結)"
        else:
            kd_signal = "Warning"
            kd_reason = "KD 過熱區"
            
    details.append({
        "metric": "KD 指標 (Timing)",
        "value": f"K: {k:.1f}, D: {d:.1f}",
        "signal": kd_signal,
        "reason": kd_reason
    })

    # Final Verdict
    style = determine_operation_style(df)
    
    if score >= 4:
        return "Strong Buy", details, score, style
    elif score >= 2:
        return "Buy", details, score, style
    elif score <= -1:
        return "Sell", details, score, style
    else:
        return "Wait", details, score, style

def analyze_long_term(info, eps_df, inst_df, stock_obj=None, df=None):
    """
    Analyzes stock for long-term investment.
    Returns: (Signal, Details_List, Score, Style)
    """
    score = 0
    details = []
    
    # Default style for long term analysis context
    style = "🐢 中長線 (Position Trading)"
    
    if not info:
        return "Neutral", [], 0, style
        
    # --- 0. Trend Filter (Avoid Value Traps) ---
    trend_score = 0
    trend_signal = "Neutral"
    trend_reason = "資料不足"
    
    if df is not None and not df.empty:
        # Ensure indicators are present
        if 'MA60' not in df.columns:
            df = technical_analysis.add_technical_indicators(df)
            
        current_price = df['Close'].iloc[-1]
        ma5 = df['MA5'].iloc[-1]
        ma20 = df['MA20'].iloc[-1]
        ma60 = df['MA60'].iloc[-1]
        
        # Check 1: Bearish Alignment (Strong Downtrend)
        if ma5 < ma20 < ma60:
            trend_score -= 2
            trend_signal = "Bearish"
            trend_reason = "❌ 均線空頭排列 (趨勢向下)"
        # Check 2: Price significantly below MA60 (Broken Trend)
        elif current_price < ma60 * 0.9:
            trend_score -= 1
            trend_signal = "Warning"
            trend_reason = "⚠️ 股價跌破季線 > 10%"
        # Check 3: Bullish Alignment
        elif ma5 > ma20 > ma60:
            trend_score += 1
            trend_signal = "Bullish"
            trend_reason = "✅ 均線多頭排列"
        else:
            trend_reason = "趨勢盤整中"
            
    score += trend_score
    details.append({
        "metric": "趨勢濾網 (Trend)",
        "value": trend_reason,
        "signal": trend_signal,
        "reason": trend_reason
    })

    # --- 0.5 Industry Leader Bonus (Moat) ---
    # Market Cap > 500B TWD AND ROE > 15%
    mkt_cap = info.get('marketCap', 0)
    roe = info.get('returnOnEquity', 0)
    
    moat_score = 0
    moat_signal = "Neutral"
    moat_reason = "未達標準"
    
    if mkt_cap > 500_000_000_000 and roe > 0.15:
        moat_score = 2
        score += moat_score
        moat_signal = "Bullish"
        moat_reason = "🏆 具備產業護城河優勢 (龍頭股)"
        
    details.append({
        "metric": "護城河 (Moat)",
        "value": f"Cap: {mkt_cap/100000000:.0f}億, ROE: {roe*100:.1f}%",
        "signal": moat_signal,
        "reason": moat_reason
    })
    
    # --- 0.6 Beta (Risk) ---
    beta = info.get('beta3Year') # yfinance often uses beta3Year
    if not beta: beta = info.get('beta')
    
    beta_score = 0
    beta_signal = "Neutral"
    beta_reason = "無資料"
    
    if beta:
        if beta < 0.8:
            beta_score += 1
            score += beta_score
            beta_signal = "Bullish"
            beta_reason = "✅ 低波動 (Beta < 0.8)，抗跌"
        elif beta > 1.5:
            beta_signal = "Warning"
            beta_reason = "⚠️ 高波動 (Beta > 1.5)，風險高"
        else:
            beta_reason = "波動適中"
            
    details.append({
        "metric": "風險係數 (Beta)",
        "value": f"{beta:.2f}" if beta else "N/A",
        "signal": beta_signal,
        "reason": beta_reason
    })

    # 1. Valuation (P/E)
    pe = info.get('trailingPE')
    pe_signal = "Neutral"
    pe_reason = "無資料"
    if pe:
        if pe < 15:
            score += 2
            pe_signal = "Bullish"
            pe_reason = "低估"
        elif pe < 25:
            score += 1
            pe_signal = "Bullish"
            pe_reason = "合理"
        else:
            pe_signal = "Warning"
            pe_reason = "偏高"
            
    details.append({
        "metric": "本益比 (P/E)",
        "value": f"{pe:.1f}" if pe else "N/A",
        "signal": pe_signal,
        "reason": pe_reason
    })
            
    # 2. Dividend Yield
    yield_val = info.get('dividendYield')
    yield_signal = "Neutral"
    yield_reason = "無資料"
    if yield_val:
        yield_pct = yield_val * 100
        if yield_pct > 4:
            score += 2
            yield_signal = "Bullish"
            yield_reason = "高殖利率"
        elif yield_pct > 2:
            score += 1
            yield_signal = "Bullish"
            yield_reason = "尚可"
        else:
            yield_reason = "偏低"
            
    details.append({
        "metric": "殖利率 (Yield)",
        "value": f"{yield_pct:.2f}%" if yield_val else "N/A",
        "signal": yield_signal,
        "reason": yield_reason
    })
            
    # 3. Market Cap (Stability)
    mkt_cap = info.get('marketCap', 0)
    mkt_signal = "Neutral"
    if mkt_cap > 100_000_000_000: # 1000億
        score += 1
        mkt_signal = "Bullish"
        mkt_reason = "大型權值股"
    else:
        mkt_reason = "中小型股"
        
    details.append({
        "metric": "市值 (Market Cap)",
        "value": f"{mkt_cap / 100000000:.1f} 億",
        "signal": mkt_signal,
        "reason": mkt_reason
    })
        
    # 4. Institutional Confidence (Longer term)
    inst_val = "N/A"
    inst_signal = "Neutral"
    inst_reason = "無資料"
    if inst_df is not None and not inst_df.empty:
        total_buy = inst_df['Foreign'].sum() + inst_df['Trust'].sum()
        inst_val = f"{total_buy:,}"
        if total_buy > 0:
            score += 1
            inst_signal = "Bullish"
            inst_reason = "近月法人買超"
        else:
            inst_reason = "近月法人賣超"
            
    details.append({
        "metric": "法人籌碼 (Chips)",
        "value": inst_val,
        "signal": inst_signal,
        "reason": inst_reason
    })

    # 5. Financial Health (Revenue & Margin)
    # Fetch quarterly financials if stock_obj provided
    fin_signal = "Neutral"
    fin_reason = "無資料"
    fin_value = "N/A"
    
    if stock_obj:
        try:
            q_fin = stock_obj.quarterly_financials
            if not q_fin.empty:
                # Revenue Growth (YoY for latest quarter)
                # Note: yfinance structure varies, this is a best effort
                if 'Total Revenue' in q_fin.index:
                    revs = q_fin.loc['Total Revenue']
                    if len(revs) >= 5: # Need same quarter last year
                        # Simple QoQ or YoY check
                        # Let's check Gross Margin Trend instead, it's often more reliable in structure
                        pass
                
                # Gross Margin Trend
                if 'Gross Profit' in q_fin.index and 'Total Revenue' in q_fin.index:
                    gp = q_fin.loc['Gross Profit'].iloc[0]
                    rev = q_fin.loc['Total Revenue'].iloc[0]
                    margin = (gp / rev) * 100
                    
                    # Previous quarter
                    gp_prev = q_fin.loc['Gross Profit'].iloc[1]
                    rev_prev = q_fin.loc['Total Revenue'].iloc[1]
                    margin_prev = (gp_prev / rev_prev) * 100
                    
                    fin_value = f"毛利: {margin:.1f}% (前季: {margin_prev:.1f}%)"
                    
                    if margin > margin_prev:
                        score += 1
                        fin_signal = "Bullish"
                        fin_reason = "毛利率提升"
                    else:
                        fin_reason = "毛利率持平/下滑"
        except Exception as e:
            print(f"Error fetching financials: {e}")
            
    details.append({
        "metric": "財報體質 (Financials)",
        "value": fin_value,
        "signal": fin_signal,
        "reason": fin_reason
    })

    # Final Verdict
    if score >= 5:
        return "Strong Buy", details, score, style
    elif score >= 3:
        return "Buy", details, score, style
    else:
        return "Wait", details, score, style

def determine_operation_style(df):
    """
    Determines suitable operation style based on volatility and volume.
    """
    if df is None or df.empty: return "N/A"
    
    # Metrics
    close = df['Close'].iloc[-1]
    high = df['High'].iloc[-1]
    low = df['Low'].iloc[-1]
    vol = df['Volume'].iloc[-1]
    vol_avg = df['Volume'].rolling(5).mean().iloc[-1]
    
    daily_range_pct = ((high - low) / close) * 100
    
    ma5 = df['MA5'].iloc[-1]
    ma20 = df['MA20'].iloc[-1]
    ma60 = df['MA60'].iloc[-1]
    
    # Logic
    # 1. Day Trading (High Volatility + Volume)
    if daily_range_pct > 2.5 and vol > 1.5 * vol_avg:
        return "⚡ 當沖/隔日沖 (Day Trading) - 波動大且爆量"
        
    # 2. Swing Trading (Trend Starting)
    if ma5 > ma20 and ma20 > ma60:
         return "🌊 短波段 (Swing Trading) - 多頭排列"
    if ma5 > ma20:
        return "🌊 短波段 (Swing Trading) - 短期轉強"
        
    # 3. Position Trading (Stable)
    if ma20 > ma60 and daily_range_pct < 2.0:
        return "🐢 中長線 (Position Trading) - 趨勢穩健"
        
    return "👀 觀望/區間操作 (Wait/Range)"

import concurrent.futures

def process_ticker(ticker, mode):
    """
    Helper function to process a single ticker for recommendation.
    """
    try:
        # Basic check to skip if data fails
        # Always fetch history now for trend check
        df, stock_obj = data_manager.fetch_stock_history(ticker, period="6mo")
        if df.empty: return None
        
        # Get Chinese Name
        ch_name = data_manager.get_stock_name(ticker)
        
        if mode == "Short-term":
            df = technical_analysis.add_technical_indicators(df)
            inst_df = data_manager.fetch_institutional_data_history(ticker, days=3) 
            
            signal, details, score, style = analyze_short_term(df, inst_df)
            
            # Convert details to simple reasons list for the card view
            reasons = [f"{d['metric']}: {d['reason']}" for d in details if d['signal'] in ['Bullish', 'Warning']]
            
            if score >= 3: 
                return {
                    "ticker": ticker,
                    "name": ch_name, # Use Chinese name
                    "signal": signal,
                    "score": score,
                    "reasons": reasons,
                    "price": df['Close'].iloc[-1],
                    "style": style
                }
                
        elif mode == "Long-term":
            info = data_manager.fetch_stock_info(ticker)
            if not info: return None
            
            inst_df = data_manager.fetch_institutional_data_history(ticker, days=10)
            
            # Pass stock_obj for financial data AND df for trend check
            signal, details, score, style = analyze_long_term(info, None, inst_df, stock_obj=stock_obj, df=df)
            
            reasons = [f"{d['metric']}: {d['reason']}" for d in details if d['signal'] in ['Bullish', 'Warning']]
            
            if score >= 4:
                return {
                    "ticker": ticker,
                    "name": ch_name, # Use Chinese name
                    "signal": signal,
                    "score": score,
                    "reasons": reasons,
                    "price": info.get('currentPrice', 0),
                    "style": style
                }

                
    except Exception as e:
        print(f"Skipping {ticker}: {e}")
        return None
    return None
