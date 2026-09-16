"""Allowlisted diagnostics without credentials, IDs, consumption or invoice values."""

from .api.diagnostics import diagnostic_summary


async def async_get_config_entry_diagnostics(hass, entry):
    coordinator = getattr(entry, "runtime_data", None)
    data = getattr(coordinator, "data", None) or {}
    return {
        "schema_version": 1,
        "last_update_success": bool(getattr(coordinator, "last_update_success", False)),
        "invoice_data_status": getattr(
            getattr(coordinator, "billing", None), "status", "error"
        ),
        "supplies": [
            {"utility": item.supply.utility.value, "status": item.status}
            for item in data.values()
        ],
        "readings": diagnostic_summary(
            item.readings.snapshot for item in data.values() if item.readings
        ),
    }
