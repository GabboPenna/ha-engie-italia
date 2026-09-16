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


# Public documents reviewed on 2026-09-17. Dates describe subscription,
# not the account's economic validity. Each exact code has its own prices.
# PUMD#00019 remains unverified. See docs/TARIFFS.md and docs/TARIFF_SOURCES.md.
VERIFIED_TARIFFS = MappingProxyType(
    {
        "PUMD#00008": VerifiedTariff(
            source_url="https://www.engie.it/documents/d/casa/223_pumd-00008",
            source_sha256=(
                "b897d5d682a7797fb27a6ad717dcdc5f73555c1b31c7960783325e57951851ec"
            ),
            offered_from=date(2026, 5, 7),
            offered_until=date(2026, 5, 13),
            electricity=TariffRate(
                Decimal("0.11620"), Decimal("72.00"), "EUR/kWh", True
            ),
            gas=TariffRate(
                Decimal("0.48400"),
                Decimal("84.00"),
                "EUR/Smc",
                reference_pcs_gj_smc=Decimal("0.03852"),
            ),
        ),
        "PUMD#00009": VerifiedTariff(
            source_url="https://www.engie.it/documents/d/casa/223_pumd-00009",
            source_sha256=(
                "812d3f563df69361fedada0e5b2779653438dc2008682be97b56eabc566f152d"
            ),
            offered_from=date(2026, 5, 14),
            offered_until=date(2026, 5, 20),
            electricity=TariffRate(
                Decimal("0.11620"), Decimal("72.00"), "EUR/kWh", True
            ),
            gas=TariffRate(
                Decimal("0.47600"),
                Decimal("84.00"),
                "EUR/Smc",
                reference_pcs_gj_smc=Decimal("0.03852"),
            ),
        ),
        "PUMD#00010": VerifiedTariff(
            source_url="https://www.engie.it/documents/d/casa/223_pumd-00010",
            source_sha256=(
                "6c080299b38b0600bec24296bb630d740fc19a29a29c7a87f3c44cc068d1951b"
            ),
            offered_from=date(2026, 5, 21),
            offered_until=date(2026, 5, 27),
            electricity=TariffRate(
                Decimal("0.11675"), Decimal("72.00"), "EUR/kWh", True
            ),
            gas=TariffRate(
                Decimal("0.48300"),
                Decimal("84.00"),
                "EUR/Smc",
                reference_pcs_gj_smc=Decimal("0.03852"),
            ),
        ),
        "PUMD#00011": VerifiedTariff(
            source_url="https://www.engie.it/documents/d/casa/223_pumd-00011",
            source_sha256=(
                "7e4d65e774e8b381543478b376b323764515a910a888fdb92cf102748408be46"
            ),
            offered_from=date(2026, 5, 28),
            offered_until=date(2026, 6, 10),
            electricity=TariffRate(
                Decimal("0.12290"), Decimal("72.00"), "EUR/kWh", True
            ),
            gas=TariffRate(
                Decimal("0.48300"),
                Decimal("84.00"),
                "EUR/Smc",
                reference_pcs_gj_smc=Decimal("0.03852"),
            ),
        ),
        "PUMD#00012": VerifiedTariff(
            source_url="https://www.engie.it/documents/d/casa/223_pumd-00012",
            source_sha256=(
                "6302f1974c755a311f7da87c32039f9440663da1fee298da7613ce15771ee606"
            ),
            offered_from=date(2026, 6, 11),
            offered_until=date(2026, 6, 17),
            electricity=TariffRate(
                Decimal("0.12290"), Decimal("72.00"), "EUR/kWh", True
            ),
            gas=TariffRate(
                Decimal("0.48300"),
                Decimal("84.00"),
                "EUR/Smc",
                reference_pcs_gj_smc=Decimal("0.03852"),
            ),
        ),
        "PUMD#00013": VerifiedTariff(
            source_url="https://www.engie.it/documents/d/casa/223_pumd-00013",
            source_sha256=(
                "900f074fb8296e05ab0dbcafe1122b636edcf18ffc239eba2cb42414233ebdd8"
            ),
            offered_from=date(2026, 6, 18),
            offered_until=date(2026, 6, 24),
            electricity=TariffRate(
                Decimal("0.11860"), Decimal("72.00"), "EUR/kWh", True
            ),
            gas=TariffRate(
                Decimal("0.48300"),
                Decimal("84.00"),
                "EUR/Smc",
                reference_pcs_gj_smc=Decimal("0.03852"),
            ),
        ),
        "PUMD#00014": VerifiedTariff(
            source_url="https://www.engie.it/documents/d/casa/223_pumd-00014",
            source_sha256=(
                "cc4550698514f0c8a96f3987c8b72d8a5575fd3d318138c1c9b14542714bc0a5"
            ),
            offered_from=date(2026, 6, 25),
            offered_until=date(2026, 7, 1),
            electricity=TariffRate(
                Decimal("0.11860"), Decimal("72.00"), "EUR/kWh", True
            ),
            gas=TariffRate(
                Decimal("0.48300"),
                Decimal("84.00"),
                "EUR/Smc",
                reference_pcs_gj_smc=Decimal("0.03852"),
            ),
        ),
        "PUMD#00015": VerifiedTariff(
            source_url="https://www.engie.it/documents/d/casa/223_pumd-00015",
            source_sha256=(
                "ec8c021db45cd756ab32de26221e595af23f6195777cfd1ec5e07aa471c46344"
            ),
            offered_from=date(2026, 7, 2),
            offered_until=date(2026, 7, 8),
            electricity=TariffRate(
                Decimal("0.11860"), Decimal("72.00"), "EUR/kWh", True
            ),
            gas=TariffRate(
                Decimal("0.46450"),
                Decimal("84.00"),
                "EUR/Smc",
                reference_pcs_gj_smc=Decimal("0.03852"),
            ),
        ),
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
        "PUMD#00017": VerifiedTariff(
            source_url="https://www.engie.it/documents/d/casa/223_pumd-00017",
            source_sha256=(
                "12e2bdbd95e65f9ef666ae582c0a416c427e56d9a9c4ea483ae7a04ca368df2a"
            ),
            offered_from=date(2026, 7, 16),
            offered_until=date(2026, 7, 22),
            electricity=TariffRate(
                Decimal("0.11340"), Decimal("72.00"), "EUR/kWh", True
            ),
            gas=TariffRate(
                Decimal("0.45450"),
                Decimal("84.00"),
                "EUR/Smc",
                reference_pcs_gj_smc=Decimal("0.03852"),
            ),
        ),
        "PUMD#00018": VerifiedTariff(
            source_url="https://www.engie.it/documents/d/casa/223_pumd-00018",
            source_sha256=(
                "9693c4bcf55700455f8100dfd5d759c5490e6baf98047befa5b0f87196abc36d"
            ),
            offered_from=date(2026, 7, 23),
            offered_until=date(2026, 7, 29),
            electricity=TariffRate(
                Decimal("0.12051"), Decimal("72.00"), "EUR/kWh", True
            ),
            gas=TariffRate(
                Decimal("0.53900"),
                Decimal("84.00"),
                "EUR/Smc",
                reference_pcs_gj_smc=Decimal("0.03852"),
            ),
        ),
        "PUMD#00020": VerifiedTariff(
            source_url="https://www.engie.it/documents/d/casa/223_pumd-00020",
            source_sha256=(
                "e479ea6ae30189c3ed0fcf64edbe3adeb6a1c3cf8012adfb27ec5fca8476a0f9"
            ),
            offered_from=date(2026, 8, 6),
            offered_until=date(2026, 8, 19),
            electricity=TariffRate(
                Decimal("0.12865"), Decimal("72.00"), "EUR/kWh", True
            ),
            gas=TariffRate(
                Decimal("0.55450"),
                Decimal("84.00"),
                "EUR/Smc",
                reference_pcs_gj_smc=Decimal("0.03852"),
            ),
        ),
        "PUMD#00021": VerifiedTariff(
            source_url="https://www.engie.it/documents/d/casa/223_pumd-00021",
            source_sha256=(
                "67f54b1a1ae2b607930205ae6355834851c540b0f6557d54279c6af3aff15997"
            ),
            offered_from=date(2026, 8, 20),
            offered_until=date(2026, 8, 26),
            electricity=TariffRate(
                Decimal("0.13500"), Decimal("72.00"), "EUR/kWh", True
            ),
            gas=TariffRate(
                Decimal("0.55450"),
                Decimal("84.00"),
                "EUR/Smc",
                reference_pcs_gj_smc=Decimal("0.03852"),
            ),
        ),
        "PUMD#00022": VerifiedTariff(
            source_url="https://www.engie.it/documents/d/casa/223_pumd-00022",
            source_sha256=(
                "c5817d1f6f5fb1bc1e7d44e015aa4196fd691d4cdb06afa2220dbaad5b657088"
            ),
            offered_from=date(2026, 8, 27),
            offered_until=date(2026, 9, 2),
            electricity=TariffRate(
                Decimal("0.14090"), Decimal("72.00"), "EUR/kWh", True
            ),
            gas=TariffRate(
                Decimal("0.59900"),
                Decimal("84.00"),
                "EUR/Smc",
                reference_pcs_gj_smc=Decimal("0.03852"),
            ),
        ),
        "PUMD#00023": VerifiedTariff(
            source_url="https://www.engie.it/documents/d/casa/223_pumd-00023",
            source_sha256=(
                "ae69c0941d7f2696347efd60e020fc3b5976672e30761320199b309684ef659d"
            ),
            offered_from=date(2026, 9, 3),
            offered_until=date(2026, 9, 9),
            electricity=TariffRate(
                Decimal("0.14090"), Decimal("72.00"), "EUR/kWh", True
            ),
            gas=TariffRate(
                Decimal("0.69000"),
                Decimal("84.00"),
                "EUR/Smc",
                reference_pcs_gj_smc=Decimal("0.03852"),
            ),
        ),
        "PUMD#00024": VerifiedTariff(
            source_url="https://www.engie.it/documents/d/casa/223_pumd-00024",
            source_sha256=(
                "892bd27e3e0b0c208dc683d6d1078f8cc66374283827c8781e16954efac3721c"
            ),
            offered_from=date(2026, 9, 10),
            offered_until=date(2026, 9, 16),
            electricity=TariffRate(
                Decimal("0.18400"), Decimal("120.00"), "EUR/kWh", True
            ),
            gas=TariffRate(
                Decimal("0.75000"),
                Decimal("120.00"),
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
