import pandas as pd
import json
import os

# --- 原始 CSV 檔案名稱 ---
INCIDENTS_CSV = 'merged_incident_data.csv' 
DEFENSES_CSV = 'AI_Defense_Techniques.csv'
MAPPING_CSV = 'llm_defense_mapping.csv'

# --- 輸出 JSON 檔案名稱 ---
INCIDENTS_JSON = 'incidents.json'
DEFENSES_JSON = 'defenses.json'
MAPPING_JSON = 'mapping.json'

print("--- 開始執行最終的 CSV 轉 JSON 轉換 (包含重命名) ---")

def safe_convert_to_json(df, json_file):
    """
    使用 Python 的 json 模組將 DataFrame 安全地寫入 JSON 檔案。
    """
    try:
        # 將 DataFrame 轉換為 Python 字典列表
        records = df.to_dict(orient='records')
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=4)
            
        print(f"✅ 成功將數據轉換並儲存為 {json_file}")
    except Exception as e:
        print(f"❌ 轉換 {json_file} 時發生嚴重錯誤: {e}")

# --- 1. 處理事故數據 (incidents.json) ---
try:
    incident_df = pd.read_csv(INCIDENTS_CSV).fillna('')
    safe_convert_to_json(incident_df, INCIDENTS_JSON)
except FileNotFoundError:
    print(f"❌ 錯誤: 找不到 {INCIDENTS_CSV}")

# --- 2. 處理防禦清單 (defenses.json) ---
# 這是最關鍵的修正！
try:
    defense_df = pd.read_csv(DEFENSES_CSV)
    
    # 關鍵修正：重命名欄位以匹配 app.js 的期望
    defense_df.rename(columns={
        'Technique ID': 'defense_id', 
        'Technique Name': 'name',
        'Description': 'description',
        'Tactic': 'tactic'
    }, inplace=True)
    
    # 只保留網頁需要的欄位，並填充空值
    defense_df_clean = defense_df[['defense_id', 'name', 'description', 'tactic']].fillna('')
    
    safe_convert_to_json(defense_df_clean, DEFENSES_JSON)
except FileNotFoundError:
    print(f"❌ 錯誤: 找不到 {DEFENSES_CSV}")

# --- 3. 處理配對結果 (mapping.json) ---
try:
    mapping_df = pd.read_csv(MAPPING_CSV).fillna('')
    safe_convert_to_json(mapping_df, MAPPING_JSON)
except FileNotFoundError:
    print(f"❌ 錯誤: 找不到 {MAPPING_CSV}")

print("\n--- 轉換完成 ---")
print("所有 JSON 檔案已重新生成。請強制重新整理您的 http://localhost:8000 頁面。")