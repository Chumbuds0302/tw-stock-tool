# Taiwan Stock Analysis Tool (台股分析工具)

這是一個基於 Streamlit 的台股分析與推薦工具，支援上市 (.TW) 與上櫃 (.TWO) 股票。

## 功能特色

- **每日精選推薦**：自動掃描熱門股與 ETF，提供短線與長線推薦。
- **AI 智能診斷**：分析個股的技術面、籌碼面、基本面，並給予操作建議。
- **互動式圖表**：包含 K 線圖、均線、RSI、MACD、KD 等指標，支援畫圖功能。
- **完整數據**：整合 Yahoo Finance 歷史數據與證交所法人籌碼。
- **自動上櫃支援**：搜尋股票時會自動偵測上市/上櫃，無需手動指定後綴。

## 專案結構

```
stock_analysis_tool/
├── app.py                      # Streamlit 主程式 (UI & 邏輯控制)
├── data_manager.py             # 資料抓取模組 (Yahoo Finance + 證交所)
├── analysis_engine.py          # 分析引擎 (選股邏輯與評分)
├── technical_analysis.py       # 技術指標計算
├── fundamental_analysis.py     # 基本面指標格式化
├── tw_stocks.json              # 台股名稱與代碼對照表
├── requirements.txt            # Python 套件清單
├── run_app.bat                 # 本地啟動腳本 (Windows)
├── sync_updates.bat            # 同步更新至 GitHub 腳本
└── README.md                   # 本檔案
```

## 本地執行

### 方法 1：使用啟動腳本 (推薦)
雙擊 `run_app.bat`，瀏覽器會自動開啟 http://localhost:8501

### 方法 2：手動執行
```bash
pip install -r requirements.txt
streamlit run app.py
```

執行後，請在瀏覽器開啟：**http://localhost:8501**

## 搜尋股票說明

支援以下搜尋方式：
- **上市股票**：直接輸入代號 (例如：`2330`) 或名稱 (例如：`台積電`)
- **上櫃股票**：直接輸入代號 (例如：`4772`)，系統會自動偵測
- **手動指定**：可輸入完整代碼 `2330.TW` (上市) 或 `4772.TWO` (上櫃)

## 如何部署到 Streamlit Community Cloud (免費公開)

不需要使用 ngrok，Streamlit 官方提供免費的雲端託管服務。

### 步驟 1：上傳程式碼到 GitHub
1. 註冊/登入 [GitHub](https://github.com/)。
2. 建立一個新的 Repository (例如命名為 `tw-stock-tool`)。
3. 將此資料夾中的所有檔案上傳到該 Repository。
   - 確保包含 `requirements.txt`, `app.py`, `analysis_engine.py` 等所有 .py 檔案與 .json 檔案。

### 步驟 2：在 Streamlit Cloud 部署
1. 前往 [Streamlit Community Cloud](https://streamlit.io/cloud) 並使用 GitHub 帳號登入。
2. 點擊 **"New app"**。
3. 選擇剛才建立的 GitHub Repository。
4. 設定如下：
   - **Main file path**: `app.py`
5. 點擊 **"Deploy!"**。

### 步驟 3：完成
等待幾分鐘後，您的網站就會上線，並獲得一個公開的網址 (例如 `https://tw-stock-tool.streamlit.app`)，您可以分享給任何人使用。

## 如何即時更新網站 (How to Update)

當您請 Antigravity 修改完程式碼後，只需要執行以下步驟即可更新公開網站：

1. 在資料夾中找到 **`sync_updates.bat`** 檔案。
2. **點擊兩下**執行它。
3. 輸入更新備註 (例如 "update") 並按下 Enter。
4. 等待視窗跑完並自動關閉。
5. Streamlit Cloud 會在 **1-2 分鐘內** 自動偵測並更新您的網站。

## 自行修改指南

如果您想自行調整程式功能，請參考以下檔案：

| 目標 | 修改檔案 | 說明 |
| :--- | :--- | :--- |
| **增加掃描的股票清單** | `analysis_engine.py` | 修改 `TOP_STOCKS` 列表 |
| **調整買賣訊號標準** | `analysis_engine.py` | 修改 `analyze_short_term` 或 `analyze_long_term` 函數 |
| **修改網頁介面** | `app.py` | 調整 Streamlit UI 元件與排版 |
| **新增資料來源** | `data_manager.py` | 加入新的 API 或爬蟲邏輯 |
| **新增技術指標** | `technical_analysis.py` | 使用 `ta` 套件新增指標 |

## 技術說明

- **前端框架**：Streamlit
- **資料來源**：Yahoo Finance (yfinance) + 台灣證券交易所 (TWSE)
- **技術指標庫**：ta (Technical Analysis Library)
- **圖表視覺化**：Plotly
- **Python 版本**：3.8+

## 授權

本專案僅供學習與個人使用，資料來源為公開資訊，投資前請務必謹慎評估風險。
