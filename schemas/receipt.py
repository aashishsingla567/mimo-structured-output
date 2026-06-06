from pydantic import BaseModel


class ReceiptItem(BaseModel):
    description: str
    quantity: float
    unit_price: float
    amount: float


class RestaurantReceipt(BaseModel):
    merchant_name: str
    merchant_address: str | None = None
    date: str
    items: list[ReceiptItem]
    subtotal: float
    tax: float
    tip: float | None = None
    total: float
    payment_method: str | None = None
