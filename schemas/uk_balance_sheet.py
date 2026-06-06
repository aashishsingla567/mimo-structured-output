from pydantic import BaseModel


class UKBalanceSheet(BaseModel):
    company_name: str
    registered_number: str | None = None
    reporting_date: str
    currency: str | None = None
    current_assets: float | None = None
    creditors_amounts_falling_due_within_one_year: float | None = None
    net_current_liabilities: float | None = None
    total_assets_less_current_liabilities: float | None = None
    accruals_and_deferred_income: float | None = None
    net_liabilities: float | None = None
    capital_and_reserves: float | None = None
    fixed_assets_total: float | None = None
    intangible_assets: float | None = None
    tangible_assets: float | None = None
    debtors_amounts_falling_due_within_one_year: float | None = None
    cash_at_bank_and_in_hand: float | None = None
    net_current_assets: float | None = None
    net_assets: float | None = None
    called_up_share_capital: float | None = None
    profit_and_loss_account: float | None = None
    shareholders_funds: float | None = None
