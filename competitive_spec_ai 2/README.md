# SpecCompare AI — 競品規格比較表產生器

## Mac 啟動

1. 解壓縮 ZIP，開啟 Terminal。
2. `cd` 進入解壓縮後的 `competitive_spec_ai` 資料夾（可以先輸入 `cd ` 再把資料夾拖入 Terminal）。
3. 執行：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

瀏覽器會開啟 `http://localhost:8501`。日後可直接執行 `source .venv/bin/activate && streamlit run streamlit_app.py`。也提供 `start_mac.command`，但 macOS 首次可能要求右鍵開啟。

## 使用

1. 上傳多份文字型 PDF（每份檔案最好對應一個產品或型號）。
2. 選擇模板並自訂欄位，確認產品名稱。
3. 選擇「本機規則」免付費測試，或「AI 語意擷取」並自行提供 OpenAI API Key（API 呼叫可能收費）。
4. 產生比較表，點選產品與規格查看證據及 PDF 頁面。
5. 人工校正後下載 Excel、CSV。

`samples/` 有三份虛構品牌的測試 PDF，可直接上傳。

## 支援與限制

- 完成：多 PDF、擷取、來源 PDF 頁碼、逐字引文檢查、AI 選用模式、比較表編輯、Excel 工作簿含註解與證據表、CSV。
- 尚未完成：OCR、DOCX/XLSX 匯入、公開 URL 抓取、PDF 文字高亮定位、多型號同 PDF 自動拆分、跨文件規格單位換算、版本管理、登入權限。
- **本機規則**基於文字層及欄位名稱，適用有明確 `Field: Value` 的文件；複雜表格可能漏擷取。
- **AI 模式**核對引文是否位於指定頁，但不保證引文中的值一定屬於正確產品型號；此項需人工核實。`verified` 僅表示證據原文存在，非第三方認證。
- 不要將機密或不被授權上傳的文件提交到外部 AI API。

## 執行測試

```bash
pytest -q
```
