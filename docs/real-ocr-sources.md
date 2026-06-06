# Real OCR Financial Document Sources

Research compiled 2026-06-06. Sources verified for: real OCR text availability, ground truth data, document complexity.

---

## Tier 1: Best Sources (Raw OCR Text + Ground Truth Available)

### 1. UK Companies House Balance Sheets

- **Repo:** `ap539813/Financial-data-extraction-from-ocr-images`
- **URL:** https://github.com/ap539813/Financial-data-extraction-from-ocr-images/tree/master/Sample%20Dataset
- **What:** 500 real OCR text files of UK company balance sheets scanned from Companies House PDFs
- **Sample files in repo:** `sample1_0000001R.txt` (FLEXI BUSINESS LIMITED), `sample2_0000001R.txt` (EARLY MORNING MEDIA LIMITED)
- **Ground truth:** `sol1.csv` — 500 rows mapping filename → JSON dict of extracted fields
- **OCR artifacts:** Massive whitespace padding, `{` instead of `(`, `= =` noise, broken column alignment, note numbers merged into data
- **Company #1 (06101470):** 7 line items — Current assets, Creditors, Net current liabilities, Total assets less current liabilities, Accruals, Net liabilities, Capital and reserves
- **Company #2 (06719248):** 15 line items — Fixed assets (intangible, tangible), Current assets (debtors, cash), Creditors, Net current assets, Net assets, Capital and reserves (share capital, P&L, shareholders funds)
- **Data is REAL** — actual UK Companies House filings
- **Note:** Full 500-file dataset was hosted externally (competition dataset), only 2 samples in repo

### 2. NSDL/CAMS CAS Statements

- **Source:** https://www.scribd.com/document/989793884/Cas (CAMS CAS, 3 pages)
- **Source:** https://www.scribd.com/document/918326822/Nsdlcas-March2022-Rk (NSDL CAS, 28 pages)
- **What:** Real CAS PDF text extracted from actual investor statements
- **CAMS CAS sample:** PAN ABCDE1234F, HDFC Equity Fund, SBI Bluechip Fund, ICICI Pru Technology Fund, transactions with dates/amounts/units/NAV
- **NSDL CAS sample:** Investor KAMALA R (PAN AQJPK5658D), 5 NSDL demat accounts + 1 CDSL, portfolio value ₹32,28,92,982.20, equity holdings with ISINs
- **OCR artifacts:** Concatenated transaction lines, merged column headers, tab-separated fields
- **Ground truth format (casparser):** JSON with statement_period, investor_info, folios[], schemes[], transactions[]
- **Data is REAL** — actual investor financial data

### 3. Loyal Textile Mills — Indian P&L (Scanned PDF OCR)

- **Source:** https://loyaltextiles.com/wp-content/uploads/2025/05/BMOutcomeQ4Financial-Results.pdf
- **What:** Real OCR from scanned quarterly/annual financial results
- **OCR artifacts:** "LOYAL TEXTIE MIWS" (OCR error for TEXTILE MILLS), "31"" (stray quote), Indian number formatting (1,01,302), multi-column layout
- **Structure:** Particulars | Quarter Ended (3 dates) | Year Ended (2 dates), amounts in Lakhs
- **Line items:** Revenue from operations, Other income, Total income, Cost of materials consumed, Purchases of stock in trade, Changes in inventories (FG + WIP), Employee benefits, Finance costs, Depreciation, Other expenses, Total expenses, Profit before exceptional items, Exceptional items, Profit before tax
- **Data is REAL** — actual Indian company annual report

### 4. Hikal Limited — Indian Balance Sheet + P&L (Digital PDF, clean)

- **Source:** https://www.hikal.com/AnnualReports/2025/pdf/Hikal-AR2025_Standalone%20Financial%20Statements.pdf
- **What:** Full standalone financial statements — Balance Sheet + P&L + Cash Flow
- **Balance Sheet:** 25+ line items across Non-current assets, Current assets, Equity, Non-current liabilities, Current liabilities
- **P&L:** Revenue from operations, Other income, Cost of materials, Changes in inventories, Employee benefits, Finance costs, Depreciation, Other expenses, Tax expense, Profit for the year
- **Currency:** ₹ Lakhs
- **Data is REAL** — actual Indian company annual report (2024-25)

---

## Tier 2: Good Sources (Structured Data, Clean Format)

### 5. Crescent Textiles Trial Balance (IFRS)

- **Repo:** `panaversity/ca-cpa-practice-agents`
- **URL:** https://github.com/panaversity/ca-cpa-practice-agents/blob/main/exercises/trial-balances/textile-manufacturer-tb.csv
- **What:** Full IFRS-compliant trial balance with 57 line items
- **Structure:** Account Code, Account Name, Debit (PKR '000), Credit (PKR '000)
- **Sections:** Assets (1010-1071), Liabilities (2010-2110), Equity (3010-3030), Revenue (4010-4030), COGS (5010-5050), OpEx (6010-6100), Finance costs (7010-7040), Tax (8010-8020)
- **Totals:** 807,350 debit = 807,350 credit (balanced)
- **Data is SYNTHETIC** (educational) but realistic IFRS structure
- **Also available:** `textile-manufacturer-tb-may-2025.csv` — prior month TB with 59 line items

### 6. Vodafone Limited — UK Annual Report (Digital, clean)

- **Repo:** `ascender1729/vodafone-financial-analysis`
- **URL:** https://github.com/ascender1729/vodafone-financial-analysis
- **What:** Full annual report OCR text (785 lines) + extracted CSVs
- **Files:** `extracted_text.txt` (full report), `INCOME STATEMENT.csv`, `STATEMENT OF FINANCIAL POSITION.csv`
- **Balance Sheet:** Non-current assets (intangible, PPE, investments, deferred tax, post-employment), Current assets (inventories, receivables, cash), Creditors, Equity (share capital, premium, retained earnings)
- **P&L:** Revenue, Cost of sales, Gross profit, Selling costs, Admin expenses, Credit losses, Operating loss, Finance expense, Tax, Loss for year
- **Data is REAL** — actual Vodafone Limited annual report (year ended 31 March 2020)
- **Note:** Text is clean digital extraction, not messy OCR

