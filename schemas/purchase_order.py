from pydantic import BaseModel


class Address(BaseModel):
    name: str
    line1: str | None = None
    line2: str | None = None
    city: str | None = None
    state: str | None = None
    pincode: str | None = None
    phone: str | None = None


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
