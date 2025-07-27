from homeassistant import config_entries
import voluptuous as vol
from .const import DOMAIN, CONF_MAC

class WP6003ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title="WP6003 BLE Sensor",
                data=user_input  # stores {"mac_address": "..."}
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_MAC): str}),
        )
