import logging

_LOGGER = logging.getLogger(__name__)

def parse_wp6003_ble_packet(payload: bytes) -> dict | None:
    if len(payload) < 18:
        _LOGGER.warning("Invalid packet length: %d", len(payload))
        return None

    try:
        temperature = ((payload[6] << 8) | payload[7]) / 10.0
        tvoc = ((payload[10] << 8) | payload[11]) / 1000.0
        hcho = ((payload[12] << 8) | payload[13]) / 1000.0
        co2 = ((payload[16] << 8) | payload[17]) - 150

        return {
            "temperature": temperature,
            "tvoc": tvoc,
            "hcho": hcho,
            "co2": co2
        }
    except Exception as e:
        _LOGGER.error("Error decoding WP6003 packet: %s", e)
        return None