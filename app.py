"""
app.py - 台股 AI 決策支援系統

訊號儀表板：即時預測機率與回測摘要
"""

import streamlit as st
import pandas as pd
from pathlib import Path

import data_manager
import analysis_engine

# --- 模型路徑設定 (如需更換模型請修改此處) ---
DEFAULT_MODEL_PATH = "models/rf_baseline.joblib"

# --- 頁面設定 ---
st.set_page_config(page_title="台股 AI 決策系統", layout="wide", page_icon="📊")

# --- UI 文字常數 ---
UI_TEXT = {
    # 標題
    "app_title": "📊 訊號儀表板",
    "sidebar_title": "📊 台股 AI 決策系統",
    
    # 側邊欄
    "ticker_label": "🔍 輸入股票代號或名稱",
    "period_label": "📅 資料期間",
    "admin_section": "管理工具",
    "build_universe": "建立股票清單",
    "clear_cache": "清除快取",
    "universe_built": "已建立 {count} 檔股票",
    "cache_cleared": "快取已清除",
    
    # 模型狀態
    "model_loaded": "✅ 模型已載入",
    "model_not_found": "⚠️ 尚未載入模型，將以 0.50 顯示（請依 README 修改模型路徑）",
    
    # 儀表板
    "using_model": "🤖 使用 AI 模型預測",
    "fallback_mode": "📊 預設模式（尚未載入模型）",
    "last_close": "最新收盤價",
    "direction": "方向",
    "prob_up": "上漲機率",
    "confidence": "信心分數",
    
    # 關鍵指標
    "key_metrics": "📈 關鍵指標",
    "return_1d": "1日報酬率",
    "return_5d": "5日報酬率",
    "volatility_20d": "20日波動率",
    "volume_ratio": "量能比",
    "no_data": "無資料",
    
    # 回測
    "backtest_title": "📊 回測摘要（近一年）",
    "total_return": "總報酬",
    "win_rate": "勝率",
    "max_drawdown": "最大回撤",
    "trades": "交易次數",
    "backtest_error": "回測錯誤：{error}",
    "backtest_no_model": "📈 請載入模型以查看回測結果",
    "backtest_no_data": "資料不足，無法進行回測",
    
    # 圖表
    "chart_title": "📉 收盤價走勢",
    
    # 資料預覽
    "data_preview": "📋 資料預覽（近 20 筆）",
    
    # 錯誤訊息
    "error_no_data": "❌ 找不到此代號/名稱，請重新輸入",
    "error_general": "❌ 發生錯誤：{error}",
    "input_hint": "👆 請在左側輸入股票代號或名稱開始查詢",
    
    # 警語
    "disclaimer": "⚠️ 投資警語：本系統僅供參考，不構成投資建議。投資有風險，請審慎評估。"
}

# --- 啟動：檢查股票清單 ---
@st.cache_resource
def ensure_universe():
    """首次啟動時自動建立股票清單"""
    if not data_manager.UNIVERSE_PATH.exists():
        try:
            data_manager.build_universe()
            return True, "股票清單已建立"
        except Exception as e:
            return False, f"無法建立股票清單：{e}"
    return True, "股票清單已載入"

universe_ok, universe_msg = ensure_universe()
if not universe_ok:
    st.warning(f"⚠️ {universe_msg}")

# --- 檢查模型是否存在 ---
model_path = DEFAULT_MODEL_PATH
model_exists = Path(model_path).exists()

# --- 側邊欄 ---
st.sidebar.title(UI_TEXT["sidebar_title"])
st.sidebar.markdown("---")

# 股票代號輸入
ticker_input = st.sidebar.text_input(UI_TEXT["ticker_label"], value="2330")

# 資料期間選擇
period = st.sidebar.selectbox(UI_TEXT["period_label"], ["3mo", "6mo", "1y", "2y", "5y"], index=1)

st.sidebar.markdown("---")

# 模型狀態顯示
if model_exists:
    st.sidebar.success(UI_TEXT["model_loaded"])
else:
    st.sidebar.warning(UI_TEXT["model_not_found"])

st.sidebar.markdown("---")

# 管理工具
st.sidebar.caption(UI_TEXT["admin_section"])
col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button(UI_TEXT["build_universe"], use_container_width=True):
        with st.spinner("建立中..."):
            try:
                df = data_manager.build_universe()
                st.sidebar.success(UI_TEXT["universe_built"].format(count=len(df)))
            except Exception as e:
                st.sidebar.error(str(e))

with col2:
    if st.button(UI_TEXT["clear_cache"], use_container_width=True):
        st.cache_data.clear()
        analysis_engine.load_model_cached.cache_clear()
        st.sidebar.success(UI_TEXT["cache_cleared"])

# 投資警語
st.sidebar.markdown("---")
st.sidebar.caption(UI_TEXT["disclaimer"])

# --- 主畫面 ---
st.title(UI_TEXT["app_title"])

