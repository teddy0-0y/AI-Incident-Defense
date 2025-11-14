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


## 📂 Key Files

* `README.md`: (This file) You are here.
* `generate_mapping.py`: **(Step 1)** Python script to call the Gemini API and generate defense mappings.
* `convert_to_json.py`: **(Step 2)** Python script to convert all CSVs into the JSON format required for the web.
* `index.html`: The main (and only) HTML file for the web interface.
* `app.js`: The frontend JavaScript logic that handles searching, data loading, and pop-up modals.
* `incidents.json`: (Generated) AI incident data for the website.
* `defenses.json`: (Generated) AIDEFEND catalog data for the website.
* `mapping.json`: (Generated) The LLM-generated mapping data.

## 🙏 Acknowledgements

* Incident data is sourced from the [AI Incident Database (AIID)](https://incidentdatabase.ai/).
* Defense techniques are sourced from the [AIDEFEND Framework](https://github.com/mitre-atlas/aidefend).
