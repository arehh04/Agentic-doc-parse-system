-- Migration Script for SROIE Pipeline

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create the receipts table
CREATE TABLE IF NOT EXISTS receipts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename TEXT UNIQUE NOT NULL,
    company_name TEXT,
    receipt_date DATE,
    receipt_time TIME,
    address TEXT,
    total_amount NUMERIC,
    tax_amount NUMERIC,
    currency TEXT,
    raw_text TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Index on filename for faster duplicate checking and upserts
CREATE INDEX IF NOT EXISTS idx_receipts_filename ON receipts(filename);
