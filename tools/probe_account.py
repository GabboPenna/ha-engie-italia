"""Optional interactive supply probe; no stored session or account response dumps."""

import argparse
import json
from urllib.parse import urlsplit

from engie_italia.diagnostics import portal_summary
from engie_italia.portal import PortalPayloadError, parse_dashboard_supplies

PORTAL = "https://4you.engie.it/spazioclienti/ACMAAuthentication"
DASHBOARD = "https://4you.engie.it/spazioclienti/ACMADashboard"


def read_supply_summary(page) -> dict:
    url = urlsplit(page.url)
    if (url.scheme, url.netloc, url.path) != (
        "https",
        "4you.engie.it",
        "/spazioclienti/ACMADashboard",
    ):
        raise PortalPayloadError("An authenticated dashboard is required")
    supplies = parse_dashboard_supplies(page.evaluate("() => window.__data__"))
    return {
        "probe_status": "supplies_read",
        "consumption_history": "not_tested",
        "automatic_authentication": "not_implemented",
        "session_persisted": False,
        **portal_summary(supplies),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--timeout", type=int, default=600, help="Login timeout in seconds"
    )
    args = parser.parse_args()
    if not 60 <= args.timeout <= 1800:
        parser.error("--timeout must be between 60 and 1800 seconds")
    try:
        from playwright.sync_api import Error, sync_playwright
    except ImportError:
        print("Install the browser extra and Chromium as described in README.md.")
        return 2

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            try:
                context = browser.new_context()
                page = context.new_page()
                page.goto(PORTAL, wait_until="domcontentloaded", timeout=30000)
                page.get_by_role(
                    "button", name="Continua senza accettare", exact=True
                ).click(timeout=15000)
                page.get_by_role("button", name="Accedi", exact=True).click(
                    timeout=15000
                )
                print("Completa il login nel browser, incluso l'eventuale OTP.")
                print(
                    "Non inserire credenziali nel terminale. "
                    "Chiudi il browser per annullare."
                )
                page.wait_for_url(DASHBOARD, timeout=args.timeout * 1000)
                page.wait_for_function(
                    "() => window.__data__?.contractChains != null", timeout=30000
                )
                print(json.dumps(read_supply_summary(page), indent=2))
            finally:
                browser.close()
    except (Error, PortalPayloadError):
        # Do not print exception details: URLs and payloads can identify an account.
        print("Account probe failed or cancelled. No session was exported.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
