"""Invented invoice metadata matching the statically verified mobile DTO."""


def invoice(**changes):
    return {
        "fiscalNumber": "SYNTHETIC-2025-002",
        "documentId": "synthetic-private-document-id",
        "amount": 100.75,
        "unpaidRemainingAmount": 100.75,
        "vatAmount": 9.16,
        "emissionDate": "2025-03-01",
        "expiryDate": "2025-03-20",
        "billingPeriodStartDate": "2025-01-01",
        "billingPeriodEndDate": "2025-02-28",
        "invoiceStatus": "NOT_PAID",
        "pdfUrl": "https://example.invalid/private-invoice.pdf",
        "supply": "synthetic-private-supply",
        **changes,
    }


def invoices(*rows, **changes):
    return {
        "code": "OK",
        "response": {"invoices": list(rows), "inMaintenance": False},
        **changes,
    }
