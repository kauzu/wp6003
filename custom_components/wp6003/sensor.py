from homeassistant.helpers.entity import Entity
from .const import DOMAIN

class WP6003PM25Sensor(Entity):
    def __init__(self):
        self._state = None
        self._attr_name = "WP6003 PM2.5"

    async def async_added_to_hass(self):
        async def handle_update(event):
            self._state = event.data.get("pm2_5")
            self.async_write_ha_state()

        self._remove_listener = self.hass.bus.async_listen(f"{DOMAIN}_update", handle_update)

    async def async_will_remove_from_hass(self):
        self._remove_listener()

    @property
    def state(self):
        return self._state