from pydantic import BaseModel


class Address(BaseModel):
    name: str
    line1: str | None = None
    line2: str | None = None
    city: str | None = None
    state: str | None = None
    pincode: str | None = None
    phone: str | None = None


class ShippingLabel(BaseModel):
    tracking_number: str
    carrier: str | None = None
    service_type: str | None = None
    sender: Address
    recipient: Address
    weight: str | None = None
    dimensions: str | None = None
    pieces: int | None = None
