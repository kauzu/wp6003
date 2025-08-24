from __future__ import annotations

from homeassistant.helpers.entity import Entity
from .const import DOMAIN
import logging
import time

_LOGGER = logging.getLogger(__name__)
_LOGGER.debug("[wp6003] sensor module imported")

SENSOR_DESCRIPTORS = [
    ("temperature", "Temperature", "°C"),
    ("tvoc", "TVOC", "mg/m³"),
    ("hcho", "HCHO", "mg/m³"),
    ("co2", "CO₂", "ppm"),
]


async def async_setup_entry(hass, entry, async_add_entities):
    _LOGGER.debug("[wp6003] sensor.async_setup_entry for %s", entry.entry_id)
    entities = [WP6003DynamicSensor(key, name, unit) for key, name, unit in SENSOR_DESCRIPTORS]
    async_add_entities(entities)
    _LOGGER.debug("[wp6003] sensor.async_setup_entry added %d entities", len(entities))


class WP6003DynamicSensor(Entity):
    def __init__(self, key: str, name: str, unit: str):
        self._attr_name = f"WP6003 {name}"
        self._attr_unique_id = f"wp6003_{key}"
        self._key = key
        self._unit = unit
        self._state = None
        self._remove_listener = None
        _LOGGER.debug("[wp6003] sensor %s instantiated", self._attr_unique_id)

    @property
    def native_value(self):  # new HA style
        return self._state

    @property
    def native_unit_of_measurement(self):
        return self._unit

    async def async_added_to_hass(self):
        _LOGGER.debug("[wp6003] sensor %s added to hass", self._attr_unique_id)

        async def handle_update(event):
            start = time.time()
            if self._key in event.data:
                old = self._state
                self._state = event.data[self._key]
                _LOGGER.debug(
                    "[wp6003] sensor %s update key=%s old=%s new=%s dt=%.4f",
                    self._attr_unique_id,
                    self._key,
                    old,
                    self._state,
                    time.time() - start,
                )
                self.async_write_ha_state()

        self._remove_listener = self.hass.bus.async_listen(f"{DOMAIN}_update", handle_update)

    async def async_will_remove_from_hass(self):
        _LOGGER.debug("[wp6003] sensor %s will be removed", self._attr_unique_id)
        if self._remove_listener:
            self._remove_listener()
            self._remove_listener = None