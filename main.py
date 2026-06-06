import logging

from extraction import get_client, extract_structured
from schemas.invoice import Invoice

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

OCR_DOCUMENT = """--------------------------------------------------
INVOICE / TAX INV0ICE
Doc No : INV-2026-00481

Custorner Name : Acme Trading Pvt Ltd
GSTlN : 29ABCDE1234F1Z5

Bill To
Acme Trading Pvt Ltd.
#18 3rd Fioor Tech Park
WhitefieId Bangalore Karnatka

Phone : 98B76 54321
Email : accounts@acmetrading.co.in

Item Descriptlon

1 Wireless Mouse Qty 2
Rate 899.00 Amount 1798.00

2 Mechanical Keyboad Qty 1
Rate 3499.00 Amount 3499.00

3 USB-C Hub
Qty l
Rate 1499.OO
Amount 1499.00

Sub TotaI 6796.00

Discount
5 % -339.80

Taxable Value 6456.20

CGST @ 9% 581.06
SGST @ 9% 581.06

Grand TotaI 7618.32

Amount in Words
Seven Thousand Six Hundred Eighteen Rupees and
Thirty Two Paisa Only

Payment Terms : Net 30 Days

Bank Name : HDFC BANK
A/c No : 50100123456789
IFSC : HDFC0001234

Date : O2/O6/2O26

Thank you for your buslness

*** Scanned using Mobile Scanner ***
Page 1 of 1

Ref : SO-7782
Customer PO : PO-99182

Signature"""


def main():
    client = get_client()

    result = extract_structured(
        client=client,
        document=OCR_DOCUMENT,
        schema=Invoice,
        tool_name="parse_invoice",
        tool_description="Parse an OCR-scanned invoice into structured data.",
    )

    log.info("═══ Summary ═══")
    log.info("Data         : %s", result.data)
    log.info("Time         : %.2fs", result.elapsed)
    log.info("Attempts     : %d", result.attempts)
    log.info("Input tokens : %d", result.input_tokens)
    log.info("Output tokens: %d", result.output_tokens)
    log.info("Total tokens : %d", result.input_tokens + result.output_tokens)


if __name__ == "__main__":
    main()
