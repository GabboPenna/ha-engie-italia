"""Inspect the public sign-in route without credentials or persistent browser data."""

import json
from urllib.parse import urlsplit

PORTAL = "https://4you.engie.it/spazioclienti/ACMAAuthentication"


def main() -> int:
    try:
        from playwright.sync_api import Error, sync_playwright
    except ImportError:
        print("Install the browser extra and Chromium as described in README.md.")
        return 2

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
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
                page.wait_for_url("https://login.engie.it/**", timeout=15000)
                page.locator("input[name='username']").wait_for(
                    state="visible", timeout=15000
                )
                login = urlsplit(page.url)
                print(
                    json.dumps(
                        {
                            "portal_origin": "https://4you.engie.it",
                            "login_origin": f"{login.scheme}://{login.netloc}",
                            "email_field_visible": True,
                            "authenticated": False,
                            "session_persisted": False,
                        },
                        indent=2,
                    )
                )
            finally:
                browser.close()
    except Error:
        # Browser errors may contain redirect URLs with transient session values.
        print("Public login inspection failed; no authenticated access was attempted.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
