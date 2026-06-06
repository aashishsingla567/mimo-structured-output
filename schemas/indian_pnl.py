from pydantic import BaseModel


class PnLLineItem(BaseModel):
    description: str
    quarter_ended: float | None = None
    year_ended: float | None = None


class IndianPnL(BaseModel):
    company_name: str
    reporting_period: str
    currency: str | None = None
    revenue_from_operations: float | None = None
    other_income: float | None = None
    total_income: float | None = None
    cost_of_materials_consumed: float | None = None
    purchases_of_stock_in_trade: float | None = None
    changes_in_inventories_finished_goods: float | None = None
    changes_in_inventories_work_in_progress: float | None = None
    employee_benefits_expense: float | None = None
    finance_costs: float | None = None
    depreciation_and_amortisation: float | None = None
    other_expenses: float | None = None
    total_expenses: float | None = None
    profit_before_exceptional_items: float | None = None
    exceptional_items: float | None = None
    profit_before_tax: float | None = None
    tax_expense_current: float | None = None
    tax_expense_deferred: float | None = None
    profit_for_the_year: float | None = None
