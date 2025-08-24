import asyncio
import logging
from typing import Optional

from homeassistant.core import HomeAssistant
from homeassistant.components.bluetooth import (
    async_ble_device_from_address,
)

from .ble_decoder import parse_wp6003_ble_packet
from .const import DOMAIN

_LOGGER = logging.getLogger("custom_components.wp6003.gatt")

CHAR_FFF4_SHORT = "fff4"
CHAR_FFF4_FULL = "0000fff4-0000-1000-8000-00805f9b34fb"


def _match_char(uuid: str) -> bool:
    u = uuid.lower()
    return u == CHAR_FFF4_SHORT or u == CHAR_FFF4_FULL


def ensure_gatt_task(hass: HomeAssistant, entry_id: str, mac: str):
    """Create (or return existing) background task maintaining a GATT notify subscription.

    We keep it simple: perpetual loop; if the device not present or connect fails we backoff.
    """
    key = f"gatt_task_{entry_id}"
    if key in hass.data.setdefault(DOMAIN, {}):
        return

    async def _runner():
        backoff = 5
        from bleak import BleakClient  # local import to avoid HA startup cost if unused

        while True:
            device = async_ble_device_from_address(hass, mac, connectable=True)
            if not device:
                _LOGGER.debug("[wp6003] GATT: device %s not yet in registry; sleeping", mac)
                await asyncio.sleep(min(backoff, 30))
                backoff = min(backoff * 2, 60)
                continue

            backoff = 5  # reset once we see device
            _LOGGER.critical("[wp6003] GATT: attempting connect to %s", mac)
            client: Optional[BleakClient] = None
            try:
                client = BleakClient(device)
                await client.connect()
                _LOGGER.critical("[wp6003] GATT: connected %s; discovering services", mac)
                svcs = await client.get_services()
                char_uuid = None
                for service in svcs:
                    for char in service.characteristics:
                        if _match_char(char.uuid):
                            char_uuid = char.uuid
                            break
                    if char_uuid:
                        break
                if not char_uuid:
                    _LOGGER.warning("[wp6003] GATT: characteristic fff4 not found on %s", mac)
                    await client.disconnect()
                    await asyncio.sleep(30)
                    continue

                _LOGGER.critical("[wp6003] GATT: subscribing to %s", char_uuid)

                def _handle_notify(_, data: bytearray):
                    payload = bytes(data)
                    parsed = parse_wp6003_ble_packet(payload)
                    if parsed:
                        _LOGGER.critical("[wp6003] GATT notify decoded %s raw=%s", parsed, payload.hex()[:60])
                        hass.bus.fire(f"{DOMAIN}_update", parsed)
                    else:
                        _LOGGER.critical("[wp6003] GATT notify undecodable len=%d raw=%s", len(payload), payload.hex()[:40])

                await client.start_notify(char_uuid, _handle_notify)
                # Stay connected while HA runs; poll connection every minute
                while True:
                    if not client.is_connected:
                        raise RuntimeError("Disconnected")
                    await asyncio.sleep(60)
            except asyncio.CancelledError:  # pragma: no cover - service shutdown
                _LOGGER.critical("[wp6003] GATT runner cancelled for %s", mac)
                if client and client.is_connected:
                    try:
                        await client.disconnect()
                    except Exception:  # pragma: no cover
                        pass
                break
            except Exception as e:  # pragma: no cover - resilience
                _LOGGER.warning("[wp6003] GATT loop error %s; retrying shortly", e)
                try:
                    if client and client.is_connected:
                        await client.disconnect()
                except Exception:
                    pass
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 120)

    task = hass.loop.create_task(_runner())
    hass.data[DOMAIN][key] = task
    _LOGGER.critical("[wp6003] GATT background task started for %s", mac)


async def stop_gatt_task(hass: HomeAssistant, entry_id: str):
    key = f"gatt_task_{entry_id}"
    task: asyncio.Task | None = hass.data.get(DOMAIN, {}).pop(key, None)
    if task:
        task.cancel()
        try:
            await task
        except Exception:  # pragma: no cover
            pass
        _LOGGER.critical("[wp6003] GATT background task stopped for %s", entry_id)
