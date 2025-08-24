from homeassistant.components.bluetooth import (
    async_register_callback,
    BluetoothCallbackMatcher,
    BluetoothChange,
    BluetoothServiceInfoBleak,
)
from .const import CONF_MAC, DOMAIN
from .ble_decoder import parse_wp6003_ble_packet
import logging
import time

_LOGGER = logging.getLogger(__name__)
_LOGGER.warning("[wp6003] bluetooth module imported (passive mode; manifest bluetooth key removed for isolation)")


async def async_setup_entry(hass, config_entry, async_add_entities=None):
    """Register a bluetooth callback for the target MAC and return unregister callable."""
    target_mac = config_entry.data.get(CONF_MAC, "").lower()
    _LOGGER.warning("[wp6003] bluetooth.async_setup_entry target_mac=%s entry=%s (callback temporarily disabled)", target_mac, config_entry.entry_id)

    def ble_callback(service_info: BluetoothServiceInfoBleak, change: BluetoothChange):
        start = time.time()
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
        finally:
            _LOGGER.debug("[wp6003] ble_callback dt=%.4f", time.time() - start)

    # Temporarily skip registering callback to isolate startup failure
    _LOGGER.warning("[wp6003] Skipping BLE callback registration for isolation test")
    def dummy_unregister():
        _LOGGER.warning("[wp6003] dummy_unregister called")
    return dummy_unregister
