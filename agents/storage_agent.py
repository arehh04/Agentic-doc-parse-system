import os
import logging
import pandas as pd
from supabase import create_client, Client
from models.schema import ReceiptSchema

class StorageAgent:
    """
    Agent responsible for persisting data into Supabase cloud storage.
    """
    def __init__(self):
        self.logger = logging.getLogger("storage_agent")
        self.logger.setLevel(logging.INFO)
        if not self.logger.hasHandlers():
            self.logger.addHandler(logging.StreamHandler())
            
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        self.supabase = None
        if url and key and "your_supabase" not in url:
            self.supabase = create_client(url, key)

    def _format_date(self, date_str):
        if not date_str: return None
        try: return pd.to_datetime(date_str).strftime('%Y-%m-%d')
        except Exception: return None

    def _format_time(self, time_str):
        if not time_str: return None
        try: return pd.to_datetime(time_str).strftime('%H:%M:%S')
        except Exception: return None

    def store(self, filename: str, raw_text: str, validated_data: ReceiptSchema) -> dict:
        """
        Saves the validated receipt to Supabase. Returns the API response or an empty dict if DB is offline.
        """
        if not self.supabase:
            self.logger.warning("Supabase credentials missing. Skipping storage.")
            return {}

        try:
            db_record = {
                "filename": filename,
                "company_name": validated_data.company_name,
                "receipt_date": self._format_date(validated_data.receipt_date),
                "receipt_time": self._format_time(validated_data.receipt_time),
                "address": validated_data.address,
                "total_amount": validated_data.total_amount,
                "tax_amount": validated_data.tax_amount,
                "currency": validated_data.currency,
                "raw_text": raw_text
            }
            
            response = self.supabase.table("receipts").upsert(db_record, on_conflict="filename").execute()
            self.logger.info(f"Successfully stored {filename} in Supabase.")
            return response.data
        except Exception as e:
            self.logger.error(f"Failed to store {filename} in Supabase: {e}")
            raise e
