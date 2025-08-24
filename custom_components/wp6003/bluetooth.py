from homeassistant.components.bluetooth import (
    async_register_callback,
    BluetoothCallbackMatcher,
    BluetoothChange,
    BluetoothServiceInfoBleak,
)
from .const import CONF_MAC, DOMAIN
from .ble_decoder import parse_wp6003_ble_packet


async def async_setup_entry(hass, config_entry, async_add_entities=None):
    """Register a bluetooth callback for the target MAC and return unregister callable."""
    target_mac = config_entry.data[CONF_MAC].lower()

    def ble_callback(service_info: BluetoothServiceInfoBleak, change: BluetoothChange):
        if service_info.address.lower() != target_mac:
            return

        # Manufacturer data id (0xEB01 == 60161) per manifest
        payload = service_info.manufacturer_data.get(0xEB01)
        if not payload:
            return
        data = parse_wp6003_ble_packet(payload)
        if not data:
            return
        # Fire a single domain-scoped event with parsed metrics
        hass.bus.fire(f"{DOMAIN}_update", data)

    matcher: BluetoothCallbackMatcher = {"manufacturer_id": 0xEB01}
    unregister = async_register_callback(hass, ble_callback, matcher, bluetooth_adapter=None)
    return unregister
