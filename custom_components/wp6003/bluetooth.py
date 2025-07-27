from homeassistant.components.bluetooth import (
    async_register_callback,
)
from .ble_decoder import parse_wp6003_ble_packet
from .const import DOMAIN, CONF_MAC

async def async_setup_entry(hass, config_entry, async_add_entities=None):
    target_mac = config_entry.data[CONF_MAC].lower()

    def ble_callback(service_info, change):
        if service_info.address.lower() != target_mac:
            return

        payload = service_info.manufacturer_data.get(0xEB01)
        if payload:
            data = parse_wp6003_ble_packet(payload)
            if data:
                hass.bus.fire(f"{DOMAIN}_update", data)

    async_register_callback(hass, ble_callback, {"manufacturer_id": 0xEB01})
