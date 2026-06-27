from models.schema import ReceiptSchema
import logging
import re

class DataQualityAgent:
    """
    Agent responsible for applying business-logic rules and detecting anomalies
    in the extracted data that pass structural validation but might be semantically wrong.
    """
    def __init__(self):
        self.logger = logging.getLogger("quality_agent")
        self.logger.setLevel(logging.INFO)
        if not self.logger.hasHandlers():
            self.logger.addHandler(logging.StreamHandler())

    def analyze(self, validated_receipt: ReceiptSchema) -> dict:
        """
        Analyzes the receipt and returns a quality report with flags and severity levels.
        """
        flags = []
        
        # ── Rule 1: Unusually High Total Amount ──────────────────────────
        if validated_receipt.total_amount is not None and validated_receipt.total_amount > 1000:
            flags.append({
                "rule": "HIGH_TOTAL_AMOUNT",
                "severity": "warning",
                "reason": f"Unusually high amount ({validated_receipt.total_amount}). Possible OCR misread."
            })
            
        # ── Rule 2: Suspiciously Low Total Amount ────────────────────────
        if validated_receipt.total_amount is not None and 0 < validated_receipt.total_amount < 0.10:
            flags.append({
                "rule": "SUSPICIOUSLY_LOW_AMOUNT",
                "severity": "warning",
                "reason": f"Total amount ({validated_receipt.total_amount}) is suspiciously low. Possible extraction error."
            })

        # ── Rule 3: Zero or Negative Total ───────────────────────────────
        if validated_receipt.total_amount is not None and validated_receipt.total_amount <= 0:
            flags.append({
                "rule": "INVALID_TOTAL",
                "severity": "critical",
                "reason": f"Total amount ({validated_receipt.total_amount}) is zero or negative."
            })
            
        # ── Rule 4: Missing Company Name ─────────────────────────────────
        if not validated_receipt.company_name or validated_receipt.company_name.strip() == "":
            flags.append({
                "rule": "MISSING_COMPANY",
                "severity": "critical",
                "reason": "Company name is missing or empty."
            })
            
        # ── Rule 5: Missing Date ─────────────────────────────────────────
        if not validated_receipt.receipt_date or validated_receipt.receipt_date.strip() == "":
            flags.append({
                "rule": "MISSING_DATE",
                "severity": "warning",
                "reason": "Receipt date could not be found."
            })

        # ── Rule 6: Tax Exceeds Total (logical impossibility) ────────────
        if validated_receipt.tax_amount and validated_receipt.total_amount:
            if validated_receipt.tax_amount > validated_receipt.total_amount:
                flags.append({
                    "rule": "TAX_EXCEEDS_TOTAL",
                    "severity": "critical",
                    "reason": f"Tax ({validated_receipt.tax_amount}) is larger than total ({validated_receipt.total_amount})."
                })

        # ── Rule 7: Negative Tax ─────────────────────────────────────────
        if validated_receipt.tax_amount is not None and validated_receipt.tax_amount < 0:
            flags.append({
                "rule": "NEGATIVE_TAX",
                "severity": "critical",
                "reason": f"Tax amount ({validated_receipt.tax_amount}) is negative."
            })

        # ── Rule 8: Company Name Looks Like Garbage OCR ──────────────────
        if validated_receipt.company_name:
            digit_ratio = sum(c.isdigit() for c in validated_receipt.company_name) / max(len(validated_receipt.company_name), 1)
            if digit_ratio > 0.5:
                flags.append({
                    "rule": "GARBAGE_COMPANY_NAME",
                    "severity": "warning",
                    "reason": f"Company name '{validated_receipt.company_name}' contains >50% digits. Likely OCR noise."
                })

        # ── Rule 9: Invalid Date Format ──────────────────────────────────
        if validated_receipt.receipt_date:
            date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$|^\d{2}/\d{2}/\d{4}$|^\d{2}-\d{2}-\d{4}$")
            if not date_pattern.match(validated_receipt.receipt_date.strip()):
                flags.append({
                    "rule": "INVALID_DATE_FORMAT",
                    "severity": "warning",
                    "reason": f"Date '{validated_receipt.receipt_date}' does not match expected formats (YYYY-MM-DD, DD/MM/YYYY)."
                })
                
        # ── Build Report ─────────────────────────────────────────────────
        is_clean = len(flags) == 0
        has_critical = any(f["severity"] == "critical" for f in flags)
        
        report = {
            "is_clean": is_clean,
            "quality": "critical" if has_critical else ("warning" if flags else "pass"),
            "flags_count": len(flags),
            "flags": flags
        }
        
        if not is_clean:
            self.logger.warning(f"Quality flags detected ({len(flags)}): {[f['rule'] for f in flags]}")
            
        return report
