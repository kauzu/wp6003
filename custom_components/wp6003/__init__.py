from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType
from .const import DOMAIN
import logging
import time

_LOGGER = logging.getLogger("custom_components.wp6003")
_LOGGER.critical("[wp6003] module import")

PLATFORMS: list[str] = ["sensor"]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the wp6003 namespace."""
    t0 = time.time()
    hass.data.setdefault(DOMAIN, {})
    _LOGGER.critical("[wp6003] async_setup start t=%.3f", t0)

    async def _handle_test_log(call: ServiceCall):
        suffix = call.data.get("message", "(no message)")
        _LOGGER.critical("[wp6003] test_log service_call %s", suffix)

    hass.services.async_register(DOMAIN, "test_log", _handle_test_log)
    _LOGGER.critical("[wp6003] registered service %s.test_log", DOMAIN)

    async def _handle_reload(call: ServiceCall):
        _LOGGER.critical("[wp6003] reload service invoked")
        for entry in hass.config_entries.async_entries(DOMAIN):
            await hass.config_entries.async_reload(entry.entry_id)
        _LOGGER.critical("[wp6003] reload complete")

    hass.services.async_register(DOMAIN, "reload", _handle_reload)
    _LOGGER.critical("[wp6003] registered service %s.reload", DOMAIN)

    dt = time.time() - t0
    _LOGGER.critical("[wp6003] async_setup end dt=%.3f", dt)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a config entry: register BLE callback + forward platforms."""
    from . import bluetooth  # local import to avoid circulars
    _LOGGER.critical("[wp6003] async_setup_entry start %s", entry.entry_id)
    t0 = time.time()
    try:
        unregister = await bluetooth.async_setup_entry(hass, entry)
    except Exception:  # pragma: no cover
        _LOGGER.exception("Failed to register bluetooth callback")
        unregister = None

    hass.data[DOMAIN][entry.entry_id] = {"unregister_callback": unregister}

    try:
        # Newer HA (2023.8+) helper for multiple platforms
        forward = getattr(hass.config_entries, "async_forward_entry_setups", None)
        if forward:
            _LOGGER.critical("[wp6003] forwarding platforms %s", PLATFORMS)
            await forward(entry, PLATFORMS)
        else:
            # Fallback for older cores
            for platform in PLATFORMS:
                _LOGGER.critical("[wp6003] scheduling forward platform %s", platform)
                hass.async_create_task(
                    hass.config_entries.async_forward_entry_setup(entry, platform)
                )
    except Exception:  # pragma: no cover
        _LOGGER.exception("Error forwarding platforms for %s", entry.entry_id)
        return False
    _LOGGER.critical("[wp6003] async_setup_entry end dt=%.3f", time.time() - t0)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.critical("[wp6003] async_unload_entry start %s", entry.entry_id)
    data = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if data and (unregister := data.get("unregister_callback")):
        try:
            unregister()
            _LOGGER.critical("[wp6003] unregistered bluetooth callback %s", entry.entry_id)
        except Exception:  # pragma: no cover - defensive
            pass

    try:
        unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    except Exception:  # pragma: no cover
        _LOGGER.exception("Error unloading platforms for %s", entry.entry_id)
        unload_ok = False
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    _LOGGER.critical("[wp6003] async_unload_entry end unload_ok=%s", unload_ok)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    _LOGGER.critical("[wp6003] async_reload_entry %s", entry.entry_id)
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)