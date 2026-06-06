from pydantic import BaseModel


class Transaction(BaseModel):
    date: str
    description: str
    debit: float | None = None
    credit: float | None = None
    balance: float


class BankStatement(BaseModel):
    account_holder: str
    account_number: str
    bank_name: str | None = None
    statement_period: str
    opening_balance: float
    closing_balance: float
    transactions: list[Transaction]
