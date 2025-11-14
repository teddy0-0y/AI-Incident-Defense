import pandas as pd
import json
import os

# --- Original CSV file names ---
INCIDENTS_CSV = 'merged_incident_data.csv'
DEFENSES_CSV = 'AI_Defense_Techniques.csv'
MAPPING_CSV = 'llm_defense_mapping.csv'

# --- Output JSON file names ---
INCIDENTS_JSON = 'incidents.json'
DEFENSES_JSON = 'defenses.json'
MAPPING_JSON = 'mapping.json'

print("--- Starting final CSV → JSON conversion (with column renaming) ---")

def safe_convert_to_json(df, json_file):
    """
    Safely convert a DataFrame into a JSON file using Python's json module.
    """
    try:
        # Convert DataFrame into a list of Python dictionaries
        records = df.to_dict(orient='records')
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=4)

        print(f"✅ Successfully converted and saved: {json_file}")
    except Exception as e:
        print(f"❌ Critical error while converting {json_file}: {e}")

# --- 1. Process incidents data (incidents.json) ---
try:
    incident_df = pd.read_csv(INCIDENTS_CSV).fillna('')
    safe_convert_to_json(incident_df, INCIDENTS_JSON)
except FileNotFoundError:
    print(f"❌ Error: Cannot find {INCIDENTS_CSV}")

# --- 2. Process defense list (defenses.json) ---
# This is the key fix!
try:
    defense_df = pd.read_csv(DEFENSES_CSV)
    
    # Important fix: rename columns to match what app.js expects
    defense_df.rename(columns={
        'Technique ID': 'defense_id',
        'Technique Name': 'name',
        'Description': 'description',
        'Tactic': 'tactic'
    }, inplace=True)
    
    # Keep only the fields required by the website and fill missing values
    defense_df_clean = defense_df[['defense_id', 'name', 'description', 'tactic']].fillna('')
    
    safe_convert_to_json(defense_df_clean, DEFENSES_JSON)
except FileNotFoundError:
    print(f"❌ Error: Cannot find {DEFENSES_CSV}")

# --- 3. Process mapping results (mapping.json) ---
try:
    mapping_df = pd.read_csv(MAPPING_CSV).fillna('')
    safe_convert_to_json(mapping_df, MAPPING_JSON)
except FileNotFoundError:
    print(f"❌ Error: Cannot find {MAPPING_CSV}")

print("\n--- Conversion complete ---")
print("All JSON files have been regenerated. Please force-refresh your http://localhost:8000 page.")
