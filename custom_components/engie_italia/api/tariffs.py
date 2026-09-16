"""Exact offer matching against reviewed public terms; no inferred bill totals."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from types import MappingProxyType
from typing import TYPE_CHECKING

from .models import Utility
from .portal import SupplyStatus

if TYPE_CHECKING:
    from .mobile import MobileSupply


@dataclass(frozen=True, slots=True, repr=False)
class SupplyOffer:
    code: str
    price_type: str
    contract_type: str
    valid_from: date
    valid_until: date
    duration_months: int
    first_activation: date | None


@dataclass(frozen=True, slots=True)
class TariffRate:
    unit_price: Decimal
    annual_fee: Decimal
    unit: str
    network_losses_included: bool = False
    reference_pcs_gj_smc: Decimal | None = None


@dataclass(frozen=True, slots=True)
class VerifiedTariff:
    source_url: str
    source_sha256: str
    offered_from: date
    offered_until: date
    electricity: TariffRate
    gas: TariffRate

    def rate(self, utility: Utility) -> TariffRate:
        return self.electricity if utility is Utility.ELECTRICITY else self.gas


# Public document, reviewed on 2026-09-16. Dates below describe subscription,
# not the account's economic validity. See docs/TARIFFS.md before adding offers.
VERIFIED_TARIFFS = MappingProxyType(
    {
        "PUMD#00016": VerifiedTariff(
            source_url="https://www.engie.it/documents/d/casa/223_pumd-00016",
            source_sha256=(
                "d9342c1e1c7a6813294cef34017928c47442e005b1ef6131443144f4dcc843e5"
            ),
            offered_from=date(2026, 7, 9),
            offered_until=date(2026, 7, 15),
            electricity=TariffRate(
                Decimal("0.11670"), Decimal("72.00"), "EUR/kWh", True
            ),
            gas=TariffRate(
                Decimal("0.45450"),
                Decimal("84.00"),
                "EUR/Smc",
                reference_pcs_gj_smc=Decimal("0.03852"),
            ),
        ),
    }
)


def parse_supply_offer(
    supply: dict, first_activation: date | None
) -> SupplyOffer | None:
    """Optional malformed offer data must not break consumption retrieval."""
    code = supply.get("prodottoCodiceUnivoco")
    if not isinstance(code, str) or not re.fullmatch(r"[A-Z0-9]{2,16}#[0-9]{5}", code):
        return None
    if supply.get("productCode") != code.split("#")[0]:
        return None
    price_type, contract_type = supply.get("priceType"), supply.get("tipoContratto")
    if not isinstance(price_type, str) or not isinstance(contract_type, str):
        return None
    duration = supply.get("durataCE")
    if type(duration) is not int or duration <= 0:
        return None
    dates = []
    for key in ("inizioCE", "fineCE"):
        value = supply.get(key)
        if not isinstance(value, str) or not re.fullmatch(
            r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value
        ):
            return None
        try:
            dates.append(date.fromisoformat(value))
        except ValueError:
            return None
    if dates[0] > dates[1] or dates[0].year == 9999:
        return None
    return SupplyOffer(
        code, price_type, contract_type, *dates, duration, first_activation
    )


def tariff_status(supply: MobileSupply, today: date) -> str:
    """Conservative first-period support; renewal terms need separate evidence."""
    if supply.status is not SupplyStatus.ACTIVE:
        return "inactive"
    offer = supply.offer
    if offer is None:
        return "missing_metadata"
    verified = VERIFIED_TARIFFS.get(offer.code)
    if verified is None:
        return "unverified_offer"
    # These domestic labels have been observed in the Italian mobile response.
    domestic_type = (
        "Domestico residente"
        if supply.utility is Utility.ELECTRICITY
        else "A \u2013 Uso Domestico"
    )
    if offer.price_type != "FIXED" or offer.contract_type != domestic_type:
        return "unsupported_terms"
    if offer.first_activation != offer.valid_from:
        return "unverified_renewal"
    try:
        anniversary = offer.valid_from.replace(year=offer.valid_from.year + 1)
    except ValueError:
        anniversary = date(offer.valid_from.year + 1, 2, 28)
    if (
        offer.duration_months != 12
        or offer.valid_until != anniversary - timedelta(days=1)
        or offer.valid_from < verified.offered_from
        or supply.activation_date is None
        or not offer.valid_from <= supply.activation_date <= offer.valid_until
    ):
        return "unsupported_terms"
    if today < max(offer.valid_from, supply.activation_date):
        return "not_yet_valid"
    if today > offer.valid_until:
        return "expired"
    return "verified"


def current_tariff(supply: MobileSupply, today: date) -> TariffRate | None:
    if tariff_status(supply, today) != "verified":
        return None
    return VERIFIED_TARIFFS[supply.offer.code].rate(supply.utility)
