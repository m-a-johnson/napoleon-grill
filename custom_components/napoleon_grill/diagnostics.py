"""Diagnostics support for Napoleon Grill."""
from __future__ import annotations

import re
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant

from .const import CONF_APP_ID, CONF_APP_SECRET, DOMAIN
from .coordinator import NapoleonGrillCoordinator

TO_REDACT_CONFIG = {CONF_EMAIL, CONF_PASSWORD, CONF_APP_ID, CONF_APP_SECRET}
TO_REDACT_DEVICE = {"serial_number"}

# Only these fields are copied from each raw Ayla property. Everything else in
# the raw property (ids, keys, urls) is left out on purpose.
PROPERTY_FIELDS = (
    "display_name",
    "base_type",
    "direction",
    "read_only",
    "value",
    "data_updated_at",
)
MAX_VALUE_LENGTH = 200


SENSITIVE_SUBSTRINGS = ("ssid", "password", "passwd", "token", "secret")
SENSITIVE_TOKENS = {"mac", "ip", "addr", "address", "lan"}
REDACTED = "**REDACTED**"


def _is_sensitive(name: str) -> bool:
    """Best-effort guess that a property holds network or credential data."""
    lowered = name.lower()
    if any(part in lowered for part in SENSITIVE_SUBSTRINGS):
        return True
    return any(token in SENSITIVE_TOKENS for token in re.split(r"[^a-z0-9]+", lowered))


def _clip(value: Any) -> Any:
    """Keep very long strings (e.g. file URLs) from bloating the report."""
    if isinstance(value, str) and len(value) > MAX_VALUE_LENGTH:
        return value[:MAX_VALUE_LENGTH] + "...(truncated)"
    return value


def _token_info(coordinator: NapoleonGrillCoordinator) -> dict[str, Any]:
    """Token timing only (never the token itself)."""
    api = coordinator.api
    try:
        expires = api.auth_expiration
    except Exception as err:  # noqa: BLE001 - diagnostics must not fail
        return {"error": repr(err)}
    return {
        "expires_at": expires.isoformat() if expires else None,
        "expiring_soon": api.token_expiring_soon,
        "expired": api.token_expired,
    }


def _device_info(index: int, device: Any) -> dict[str, Any]:
    """Describe one device and every property the API reports for it."""
    settable = getattr(device, "_settable_properties", None) or set()
    properties = {}
    for name, raw in sorted(device.properties_full.items()):
        fields = {field: _clip(raw[field]) for field in PROPERTY_FIELDS if field in raw}
        if "value" in fields and _is_sensitive(name):
            fields["value"] = REDACTED
        properties[name] = fields
    return {
        "device_index": index,
        "name": device.name,
        "oem_model_number": device.oem_model_number,
        "device_model_number": device.device_model_number,
        "serial_number": device.serial_number,
        "settable_properties": sorted(settable),
        "property_count": len(properties),
        "properties": properties,
    }


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: NapoleonGrillCoordinator = hass.data[DOMAIN][entry.entry_id]

    return {
        "config_entry": async_redact_data(dict(entry.data), TO_REDACT_CONFIG),
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "update_interval_seconds": (
                coordinator.update_interval.total_seconds()
                if coordinator.update_interval
                else None
            ),
            "token": _token_info(coordinator),
        },
        "devices": [
            async_redact_data(_device_info(index, device), TO_REDACT_DEVICE)
            for index, device in enumerate(coordinator.devices)
        ],
    }
