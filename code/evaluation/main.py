import os
import sys
import pandas as pd

# Add the project root to python path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, ROOT_DIR)

from code.main import run_prediction
from code.evaluation.metrics import calculate_metrics, generate_report
from code.config import DATA_DIR

def run_evaluation():
    input_file = "sample_claims.csv"
    output_file = "evaluation_sample_output.csv"
    
    print(f"Running pipeline on {input_file}...")
    run_prediction(input_file, output_file)
    
    pred_path = os.path.join(ROOT_DIR, output_file)
    gt_path = os.path.join(DATA_DIR, input_file)
    
    pred_df = pd.read_csv(pred_path)
    gt_df = pd.read_csv(gt_path)
    
    print("Calculating metrics...")
    metrics = calculate_metrics(pred_df, gt_df)
    
    report_path = os.path.join(ROOT_DIR, "evaluation", "evaluation_report.md")
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    generate_report(metrics, report_path)
    print(f"Evaluation report generated at {report_path}")
    
if __name__ == "__main__":
    run_evaluation()
