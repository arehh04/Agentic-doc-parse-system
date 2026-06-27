from pydantic import BaseModel, Field
from typing import Optional

class ReceiptSchema(BaseModel):
    company_name: Optional[str] = Field(default=None, description="The name of the company or store.")
    receipt_date: Optional[str] = Field(default=None, description="The date of the receipt (e.g., YYYY-MM-DD).")
    receipt_time: Optional[str] = Field(default=None, description="The time of the receipt (e.g., HH:MM).")
    address: Optional[str] = Field(default=None, description="The physical address of the store.")
    total_amount: Optional[float] = Field(default=None, description="The total amount paid.")
    tax_amount: Optional[float] = Field(default=None, description="The tax amount, if explicitly stated.")
    currency: Optional[str] = Field(default="MYR", description="The currency code (e.g., MYR, USD).")
