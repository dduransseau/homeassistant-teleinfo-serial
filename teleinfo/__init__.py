import logging

from homeassistant import config_entries, core
from homeassistant.const import (
    Platform
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    """Set up platform from a ConfigEntry."""
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {"port": entry.data["serial_port"], "type": entry.data["teleinfo_type"]}
    # Forward the setup to the sensor platform.
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, Platform.SENSOR)
    )
    
    return True
