# 台股 AI 決策支援系統

基於機器學習的台股分析工具，提供即時預測機率與回測摘要。

## 快速開始

```bash
pip install -r requirements.txt
streamlit run app.py
```

開啟瀏覽器前往：**http://localhost:8501**

---

## 更換模型路徑

如需使用不同的預測模型，請依照以下步驟修改：

### 修改位置

**檔案**：`app.py`  
**變數名稱**：`DEFAULT_MODEL_PATH`  
**位置**：檔案開頭（約第 14 行）

### 目前設定

```python
DEFAULT_MODEL_PATH = "models/rf_baseline.joblib"
```

### 修改範例

若您訓練了新模型並儲存為 `models/my_new_model.joblib`，請將該行修改為：

```python
DEFAULT_MODEL_PATH = "models/my_new_model.joblib"
```

儲存後重新啟動 Streamlit 即可套用新模型。

---

## 訓練新模型

使用 `model_trainer.py` 訓練新模型：

```python
import data_manager
import model_trainer

# 載入多檔股票資料
ohlcv_list = []
for ticker in ['2330.TW', '2317.TW', '2454.TW']:
    df, _ = data_manager.fetch_stock_history(ticker, period='2y')
    if not df.empty:
        ohlcv_list.append(df)

# 訓練並儲存模型
result = model_trainer.fit_from_pooled(
    ohlcv_list, 
    'models/my_new_model.joblib'
)
print(f"訓練結果：{result.get('metrics', {})}")
```

---

## 專案結構

```
stock_analysis_tool/
├── app.py                  # Streamlit 主程式
├── data_manager.py         # 資料抓取與快取
├── analysis_engine.py      # 分析引擎
├── feature_engineering.py  # 特徵工程
├── model_trainer.py        # 模型訓練
├── backtest_engine.py      # 回測引擎
├── models/                 # 模型儲存目錄
│   └── rf_baseline.joblib  # 預設模型
├── data/                   # 資料快取目錄
│   ├── universe.parquet    # 股票清單
│   └── ohlcv/              # OHLCV 快取
└── tw_stocks.json          # 台股代碼對照表
```

---

## 注意事項

⚠️ **投資警語**：本系統僅供參考，不構成投資建議。投資有風險，請審慎評估。
