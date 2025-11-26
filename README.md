# Taiwan Stock Analysis Tool (台股分析工具)

這是一個基於 Streamlit 的台股分析與推薦工具。

## 功能特色
- **每日精選推薦**：自動掃描熱門股與 ETF，提供短線與長線推薦。
- **AI 智能診斷**：分析個股的技術面、籌碼面、基本面，並給予操作建議。
- **互動式圖表**：包含 K 線圖、均線、RSI、MACD、KD 等指標，支援畫圖功能。
- **完整數據**：整合 Yahoo Finance 歷史數據與證交所法人籌碼。

## 如何部署到 Streamlit Community Cloud (免費公開)

不需要使用 ngrok，Streamlit 官方提供免費的雲端託管服務。

### 步驟 1：上傳程式碼到 GitHub
1.  註冊/登入 [GitHub](https://github.com/)。
2.  建立一個新的 Repository (例如命名為 `tw-stock-tool`)。
3.  將此資料夾中的所有檔案上傳到該 Repository。
    - 確保包含 `requirements.txt`, `app.py`, `analysis_engine.py` 等所有 .py 檔案與 .json 檔案。

### 步驟 2：在 Streamlit Cloud 部署
1.  前往 [Streamlit Community Cloud](https://streamlit.io/cloud) 並使用 GitHub 帳號登入。
2.  點擊 **"New app"**。
3.  選擇剛才建立的 GitHub Repository。
4.  設定如下：
    - **Main file path**: `app.py`
5.  點擊 **"Deploy!"**。

### 步驟 3：完成
等待幾分鐘後，您的網站就會上線，並獲得一個公開的網址 (例如 `https://tw-stock-tool.streamlit.app`)，您可以分享給任何人使用。

## 本地執行
```bash
pip install -r requirements.txt
streamlit run app.py
```

執行後，請在瀏覽器開啟：**http://localhost:8502**

## 如何即時更新網站 (How to Update)

當您請 Antigravity 修改完程式碼後，只需要執行以下步驟即可更新公開網站：

1.  在資料夾中找到 **`sync_updates.bat`** 檔案。
2.  **點擊兩下**執行它。
3.  輸入更新備註 (例如 "update") 並按下 Enter。
4.  等待視窗跑完並自動關閉。
5.  Streamlit Cloud 會在 **1-2 分鐘內** 自動偵測並更新您的網站。

