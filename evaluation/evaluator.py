import os
import json
import glob
from collections import Counter
import pandas as pd
from dateutil import parser as date_parser

def normalize_text(text):
    if text is None:
        return ""
    return str(text).strip().lower()

def compute_f1(pred_text, true_text):
    """
    Computes token-level Precision, Recall, and F1 score.
    """
    pred_tokens = normalize_text(pred_text).split()
    true_tokens = normalize_text(true_text).split()
    
    common = Counter(pred_tokens) & Counter(true_tokens)
    num_same = sum(common.values())
    
    if len(pred_tokens) == 0 or len(true_tokens) == 0:
        match = int(pred_tokens == true_tokens)
        return match, match, match
        
    precision = 1.0 * num_same / len(pred_tokens)
    recall = 1.0 * num_same / len(true_tokens)
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    return precision, recall, f1

def compare_dates(pred_date, gt_date):
    """
    Smart date comparison to handle SROIE raw string (DD/MM/YYYY) vs Pydantic ISO string (YYYY-MM-DD).
    """
    if not pred_date and not gt_date:
        return True
    if not pred_date or not gt_date or pred_date == "None" or gt_date == "None":
        return False
    try:
        p = date_parser.parse(pred_date, dayfirst=False)
        g = date_parser.parse(gt_date, dayfirst=True) 
        return p.date() == g.date()
    except:
        return normalize_text(pred_date) == normalize_text(gt_date)

def evaluate_pipeline(predictions_dir: str, ground_truth_dir: str, output_report_path: str):
    pred_files = glob.glob(os.path.join(predictions_dir, "*.json"))
    results = []
    failed_cases = []
    total_processing_time = 0.0
    
    field_mapping = {
        "company_name": "company",
        "receipt_date": "date",
        "address": "address",
        "total_amount": "total"
    }
    
    for pred_file in pred_files:
        filename = os.path.basename(pred_file)
        gt_file = os.path.join(ground_truth_dir, filename.replace('.json', '.txt'))
        
        if not os.path.exists(gt_file):
            continue
            
        with open(pred_file, 'r', encoding='utf-8') as f:
            pred_data = json.load(f)
            
        total_processing_time += pred_data.get("processing_time_seconds", 0)
            
        with open(gt_file, 'r', encoding='utf-8') as f:
            try:
                gt_data = json.load(f)
            except json.JSONDecodeError:
                continue
                
        file_metrics = {"filename": filename}
        file_errors = {}
        
        for pred_key, gt_key in field_mapping.items():
            pred_val = str(pred_data.get(pred_key, ""))
            gt_val = str(gt_data.get(gt_key, ""))
            
            # Standardize floats
            if pred_key == "total_amount" and pred_val and pred_val != "None":
                try: pred_val = f"{float(pred_val):.2f}"
                except ValueError: pass
            if gt_key == "total" and gt_val:
                try: gt_val = f"{float(gt_val.replace(',', '')):.2f}"
                except ValueError: pass
                    
            if pred_key == "receipt_date":
                is_match = compare_dates(pred_val, gt_val)
                p = r = f1 = exact_match = 1 if is_match else 0
            else:
                p, r, f1 = compute_f1(pred_val, gt_val)
                exact_match = 1 if normalize_text(pred_val) == normalize_text(gt_val) else 0
            
            file_metrics[f"{gt_key}_precision"] = p
            file_metrics[f"{gt_key}_recall"] = r
            file_metrics[f"{gt_key}_f1"] = f1
            file_metrics[f"{gt_key}_exact_match"] = exact_match
            
            if exact_match == 0:
                file_errors[gt_key] = {"expected": gt_val, "predicted": pred_val}
                
        if file_errors:
            failed_cases.append({
                "filename": filename,
                "errors": file_errors
            })
            
        results.append(file_metrics)
        
    if not results:
        print("No matching files found for evaluation.")
        return
        
    df = pd.DataFrame(results)
    
    report = {
        "total_files_evaluated": len(df),
        "processing_time": {
            "total_seconds": round(total_processing_time, 2),
            "average_seconds_per_receipt": round(total_processing_time / len(df) if len(df) > 0 else 0, 2)
        },
        "aggregate_metrics": {},
        "error_analysis": {
            "total_failed_cases": len(failed_cases),
            "failure_rate_exact_match": round(len(failed_cases) / len(df), 4)
        },
        "failed_cases": failed_cases
    }
    
    for _, gt_key in field_mapping.items():
        report["aggregate_metrics"][gt_key] = {
            "precision": round(df[f"{gt_key}_precision"].mean(), 4),
            "recall": round(df[f"{gt_key}_recall"].mean(), 4),
            "f1_score": round(df[f"{gt_key}_f1"].mean(), 4),
            "exact_match_accuracy": round(df[f"{gt_key}_exact_match"].mean(), 4)
        }
        
    overall_f1 = df[[f"{gt}_f1" for gt in field_mapping.values()]].mean().mean()
    report["aggregate_metrics"]["overall_f1_score"] = round(overall_f1, 4)
    
    os.makedirs(os.path.dirname(output_report_path), exist_ok=True)
    with open(output_report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=4)
        
    print(f"Evaluation complete. Report saved to {output_report_path}")

if __name__ == "__main__":
    preds = os.path.join(os.path.dirname(__file__), "..", "data", "output")
    gt = r"C:\Users\HP\Desktop\Portfolio\sroie-pipeline\SROIE2019\train\entities"
    report_out = os.path.join(os.path.dirname(__file__), "..", "data", "evaluation_report.json")
    evaluate_pipeline(preds, gt, report_out)
