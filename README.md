WP6003 Home Assistant BLE Integration
=====================================

Quick, minimal custom component to read environmental data from a WP6003 BLE sensor (AliExpress variant) via passive Bluetooth advertisements.

Features
--------
* Config Flow: Add via UI by entering the device MAC address.
* Passive BLE listening (no active connects) filtered by manufacturer id 0xEB01.
* Decodes and exposes the following sensors:
	* Temperature (°C)
	* TVOC (mg/m³)
	* HCHO (mg/m³)
	* CO₂ (ppm)

Installation
-----------
1. Copy the `custom_components/wp6003` directory into your Home Assistant `config/custom_components` folder.
2. Restart Home Assistant.
3. Go to Settings -> Devices & Services -> Add Integration -> search for WP6003.
4. Enter the sensor's MAC address (Bluetooth MAC, can be found via HA logs or OS tools like `bluetoothctl`).

How it works
------------
* Uses the core Bluetooth integration to register a callback filtered by manufacturer id (60161 / 0xEB01).
* Parses raw manufacturer payload bytes into values and fires an internal event `wp6003_update` that sensor entities listen for.

Troubleshooting
---------------
* If other Bluetooth integrations stop starting, ensure no exceptions are raised during setup (this repo version fixes missing imports that previously caused that).
* Turn on debug logging for `custom_components.wp6003` to inspect raw packet lengths and decode issues.

Planned / Ideas
---------------
* Add signal strength (RSSI) entity.
* Add diagnostics file for last raw payload.

License
-------
MIT (add a LICENSE file if distributing widely).
