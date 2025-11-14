# AI Incident Database with LLM-Powered Defense Mapping

This project is a web-based tool that provides a searchable database of AI incidents, enriched with automated security defense mapping. Using a Large Language Model (Google's Gemini), this tool analyzes each incident report and suggests relevant mitigation and defense techniques from the **AIDEFEND framework**.

This provides a powerful interface for security researchers, developers, and policymakers to understand AI risks and discover corresponding, actionable defenses.

## ✨ Features

* **Searchable Database:** Instantly search and filter thousands of AI incidents by title, report text, or MITRE classification.
* **Automated LLM Mapping:** Each incident is programmatically analyzed by the Gemini LLM to generate a list of relevant AIDEFEND defense techniques.
* **Interactive Interface:** Click an incident to see its full details, including the report summary and the LLM-suggested defenses.
* **Dynamic Defense Details:** Click any suggested defense card to view its full description and Tactic from the AIDEFEND catalog in a pop-up modal.

## 📊 Data Pipeline

The core of this project is its data pipeline, which processes raw data into a fully interactive web application.



1.  **Ingestion:** Raw incident data (from the AIID) and defense data (from AIDEFEND) are ingested as CSV files.
2.  **LLM Mapping:** A Python script (`generate_mapping.py`) iterates through each incident, sends the report text to the Gemini API, and receives a list of suggested defense IDs. This result is saved as `llm_defense_mapping.csv`.
3.  **JSON Conversion:** A second Python script (`convert_to_json.py`) cleans and formats all three CSV files (incidents, defenses, and the new mapping) into clean JSON files. This step is crucial for the web frontend.
4.  **Frontend Hydration:** The `index.html` and `app.js` files load these three JSON files to create the dynamic, searchable database interface in your browser.

## 🛠️ Tech Stack

* **Data Processing:** Python, Pandas
* **AI / LLM:** Google Gemini Pro (via the `google-genai` SDK)
* **Frontend:** HTML5, CSS3, Vanilla JavaScript
* **Local Server:** Python's built-in `http.server` module


## 📂 Key Files (核心檔案)

* `README.md`: (This file) 您正在閱讀的檔案。
* `generate_mapping.py`: **(第一步)** 用於呼叫 Gemini API 並生成防禦配對的 Python 腳本。
* `convert_to_json.py`: **(第二步)** 用於將所有 CSV 轉換為網頁所需 JSON 格式的 Python 腳本。
* `index.html`: 網頁介面的主要 (也是唯一) HTML 檔案。
* `app.js`: 處理搜尋、數據載入和彈窗功能的 前端 JavaScript 邏輯。
* `incidents.json`: (由腳本生成) 用於網頁的 AI 事故數據。
* `defenses.json`: (由腳本生成) 用於網頁的 AIDEFEND 防禦清單數據。
* `mapping.json`: (由腳本生成) LLM 產生的事故與防禦配對數據。

## 🙏 Acknowledgements (致謝)

* 事故數據來源於 [AI Incident Database (AIID)](https://incidentdatabase.ai/)。
* 防禦技術框架來源於 [AIDEFEND Framework](https://github.com/mitre-atlas/aidefend)。
