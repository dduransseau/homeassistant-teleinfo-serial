import serial.tools.list_ports

import logging

from typing import Any, Dict, Optional

from homeassistant import config_entries, core
import homeassistant.helpers.config_validation as cv

import voluptuous as vol

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)



class TeleinfoSerialConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    # Home Assistant will call your migrate method if the version changes
    VERSION = 1

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None):
        errors: Dict[str, str] = {}
        config_entry = dict()
        
        
        available_ports = await self.hass.async_add_executor_job(serial.tools.list_ports.comports)
        port_options = []
        teleinfo_type_options = ['historique', 'standard']

        config_fieldset = dict()
        for port in available_ports:
            port_options.append(port.device)

        if not port_options:
            # No serial ports found
            return self.async_abort(reason="no_ports")
        elif len(port_options) > 1:
            config_fieldset[vol.Required("serial_port")] = vol.In(port_options)
        else: # Only one port found, set is as default value
            config_fieldset[vol.Required("serial_port", default=port_options[0])] = vol.In(port_options)
            config_entry["serial_port"] = port_options[0]
        
        if user_input is not None:
            data = config_entry | user_input
            return self.async_create_entry(title=f"Teleinfo serial", data=data)
        
        config_fieldset[vol.Required("teleinfo_type")] = vol.In(teleinfo_type_options)
        
        CONFIG_SCHEMA  = vol.Schema(config_fieldset)

        return self.async_show_form(
            step_id="user", 
            data_schema=CONFIG_SCHEMA,
            errors=errors
        )
