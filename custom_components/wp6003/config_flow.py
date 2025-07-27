from homeassistant import config_entries
from homeassistant.const import CONF_MAC
import voluptuous as vol
from .const import DOMAIN

class WP6003ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            return self.async_create_entry(title="WP6003 BLE Sensor", data=user_input)

        schema = vol.Schema({
            vol.Required(CONF_MAC): str
        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors
        )