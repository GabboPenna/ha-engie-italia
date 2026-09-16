"""No network or credentials: exercise the account probe with a fake page."""

import unittest
from unittest.mock import Mock

from engie_italia.portal import PortalPayloadError
from tools.probe_account import DASHBOARD, read_supply_summary


class AccountProbeTests(unittest.TestCase):
    def test_only_supply_summary_is_returned(self):
        page = Mock(url=DASHBOARD)
        page.evaluate.return_value = {
            "info": {"email": "synthetic@example.invalid"},
            "contractChains": {
                "synthetic-chain": {
                    "forniture": [
                        {"id": "synthetic", "commodity": "Gas", "statoCalc": "attiva"}
                    ]
                }
            },
        }
        result = read_supply_summary(page)
        self.assertEqual(result["supplies"], [{"utility": "gas", "status": "active"}])
        self.assertEqual(result["consumption_history"], "not_tested")
        self.assertFalse(result["session_persisted"])
        self.assertNotIn("synthetic", str(result))
        page.evaluate.assert_called_once_with("() => window.__data__")

    def test_login_and_other_origins_are_never_inspected(self):
        for url in (
            "https://login.engie.it/u/login/password",
            "https://example.invalid/spazioclienti/ACMADashboard",
            DASHBOARD.replace("https:", "http:"),
            DASHBOARD.replace("4you.engie.it", "4you.engie.it.example.invalid"),
            DASHBOARD.replace("4you.engie.it", "user@4you.engie.it"),
            "https://4you.engie.it/spazioclienti/ACMAAuthentication",
        ):
            page = Mock(url=url)
            with self.subTest(url=url), self.assertRaises(PortalPayloadError):
                read_supply_summary(page)
            page.evaluate.assert_not_called()

    def test_missing_payload_is_not_a_successful_empty_account(self):
        page = Mock(url=DASHBOARD)
        page.evaluate.return_value = None
        with self.assertRaises(PortalPayloadError):
            read_supply_summary(page)


if __name__ == "__main__":
    unittest.main()
