import pandas as pd
import ast

# 1. 載入數據 (Load data)
incidents_df = pd.read_csv("../mongodump_full_snapshot/incidents.csv")
reports_df = pd.read_csv("../mongodump_full_snapshot/reports.csv")
mit_df = pd.read_csv("../mongodump_full_snapshot/classifications_MIT.csv")

# 2. 準備 incidents.csv: 展開報告 ID (Explode reports column)
# 將 'reports' 欄位的字串表示轉換為實際的整數列表
def safe_literal_eval(x):
    """安全地評估字串，將其轉換為 Python 列表"""
    try:
        # ast.literal_eval 安全地將字串列表轉換為 Python 列表
        return ast.literal_eval(x)
    except:
        return []

# 將報告 ID 字串轉換為列表，並命名為新的欄位
incidents_df['report_number'] = incidents_df['reports'].apply(safe_literal_eval)

# 展開 incidents_df，讓每個事件-報告 ID 對應一行
incidents_exploded = incidents_df.explode('report_number')

# 選取核心事件資訊並確保 report_number 為整數
incident_core = incidents_exploded[['incident_id', 'date', 'Alleged deployer of AI system', 
                                   'Alleged developer of AI system', 'Alleged harmed or nearly harmed parties', 
                                   'title', 'report_number']].copy()
# 轉換 report_number 為整數類型
incident_core['report_number'] = pd.to_numeric(incident_core['report_number'], errors='coerce').fillna(-1).astype(int)

# 3. 合併 reports.csv (Merge reports.csv)
# reports_df 只保留報告 ID 和文本
reports_text = reports_df[['report_number', 'text']].rename(columns={'text': 'detailed_report_text'})

# 合併數據：使用 'report_number' 作為連接鍵
merged_reports = pd.merge(
    incident_core,
    reports_text,
    on='report_number',
    how='left'
)

# 4. 彙總文本: 針對每個 incident_id 串聯所有詳細報告文本
merged_reports_grouped = merged_reports.groupby('incident_id').agg(
    incident_title=('title', 'first'),
    incident_date=('date', 'first'),
    deployer=('Alleged deployer of AI system', 'first'),
    developer=('Alleged developer of AI system', 'first'),
    harmed_parties=('Alleged harmed or nearly harmed parties', 'first'),
    # 串聯所有不重複且非空值的報告文本，作為 LLM 的輸入
    full_report_text=('detailed_report_text', lambda x: ' '.join(x.dropna().astype(str).unique()).strip())
).reset_index()

# 5. 合併分類數據 (Merge Classifications - MITRE)
# 修正欄位名稱：將 'Incident ID' 重命名為 'incident_id' 以便合併
mit_df.rename(columns={'Incident ID': 'incident_id'}, inplace=True)

# 創建一個組合的分類名稱：Domain: Subdomain
mit_df['classification_name'] = mit_df['Risk Domain'] + ': ' + mit_df['Risk Subdomain']

# 彙總 MITRE 分類，將同一事件的多個分類合併為一個字串 (用 ' | ' 分隔)
mit_df_agg = mit_df.groupby('incident_id').agg(
    mitre_classification=('classification_name', lambda x: ' | '.join(x.unique()))
).reset_index()

# 最終合併：將彙總後的事件報告數據與 MITRE 分類合併
final_merged_df = pd.merge(
    merged_reports_grouped,
    mit_df_agg,
    on='incident_id',
    how='left'
)

# 6. 儲存為 CSV 文件
final_merged_df.to_csv('merged_incident_data.csv', index=False)

merge_p = pd.read_csv("merged_incident_data.csv")
print(merge_p.head())