import pandas as pd
import json
import os
from google import genai 
from google.genai import types 
import random # 僅用於錯誤時返回隨機 ID，確保程式不中斷

# --- 1. 設定檔案名稱與 API 客戶端 ---
INCIDENTS_FILE = 'merged_incident_data.csv'
DEFENSES_FILE = 'AI_Defense_Techniques.csv'
OUTPUT_MAPPING_FILE = 'llm_defense_mapping.csv'
MODEL_NAME = "gemini-2.5-pro"  # 推薦使用 Pro 模型

# 初始化客戶端
try:
    client = genai.Client()
    print("✅ Gemini 客戶端初始化成功。")
except Exception as e:
    print(f"❌ 錯誤：初始化 Gemini 客戶端失敗。請檢查您的 GEMINI_API_KEY 環境變數。錯誤: {e}")
    exit()

# --- 2. 準備 AIDEFEND 防禦知識庫 ---
try:
    defense_df = pd.read_csv(DEFENSES_FILE)
    defense_df.rename(columns={'Technique ID': 'defense_id', 
                              'Technique Name': 'name',
                              'Description': 'description'}, inplace=True)
    
    # 建立 LLM 易讀的清單 (ID: Name - Description 截斷)
    defense_df['LLM_Entry'] = (
        defense_df['defense_id'] + ': ' + 
        defense_df['name'] + ' - ' + 
        defense_df['description'].fillna('').str.slice(0, 100).str.replace('\n', ' ') + '...'
    )
    DEFENSE_LIST_STR = "\n".join(defense_df['LLM_Entry'].tolist())
    DEFENSE_IDS = defense_df['defense_id'].tolist()
    print(f"✅ 已載入 {len(DEFENSE_IDS)} 條防禦措施作為 LLM 知識庫。")

except FileNotFoundError:
    print(f"❌ 錯誤：找不到防禦清單檔案 {DEFENSES_FILE}。")
    exit()

# --- 3. LLM Prompt 結構 ---
def generate_llm_prompt(incident_data, defense_list):
    """根據事件數據和防禦清單生成 LLM 提示詞"""
    
    prompt = f"""
    你是一位頂尖的 AI 安全分析師。你的任務是分析一則 AI 事故，並從提供的 AIDEFEND 防禦框架清單中，選出 3 到 5 個最相關、最能有效防禦此類事故的技術 ID。

    【可選 AIDEFEND 防禦清單】
    請**嚴格只從**以下清單的 ID 中選擇，**不要捏造**：
    {defense_list}

    【AI 事故數據分析】
    事件 ID: {incident_data['incident_id']}
    事件標題: {incident_data['incident_title']}
    部署者/開發者: {incident_data['deployer']} / {incident_data['developer']}
    MITRE 風險分類 (供參考): {incident_data.get('mitre_classification', 'N/A')}

    事件詳細報告 (LLM 分析的核心文本):
    ---
    {incident_data['full_report_text']}
    ---

    【任務要求】
    1. 識別事故的核心攻擊手法和受影響的 AI 元件。
    2. 從清單中選出 3 到 5 個最能減輕或預防此類事件的防禦措施 ID。
    3. 輸出必須是純 JSON 格式的字串。
    """
    return prompt

# --- 4. 替換此函數為您的實際 LLM API 調用 ---
def call_llm_for_matching(incident_data, defense_list):
    """
    使用 Gemini API 進行防禦配對。
    """
    prompt = generate_llm_prompt(incident_data, defense_list)
    
    # 定義輸出的 JSON 結構 (Schema)
    response_schema = types.Schema(
        type=types.Type.OBJECT,
        properties={
            "incident_id": types.Schema(type=types.Type.INTEGER),
            "matched_defense_ids": types.Schema(
                type=types.Type.ARRAY, 
                description="List of 3 to 5 matching AIDEFEND Technique IDs.",
                items=types.Schema(type=types.Type.STRING)
            ),
        }
    )

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=response_schema
            )
        )
        
        # 嘗試安全地解析模型的輸出文本
        return json.loads(response.text)
        
    except Exception as e:
        # 捕獲 API 錯誤、JSON 解析錯誤等
        print(f"   ❌ 處理事故 {incident_data['incident_id']} 失敗: {e}")
        # 返回一個錯誤標記，確保程式不崩潰
        return {"incident_id": incident_data['incident_id'], "matched_defense_ids": ["LLM_ERROR"]}

# --- 5. 主執行流程 ---
try:
    incidents_df = pd.read_csv(INCIDENTS_FILE)
    incidents_df = incidents_df.fillna('') 
except FileNotFoundError:
    print(f"❌ 錯誤：找不到事故清單檔案 {INCIDENTS_FILE}。")
    exit()

llm_results = []
# 建議先測試前 10 筆數據，以確認 API 和 Prompt 正確無誤
incidents_to_process = incidents_df.head(30) 
# 當您確認無誤後，將上一行替換為下一行來處理所有數據
# incidents_to_process = incidents_df 

print(f"\n--- 開始處理 {len(incidents_to_process)} 筆 AI 事故 (請確認您已設定好 API Key) ---")

for index, row in incidents_to_process.iterrows():
    incident_data = row.to_dict()
    
    if index % 1 == 0: # 每處理 1 筆打印進度 (測試階段)
        print(f"\n-> 處理中: 第 {index} 筆事故 (ID: {incident_data['incident_id']})")

    match = call_llm_for_matching(incident_data, DEFENSE_LIST_STR)
    llm_results.append(match)

# 6. 儲存 LLM 配對結果
final_mapping_df = pd.DataFrame(llm_results)

# 將 matched_defense_ids 列表轉換為逗號分隔的字串
final_mapping_df['matched_defense_ids'] = final_mapping_df['matched_defense_ids'].apply(lambda x: ', '.join(x) if isinstance(x, list) else x)

final_mapping_df.to_csv(OUTPUT_MAPPING_FILE, index=False)

print("\n--- LLM 配對結果已完成 ---")
print(f"✅ 最終配對結果已儲存到 '{OUTPUT_MAPPING_FILE}'。")
print(f"請檢查該檔案並開始您的網頁整合工作。")