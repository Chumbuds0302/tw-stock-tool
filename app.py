import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import data_manager
import technical_analysis
import fundamental_analysis
import datetime

# --- Page Config ---
st.set_page_config(page_title="TW Stock Analysis", layout="wide", page_icon="📈")

# --- Custom CSS for Premium Look ---
# Note: config.toml handles the base theme. We only add specific overrides here.
st.markdown("""
<style>
    /* Cards/Metrics */
    div[data-testid="metric-container"] {
        background-color: #21262d;
        border: 1px solid #30363d;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Tables */
    .stDataFrame {
        border: 1px solid #30363d;
        border-radius: 5px;
    }
    
    /* Buttons */
    .stButton>button {
        background-color: #238636;
        color: white !important;
        border-radius: 5px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #2ea043;
    }
    
    /* News Links */
    a.news-link {
        text-decoration: none;
        color: #58a6ff !important;
        font-weight: 500;
        display: block;
        padding: 10px;
        background: #161b22;
        border-radius: 5px;
        margin-bottom: 8px;
        border: 1px solid #30363d;
        transition: all 0.2s;
    }
    a.news-link:hover {
        background: #21262d;
        border-color: #58a6ff;
        transform: translateX(5px);
    }
</style>
""", unsafe_allow_html=True)

# --- Institutional Data Functions (moved here to avoid import caching) ---
@st.cache_data(ttl=3600) # Cache for 1 hour
def fetch_daily_institutional_data(date_str):
    """Fetches institutional data for a specific date from TWSE"""
    import requests
    url = f"https://www.twse.com.tw/rwd/zh/fund/T86?response=json&selectType=ALL&date={date_str}"
    try:
        res = requests.get(url, timeout=10)
        data = res.json()
        
        if data.get('stat') == 'OK':
            daily_data = {}
            for row in data['data']:
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

def get_multi_day_institutional_data(ticker, days=5):
    code = ticker.replace(".TW", "")
    if not code.isdigit():
        return None
        
    data_list = []
    current_date = datetime.date.today()
    attempts = 0
    max_attempts = days * 3
    
    while len(data_list) < days and attempts < max_attempts:
        date_str = current_date.strftime('%Y%m%d')
        daily_data = fetch_daily_institutional_data(date_str)
        
        if daily_data and code in daily_data:
            row = daily_data[code]
            data_list.append({
                "Date": current_date.strftime('%Y-%m-%d'),
                "Foreign": row['Foreign'],
                "Trust": row['Trust'],
                "Dealer": row['Dealer']
            })
        
        current_date -= datetime.timedelta(days=1)
        attempts += 1
        
    if not data_list:
        return None
        
    return pd.DataFrame(data_list[::-1])

import analysis_engine

# --- Sidebar ---
st.sidebar.title("📈 台股分析 (TW Stock)")
st.sidebar.markdown("---")

# Initialize session state for ticker if not exists
if 'ticker' not in st.session_state:
    st.session_state['ticker'] = "" # No default stock

# Initialize view state - Default to Recommendation View for speed
if 'show_recommendation' not in st.session_state:
    st.session_state['show_recommendation'] = True
if 'show_analysis' not in st.session_state:
    st.session_state['show_analysis'] = False

# Use session state for the input widget
ticker_input = st.sidebar.text_input("🔍 搜尋代號或名稱 (Search)", key='ticker_input', value=st.session_state['ticker'])

# Sync input back to ticker state if changed manually
if ticker_input != st.session_state['ticker']:
    st.session_state['ticker'] = ticker_input

period = st.sidebar.selectbox("📅 資料期間 (Period)", ["3mo", "6mo", "1y", "2y", "5y"], index=1)
mode = st.sidebar.radio("📊 分析模式 (Mode)", ["短期操作 (Short-term)", "長期投資 (Long-term)"])

st.sidebar.markdown("---")

# AI Advice Button (Current Stock)
if st.sidebar.button("🤖 智能診斷 (AI Analysis)"):
    if st.session_state['ticker']:
        st.session_state['show_analysis'] = True
        st.session_state['show_recommendation'] = False
    else:
        st.sidebar.warning("請先輸入股票代號")

