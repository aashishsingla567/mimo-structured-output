from pydantic import BaseModel

from schemas.common import Address


class ShippingLabel(BaseModel):
    tracking_number: str
    carrier: str | None = None
    service_type: str | None = None
    sender: Address
    recipient: Address
    weight: str | None = None
    dimensions: str | None = None
    pieces: int | None = None
