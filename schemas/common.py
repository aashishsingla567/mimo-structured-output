"""Shared schema types used across multiple document schemas."""

from pydantic import BaseModel


class Address(BaseModel):
    name: str
    line1: str | None = None
    line2: str | None = None
    city: str | None = None
    state: str | None = None
    pincode: str | None = None
    phone: str | None = None
