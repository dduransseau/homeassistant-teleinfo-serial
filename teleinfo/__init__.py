import logging

from homeassistant import config_entries, core
from homeassistant.helpers.typing import ConfigType
from homeassistant.const import Platform

from .const import TELEINFO_KEY, DOMAIN

_LOGGER = logging.getLogger(__name__)

def init_teleinfo_metadata():
    # Calculate the length of payload to calculate checksum
    for k, v in TELEINFO_KEY.items():
        if v.get("timestamp", False):
            payload_length = len(k) + 1 + 13 + 1 + v["metric_length"] + 1
            v["payload_length"] = payload_length
        else:
            payload_length = len(k) + 1 + v["metric_length"] + 1
            v["payload_length"] = payload_length

async def async_setup_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    """Set up platform from a ConfigEntry."""
    init_teleinfo_metadata()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {"port": entry.data["serial_port"], "type": entry.data["teleinfo_type"]}
    # Forward the setup to the sensor platform.
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, Platform.SENSOR)
    )
    
    return True
