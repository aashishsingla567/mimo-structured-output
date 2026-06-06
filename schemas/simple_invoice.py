from typing import Literal

from pydantic import BaseModel


class InvoiceSummary(BaseModel):
    invoice_id: str
    total: float
    currency: Literal["USD", "EUR", "INR"]
    status: Literal["pending", "paid", "failed"]