# Recommendation Button (Screener)
if st.sidebar.button("🌟 每日精選推薦 (Daily Picks)"):
    st.session_state['show_recommendation'] = True
    st.session_state['show_analysis'] = False

st.sidebar.markdown("---")

# 1. Recommendation View
if st.session_state.get('show_recommendation', False):
    st.title("🌟 每日精選推薦 (Daily Picks)")
    st.markdown(f"針對 **{mode}** 策略，從熱門股中篩選出的潛力標的：")
    
    with st.spinner("正在掃描市場資料 (Scanning Market)... 這可能需要一點時間"):
        rec_mode = "Short-term" if "Short-term" in mode else "Long-term"
        picks = analysis_engine.get_stock_recommendations(rec_mode)
        
        if picks:
            for p in picks:
                with st.expander(f"🏆 {p['name']} ({p['ticker']}) - {p['signal']} (Score: {p['score']})"):
                    st.markdown(f"**股價 (Price):** {p['price']:.2f}")
                    st.markdown("**入選理由:**")
                    for r in p['reasons']:
                        st.markdown(f"- {r}")
                    if st.button(f"前往分析 {p['ticker']}", key=f"btn_{p['ticker']}"):
                        # Update ticker and switch view
                        st.session_state['ticker'] = p['ticker']
                        st.session_state['show_recommendation'] = False
                        st.session_state['show_analysis'] = True # Optional: Auto show analysis
                        st.rerun()
        else:
            st.warning("目前沒有符合高標準的推薦標的。")
            
    if st.button("返回分析 (Back)"):
        st.session_state['show_recommendation'] = False
        st.rerun()

