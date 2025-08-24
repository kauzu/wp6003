from __future__ import annotations

from homeassistant.helpers.entity import Entity
from .const import DOMAIN

SENSOR_DESCRIPTORS = [
    ("temperature", "Temperature", "°C"),
    ("tvoc", "TVOC", "mg/m³"),
    ("hcho", "HCHO", "mg/m³"),
    ("co2", "CO₂", "ppm"),
]


async def async_setup_entry(hass, entry, async_add_entities):
    entities = [WP6003DynamicSensor(key, name, unit) for key, name, unit in SENSOR_DESCRIPTORS]
    async_add_entities(entities)


class WP6003DynamicSensor(Entity):
    def __init__(self, key: str, name: str, unit: str):
        self._attr_name = f"WP6003 {name}"
        self._attr_unique_id = f"wp6003_{key}"
        self._key = key
        self._unit = unit
        self._state = None
        self._remove_listener = None

    @property
    def native_value(self):  # new HA style
        return self._state

    @property
    def native_unit_of_measurement(self):
        return self._unit

    async def async_added_to_hass(self):
        async def handle_update(event):
            if self._key in event.data:
                self._state = event.data[self._key]
                self.async_write_ha_state()

        self._remove_listener = self.hass.bus.async_listen(f"{DOMAIN}_update", handle_update)

    async def async_will_remove_from_hass(self):
        if self._remove_listener:
            self._remove_listener()
            self._remove_listener = None