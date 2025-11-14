import pandas as pd
import json
import os
from google import genai 
from google.genai import types 
import random  # Only used for fallback random ID when errors occur, preventing crashes

# --- 1. File settings and API client initialization ---
INCIDENTS_FILE = 'merged_incident_data.csv'
DEFENSES_FILE = 'AI_Defense_Techniques.csv'
OUTPUT_MAPPING_FILE = 'llm_defense_mapping.csv'
MODEL_NAME = "gemini-2.5-pro"  # Recommended model

# Initialize Gemini client
try:
    client = genai.Client()
    print("✅ Gemini client initialized successfully.")
except Exception as e:
    print(f"❌ Error: Failed to initialize Gemini client. Please check your GEMINI_API_KEY environment variable. Error: {e}")
    exit()

# --- 2. Prepare AIDEFEND defense knowledge base ---
try:
    defense_df = pd.read_csv(DEFENSES_FILE)
    defense_df.rename(columns={
        'Technique ID': 'defense_id',
        'Technique Name': 'name',
        'Description': 'description'
    }, inplace=True)
    
    # Create an LLM-friendly entry format (ID: Name - Truncated Description)
    defense_df['LLM_Entry'] = (
        defense_df['defense_id'] + ': ' +
        defense_df['name'] + ' - ' +
        defense_df['description'].fillna('').str.slice(0, 100).str.replace('\n', ' ') + '...'
    )
    
    DEFENSE_LIST_STR = "\n".join(defense_df['LLM_Entry'].tolist())
    DEFENSE_IDS = defense_df['defense_id'].tolist()
    print(f"✅ Loaded {len(DEFENSE_IDS)} defense techniques into LLM knowledge base.")

except FileNotFoundError:
    print(f"❌ Error: Defense list file not found: {DEFENSES_FILE}")
    exit()

# --- 3. Prompt structure for the LLM ---
def generate_llm_prompt(incident_data, defense_list):
    """Generate the LLM prompt using incident data and defense list."""
    
    prompt = f"""
    You are a top-tier AI security analyst. Your task is to analyze an AI incident and select 3 to 5 AIDEFEND defense technique IDs that are most relevant and effective at mitigating this incident.

    【Available AIDEFEND Defense List】
    You MUST strictly choose only from the IDs in this list. **Do NOT fabricate IDs**:
    {defense_list}

    【AI Incident Data】
    Incident ID: {incident_data['incident_id']}
    Title: {incident_data['incident_title']}
    Deployer / Developer: {incident_data['deployer']} / {incident_data['developer']}
    MITRE Risk Classification (reference only): {incident_data.get('mitre_classification', 'N/A')}

    Detailed Report (Core LLM Analysis Text):
    ---
    {incident_data['full_report_text']}
    ---

    【Task Requirements】
    1. Identify the core attack mechanism and affected AI components.
    2. Select 3 to 5 defense technique IDs from the list that best mitigate or prevent this incident.
    3. Output MUST be a pure JSON string.
    """
    return prompt

# --- 4. Gemini API call for defense matching ---
def call_llm_for_matching(incident_data, defense_list):
    """
    Perform matching using Gemini API.
    Returns parsed JSON results or an error placeholder.
    """
    prompt = generate_llm_prompt(incident_data, defense_list)
    
    # Define the JSON output schema
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
        
        # Safely parse the model's JSON output
        return json.loads(response.text)
        
    except Exception as e:
        # Capture all runtime errors (API timeout, JSON parse errors, etc.)
        print(f"   ❌ Failed to process incident {incident_data['incident_id']}: {e}")
        # Return placeholder to avoid stopping the pipeline
        return {"incident_id": incident_data['incident_id'], "matched_defense_ids": ["LLM_ERROR"]}

# --- 5. Main execution pipeline ---
try:
    incidents_df = pd.read_csv(INCIDENTS_FILE)
    incidents_df = incidents_df.fillna('')
except FileNotFoundError:
    print(f"❌ Error: Incident file not found: {INCIDENTS_FILE}")
    exit()

llm_results = []

# Test with first 30 incidents first (recommended for debugging)
incidents_to_process = incidents_df.head(30)
# After verifying correctness, replace with:
# incidents_to_process = incidents_df

print(f"\n--- Processing {len(incidents_to_process)} AI incidents (ensure API key is set) ---")

for index, row in incidents_to_process.iterrows():
    incident_data = row.to_dict()
    
    if index % 1 == 0:  # Print progress for every incident during testing
        print(f"\n-> Processing incident #{index} (ID: {incident_data['incident_id']})")

    match = call_llm_for_matching(incident_data, DEFENSE_LIST_STR)
    llm_results.append(match)

# 6. Save LLM mapping results
final_mapping_df = pd.DataFrame(llm_results)

# Convert ID list into comma-separated string
final_mapping_df['matched_defense_ids'] = final_mapping_df['matched_defense_ids'].apply(
    lambda x: ', '.join(x) if isinstance(x, list) else x
)

final_mapping_df.to_csv(OUTPUT_MAPPING_FILE, index=False)

print("\n--- LLM matching completed ---")
print(f"✅ Final mapping saved to '{OUTPUT_MAPPING_FILE}'.")
print("You may now integrate the results into your website.")