# 2. Single Stock Analysis View
elif ticker_input:
    with st.spinner("正在獲取資料 (Fetching Data)..."):
        try:
            # 1. Fetch Basic Info & History
            df, stock = data_manager.fetch_stock_history(ticker_input, period)
            info = data_manager.fetch_stock_info(ticker_input)
            
            if df.empty:
                st.error("❌ 找不到資料，請檢查代號或名稱 (No data found).")
            else:
                # Header Section
                col1, col2 = st.columns([3, 1])
                with col1:
                    # Check if input was a name and show the resolved code
                    resolved_code = info.get('symbol', '').replace('.TW', '')
                    if ticker_input != resolved_code and not ticker_input.isdigit():
                         st.caption(f"🔍 已找到: {ticker_input} -> {resolved_code}")
                    
                    st.title(f"{info.get('longName', ticker_input)} ({info.get('symbol')})")
                    current_price = info.get('currentPrice', df['Close'].iloc[-1])
                    prev_close = info.get('previousClose', df['Close'].iloc[-2])
                    change = current_price - prev_close
                    pct_change = (change / prev_close) * 100
                    color = "red" if change > 0 else "green" # TW stock color: Red is up
                    st.markdown(f"<h2 style='color: {color};'>NT$ {current_price:.2f} <span style='font-size: 0.6em;'>({change:+.2f} / {pct_change:+.2f}%)</span></h2>", unsafe_allow_html=True)
                
                with col2:
                    # Clear drawings button moved here
                    if st.button("🗑️ 清除繪圖"):
                        st.rerun()
                    
                    st.markdown(f"**產業:** {info.get('industry', 'N/A')}")
                    st.markdown(f"**市值:** {info.get('marketCap', 0) / 100000000:.2f} 億")

                # AI Analysis Result Section
                if st.session_state.get('show_analysis', False):
                    st.markdown("---")
                    st.subheader("🤖 智能診斷報告 (AI Analysis Report)")
                    
                    # Prepare data for analysis
                    inst_df_short = get_multi_day_institutional_data(info.get('symbol', ticker_input), days=5)
                    inst_df_long = get_multi_day_institutional_data(info.get('symbol', ticker_input), days=10)
                    eps_df = data_manager.fetch_eps_data(stock)
                    
                    if "Short-term" in mode:
                        # Ensure indicators are calculated
                        df_tech = technical_analysis.add_technical_indicators(df.copy())
                        signal, details, score, style = analysis_engine.analyze_short_term(df_tech, inst_df_short)
                    else:
                        # Pass stock object for financial data AND df for trend check
                        signal, details, score, style = analysis_engine.analyze_long_term(info, eps_df, inst_df_long, stock_obj=stock, df=df)
                        
                    # Display Result
                    color_map = {"Strong Buy": "red", "Buy": "#ff4b4b", "Sell": "green", "Wait": "gray", "Neutral": "gray"}
                    signal_color = next((v for k, v in color_map.items() if k in signal), "white")
                    
                    st.markdown(f"### 評級: <span style='color:{signal_color}'>{signal}</span> (Score: {score})", unsafe_allow_html=True)
                    
                    # Display Operation Style Recommendation
                    st.info(f"💡 建議操作週期: **{style}**")
                    
                    # Create a DataFrame for the details
                    details_df = pd.DataFrame(details)
                    if not details_df.empty:
                        # Rename columns for display
                        details_df = details_df.rename(columns={
                            "metric": "檢測項目 (Metric)",
                            "value": "數值 (Value)",
                            "signal": "訊號 (Signal)",
                            "reason": "診斷 (Diagnosis)"
                        })
                        
                        # Apply some styling
                        st.table(details_df)
                    else:
                        st.write("無詳細分析資料。")
                    
                    st.markdown("---")

                st.markdown("---")

                # --- Short-term Mode ---
                if mode == "短期操作 (Short-term)":
                    st.subheader("⚡ 短期技術分析 (Technical Analysis)")
                    
                    # Market Indices (Reference)
                    st.markdown("##### 參考指數 (Market Indices)")
                    idx_col1, idx_col2 = st.columns(2)
                    try:
                        taiex_df, _ = data_manager.fetch_stock_history("^TWII", "5d")
                        otc_df, _ = data_manager.fetch_stock_history("^TWO", "5d")
                        
                        with idx_col1:
                            if not taiex_df.empty:
                                t_price = taiex_df['Close'].iloc[-1]
                                t_change = t_price - taiex_df['Close'].iloc[-2]
                                t_color = "red" if t_change > 0 else "green"
                                st.metric("加權指數 (TAIEX)", f"{t_price:.2f}", f"{t_change:+.2f}")
                        with idx_col2:
                            if not otc_df.empty:
                                o_price = otc_df['Close'].iloc[-1]
                                o_change = o_price - otc_df['Close'].iloc[-2]
                                o_color = "red" if o_change > 0 else "green"
                                st.metric("櫃買指數 (OTC)", f"{o_price:.2f}", f"{o_change:+.2f}")
                    except:
                        st.warning("無法獲取大盤指數 (Failed to fetch indices).")

                    # Technical Indicators Calculation
                    df = technical_analysis.add_technical_indicators(df)

                    # Main Chart (Price + MA + BB + Volume)
                    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                        vertical_spacing=0.05, row_heights=[0.7, 0.3])

                    # Candlestick
                    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'],
                                                 low=df['Low'], close=df['Close'], name='OHLC'), row=1, col=1)
                    
                    # MAs
                    fig.add_trace(go.Scatter(x=df.index, y=df['MA5'], line=dict(color='orange', width=1), name='MA5'), row=1, col=1)
                    fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='purple', width=1), name='MA20'), row=1, col=1)
                    fig.add_trace(go.Scatter(x=df.index, y=df['MA60'], line=dict(color='blue', width=1), name='MA60'), row=1, col=1)
                    
                    # BB
                    fig.add_trace(go.Scatter(x=df.index, y=df['BB_High'], line=dict(color='gray', width=1, dash='dot'), name='BB High'), row=1, col=1)
                    fig.add_trace(go.Scatter(x=df.index, y=df['BB_Low'], line=dict(color='gray', width=1, dash='dot'), name='BB Low'), row=1, col=1)

                    # Volume
                    colors = ['red' if row['Open'] < row['Close'] else 'green' for index, row in df.iterrows()]
                    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name='Volume'), row=2, col=1)

                    fig.update_layout(
                        height=800,  # Increased from 600
                        template="plotly_dark", 
                        margin=dict(l=0, r=0, t=30, b=0),
                        dragmode='pan'
                    )
                    fig.update_xaxes(rangeslider_visible=False)
                    st.plotly_chart(fig, use_container_width=True, config={
                        'scrollZoom': True,
                        'displayModeBar': True,
                        'displaylogo': False,
                        'modeBarButtonsToAdd': [
                            'drawline',
                            'drawopenpath',
                            'drawrect',
                            'drawcircle',
                            'eraseshape'
                        ]
                    })

                    # Sub-indicators (RSI, MACD, KD)
                    st.markdown("##### 技術指標 (Indicators)")
                    tab1, tab2, tab3 = st.tabs(["RSI", "MACD", "KD"])
                    
                    with tab1:
                        fig_rsi = go.Figure(go.Scatter(x=df.index, y=df['RSI'], name='RSI', line=dict(color='#ab63fa')))
                        fig_rsi.add_hline(y=70, line_dash="dash", line_color="red")
                        fig_rsi.add_hline(y=30, line_dash="dash", line_color="green")
                        fig_rsi.update_layout(
                            height=400,  # Increased from 300
                            template="plotly_dark", 
                            margin=dict(l=0, r=0, t=10, b=0), 
                            title="RSI (14)",
                            dragmode='pan'
                        )
                        st.plotly_chart(fig_rsi, use_container_width=True, config={
                            'scrollZoom': True, 
                            'displaylogo': False,
                            'modeBarButtonsToAdd': ['drawline', 'drawopenpath', 'drawrect', 'eraseshape']
                        })
                        
                    with tab2:
                        fig_macd = make_subplots(specs=[[{"secondary_y": False}]])
                        fig_macd.add_trace(go.Scatter(x=df.index, y=df['MACD'], name='MACD', line=dict(color='#00CC96')), secondary_y=False)
                        fig_macd.add_trace(go.Scatter(x=df.index, y=df['MACD_Signal'], name='Signal', line=dict(color='#EF553B')), secondary_y=False)
                        fig_macd.add_trace(go.Bar(x=df.index, y=df['MACD_Diff'], name='Hist', marker_color='gray'), secondary_y=False)
                        fig_macd.update_layout(
                            height=400,  # Increased from 300
                            template="plotly_dark", 
                            margin=dict(l=0, r=0, t=10, b=0), 
                            title="MACD",
                            dragmode='pan'
                        )
                        st.plotly_chart(fig_macd, use_container_width=True, config={
                            'scrollZoom': True, 
                            'displaylogo': False,
                            'modeBarButtonsToAdd': ['drawline', 'drawopenpath', 'drawrect', 'eraseshape']
                        })

                    with tab3:
                        fig_kd = go.Figure()
                        fig_kd.add_trace(go.Scatter(x=df.index, y=df['K'], name='K', line=dict(color='#FFA15A')))
                        fig_kd.add_trace(go.Scatter(x=df.index, y=df['D'], name='D', line=dict(color='#19D3F3')))
                        fig_kd.add_hline(y=80, line_dash="dash", line_color="red")
                        fig_kd.add_hline(y=20, line_dash="dash", line_color="green")
                        fig_kd.update_layout(
                            height=400,  # Increased from 300
                            template="plotly_dark", 
                            margin=dict(l=0, r=0, t=10, b=0), 
                            title="KD (Stochastic)",
                            dragmode='pan'
                        )
                        st.plotly_chart(fig_kd, use_container_width=True, config={
                            'scrollZoom': True, 
                            'displaylogo': False,
                            'modeBarButtonsToAdd': ['drawline', 'drawopenpath', 'drawrect', 'eraseshape']
                        })

                # --- Long-term Mode ---
                elif mode == "長期投資 (Long-term)":
                    st.subheader("💎 長期投資分析 (Fundamental Analysis)")
                    
                    # Price Chart for Long-term (Simple Line/Candle)
                    st.markdown("##### 股價走勢 (Price Trend)")
                    fig_lt = go.Figure()
                    fig_lt.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'],
                                                 low=df['Low'], close=df['Close'], name='OHLC'))
                    fig_lt.update_layout(
                        height=500, 
                        template="plotly_dark", 
                        margin=dict(l=0, r=0, t=10, b=0),
                        dragmode='pan',
                        title_text=f"{ticker_input} - {period}"
                    )
                    fig_lt.update_xaxes(rangeslider_visible=False)
                    st.plotly_chart(fig_lt, use_container_width=True, config={'scrollZoom': True, 'displaylogo': False})

                    # Fundamental Metrics
                    metrics = fundamental_analysis.get_fundamental_metrics(info)
                    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
                    m_col1.metric("本益比 (P/E)", metrics.get("P/E Ratio", "N/A"))
                    m_col2.metric("殖利率 (Yield)", metrics.get("Dividend Yield", "N/A"))
                    m_col3.metric("ROE", metrics.get("ROE", "N/A"))
                    m_col4.metric("股價淨值比 (P/B)", info.get('priceToBook', 'N/A'))

                    # Institutional Data
                    st.markdown("### 🏛️ 三大法人動態 (Institutional Investors - Last 10 Days)")
                    
                    # Use the new cached function in app.py
                    inst_df = get_multi_day_institutional_data(info.get('symbol', ticker_input), days=10)
                    
                    if inst_df is not None and not inst_df.empty:
                        # Create a stacked bar chart or grouped bar chart
                        fig_inst = go.Figure()
                        fig_inst.add_trace(go.Bar(x=inst_df['Date'], y=inst_df['Foreign'], name='外資 (Foreign)'))
                        fig_inst.add_trace(go.Bar(x=inst_df['Date'], y=inst_df['Trust'], name='投信 (Trust)'))
                        fig_inst.add_trace(go.Bar(x=inst_df['Date'], y=inst_df['Dealer'], name='自營商 (Dealer)'))
                        
                        fig_inst.update_layout(
                            barmode='group', 
                            template="plotly_dark", 
                            height=400,
                            title="Institutional Net Buy/Sell (Shares)"
                        )
                        st.plotly_chart(fig_inst, use_container_width=True)
                        
                        # Show data table
                        st.dataframe(inst_df.style.format({
                            "Foreign": "{:,}",
                            "Trust": "{:,}",
                            "Dealer": "{:,}"
                        }))
                    else:
                        st.info("查無近期法人資料 (No recent institutional data found).")

                    # EPS Chart
                    st.markdown("### 💰 每股盈餘 (Quarterly EPS - Last 2 Years)")
                    eps_df = data_manager.fetch_eps_data(stock)
                    if eps_df is not None and not eps_df.empty:
                        # Data is already sorted from fetch_eps_data
                        eps_df['Date'] = pd.to_datetime(eps_df['Date'])
                        
                        fig_eps = go.Figure(go.Bar(
                            x=eps_df['Date'].dt.strftime('%Y Q%q'), 
                            y=eps_df['EPS'],
                            text=eps_df['EPS'].round(2),
                            textposition='auto',
                            marker_color='#238636'
                        ))
                        fig_eps.update_layout(template="plotly_dark", height=400, title="Quarterly EPS (Last 8 Quarters)")
                        st.plotly_chart(fig_eps, use_container_width=True)
                    else:
                        st.info("查無 EPS 資料 (No EPS data found).")

                    # News Section
                    st.markdown("### 📰 最新消息 (Latest News)")
                    news = data_manager.fetch_news(stock)
                    if news:
                        for n in news[:5]:
                            st.markdown(f"<a href='{n['link']}' target='_blank' class='news-link'>{n['title']}</a>", unsafe_allow_html=True)
                    else:
                        st.info("查無相關新聞 (No news found).")

        except Exception as e:
            st.error(f"發生錯誤 (Error): {e}")
else:
    st.info("👈 請在左側輸入代號並點擊「開始分析」 (Please enter ticker and click Analyze).")
