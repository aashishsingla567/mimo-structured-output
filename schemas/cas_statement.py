from pydantic import BaseModel


class CASInvestorInfo(BaseModel):
    pan: str | None = None
    name: str | None = None
    email: str | None = None
    address: str | None = None


class CASTransaction(BaseModel):
    date: str
    description: str
    amount: float | None = None
    units: float | None = None
    nav: float | None = None
    balance_units: float | None = None


class CASScheme(BaseModel):
    fund_house: str | None = None
    scheme_name: str
    isin: str | None = None
    folio_number: str | None = None
    opening_units: float | None = None
    closing_units: float | None = None
    nav: float | None = None
    closing_value: float | None = None
    transactions: list[CASTransaction] | None = None


class CASStatement(BaseModel):
    statement_type: str | None = None
    statement_period_from: str | None = None
    statement_period_to: str | None = None
    statement_date: str | None = None
    registrar: str | None = None
    investor: CASInvestorInfo | None = None
    schemes: list[CASScheme]
    total_portfolio_value: float | None = None
