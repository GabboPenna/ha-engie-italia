"""Entirely invented offer metadata and prices for offline tests."""

from datetime import date
from decimal import Decimal

from mobile_fixtures import supplies


def tariff_supplies():
    data = supplies()
    for supply in data["listaContratti"][0]["forniture"]:
        supply.update(
            productCode="SYNTHETIC",
            prodottoCodiceUnivoco="SYNTHETIC#00123",
            nomeOfferta="Invented offer, not used to find a price",
            priceType="FIXED",
            tipoContratto="Domestico residente"
            if supply["commodity"] == "Luce"
            else "A \u2013 Uso Domestico",
            inizioCE="2025-03-01",
            fineCE="2026-02-28",
            durataCE=12,
        )
    return data


def catalog(api):
    return {
        "SYNTHETIC#00123": api.VerifiedTariff(
            source_url="https://example.invalid/synthetic-terms.pdf",
            source_sha256="b" * 64,
            offered_from=date(2025, 1, 1),
            offered_until=date(2025, 1, 8),
            electricity=api.TariffRate(
                Decimal("0.12345"), Decimal("65.00"), "EUR/kWh", True
            ),
            gas=api.TariffRate(
                Decimal("0.56789"),
                Decimal("75.00"),
                "EUR/Smc",
                reference_pcs_gj_smc=Decimal("0.03999"),
            ),
        )
    }
