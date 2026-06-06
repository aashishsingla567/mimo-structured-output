from pydantic import BaseModel


class Seller(BaseModel):
    name: str | None = None
    gstin: str | None = None


class Customer(BaseModel):
    name: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None


class LineItem(BaseModel):
    description: str
    quantity: float
    unit_price: float
    amount: float


class Summary(BaseModel):
    subtotal: float | None = None
    discount: float | None = None
    taxable_value: float | None = None
    cgst: float | None = None
    sgst: float | None = None
    grand_total: float | None = None
    amount_in_words: str | None = None


class Payment(BaseModel):
    payment_terms: str | None = None
    bank_name: str | None = None
    account_number: str | None = None
    ifsc: str | None = None


class References(BaseModel):
    sales_order: str | None = None
    customer_po: str | None = None


class Invoice(BaseModel):
    invoice_number: str
    invoice_date: str
    seller: Seller | None = None
    customer: Customer
    items: list[LineItem]
    summary: Summary
    payment: Payment | None = None
    references: References | None = None
