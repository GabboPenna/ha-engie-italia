import unittest
from datetime import UTC, date, datetime
from decimal import Decimal

from invoice_fixtures import invoice, invoices

from engie_italia.errors import PayloadError, ServiceError
from engie_italia.invoices import InvoiceSnapshot, merge_invoices, parse_invoices

NOW = datetime(2025, 3, 11, tzinfo=UTC)


def snapshot(*rows):
    return InvoiceSnapshot(parse_invoices(invoices(*rows)), NOW)


class InvoiceTests(unittest.TestCase):
    def test_partial_payments_use_residual_and_paid_documents_do_not_add_debt(self):
        result = snapshot(
            invoice(
                fiscalNumber="SYNTHETIC-OLD",
                emissionDate="2025-01-01",
                invoiceStatus="PAID",
                unpaidRemainingAmount=0,
            ),
            invoice(),
            invoice(
                fiscalNumber="SYNTHETIC-PARTIAL",
                emissionDate="2025-02-01",
                invoiceStatus="PARTIALLY_PAID",
                unpaidRemainingAmount=20.25,
                expiryDate="2025-03-10",
            ),
        )
        self.assertEqual(result.open_count, 2)
        self.assertEqual(result.outstanding, Decimal("121.00"))
        self.assertEqual(result.overdue_count(NOW.date()), 1)
        self.assertEqual(result.earliest_due, date(2025, 3, 10))
        self.assertEqual(result.latest.reference, "SYNTHETIC-2025-002")
        self.assertEqual(result.latest.amount, Decimal("100.75"))
        self.assertEqual(result.data_status(NOW.date()), "available")

    def test_valid_empty_history_and_fully_paid_history_report_zero(self):
        for result in (
            snapshot(),
            snapshot(invoice(invoiceStatus="PAID", unpaidRemainingAmount=None)),
        ):
            self.assertEqual(result.open_count, 0)
            self.assertEqual(result.outstanding, Decimal(0))
            self.assertEqual(result.overdue_count(NOW.date()), 0)
            self.assertIsNone(result.earliest_due)
        self.assertIsNone(snapshot().latest)
        self.assertEqual(snapshot().data_status(NOW.date()), "no_invoices")

    def test_empty_response_with_engie_error_is_never_zero_debt(self):
        with self.assertRaises(ServiceError) as error:
            parse_invoices(
                invoices(engieErrorCode=9, engieDetailedErrorCode=Decimal("9.91"))
            )
        self.assertEqual(error.exception.error_code, 9)
        self.assertEqual(error.exception.detailed_code, Decimal("9.91"))
        with self.assertRaises(ServiceError):
            parse_invoices(
                invoices(invoice(), engieErrorCode=0, engieDetailedErrorCode=9.91)
            )
        self.assertEqual(
            parse_invoices(invoices(engieErrorCode=0, engieDetailedErrorCode=0)), ()
        )

    def test_maintenance_or_missing_history_cannot_clear_debt(self):
        for response, error in (
            ({"invoices": [], "inMaintenance": True}, ServiceError),
            ({"invoices": [], "inMaintenance": "false"}, PayloadError),
            ({}, PayloadError),
            ({"invoices": None}, PayloadError),
            ({"invoices": {}}, PayloadError),
        ):
            with self.subTest(response=response), self.assertRaises(error):
                parse_invoices({"code": "OK", "response": response})

    def test_unknown_status_or_contradictory_paid_balance_is_incomplete(self):
        for changes in (
            {"invoiceStatus": "FUTURE_STATUS"},
            {"invoiceStatus": None},
            {"invoiceStatus": "PAID", "unpaidRemainingAmount": 1},
            {"unpaidRemainingAmount": -1},
        ):
            with self.subTest(changes=changes):
                result = snapshot(invoice(**changes))
                self.assertIsNone(result.open_count)
                self.assertIsNone(result.outstanding)
                self.assertIsNone(result.overdue_count(NOW.date()))
                self.assertEqual(result.data_status(NOW.date()), "incomplete")
                self.assertIsNotNone(result.latest)

    def test_missing_residual_does_not_fall_back_to_full_invoice_amount(self):
        result = snapshot(
            invoice(invoiceStatus="PARTIALLY_PAID", unpaidRemainingAmount=None)
        )
        self.assertEqual(result.open_count, 1)
        self.assertIsNone(result.outstanding)
        self.assertEqual(result.data_status(NOW.date()), "incomplete")

    def test_negative_credit_is_preserved_without_cancelling_other_debt(self):
        result = snapshot(
            invoice(
                fiscalNumber="CREDIT",
                amount=-10,
                invoiceStatus="PAID",
                unpaidRemainingAmount=0,
                emissionDate="2025-03-02",
            ),
            invoice(),
        )
        self.assertEqual(result.latest.amount, Decimal(-10))
        self.assertEqual(result.outstanding, Decimal("100.75"))

    def test_missing_dates_do_not_guess_latest_or_due_date(self):
        result = snapshot(invoice(emissionDate=None))
        self.assertIsNone(result.latest)
        self.assertEqual(result.data_status(NOW.date()), "incomplete")
        result = snapshot(invoice(expiryDate=None))
        self.assertIsNone(result.earliest_due)
        self.assertIsNone(result.overdue_count(NOW.date()))
        result = snapshot(invoice(expiryDate=None, invoiceStatus="EXPIRED"))
        self.assertEqual(result.overdue_count(NOW.date()), 1)
        self.assertEqual(result.data_status(NOW.date()), "incomplete")

    def test_due_today_is_not_overdue_and_expired_status_is_respected(self):
        result = snapshot(invoice(expiryDate=NOW.date().isoformat()))
        self.assertEqual(result.overdue_count(NOW.date()), 0)
        self.assertEqual(result.overdue_count(date(2025, 3, 12)), 1)
        self.assertEqual(
            snapshot(invoice(invoiceStatus="EXPIRED")).overdue_count(NOW.date()), 1
        )

    def test_latest_reference_is_stable_on_payment_changes_and_reordering(self):
        older = invoice(fiscalNumber="SYNTHETIC-001", emissionDate="2025-02-01")
        current = invoice()
        reference = snapshot(older, current).latest.reference
        self.assertEqual(snapshot(current, older).latest.reference, reference)
        self.assertEqual(
            snapshot(
                older, invoice(invoiceStatus="PAID", unpaidRemainingAmount=0)
            ).latest.reference,
            reference,
        )
        self.assertNotEqual(
            snapshot(
                current, invoice(fiscalNumber="SYNTHETIC-2025-003")
            ).latest.reference,
            reference,
        )

    def test_duplicates_do_not_double_count_and_conflicts_reject_whole_result(self):
        rows = parse_invoices(
            invoices(invoice(), invoice(pdfUrl="https://example.invalid/changed"))
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(len(merge_invoices(rows + rows)), 1)
        with self.assertRaises(PayloadError) as error:
            parse_invoices(invoices(invoice(), invoice(amount=2)))
        self.assertNotIn("SYNTHETIC", str(error.exception))

    def test_malformed_financial_fields_fail_without_leaking_values(self):
        cases = [
            {field: value}
            for field in ("amount", "unpaidRemainingAmount")
            for value in (True, "private-amount", float("nan"), float("inf"), 1e13, {})
        ] + [
            {"fiscalNumber": ""},
            {"fiscalNumber": "x" * 256},
            {"emissionDate": "private-date"},
            {"expiryDate": "2025-02-30"},
        ]
        for changes in cases:
            with (
                self.subTest(changes=changes),
                self.assertRaises(PayloadError) as error,
            ):
                snapshot(invoice(**changes))
            self.assertNotIn("private", str(error.exception))
        with self.assertRaises(PayloadError):
            parse_invoices(invoices(engieErrorCode=True))

    def test_models_exclude_private_fields_and_do_not_log_invoice_metadata(self):
        result = snapshot(invoice())
        self.assertNotIn("SYNTHETIC", repr(result))
        self.assertNotIn("SYNTHETIC", repr(result.invoices))
        for field in ("pdfUrl", "documentId", "supply"):
            self.assertFalse(hasattr(result.latest, field))