if ticker_input:
    try:
        # 取得訊號快照
        snapshot, ohlcv_df, info = analysis_engine.get_signal_snapshot(
            ticker_input, 
            period=period,
            model_path=model_path if model_exists else None
        )
        
        if ohlcv_df.empty:
            st.error(UI_TEXT["error_no_data"])
        else:
            # --- 標題 ---
            st.subheader(f"{snapshot.name} ({snapshot.ticker})")
            
            # 模型狀態
            if snapshot.model_used:
                st.caption(UI_TEXT["using_model"])
            else:
                st.caption(UI_TEXT["fallback_mode"])
            
            # --- 訊號儀表板 ---
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    label=UI_TEXT["last_close"],
                    value=f"${snapshot.last_close:,.2f}"
                )
            
            with col2:
                direction_map = {"UP": "🟢 偏多", "DOWN": "🔴 偏空"}
                direction_text = direction_map.get(snapshot.direction, "⚪ 中性")
                st.metric(
                    label=UI_TEXT["direction"],
                    value=direction_text
                )
            
            with col3:
                st.metric(
                    label=UI_TEXT["prob_up"],
                    value=f"{snapshot.prob_up:.1%}"
                )
            
            with col4:
                conf_pct = snapshot.confidence * 100
                st.metric(
                    label=UI_TEXT["confidence"],
                    value=f"{conf_pct:.1f}%"
                )
            
            # 信心分數進度條
            st.progress(snapshot.confidence)
            
            st.markdown("---")
            
            # --- 關鍵指標 ---
            st.subheader(UI_TEXT["key_metrics"])
            
            metrics = snapshot.key_metrics
            mcol1, mcol2, mcol3, mcol4 = st.columns(4)
            
            with mcol1:
                val = metrics.get("return_1d")
                st.metric(
                    label=UI_TEXT["return_1d"],
                    value=f"{val:.2f}%" if val is not None else UI_TEXT["no_data"],
                    delta=f"{val:.2f}%" if val is not None else None
                )
            
            with mcol2:
                val = metrics.get("return_5d")
                st.metric(
                    label=UI_TEXT["return_5d"],
                    value=f"{val:.2f}%" if val is not None else UI_TEXT["no_data"]
                )
            
            with mcol3:
                val = metrics.get("volatility_20d")
                st.metric(
                    label=UI_TEXT["volatility_20d"],
                    value=f"{val:.2f}%" if val is not None else UI_TEXT["no_data"]
                )
            
            with mcol4:
                val = metrics.get("volume_ratio_20d")
                st.metric(
                    label=UI_TEXT["volume_ratio"],
                    value=f"{val:.2f}x" if val is not None else UI_TEXT["no_data"]
                )
            
            st.markdown("---")
            
            # --- 回測摘要 ---
            st.subheader(UI_TEXT["backtest_title"])
            
            if model_exists:
                try:
                    import backtest_engine
                    
                    # 取得近一年資料
                    ohlcv_1y, _ = data_manager.fetch_stock_history(ticker_input, period="1y")
                    
                    if not ohlcv_1y.empty:
                        payload = analysis_engine.load_model_cached(model_path)
                        
                        if payload:
                            bt_result = backtest_engine.run_backtest(
                                ohlcv_1y, payload, 
                                buy_threshold=0.60, sell_threshold=0.40
                            )
                            
                            if bt_result.get('error'):
                                st.warning(UI_TEXT["backtest_error"].format(error=bt_result['error']))
                            else:
                                bcol1, bcol2, bcol3, bcol4 = st.columns(4)
                                
                                with bcol1:
                                    ret = bt_result['total_return']
                                    st.metric(
                                        label=UI_TEXT["total_return"],
                                        value=f"{ret:.2f}%",
                                        delta=f"{ret:.2f}%"
                                    )
                                
                                with bcol2:
                                    st.metric(
                                        label=UI_TEXT["win_rate"],
                                        value=f"{bt_result['win_rate']:.1f}%"
                                    )
                                
                                with bcol3:
                                    st.metric(
                                        label=UI_TEXT["max_drawdown"],
                                        value=f"{bt_result['max_drawdown']:.2f}%"
                                    )
                                
                                with bcol4:
                                    st.metric(
                                        label=UI_TEXT["trades"],
                                        value=bt_result['num_trades']
                                    )
                        else:
                            st.info("模型載入失敗，已改用預設值")
                    else:
                        st.info(UI_TEXT["backtest_no_data"])
                        
                except Exception as e:
                    st.warning(UI_TEXT["backtest_error"].format(error=str(e)))
            else:
                st.info(UI_TEXT["backtest_no_model"])
            
            st.markdown("---")
            
            # --- 收盤價走勢圖 ---
            st.subheader(UI_TEXT["chart_title"])
            
            chart_df = ohlcv_df[['Close']].copy()
            chart_df.index = pd.to_datetime(chart_df.index)
            
            st.line_chart(chart_df)
            
            st.markdown("---")
            
            # --- 資料預覽 ---
            st.subheader(UI_TEXT["data_preview"])
            
            preview_df = ohlcv_df.tail(20).copy()
            preview_df.index = preview_df.index.strftime('%Y-%m-%d')
            preview_df = preview_df.round(2)
            preview_df.columns = ['開盤', '最高', '最低', '收盤', '成交量']
            
            st.dataframe(preview_df, use_container_width=True)
            
    except Exception as e:
        st.error(UI_TEXT["error_general"].format(error=str(e)))

else:
    st.info(UI_TEXT["input_hint"])
