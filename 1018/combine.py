import pandas as pd
import ast

# 1. Load data
incidents_df = pd.read_csv("../mongodump_full_snapshot/incidents.csv")
reports_df = pd.read_csv("../mongodump_full_snapshot/reports.csv")
mit_df = pd.read_csv("../mongodump_full_snapshot/classifications_MIT.csv")

# 2. Prepare incidents.csv: expand report IDs
# Convert the 'reports' column (string list) into a real Python list of integers
def safe_literal_eval(x):
    """Safely evaluate a string representation and convert it into a Python list."""
    try:
        # ast.literal_eval safely converts a string list into a Python list
        return ast.literal_eval(x)
    except:
        return []

# Convert the report ID string into an actual list and store it in a new column
incidents_df['report_number'] = incidents_df['reports'].apply(safe_literal_eval)

# Expand the incidents dataframe so each incident–report pair has its own row
incidents_exploded = incidents_df.explode('report_number')

# Select core incident information and ensure report_number is integer
incident_core = incidents_exploded[['incident_id', 'date', 'Alleged deployer of AI system',
                                   'Alleged developer of AI system', 'Alleged harmed or nearly harmed parties',
                                   'title', 'report_number']].copy()

# Convert report_number to integer
incident_core['report_number'] = pd.to_numeric(incident_core['report_number'], errors='coerce').fillna(-1).astype(int)

# 3. Merge reports.csv
# Keep only report_number and text from reports.csv
reports_text = reports_df[['report_number', 'text']].rename(columns={'text': 'detailed_report_text'})

# Merge using 'report_number' as the key
merged_reports = pd.merge(
    incident_core,
    reports_text,
    on='report_number',
    how='left'
)

# 4. Aggregate full report text per incident
merged_reports_grouped = merged_reports.groupby('incident_id').agg(
    incident_title=('title', 'first'),
    incident_date=('date', 'first'),
    deployer=('Alleged deployer of AI system', 'first'),
    developer=('Alleged developer of AI system', 'first'),
    harmed_parties=('Alleged harmed or nearly harmed parties', 'first'),
    # Concatenate all unique, non-null report texts as input for LLM
    full_report_text=('detailed_report_text', lambda x: ' '.join(x.dropna().astype(str).unique()).strip())
).reset_index()

# 5. Merge classification data (MITRE)
# Fix field name for merging: rename 'Incident ID' → 'incident_id'
mit_df.rename(columns={'Incident ID': 'incident_id'}, inplace=True)

# Create a combined classification name: "Domain: Subdomain"
mit_df['classification_name'] = mit_df['Risk Domain'] + ': ' + mit_df['Risk Subdomain']

# Aggregate MITRE classifications per incident (separated by " | ")
mit_df_agg = mit_df.groupby('incident_id').agg(
    mitre_classification=('classification_name', lambda x: ' | '.join(x.unique()))
).reset_index()

# Final merge: combine incident report summary with MITRE classifications
final_merged_df = pd.merge(
    merged_reports_grouped,
    mit_df_agg,
    on='incident_id',
    how='left'
)

# 6. Save final result as CSV
final_merged_df.to_csv('merged_incident_data.csv', index=False)

# Preview output
merge_p = pd.read_csv("merged_incident_data.csv")
print(merge_p.head())