### 7. Pirimid P&L Form (Mortgage Application)

- **Repo:** `Pirimid/financial-documents-ocr-deep-learning`
- **URL:** https://github.com/Pirimid/financial-documents-ocr-deep-learning/blob/master/data/sample_csv.csv
- **What:** OCR output from a mortgage P&L form template
- **Structure:** Gross Income (Gross Sales, Other Income), Expenses (COGS, Accounting, Advertising, Insurance, Maintenance, Supplies, Payroll ×2, Postage, Rent, Licenses, Taxes, Telephone, Travel, Utilities, Other), Net Income
- **Data is SYNTHETIC** (form template with empty fields)

### 8. DocuPipe P&L Example

- **Source:** https://www.docupipe.ai/landing/profit-loss
- **What:** Clean P&L with structured JSON ground truth
- **Structure:** Revenue (product, service, other), COGS (materials, labor, freight), Operating expenses (S&M, R&D, G&A, rent, utilities, depreciation), Other income/expenses, Tax, Net income, EBITDA, margins
- **Data is SYNTHETIC** (example document)

---

## Tier 3: Large-Scale Datasets (Require Download/Processing)

### 9. HuggingFace Financial OCR Datasets

| Dataset                                         | Size                          | Language   | Type                                             | URL                                                                           |
| ----------------------------------------------- | ----------------------------- | ---------- | ------------------------------------------------ | ----------------------------------------------------------------------------- |
| `conghuy/ocr_financials_statements_2020_2025`   | 11,400 rows                   | Vietnamese | Annual report OCR text                           | https://huggingface.co/datasets/conghuy/ocr_financials_statements_2020_2025   |
| `vduydong/ocr_annual_financials`                | 18,231 reports, 1,491 tickers | Vietnamese | OCR text `.txt` files                            | https://huggingface.co/datasets/vduydong/ocr_annual_financials                |
| `horelulus/IDX_Financial_Statements2015-2025Q2` | IDX filings                   | Indonesian | PDFs + Excel + XBRL                              | https://huggingface.co/datasets/horelulus/IDX_Financial_Statements2015-2025Q2 |
| `TheFinAI/MultiFinBen-EnglishOCR`               | SEC filings                   | English    | Page images + ground truth text                  | https://huggingface.co/datasets/TheFinAI/MultiFinBen-EnglishOCR               |
| `arcolab-dev/FinDoc-Robust`                     | 3000 docs                     | English    | Balance sheets with dirty variants, pixel bboxes | https://huggingface.co/datasets/arcolab-dev/FinDoc-Robust                     |
| `AgamiAI/Indian-Bank-Statements`                | Indian bank stmts             | English    | Synthetic, UPI/IMPS/NEFT/RTGS                    | https://huggingface.co/datasets/AgamiAI/Indian-Bank-Statements                |

### 10. Other Datasets

| Dataset                               | Description                                                   | URL                                                            |
| ------------------------------------- | ------------------------------------------------------------- | -------------------------------------------------------------- |
| `ONSBigData/parsing_company_accounts` | UK Companies House PDFs + Tesseract OCR (52 stars)            | https://github.com/ONSBigData/parsing_company_accounts         |
| `finnatsea/bankdata`                  | 1800s US National Bank balance sheets via Google Cloud Vision | https://github.com/finnatsea/bankdata                          |
| SEC EDGAR full-text search            | All US public company filings                                 | https://efts.sec.gov/LATEST/search-index?q=%22balance+sheet%22 |

---

## What Does NOT Exist (Gaps)

| What                                                              | Status                                      |
| ----------------------------------------------------------------- | ------------------------------------------- |
| Raw `.txt` Tesseract OCR output from CAS PDFs + parsed JSON pairs | Not found publicly                          |
| Kaggle dataset with Indian mutual fund statement OCR              | Not found                                   |
| Blog posts showing CAS OCR pipeline before/after                  | Not found                                   |
| casparser test fixtures as text dumps (PDFs are private)          | Private                                     |
| Real CAS PDF files (password-protected with PAN)                  | Not shareable (contain real financial data) |
| Pre-made OCR text for GST invoices                                | Not found                                   |

---

## Recommended Test Document Strategy

For realistic complex financial document tests, use:

1. **UK Balance Sheet (messy OCR):** Companies House samples — real artifacts, 7-15 line items
2. **Indian P&L (multi-column OCR):** Loyal Textile Mills — real scanned PDF, 20+ line items, quarter+year columns
3. **CAS Statement (financial):** Scribd CAMS/NSDL text — real investor data, transactions, multiple schemes
4. **Trial Balance (clean):** Crescent Textiles CSV — 57 line items, IFRS-compliant, balanced
5. **Indian Balance Sheet + P&L (clean):** Hikal Limited — real annual report, 25+ line items each

---

## Key OCR Artifact Patterns to Test Against

- Whitespace padding (column alignment noise)
- `{` instead of `(` (bracket misread)
- `= =` or `G -` (stray noise from ruled lines)
- Note numbers merged into data columns
- Line wrapping ("Creditors: amounts falling due within" → next line → "one year")
- Indian number formatting (1,01,302 = 1 lakh 1 thousand 302)
- Quarter/date column headers merged with data
- OCR character substitution (TEXTIE MIWS → TEXTILE MILLS)
- Parentheses for negatives: `(55,505)` = -55,505
