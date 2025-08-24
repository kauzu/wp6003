from homeassistant.components.bluetooth import (
    async_register_callback,
    BluetoothCallbackMatcher,
    BluetoothChange,
    BluetoothServiceInfoBleak,
)
from .const import CONF_MAC, DOMAIN
from .ble_decoder import parse_wp6003_ble_packet
import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities=None):
    """Register a bluetooth callback for the target MAC and return unregister callable."""
    target_mac = config_entry.data[CONF_MAC].lower()

    def ble_callback(service_info: BluetoothServiceInfoBleak, change: BluetoothChange):
        try:
            if service_info.address.lower() != target_mac:
                return
            payload = service_info.manufacturer_data.get(0xEB01)
            if not payload:
                _LOGGER.debug("Matched MAC %s but missing manufacturer payload", target_mac)
                return
            data = parse_wp6003_ble_packet(payload)
            if not data:
                _LOGGER.debug("Failed to decode payload len=%d for %s", len(payload), target_mac)
                return
            _LOGGER.debug("Decoded WP6003 data %s from %s (change=%s)", data, target_mac, change)
            hass.bus.fire(f"{DOMAIN}_update", data)
        except Exception:  # pragma: no cover
            _LOGGER.exception("Error in WP6003 BLE callback")

    matcher: BluetoothCallbackMatcher = {"manufacturer_id": 0xEB01}
    _LOGGER.debug("Registering WP6003 BLE callback for %s", target_mac)
    unregister = async_register_callback(hass, ble_callback, matcher, bluetooth_adapter=None)
    return unregister
