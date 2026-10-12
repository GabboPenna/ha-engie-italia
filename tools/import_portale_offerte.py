"""Inventory simple ENGIE fixed offers from official Portale Offerte snapshots."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

SELLER_VAT = b"06289781004"
BASE_URL = (
    "https://www.ilportaleofferte.it/portaleOfferte/resources/opendata/csv/offerteML"
)
OFFER_PATTERN = re.compile(rb"<offerta(?:\s[^>]*)?>.*?</offerta>", re.DOTALL)


@dataclass(frozen=True, slots=True)
class Candidate:
    code: str | None
    commodity: str
    full_code: str
    name: str
    eligible: bool
    reasons: tuple[str, ...]
    rate: dict[str, object] | None


def _text(element: ET.Element, path: str) -> str | None:
    item = element.find(path)
    return item.text.strip() if item is not None and item.text else None


def _date(value: str | None) -> date:
    if value is None:
        raise ValueError("missing offer date")
    return datetime.strptime(value, "%d/%m/%Y_%H:%M:%S").date()


def _decimal(value: str | None) -> Decimal:
    if value is None:
        raise ValueError("missing price")
    result = Decimal(value)
    if not result.is_finite() or result < 0:
        raise ValueError("invalid price")
    return result


def short_offer_code(full_code: str) -> str | None:
    """Recover the mobile API code from the standardized 32-character code."""
    if not re.fullmatch(r"[A-Z0-9]{32}", full_code) or full_code[13:15] != "XX":
        return None
    sequence, tail = full_code[11:13], full_code[15:]
    for split in range(2, min(16, len(tail) - 4)):
        family = tail[:split]
        revision = tail[split : split + 5]
        padding = tail[split + 5 :]
        if (
            re.fullmatch(r"[A-Z][A-Z0-9]{1,15}", family)
            and revision.isdigit()
            and revision[-2:] == sequence
            and padding
            and set(padding) == {"0"}
        ):
            return f"{family}#{revision}"
    return None


def _simple_component_total(
    root: ET.Element, *, macroarea: str, unit: str, electricity: bool
) -> Decimal | None:
    values: list[Decimal] = []
    matched_area = False
    for component in root.findall("ComponenteImpresa"):
        if _text(component, "MACROAREA") != macroarea:
            continue
        matched_area = True
        intervals = component.findall("IntervalloPrezzi")
        if not intervals:
            raise ValueError("component without price interval")
        for interval in intervals:
            allowed = {"PREZZO", "UNITA_MISURA"}
            if macroarea == "04":
                allowed.add("FASCIA_COMPONENTE")
            if any(child.tag not in allowed for child in interval):
                raise ValueError("tiered or time-limited component")
            if _text(interval, "UNITA_MISURA") != unit:
                raise ValueError("unsupported component unit")
            band = _text(interval, "FASCIA_COMPONENTE")
            if macroarea == "04" and band not in (None, "01"):
                raise ValueError("multi-band component")
            values.append(_decimal(_text(interval, "PREZZO")))
    if matched_area and not values:
        raise ValueError("component price not found")
    return sum(values, Decimal()) if values else None


def parse_candidate(block: bytes, source_url: str) -> Candidate:
    root = ET.fromstring(block)
    full_code = _text(root, "./IdentificativiOfferta/COD_OFFERTA") or ""
    commodity_code = full_code[6:7]
    commodity = {"E": "electricity", "G": "gas"}.get(commodity_code, "dual")
    code = short_offer_code(full_code)
    reasons: list[str] = []

    if code is None:
        reasons.append("non-standard offer code")
    if commodity == "dual":
        reasons.append("combined record needs an explicit commodity split")
    expected_market = {"electricity": "01", "gas": "02", "dual": "03"}[commodity]
    if _text(root, "./DettaglioOfferta/TIPO_MERCATO") != expected_market:
        reasons.append("not a free-market offer")
    if _text(root, "./DettaglioOfferta/TIPO_CLIENTE") != "01":
        reasons.append("not a domestic offer")
    if _text(root, "./DettaglioOfferta/TIPO_OFFERTA") != "01":
        reasons.append("not a fixed-price offer")
    if (
        commodity == "electricity"
        and _text(root, "./TipoPrezzo/TIPOLOGIA_FASCE") != "01"
    ):
        reasons.append("not a single-band electricity offer")
    if root.find(".//Sconto") is not None:
        reasons.append("discount requires explicit modelling")

    rate = None
    try:
        duration = int(_text(root, "./DettaglioOfferta/DURATA") or "")
        if duration <= 0:
            raise ValueError("invalid duration")
        offered_from = _date(_text(root, "./ValiditaOfferta/DATA_INIZIO"))
        offered_until = _date(_text(root, "./ValiditaOfferta/DATA_FINE"))
        if offered_from > offered_until:
            raise ValueError("reversed subscription dates")
        if commodity in ("electricity", "gas"):
            electricity = commodity == "electricity"
            price = _simple_component_total(
                root,
                macroarea="04",
                unit="03" if electricity else "04",
                electricity=electricity,
            )
            annual_fee = _simple_component_total(
                root, macroarea="01", unit="01", electricity=electricity
            )
            if price is None:
                raise ValueError("energy component not found")
            rate = {
                "source_url": source_url,
                "source_sha256": hashlib.sha256(block).hexdigest(),
                "offered_from": offered_from.isoformat(),
                "offered_until": offered_until.isoformat(),
                "duration_months": duration,
                "unit_price": format(price, "f"),
                "annual_fee": format(annual_fee or Decimal(), "f"),
                "unit": "EUR/kWh" if electricity else "EUR/Smc",
                (
                    "network_losses_included" if electricity else "reference_pcs_gj_smc"
                ): None,
            }
    except (ValueError, ArithmeticError) as err:
        reasons.append(str(err))

    return Candidate(
        code,
        commodity,
        full_code,
        _text(root, "./DettaglioOfferta/NOME_OFFERTA") or "",
        not reasons and rate is not None,
        tuple(dict.fromkeys(reasons)),
        rate if not reasons else None,
    )


def snapshot_url(day: date, commodity: str) -> str:
    return (
        f"{BASE_URL}/{day.year}_{day.month}/"
        f"PO_Offerte_{commodity}_MLIBERO_{day:%Y%m%d}.xml"
    )


def _remote_size(url: str, timeout: float) -> int:
    request = Request(url, method="HEAD", headers={"User-Agent": "ha-engie-italia"})
    with urlopen(request, timeout=timeout) as response:
        return int(response.headers["Content-Length"])


def _range(url: str, start: int, end: int, timeout: float) -> bytes:
    request = Request(
        url,
        headers={
            "Range": f"bytes={start}-{end}",
            "User-Agent": "ha-engie-italia",
        },
    )
    with urlopen(request, timeout=timeout) as response:
        return response.read()


def _seller_window(
    url: str, *, previous_ratio: float | None, timeout: float
) -> tuple[bytes, float]:
    size = _remote_size(url, timeout)
    if size <= 1_000_000:
        data = _range(url, 0, size - 1, timeout)
        index = data.find(SELLER_VAT)
        if index < 0:
            return data, previous_ratio or 0.5
        return data, index / size

    if previous_ratio is not None:
        span = max(1_000_000, size // 10)
        center = int(size * previous_ratio)
        start = max(0, center - span // 2)
        data = _range(url, start, min(size - 1, start + span), timeout)
        index = data.find(SELLER_VAT)
        if index >= 0:
            absolute = start + index
            margin = 750_000
            window_start = max(0, absolute - margin)
            return (
                _range(url, window_start, min(size - 1, absolute + margin), timeout),
                absolute / size,
            )

    chunk = 1_000_000
    for start in range(0, size, chunk):
        data = _range(url, start, min(size - 1, start + chunk - 1), timeout)
        index = data.find(SELLER_VAT)
        if index >= 0:
            absolute = start + index
            margin = 750_000
            window_start = max(0, absolute - margin)
            return (
                _range(url, window_start, min(size - 1, absolute + margin), timeout),
                absolute / size,
            )
    return b"", previous_ratio or 0.5


def inventory(
    start: date, end: date, *, step_days: int = 7, timeout: float = 60
) -> tuple[list[dict[str, object]], dict[str, dict[str, dict[str, object]]]]:
    found: dict[tuple[str, str], Candidate] = {}
    conflicts: set[tuple[str, str]] = set()
    ratios: dict[str, float | None] = {"E": None, "G": None, "D": None}
    day = start
    while day <= end:
        for commodity in ratios:
            url = snapshot_url(day, commodity)
            try:
                data, ratios[commodity] = _seller_window(
                    url, previous_ratio=ratios[commodity], timeout=timeout
                )
            except HTTPError as err:
                if err.code == 404:
                    continue
                raise
            for block in OFFER_PATTERN.findall(data):
                if SELLER_VAT not in block:
                    continue
                candidate = parse_candidate(block, url)
                key = (candidate.code or candidate.full_code, candidate.commodity)
                previous = found.get(key)
                if previous is None:
                    found[key] = candidate
                else:
                    merged = _merge_candidates(previous, candidate)
                    if merged is None:
                        conflicts.add(key)
                    else:
                        found[key] = merged
        day += timedelta(days=step_days)

    rows = []
    offers: dict[str, dict[str, dict[str, object]]] = {}
    for key, candidate in sorted(found.items()):
        row = asdict(candidate)
        if key in conflicts:
            row["eligible"] = False
            row["rate"] = None
            row["reasons"] = [*row["reasons"], "conflicting snapshots"]
        rows.append(row)
        if row["eligible"] and candidate.code and candidate.rate:
            offers.setdefault(candidate.code, {})[candidate.commodity] = candidate.rate
    return rows, offers


def _rate_terms(rate: dict[str, object] | None) -> dict[str, object] | None:
    if rate is None:
        return None
    return {
        key: value
        for key, value in rate.items()
        if key not in {"source_url", "source_sha256", "offered_from", "offered_until"}
    }


def _merge_candidates(previous: Candidate, current: Candidate) -> Candidate | None:
    if (
        previous.eligible != current.eligible
        or previous.reasons != current.reasons
        or _rate_terms(previous.rate) != _rate_terms(current.rate)
    ):
        return None
    if previous.rate is None or current.rate is None:
        return previous

    previous_start = str(previous.rate["offered_from"])
    previous_end = str(previous.rate["offered_until"])
    current_start = str(current.rate["offered_from"])
    current_end = str(current.rate["offered_until"])
    if current_start <= previous_start and current_end >= previous_end:
        return current
    if previous_start <= current_start and previous_end >= current_end:
        return previous
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=date.fromisoformat, default=date(2022, 7, 1))
    parser.add_argument("--end", type=date.fromisoformat, default=date.today())
    parser.add_argument("--step-days", type=int, default=7)
    parser.add_argument("--timeout", type=float, default=60)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.start > args.end or args.step_days <= 0 or args.timeout <= 0:
        parser.error("invalid date range, step or timeout")
    rows, offers = inventory(
        args.start,
        args.end,
        step_days=args.step_days,
        timeout=args.timeout,
    )
    result = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "start": args.start.isoformat(),
        "end": args.end.isoformat(),
        "step_days": args.step_days,
        "candidates": rows,
        "catalog": {"schema_version": 2, "offers": offers},
    }
    raw = json.dumps(result, indent=2, ensure_ascii=True) + "\n"
    if args.output:
        args.output.write_text(raw, encoding="utf-8")
    else:
        sys.stdout.write(raw)


if __name__ == "__main__":
    main()
