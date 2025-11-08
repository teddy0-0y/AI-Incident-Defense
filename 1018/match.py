import pandas as pd
import json
import os
from google import genai 
from google.genai import types 

# 設置模型名稱
MODEL_NAME = "gemini-2.5-pro"  # 推薦使用 Pro 模型以獲得最佳的分類精度和遵循 JSON 格式的能力

# 初始化客戶端 (它會自動尋找您的 GEMINI_API_KEY 環境變數)
try:
    client = genai.Client()
except Exception as e:
    print(f"初始化 Gemini 客戶端失敗: {e}")
    # ... 處理錯誤 ...


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

    # 進行 API 呼叫
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            # 要求模型以結構化 JSON 格式輸出
            response_mime_type="application/json",
            response_schema=response_schema
        )
    )

    # 嘗試安全地解析模型的輸出文本
    try:
        return json.loads(response.text)
    except Exception as e:
        print(f"API 響應解析失敗，返回原始文本：{response.text}")
        # 如果模型返回了無效 JSON，則返回錯誤標記
        return {"incident_id": incident_data['incident_id'], "matched_defense_ids": ["JSON_PARSE_ERROR"]}