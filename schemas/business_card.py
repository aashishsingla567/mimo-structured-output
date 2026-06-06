from pydantic import BaseModel


class BusinessCard(BaseModel):
    name: str
    title: str | None = None
    company: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    website: str | None = None
