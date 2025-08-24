from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType
from .const import DOMAIN
import logging
import time

_LOGGER = logging.getLogger("custom_components.wp6003")

# Emit probe messages at all standard levels so the logger always appears.
_LOGGER.critical("[wp6003] logger probe (CRITICAL) module import")
_LOGGER.error("[wp6003] logger probe (ERROR) module import")
_LOGGER.warning("[wp6003] logger probe (WARNING) module import")
_LOGGER.info("[wp6003] logger probe (INFO) module import")
_LOGGER.debug("[wp6003] logger probe (DEBUG) module import")

PLATFORMS: list[str] = ["sensor"]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the wp6003 namespace."""
    t0 = time.time()
    hass.data.setdefault(DOMAIN, {})
    _LOGGER.critical("[wp6003] async_setup start (CRITICAL)")
    _LOGGER.error("[wp6003] async_setup start (ERROR)")
    _LOGGER.warning("[wp6003] async_setup start (WARNING) t=%.3f", t0)
    _LOGGER.info("[wp6003] async_setup start (INFO)")
    _LOGGER.debug("[wp6003] async_setup start (DEBUG)")

    def _emit_all_levels(tag: str):
        _LOGGER.critical("[wp6003] probe %s CRITICAL", tag)
        _LOGGER.error("[wp6003] probe %s ERROR", tag)
        _LOGGER.warning("[wp6003] probe %s WARNING", tag)
        _LOGGER.info("[wp6003] probe %s INFO", tag)
        _LOGGER.debug("[wp6003] probe %s DEBUG", tag)

    _emit_all_levels("during_setup")

    async def _handle_test_log(call: ServiceCall):
        suffix = call.data.get("message", "(no message)")
        _emit_all_levels(f"service_call {suffix}")

    hass.services.async_register(DOMAIN, "test_log", _handle_test_log)
    _LOGGER.info("[wp6003] registered service %s.test_log", DOMAIN)

    dt = time.time() - t0
    _LOGGER.warning("[wp6003] async_setup end (WARNING) dt=%.3f", dt)
    _LOGGER.info("[wp6003] async_setup end (INFO) dt=%.3f", dt)
    _LOGGER.debug("[wp6003] async_setup end (DEBUG) dt=%.3f", dt)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a config entry: register BLE callback + forward platforms."""
    from . import bluetooth  # local import to avoid circulars
    _LOGGER.info("[wp6003] async_setup_entry start for %s", entry.entry_id)
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
            _LOGGER.info("[wp6003] forwarding platforms via async_forward_entry_setups: %s", PLATFORMS)
            await forward(entry, PLATFORMS)
        else:
            # Fallback for older cores
            for platform in PLATFORMS:
                _LOGGER.info("[wp6003] scheduling forward of platform %s", platform)
                hass.async_create_task(
                    hass.config_entries.async_forward_entry_setup(entry, platform)
                )
    except Exception:  # pragma: no cover
        _LOGGER.exception("Error forwarding platforms for %s", entry.entry_id)
        return False
    _LOGGER.info("[wp6003] async_setup_entry end dt=%.3f", time.time() - t0)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info("[wp6003] async_unload_entry start for %s", entry.entry_id)
    data = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if data and (unregister := data.get("unregister_callback")):
        try:
            unregister()
            _LOGGER.info("[wp6003] unregistered bluetooth callback for %s", entry.entry_id)
        except Exception:  # pragma: no cover - defensive
            pass

    try:
        unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    except Exception:  # pragma: no cover
        _LOGGER.exception("Error unloading platforms for %s", entry.entry_id)
        unload_ok = False
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    _LOGGER.info("[wp6003] async_unload_entry end unload_ok=%s", unload_ok)
    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    _LOGGER.info("[wp6003] async_reload_entry for %s", entry.entry_id)
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)