"""Invented examples, never captured account payloads."""


def sample(reference, value=1.25, quality="REAL"):
    return {
        "timeReference": reference,
        "totalValue": value,
        "totalType": quality,
        "totalString": "display-only, not parsed",
    }


def daily(day="2025-03-10", rows=None):
    year = sample(day[:4], 21.37)
    month = sample(day[:7], 7.31)
    month["days"] = [sample(day)] if rows is None else rows
    year["months"] = [month]
    return {
        "code": "OK",
        "lastUpdate": day,
        "consumptionsList": {"startYear": day[:4], "endYear": day[:4], "years": [year]},
    }


def hourly(day="2025-03-10", rows=None):
    return {
        "code": "OK",
        "lastUpdate": day,
        "consumptionsList": {
            "day": {
                "day": day,
                "totalValue": 8.57,
                "totalType": "REAL",
                "consumptions": [sample(f"{hour:02}:00", 0.2) for hour in range(24)]
                if rows is None
                else rows,
            }
        },
    }


def gas_update(day="2025-03-20"):
    return {"code": "OK", "lastUpdateDate": day}


def monthly_gas(month="2025-03", rows=None):
    year = sample(month[:4], 21)
    year["months"] = [sample(month, 7)] if rows is None else rows
    return {
        "code": "OK",
        "lastUpdate": "",
        "consumptionsList": {
            "startYear": month[:4],
            "endYear": month[:4],
            "years": [year],
        },
    }


def supplies():
    return {
        "code": "OK",
        "listaContratti": [
            {
                "id": "synthetic-crm-id-not-the-contract-code",
                "codContr": "synthetic-contract",
                "dataProxBol": ["2025-04-15"],
                "sdd": {
                    "stato": "y",
                    "attesaDoc": "n",
                    "iban": "synthetic-private-bank-data",
                },
                "bol": {"statoBOL": "y", "email": "private@example.invalid"},
                "forniture": [
                    {
                        "id": "synthetic-power",
                        "commodity": "Luce",
                        "attiva": "y",
                        "dataAttivazione": "2025-03-01",
                        "punto": {
                            "pod": "synthetic-pod",
                            "potenzaImpegnata": 3,
                            "potenzaConsumo": 3.3,
                        },
                    },
                    {
                        "id": "synthetic-gas",
                        "commodity": "Gas",
                        "attiva": "y",
                        "dataAttivazione": "2025-03-01",
                        "punto": {"pdr": "synthetic-pdr"},
                        "autolettura": {
                            "inizioFinestra": "2025-04-10",
                            "fineFinestra": "2025-04-20",
                            "ultimaLetturaValidata": "1000",
                        },
                    },
                ],
            }
        ],
    }
