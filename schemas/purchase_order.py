from pydantic import BaseModel

from schemas.common import Address


class POItem(BaseModel):
    description: str
    quantity: float
    unit_price: float
    amount: float


class PurchaseOrder(BaseModel):
    po_number: str
    date: str
    buyer: Address
    seller: Address
    items: list[POItem]
    total_amount: float
    payment_terms: str | None = None
    delivery_date: str | None = None
    shipping_terms: str | None = None
