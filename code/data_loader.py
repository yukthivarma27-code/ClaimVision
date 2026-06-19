import os
import pandas as pd
from code.config import DATA_DIR

def load_data(file_name="claims.csv"):
    claims_df = pd.read_csv(os.path.join(DATA_DIR, file_name))
    history_df = pd.read_csv(os.path.join(DATA_DIR, "user_history.csv"))
    req_df = pd.read_csv(os.path.join(DATA_DIR, "evidence_requirements.csv"))
    
    # Merge claims with history to provide risk context
    # Use left join to preserve row order from claims.csv
    merged_df = claims_df.merge(history_df, on="user_id", how="left")
    
    return merged_df, req_df

def get_requirements_for_object(req_df, claim_object):
    """Fetch 'all' requirements + requirements specific to the object type"""
    return req_df[(req_df['claim_object'] == 'all') | (req_df['claim_object'] == claim_object)]
