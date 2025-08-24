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

_LOGGER = logging.getLogger("custom_components.wp6003.bluetooth")
_LOGGER.critical("[wp6003] bluetooth module import CRITICAL")
_LOGGER.error("[wp6003] bluetooth module import ERROR")
_LOGGER.info("[wp6003] bluetooth module import INFO")
_LOGGER.debug("[wp6003] bluetooth module import DEBUG")
_LOGGER.warning("[wp6003] bluetooth module imported")


RECENT_ADVERTS_MAX = 25


async def async_setup_entry(hass, config_entry, async_add_entities=None):
    """Register a bluetooth callback for the target MAC and return unregister callable."""
    target_mac = config_entry.data.get(CONF_MAC, "").lower()
    _LOGGER.info("[wp6003] bluetooth.async_setup_entry target_mac=%s entry=%s", target_mac, config_entry.entry_id)

    store: list[dict] = []  # ring buffer of recent adverts for target MAC
    last_no_payload_log = 0.0

    def ble_callback(service_info: BluetoothServiceInfoBleak, change: BluetoothChange):
        nonlocal last_no_payload_log
        start = time.time()
        try:
            if service_info.address.lower() != target_mac:
                return

            advert = {
                "time": time.time(),
                "rssi": service_info.rssi,
                "manufacturer_ids": list(service_info.manufacturer_data.keys()),
                "service_uuids": service_info.service_uuids,
            }
            store.append(advert)
            if len(store) > RECENT_ADVERTS_MAX:
                store.pop(0)

            payload = service_info.manufacturer_data.get(0xEB01)
            if not payload:
                if time.time() - last_no_payload_log > 30:
                    last_no_payload_log = time.time()
                    _LOGGER.warning(
                        "[wp6003] target MAC %s seen but manufacturer_id 0xEB01 missing; present ids=%s", target_mac, advert["manufacturer_ids"]
                    )
                return
            data = parse_wp6003_ble_packet(payload)
            if not data:
                _LOGGER.info(
                    "[wp6003] decode failed (len=%d) ids=%s", len(payload), advert["manufacturer_ids"]
                )
                return
            _LOGGER.info("[wp6003] decoded data %s rssi=%s", data, service_info.rssi)
            hass.bus.fire(f"{DOMAIN}_update", data)
        except Exception:  # pragma: no cover
            _LOGGER.exception("Error in WP6003 BLE callback")
        finally:
            _LOGGER.debug("[wp6003] ble_callback dt=%.4f", time.time() - start)

    # Expose a service to dump recent adverts
    async def _dump_adverts_service(call):
        _LOGGER.warning("[wp6003] dumping %d recent adverts for %s", len(store), target_mac)
        for idx, adv in enumerate(store[-10:]):  # last 10
            _LOGGER.warning("[wp6003] advert %d: %s", idx, adv)

    hass.services.async_register(DOMAIN, "dump_adverts", _dump_adverts_service)

    matcher: BluetoothCallbackMatcher = {}  # catch-all, filter inside
    _LOGGER.info("[wp6003] Registering BLE callback matcher=%s", matcher)
    unregister = async_register_callback(hass, ble_callback, matcher, bluetooth_adapter=None)
    return unregister
