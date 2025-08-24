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
_LOGGER.critical("[wp6003] bluetooth module import")


RECENT_ADVERTS_MAX = 25


async def async_setup_entry(hass, config_entry, async_add_entities=None):
    """Register a bluetooth callback for the target MAC and return unregister callable."""
    target_mac = config_entry.data.get(CONF_MAC, "").lower()
    _LOGGER.critical("[wp6003] async_setup_entry target_mac=%s entry=%s", target_mac, config_entry.entry_id)

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

            # Extra diagnostic logging (rate-limited) so we can see what the device actually sends
            if time.time() - last_no_payload_log > 30:
                last_no_payload_log = time.time()  # reuse timer for generic periodic log
                manuf_summary = {
                    hex(k): len(v) for k, v in service_info.manufacturer_data.items()
                }
                _LOGGER.critical(
                    "[wp6003] seen target MAC %s rssi=%s mfr=%s svc=%s connectable=%s",  # noqa: E501
                    target_mac,
                    service_info.rssi,
                    manuf_summary,
                    service_info.service_uuids,
                    getattr(service_info, "connectable", None),
                )

            payload = service_info.manufacturer_data.get(0xEB01)
            if not payload:
                # We'll already have logged a summary every 30s; keep this terse to avoid log spam
                return
            data = parse_wp6003_ble_packet(payload)
            if not data:
                _LOGGER.critical("[wp6003] decode failed len=%d ids=%s", len(payload), advert["manufacturer_ids"])
                return
            # Show first few raw bytes for validation
            _LOGGER.critical(
                "[wp6003] decoded data %s rssi=%s raw=%s", 
                data, 
                service_info.rssi,
                payload.hex()[:60],
            )
            hass.bus.fire(f"{DOMAIN}_update", data)
        except Exception:  # pragma: no cover
            _LOGGER.exception("Error in WP6003 BLE callback")
        finally:
            _LOGGER.critical("[wp6003] ble_callback dt=%.4f", time.time() - start)

    # Expose a service to dump recent adverts
    async def _dump_adverts_service(call):
        _LOGGER.critical("[wp6003] dumping %d recent adverts for %s", len(store), target_mac)
        for idx, adv in enumerate(store[-10:]):  # last 10
            _LOGGER.critical("[wp6003] advert %d: %s", idx, adv)

    hass.services.async_register(DOMAIN, "dump_adverts", _dump_adverts_service)

    matcher: BluetoothCallbackMatcher = {}  # catch-all, filter inside
    _LOGGER.critical("[wp6003] registering callback matcher=%s", matcher)
    unregister = async_register_callback(hass, ble_callback, matcher, bluetooth_adapter=None)
    return unregister
