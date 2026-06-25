# Napoleon Grill Integration for Home Assistant

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

A custom Home Assistant integration for Napoleon Connected grills using the Ayla Networks IoT platform.

Developed by reverse-engineering the Napoleon Home app's API traffic. Currently supports the **Napoleon Prestige series** (tested on the Prestige 51B), and likely works with other Napoleon Connected grill models.

---

## Features

- **Probe temperature sensors** — up to four probes with full unit conversion support (display in °C or °F per entity)
- **Grill active binary sensor** — shows whether the grill is currently running
- **WiFi signal diagnostic sensor** — shows the grill's RSSI
- **Burner level sensor** — current burner intensity (hidden by default)
- **Tank weight sensor** — propane tank weight in grams (hidden by default)
- **30-second polling interval** — balances responsiveness with server load
- **Multi-device support** — if you have more than one Napoleon Connected grill on your account

---

## Prerequisites

Before installing this integration you will need:

1. A Napoleon Connected grill with the Napoleon Home app set up and working
2. Your Napoleon Home app **email and password**
3. The Ayla Networks **App ID** and **App Secret** for the Napoleon app (see below)

### Getting Your App ID and App Secret

Napoleon uses the [Ayla Networks](https://www.aylanetworks.com/) IoT platform. To obtain the App ID and App Secret you need to intercept the Napoleon Home app's traffic using a tool like [mitmproxy](https://mitmproxy.org/).

**Steps:**

1. Install mitmproxy on your computer (`https://mitmproxy.org/downloads`)
2. Run `mitmweb` to start the proxy with a browser-based UI
3. On your iPhone or Android phone, set your WiFi proxy to point to your computer's IP on port 8080
4. On your phone, browse to `http://mitm.it` and install the mitmproxy certificate
5. Trust the certificate under **Settings → General → About → Certificate Trust Settings** (iOS) or equivalent on Android
6. Open the Napoleon Home app and log out, then log back in
7. In mitmweb, find the POST request to `https://user-field.aylanetworks.com/users/sign_in.json`
8. The request body will contain your `app_id` and `app_secret`

> **Remember to remove the proxy from your phone and untrust the mitmproxy certificate when you are done.**

---

## Installation

### Via HACS (Recommended)

1. In Home Assistant, go to **HACS → Integrations**
2. Click the three dots menu and select **Custom repositories**
3. Add `https://github.com/m-a-johnson/napoleon-grill` as an **Integration**
4. Search for **Napoleon Grill** in HACS and install it
5. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/napoleon_grill` folder to your HA `config/custom_components/` directory
2. Restart Home Assistant

---

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **Napoleon Grill**
3. Enter your credentials:
   - **Email** — your Napoleon Home app email
   - **Password** — your Napoleon Home app password
   - **App ID** — obtained via mitmproxy (see above)
   - **App Secret** — obtained via mitmproxy (see above)
4. Click **Submit**

---

## Entities

### Sensors

| Entity | Description | Default |
|--------|-------------|---------|
| Probe 1 Temperature | Temperature of probe 1 | Enabled |
| Probe 2 Temperature | Temperature of probe 2 | Enabled |
| Probe 3 Temperature | Temperature of probe 3 | Enabled |
| Probe 4 Temperature | Temperature of probe 4 | Enabled |
| WiFi Signal | Grill WiFi RSSI in dBm | Diagnostic |
| Burner Level | Current burner intensity level | Hidden |
| Tank Weight | Propane tank weight in grams | Hidden |

### Binary Sensors

| Entity | Description | Default |
|--------|-------------|---------|
| Grill Active | Whether the grill is currently running | Enabled |
| Display Off | Whether the grill's LCD display is off | Hidden |

### Controls

| Entity | Type | Description |
|--------|------|-------------|
| LED Brightness | Select | Control display brightness (Low / Medium / High) |
| Probe 1 Target Low | Number | Lower target temperature for probe 1 |
| Probe 1 Target High | Number | Upper target temperature for probe 1 |
| Probe 2 Target Low | Number | Lower target temperature for probe 2 |
| Probe 2 Target High | Number | Upper target temperature for probe 2 |
| Probe 3 Target Low | Number | Lower target temperature for probe 3 |
| Probe 3 Target High | Number | Upper target temperature for probe 3 |
| Probe 4 Target Low | Number | Lower target temperature for probe 4 |
| Probe 4 Target High | Number | Upper target temperature for probe 4 |
| Probe 1 Name | Text | Rename probe 1 from HA |
| Probe 2 Name | Text | Rename probe 2 from HA |
| Probe 3 Name | Text | Rename probe 3 from HA |
| Probe 4 Name | Text | Rename probe 4 from HA |
| Probe 1 Cook Preset | Text | Cook preset label for probe 1 |
| Probe 2 Cook Preset | Text | Cook preset label for probe 2 |
| Probe 3 Cook Preset | Text | Cook preset label for probe 3 |
| Probe 4 Cook Preset | Text | Cook preset label for probe 4 |

### Temperature Units

All probe temperatures are stored internally in **Celsius** (as returned by the API). You can change the display unit per entity in Home Assistant under **Settings → Devices & Services → Napoleon Grill → [entity] → Unit of Measurement**. This allows you to display cooking probes in Fahrenheit while keeping ambient sensors in Celsius.

---

## Network Requirements

The Napoleon grill connects to Ayla Networks cloud infrastructure. If you use a restrictive firewall or IoT VLAN, ensure outbound **TCP port 8883** (MQTT over TLS) is allowed from the grill's IP address to the internet.

If you use Pi-hole, AdGuard, or similar DNS filtering, add `ads-field.aylanetworks.com` to your allowlist.

---

## Known Limitations

- This integration uses cloud polling and requires internet access
- No local control — all communication goes through the Ayla Networks cloud
- Control of grill settings (burner level, LED brightness) is not yet implemented
- Reauth flow is not yet implemented — if your password changes you will need to remove and re-add the integration

---

## Roadmap

- [x] LED brightness select entity (High / Medium / Low) — v0.2.0
- [x] Target temperature numbers per probe — v0.2.0
- [x] Probe name text entities — v0.2.0
- [x] Cook preset name text entities — v0.2.0
- [ ] Temperature alerts per probe
- [ ] Timer alerts per probe
- [ ] Reauth flow
- [ ] Default App ID and App Secret (pending community validation)

---

## Technical Background

This integration was developed by:

1. Capturing network traffic from a Napoleon Prestige 51B using pfSense packet capture
2. Identifying MQTT traffic to GCP infrastructure on port 8883
3. Using mitmproxy to intercept the Napoleon Home app's HTTPS API calls
4. Discovering the Ayla Networks REST API at `ads-field.aylanetworks.com`
5. Mapping the 64+ device properties exposed by the API

The grill communicates with Ayla Networks via MQTT over TLS (port 8883). The mobile app polls the Ayla REST API for device state. This integration uses the REST API via the [`ayla-iot-unofficial`](https://github.com/rewardone/ayla-iot-unofficial) Python library.

---

## Disclaimer

This integration is not affiliated with, endorsed by, or supported by Napoleon or Ayla Networks. Use at your own risk. Reverse engineering of the API was performed for personal home automation use.

---

## Contributing

Pull requests are welcome. If you have a Napoleon Connected grill model other than the Prestige 51B and can confirm compatibility (or identify issues), please open an issue.

---

## License

MIT