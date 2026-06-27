"""
Data Quality Agent - Manual Test Suite
Tests the agent with intentionally anomalous receipts to verify flagging behavior.
"""
import json
import sys
import os
sys.path.insert(0, ".")
# Fix Windows encoding
sys.stdout.reconfigure(encoding='utf-8')

from models.schema import ReceiptSchema
from agents.quality_agent import DataQualityAgent

agent = DataQualityAgent()

# --- Test Cases ---------------------------------------------------------------

test_cases = [
    {
        "name": "NORMAL - Clean Receipt (should PASS)",
        "data": {
            "company_name": "99 Speedmart",
            "receipt_date": "2024-03-15",
            "total_amount": 45.80,
            "tax_amount": 2.74,
            "currency": "MYR"
        }
    },
    {
        "name": "WARNING - Unusually High Amount (KFC RM999,999)",
        "data": {
            "company_name": "KFC",
            "receipt_date": "2024-01-10",
            "total_amount": 999999,
            "tax_amount": 5.00,
            "currency": "MYR"
        }
    },
    {
        "name": "CRITICAL - Empty Company + Suspiciously Low Amount",
        "data": {
            "company_name": "",
            "receipt_date": "2024-05-20",
            "total_amount": 0.01,
            "currency": "MYR"
        }
    },
    {
        "name": "CRITICAL - Tax Exceeds Total",
        "data": {
            "company_name": "Petronas",
            "receipt_date": "2024-07-01",
            "total_amount": 10.00,
            "tax_amount": 50.00,
            "currency": "MYR"
        }
    },
    {
        "name": "CRITICAL - Zero Total Amount",
        "data": {
            "company_name": "Giant",
            "receipt_date": "2024-02-14",
            "total_amount": 0,
            "currency": "MYR"
        }
    },
    {
        "name": "CRITICAL - Negative Total Amount",
        "data": {
            "company_name": "Mydin",
            "receipt_date": "2024-08-08",
            "total_amount": -15.50,
            "currency": "MYR"
        }
    },
    {
        "name": "WARNING - Missing Date",
        "data": {
            "company_name": "Tesco",
            "total_amount": 88.00,
            "currency": "MYR"
        }
    },
    {
        "name": "WARNING - Garbage OCR Company Name",
        "data": {
            "company_name": "123456789",
            "receipt_date": "2024-04-01",
            "total_amount": 25.00,
            "currency": "MYR"
        }
    },
    {
        "name": "WARNING - Invalid Date Format",
        "data": {
            "company_name": "Watson's",
            "receipt_date": "March 15 2024",
            "total_amount": 33.50,
            "currency": "MYR"
        }
    },
    {
        "name": "CRITICAL - Negative Tax",
        "data": {
            "company_name": "AEON",
            "receipt_date": "2024-06-06",
            "total_amount": 120.00,
            "tax_amount": -7.20,
            "currency": "MYR"
        }
    },
    {
        "name": "CRITICAL - ALL FLAGS (Maximum Chaos)",
        "data": {
            "company_name": "",
            "receipt_date": "blah",
            "total_amount": -999,
            "tax_amount": -50,
            "currency": "MYR"
        }
    },
]

# --- Run Tests ----------------------------------------------------------------

print("=" * 70)
print("  DATA QUALITY AGENT - TEST REPORT")
print("=" * 70)

results = []
for i, tc in enumerate(test_cases, 1):
    receipt = ReceiptSchema(**tc["data"])
    report = agent.analyze(receipt)
    
    print(f"\n{'-' * 70}")
    print(f"  Test {i}: {tc['name']}")
    print(f"  Input: {json.dumps(tc['data'], indent=4)}")
    print(f"  Quality: {report['quality'].upper()}")
    print(f"  Clean: {report['is_clean']}")
    print(f"  Flags ({report['flags_count']}):")
    for flag in report["flags"]:
        severity_icon = "[!!!]" if flag["severity"] == "critical" else "[!]"
        print(f"    {severity_icon} [{flag['severity'].upper()}] {flag['rule']}: {flag['reason']}")
    if report["is_clean"]:
        print(f"    [OK] No issues detected.")
        
    results.append({
        "test": tc["name"],
        "quality": report["quality"],
        "flags_count": report["flags_count"],
        "flags": [f["rule"] for f in report["flags"]]
    })

# --- Summary -----------------------------------------------------------------
print(f"\n{'=' * 70}")
print(f"  SUMMARY")
print(f"{'=' * 70}")

passed = sum(1 for r in results if r["quality"] == "pass")
warnings = sum(1 for r in results if r["quality"] == "warning")
criticals = sum(1 for r in results if r["quality"] == "critical")

print(f"  Total Tests:    {len(results)}")
print(f"  PASSED:         {passed}")
print(f"  WARNINGS:       {warnings}")
print(f"  CRITICALS:      {criticals}")
print(f"{'=' * 70}")

# --- Save JSON Report --------------------------------------------------------
report_path = os.path.join("data", "quality_test_report.json")
os.makedirs("data", exist_ok=True)
with open(report_path, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=4)
print(f"\n  Report saved to: {report_path}")
