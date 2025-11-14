import pandas as pd
import json
import os
from google import genai 
from google.genai import types 

# Set the model name
MODEL_NAME = "gemini-2.5-pro"  # Recommended model for best classification accuracy and strict JSON compliance

# Initialize the Gemini client (automatically reads GEMINI_API_KEY from environment variables)
try:
    client = genai.Client()
except Exception as e:
    print(f"Failed to initialize Gemini client: {e}")
    # ... handle error ...


def call_llm_for_matching(incident_data, defense_list):
    """
    Perform defense-technique matching using the Gemini API.
    """
    prompt = generate_llm_prompt(incident_data, defense_list)
    
    # Define the expected JSON output schema
    response_schema = types.Schema(
        type=types.Type.OBJECT,
        properties={
            "incident_id": types.Schema(type=types.Type.INTEGER),
            "matched_defense_ids": types.Schema(
                type=types.Type.ARRAY,
                description="List of 3 to 5 matched AIDEFEND technique IDs.",
                items=types.Schema(type=types.Type.STRING)
            ),
        }
    )

    # Perform the API call
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            # Instruct the model to return structured JSON output
            response_mime_type="application/json",
            response_schema=response_schema
        )
    )

    # Try to safely parse the JSON output from the model
    try:
        return json.loads(response.text)
    except Exception as e:
        print(f"Failed to parse API response, returning raw text: {response.text}")
        # Return an error marker if the model outputs invalid JSON
        return {"incident_id": incident_data['incident_id'], "matched_defense_ids": ["JSON_PARSE_ERROR"]}
