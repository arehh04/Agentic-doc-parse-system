import os
import logging
import pandas as pd
from supabase import create_client, Client

logger = logging.getLogger("database")
logger.setLevel(logging.INFO)
if not logger.hasHandlers():
    logger.addHandler(logging.StreamHandler())

def get_supabase_client() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in the environment.")
    return create_client(url, key)

def format_date(date_str):
    if not date_str: 
        return None
    try:
        return pd.to_datetime(date_str).strftime('%Y-%m-%d')
    except Exception:
        return None

def format_time(time_str):
    if not time_str: 
        return None
    try:
        return pd.to_datetime(time_str).strftime('%H:%M:%S')
    except Exception:
        return None

def save_receipt_to_db(filename: str, raw_text: str, extracted_data: dict):
    """
    Saves the extracted receipt to Supabase.
    Uses upsert to prevent duplicates based on the unique filename.
    """
    try:
        supabase = get_supabase_client()
        
        db_record = {
            "filename": filename,
            "company_name": extracted_data.get("company_name"),
            "receipt_date": format_date(extracted_data.get("receipt_date")),
            "receipt_time": format_time(extracted_data.get("receipt_time")),
            "address": extracted_data.get("address"),
            "total_amount": extracted_data.get("total_amount"),
            "tax_amount": extracted_data.get("tax_amount"),
            "currency": extracted_data.get("currency"),
            "raw_text": raw_text
        }
        
        # Upsert operation on conflict of filename to prevent duplicates
        response = supabase.table("receipts").upsert(db_record, on_conflict="filename").execute()
        
        logger.info(f"Successfully saved {filename} to Supabase.")
        return response.data
    except Exception as e:
        logger.error(f"Failed to save {filename} to Supabase: {e}")
        raise e
