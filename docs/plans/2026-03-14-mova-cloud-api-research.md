# Mova 600 Plus Cloud API Research

**Date:** 2026-03-14
**Device:** Mova 600 Plus (Model: `mova.mower.g2552b`)
**Device ID (DID):** `-113852546`
**MAC:** `10:06:48:A4:71:A1`
**Account:** MOVAhome (Username: JB581668)

---

## 1. Cloud Infrastructure

### API Base URL
```
https://eu.iot.mova-tech.com:13267
```
- Country prefix is `eu` (NOT `de` — `de.iot.mova-tech.com` doesn't resolve in DNS!)
- HA integration uses the country code from config flow. If user selects "de", the integration constructs `de.iot.mova-tech.com` which only resolves inside HA's Docker DNS. Locally you must use `eu`.
- Port `13267` for REST API

### MQTT Broker
```
20000.mt.eu.iot.mova-tech.com:19974
```
- Retrieved from device info `bindDomain` field
- This is the MQTT broker the mower connects to for real-time updates
- Subscription topic: `/{status}/{did}/{uid}/{model}/{country}/`

### API Strings
All API endpoints and auth parameters are base64+gzip encoded in `MOVA_STRINGS` constant in `const.py`. Decoded, it's a JSON array of 57 strings. Key indices:

| Index | Value | Purpose |
|-------|-------|---------|
| 0 | `.iot.mova-tech.com` | API domain suffix |
| 1 | `13267` | API port |
| 2 | `RAylYC%fmSKp7%Tq` | Password salt for MD5 |
| 3 | `Mova_Smarthome/1.5.59 (iPhone; iOS 16.0; Scale/3.00)` | User-Agent |
| 5 | `Basic ZHJlYW1lX2FwcHYxOkFQXmR2QHpAU1FZVnhOODg=` | Authorization header (Basic auth) |
| 6 | `000002` | Tenant-Id |
| 17 | `/dreame-auth/oauth/token` | Login endpoint |
| 18 | `access_token` | Token key in login response |
| 46 | `Dreame-Auth` | Auth header name for API calls |

---

## 2. Authentication

### Login Flow
```
POST https://eu.iot.mova-tech.com:13267/dreame-auth/oauth/token
Content-Type: application/x-www-form-urlencoded
User-Agent: Mova_Smarthome/1.5.59 (iPhone; iOS 16.0; Scale/3.00)
Authorization: Basic ZHJlYW1lX2FwcHYxOkFQXmR2QHpAU1FZVnhOODg=
Tenant-Id: 000002

Body: platform=IOS&scope=all&grant_type=password&username=JB581668&password=<md5(password+salt)>&type=account
```

**Password hashing:** `md5(password + "RAylYC%fmSKp7%Tq")`

**Response:** Direct JSON (NOT wrapped in `{"code": 0, "data": {...}}` like Dreame!)
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "expires_in": 7200,
  "tenant_id": "000002",
  "country": "DE",
  "region": "eu",
  "u": 13506984
}
```

**Critical difference from Dreame Vacuum:** The login response is NOT wrapped in a `code`/`data` envelope. The token is directly in the root object.

### API Auth Headers (for all subsequent calls)
```
Content-Type: application/json
User-Agent: Mova_Smarthome/1.5.59 (iPhone; iOS 16.0; Scale/3.00)
Authorization: Basic ZHJlYW1lX2FwcHYxOkFQXmR2QHpAU1FZVnhOODg=
Tenant-Id: 000002
Dreame-Auth: <access_token>
```

**Key insight:** Auth token goes in `Dreame-Auth` header, NOT `Authorization: Bearer`.

---

## 3. API Endpoints

### Working Endpoints

| Endpoint | Method | Purpose | Status |
|----------|--------|---------|--------|
| `/dreame-auth/oauth/token` | POST | Login | ✓ Works |
| `/dreame-user-iot/iotuserbind/device/listV2` | POST | Device list | ✓ Works (POST only, GET returns 10002) |
| `/dreame-user-iot/iotuserbind/device/info` | POST | Device details | ✓ Works |
| `/dreame-user-iot/iotstatus/props` | POST | Get current property values | ✓ Works |
| `/dreame-user-iot/iotstatus/history` | POST | Get property history | ✓ Works (but returns 0 entries) |
| `/dreame-user-iot/iotfile/getOss1dDownloadUrl` | POST | Get signed file download URL | ✓ Works |
| `/dreame-user-iot/iotfile/getDownloadUrl` | POST | Get file download URL (alt) | ✗ code=40020 |

### NOT Working Endpoints

| Endpoint | Method | Issue |
|----------|--------|-------|
| `/dreame-iot-com/device/sendCommand` | POST | **404 NOT FOUND** — does NOT exist for Mova! |

**This is the root cause of most integration issues.** The HA integration (forked from dreame-vacuum) uses `sendCommand` for `get_properties` REST calls. This endpoint doesn't exist on the Mova cloud. The integration only gets data because MQTT push delivers STATE/BATTERY/CHARGING updates.

---

## 4. Property API (`iotstatus/props`)

### Request Format
```
POST /dreame-user-iot/iotstatus/props
Content-Type: application/json
Dreame-Auth: <token>

{"did":"-113852546","keys":"2.1,3.1,6.8"}
```

**Keys format:** Comma-separated `siid.piid` strings. NOT JSON arrays, NOT objects.

### Response Format
```json
{
  "code": 0,
  "data": [
    {"key": "2.1", "value": "1", "updateDate": 1773512954837},
    {"key": "3.1", "value": "71", "updateDate": 1773514354890},
    {"key": "6.8"}
  ]
}
```

**Important:** Keys that exist but have no value are returned without `"value"` field. They are "registered" in the cloud but never populated.

### Mova 600 Plus Property Map (Full Scan siid 1-15, piid 1-30)

**Only 10 properties have values:**

| Key (siid.piid) | Integration Property | Value Example | Update Frequency | Notes |
|-----------------|---------------------|---------------|-----------------|-------|
| 1.1 | NOT MAPPED | `[206,0,0,0,0,0,0,0,0,0,128,68,5,35,7,0,4,185,127,206]` | Static | 20-byte device status blob. Header=0xCE, footer=0xCE |
| 1.2 | NOT MAPPED | `3` | Static | Device type? |
| 1.3 | NOT MAPPED | `100` | Static | Unknown |
| 1.4 | NOT MAPPED | `[206,152,252,79,225,255,29,111,...]` | **Every 3 seconds!** | 33-byte live telemetry frame. Position data! |
| 2.1 | STATE | `1` (mowing), `13` (charging_completed) | On state change | Maps to DreameMowerState enum |
| 2.2 | ERROR | `54` | On error change | Error code |
| 3.1 | BATTERY_LEVEL | `69`-`100` | Every ~10s while active | Percentage |
| 3.2 | CHARGING_STATUS | `0` (not charging), `2` (charging) | On state change | |
| 4.1 | TASK_STATUS | `100` | On task change | Note: mapped to siid=4,piid=1 in cloud, NOT siid=4,piid=4 |
| 4.4 | STATUS | `0` | On status change | |

**440 keys are registered but have NO value.** Including all of SIID 5-15.

### Critical Discovery: SIID 6 (Map Properties) Has NO Values

| Key | Expected Property | Status |
|-----|------------------|--------|
| 6.1 | OBJECT_NAME | Registered, NO value |
| 6.2 | MAP_DATA | Registered, NO value |
| 6.3 | ROBOT_TIME | Registered, NO value |
| 6.8 | MAP_LIST | Registered, NO value |
| 6.9 | RECOVERY_MAP_LIST | Registered, NO value |

**The Mova 600 Plus does NOT store map data as cloud properties.** The map is stored elsewhere (likely as files in Aliyun OSS).

---

## 5. Live Telemetry (SIID 1.4)

33-byte frame, updated every ~3 seconds while mowing. Structure:

```
Byte 0:  0xCE (206) — Start marker
Bytes 1-2: Position X? (changes rapidly: 152,252 → 234,252 → 62,253)
Bytes 3-4: Position Y? (changes: 79,225 → 15,230 → 207,234)
Byte 5:  0xFF (255) — constant?
Byte 6:  0x1D (29) — constant?
Byte 7:  Varies (111)
Bytes 8-9: 0x00, 0x00
Bytes 10-11: 0xFF, 0x7F or 0x80, 0x45 — varies
Bytes 12-13: 0x00, 0x80
Bytes 14-21: Rapidly changing values (sensor data? IMU?)
Bytes 22-23: 0x01, 0x02 — constant
Bytes 24-25: Incrementing counter (70,9 → 74,9 → 80,9)
Bytes 26-27: 0xEC, 0x45 — constant (236, 69)
Bytes 28-29: 0x00, varies — counter?
Bytes 30-31: Incrementing (153,16 → 160,16 → 171,16)
Byte 32: 0xCE (206) — End marker

Frame: 0xCE [payload 31 bytes] 0xCE
```

**This is likely the robot's position and sensor telemetry in a proprietary binary format.** Needs reverse engineering to decode X/Y coordinates, heading, sensor values.

---

## 6. File Storage (Aliyun OSS)

### getOss1dDownloadUrl
```
POST /dreame-user-iot/iotfile/getOss1dDownloadUrl
Content-Type: application/json
Dreame-Auth: <token>

{"did":"-113852546","uid":"13506984","model":"mova.mower.g2552b","filename":"test","region":"eu"}
```

**Response:**
```json
{
  "code": 0,
  "data": "https://dreame-eu-oss1d.oss-eu-central-1.aliyuncs.com/036M/JB581668/-113852546/test?Expires=1773517935&OSSAccessKeyId=LTAI5t96WkBXXNzQrX4HtQti&Signature=U01ey8Tg0WPxka4YGmR%2F5fCGB28%3D"
}
```

**Storage path pattern:** `036M/{username}/{did}/{filename}`
**Signed URL expires** after a configured time.

**This is the file download mechanism for map data.** If we can find the correct filename/object_name for the saved map, we can download it as a file.

### The Missing Piece: How Does the App Get the Map Filename?

The MOVAhome app shows the map. It must know the filename. Possibilities:
1. **MQTT push** — the mower sends the filename via MQTT when a map is saved
2. **Device property** — stored in a property we haven't found yet (maybe higher SIIDs?)
3. **Separate API** — a map-specific endpoint we haven't discovered
4. **Convention-based** — filename follows a pattern like `{did}/map_current`

---

## 7. What the HA Integration Gets Right/Wrong

### What Works (via MQTT Push)
The Dreame cloud MQTT broker pushes property changes to subscribed clients. The HA integration receives:
- STATE (2.1) → `lawn_mower.mova_600_plus` state
- BATTERY_LEVEL (3.1) → `sensor.mova_600_plus_battery_level`
- CHARGING_STATUS (3.2) → `sensor.mova_600_plus_charging_status`

### What's Broken

1. **`sendCommand` endpoint doesn't exist** for Mova — the integration tries REST `get_properties` via this endpoint and gets 404. It falls back to MQTT push data.

2. **SIID/PIID mapping differs** — the cloud response uses `did` as device_id (e.g., `-113852546`) not as property enum value. Our fix resolves properties by matching `siid`/`piid` instead.

3. **`iotstatus/props` is not used** — the integration could use this endpoint to actively poll ALL properties, but it doesn't know about it. This is the **correct** REST endpoint for Mova.

4. **Map data is NOT a property** — SIID 6 fields are all empty. Map data is stored as files in Aliyun OSS, not as device properties.

5. **`_request_map_from_cloud()` uses `get_device_property`** which calls `iotstatus/history` — this returns 0 entries for all SIID 6 fields.

---

## 8. Fixes Applied Today

### In the Fork (Nils3311/dreame-mower)

| Commit | Fix | Impact |
|--------|-----|--------|
| `9f13180` | Replace py-mini-racer with mini-racer in manifest | Integration installs |
| `7b452d6` | 5 surgical bug fixes (#35, #39, #41, #42, #46) | Various crash fixes |
| `ad43f17` | Make mini-racer import optional | HA Docker compatibility |
| `23acb7d` | Add `_supports_native_async_webrtc` | Camera entity loads |
| `2bc001a` | Add MAP_LIST, sensors to default_properties | Properties requested |
| `0758542` | Include all properties when data dict empty | First-connect fix |
| `049e34d` | **Resolve cloud properties by siid/piid instead of did** | **Critical — makes data flow** |
| `265ab1e` | Actively request MAP_LIST from cloud | MAP_LIST polling |
| `f1cc9cb` | Enable cloud map fetching for dreame_cloud devices | Allow map data fetch |

---

## 9. Next Steps for Map Display

### Priority 1: Find the Map File Object Name

The map exists as a file in Aliyun OSS. We need the filename/object_name. Options:

**Option A: Sniff MQTT traffic**
- Connect to `20000.mt.eu.iot.mova-tech.com:19974` with the same credentials
- Subscribe to the device topic
- Watch for messages containing filenames or object_names
- The mower likely pushes map updates as MQTT messages with the OSS filename

**Option B: Try common filename patterns**
```python
patterns = [
    f"map_current",
    f"map",
    f"saved_map",
    f"mova.mower.g2552b/{uid}/{did}/0",  # object_name pattern from protocol.py
    f"036M/JB581668/{did}/map",
]
```

**Option C: Scan `iotstatus/props` for higher SIIDs (16-30)**
Maybe the map filename is stored in a property we haven't scanned yet.

**Option D: Use `iotstatus/history` with broader time ranges**
Maybe MAP_DATA events are stored but with different time parameters.

**Option E: Intercept MOVAhome app traffic**
Use mitmproxy/Charles to capture the exact API calls the app makes to display the map.

### Priority 2: Implement `iotstatus/props` as Primary Data Source

Replace the broken `sendCommand` REST calls with `iotstatus/props` endpoint:
```python
# In protocol.py, add new method:
def get_properties_mova(self, keys: list[str]) -> list:
    """Get properties via iotstatus/props (Mova-specific)."""
    keys_str = ",".join(keys)
    response = self._api_call(
        f"{self._strings[23]}/{self._strings[25]}/{self._strings[41]}",
        {"did": str(self._did), "keys": keys_str}
    )
    if response and response.get("code") == 0:
        return response.get("data", [])
    return []
```

### Priority 3: Decode 1.4 Telemetry

The 33-byte telemetry frame contains live position data. Decoding this would give us:
- Robot X/Y position on the map
- Heading/orientation
- Possibly sensor readings (LiDAR distance, wheel encoders)

---

## 10. Local Development Setup

### Test Scripts
All in `/Users/nilshoffmann/Documents/Programmieren/hass/`:
- `test_mova_cloud.py` — Full API endpoint test
- `test_mova_props.py` — Property endpoint format testing
- `test_mova_allprops.py` — Full SIID/PIID scan
- `test_mova_telemetry.py` — Telemetry analysis

### Running Locally
```bash
pip3 install --break-system-packages pycryptodome python-miio paho-mqtt requests
python3 test_mova_cloud.py
```

### Integration Code Locations
- Live HA: `/Volumes/config/custom_components/dreame_mower/`
- Git repo: `/Volumes/config/custom_components/dreame_mower_repo/`
- Fork: `https://github.com/Nils3311/dreame-mower`

### Diagnostic Files (written by integration at runtime)
- `/Volumes/config/dreame_mower_diag.json` — Connection state at first update
- `/Volumes/config/dreame_mower_props_*.json` — Property request/response data
- `/Volumes/config/dreame_mower_map_result.json` — Map data fetch results

### Key Files to Modify
| File | What it does | Key for map |
|------|-------------|-------------|
| `dreame/protocol.py` | Cloud communication | Need to add `iotstatus/props` support, fix `sendCommand` 404 |
| `dreame/device.py` | Property management | SIID/PIID mapping, property fetching |
| `dreame/map.py` | Map rendering | `_request_map_from_cloud()` needs Mova-specific path |
| `dreame/types.py` | Property enum mapping | May need Mova-specific SIID/PIID overrides |
| `camera.py` | HA camera entity | Depends on map_manager having data |

---

## 11. Comparison: Dreame Vacuum vs Mova Mower Cloud

| Aspect | Dreame Vacuum | Mova 600 Plus |
|--------|--------------|---------------|
| Login response | `{"code": 0, "data": {"access_token": ...}}` | `{"access_token": ...}` (direct) |
| sendCommand | ✓ Works | ✗ 404 NOT FOUND |
| iotstatus/props | Uses `get_properties` via sendCommand | ✓ Works with `keys` parameter |
| Map data source | Cloud property (SIID 6, get_device_property → iotstatus/history) | NOT in properties — stored as files in Aliyun OSS |
| MQTT topics | Properties pushed on change | Only STATE, BATTERY, CHARGING pushed |
| Telemetry | Via properties | Binary frames in SIID 1.4 (proprietary format) |
| Property format | `{"did": <prop_enum>, "siid": x, "piid": y, "value": v}` | `{"key": "siid.piid", "value": "v", "updateDate": ts}` |

---

---

## 12. MAP DATA BREAKTHROUGH (Late Session)

### The Correct Endpoint: `iotuserdata/getDeviceData`

```
POST /dreame-user-iot/iotuserdata/getDeviceData
Content-Type: application/json
Dreame-Auth: <token>

{"did": "-113852546", "uid": "14935817", "region": "eu"}
```

**This returns ALL device data including the complete map!** Response is a dict with 58 keys.

### Map Data Structure

Map data is split across `MAP.0` through `MAP.29` (each 1024 chars max). `MAP.info` gives the total character count (18828). Reassemble by concatenating chunks in order and trimming to `MAP.info` length.

**Reassembled map is a JSON array of 2 map objects:**

```json
[
  {
    "mowingAreas": {"dataType": "Map", "value": [[1, {"id": 1, "type": 0, "path": [{"x": 1400, "y": 3440}, ...]}]]},
    "forbiddenAreas": {"dataType": "Map", "value": [...]},  // 4 forbidden zones
    "contours": {"dataType": "Map", "value": [...]},          // 4 contour lines
    "paths": {"dataType": "Map", "value": []},
    "spotAreas": {"dataType": "Map", "value": []},
    "cleanPoints": {"dataType": "Map", "value": []},
    "obstacles": {"dataType": "Map", "value": []},
    "boundary": {"x1": -15050, "y1": -22710, "x2": 1420, "y2": 7330},
    "totalArea": 199,
    "name": "Map1",
    "mapIndex": 0,
    "md5sum": "33617bd6a510cc29abbf37cfae20617a"
  },
  {
    "name": "Map2",
    "mapIndex": 1,
    "totalArea": 0
    // Empty second map slot
  }
]
```

**Coordinate system:** All X/Y values appear to be in millimeters relative to the charging station.

### Mowing Path Data

`M_PATH.0` through `M_PATH.15` contain the mowing path coordinates. `M_PATH.info` = total char count.

Path format: flat arrays of `[x, y]` pairs, with `[32767, -32768]` as segment separator (pen-up marker).

```
[-4,-250],[-1029,-250],[-1029,-260],[-4,-260],[0,-270],[-1034,-270],...
[32767,-32768],  // pen-up: move without cutting
[-311,284],[-311,294],[-919,294],...
```

### Other Data Keys

| Key | Content |
|-----|---------|
| `SETTINGS.0-1` | Mower config: mowing height, edge mode, obstacle avoidance settings |
| `SCHEDULE_TASK.0` | Scheduled mowing tasks with times and days |
| `FBD_NTYPE.0` | Forbidden zone notification types |
| `OTA_INFO.0` | Firmware update info |
| `prop.s_auto_upgrade` | Auto-upgrade setting |

### Implementation Plan for Map Display

**Step 1: Add `getDeviceData` API call to protocol.py**
```python
def get_device_user_data(self) -> dict:
    """Fetch all device data including map via iotuserdata endpoint."""
    response = self._api_call(
        f"{self._strings[23]}/{self._strings[26]}/{self._strings[44]}",
        {"did": str(self._did), "uid": str(self._uid), "region": self._country}
    )
    if response and response.get("code") == 0:
        return response.get("data", {})
    return {}
```

Note: `self._strings[26]` = `"iotuserdata"`, `self._strings[44]` = `"getDeviceData"`

**Step 2: Parse chunked map data**
```python
def parse_chunked_data(data: dict, prefix: str) -> str:
    """Reassemble chunked data (MAP.0, MAP.1, ..., MAP.N) using prefix.info as length."""
    total_len = int(data.get(f"{prefix}.info", 0))
    if total_len == 0:
        return None
    chunks = {}
    for key, val in data.items():
        if key.startswith(f"{prefix}.") and key != f"{prefix}.info":
            idx = int(key.split(".")[1])
            chunks[idx] = str(val)
    full_str = "".join(chunks[i] for i in sorted(chunks.keys()))
    return full_str[:total_len]
```

**Step 3: Create a Mova-specific MapManager (or adapt existing)**

The existing `DreameMapMowerMapManager` expects binary AES-encrypted map frames from `get_device_property`. For Mova, the map is:
- Plain JSON (not encrypted)
- Stored as chunked user data (not cloud property)
- Contains polygon paths (not raster pixel data)

**Two approaches:**
1. **Adapter:** Convert Mova JSON map format to the format `DreameMapMowerMapManager` expects
2. **New renderer:** Create a simpler PNG renderer that draws polygons from X/Y coordinates

Option 2 is likely easier since the Mova map format is fundamentally different (vector polygons vs raster pixels).

**Step 4: Render map as PNG**
```python
from PIL import Image, ImageDraw

def render_mova_map(map_data: dict, path_data: str = None, width=800, height=800) -> bytes:
    boundary = map_data["boundary"]
    # Scale coordinates to image size
    x_range = boundary["x2"] - boundary["x1"]
    y_range = boundary["y2"] - boundary["y1"]
    scale = min(width / x_range, height / y_range) * 0.9

    img = Image.new("RGB", (width, height), (34, 139, 34))  # green background
    draw = ImageDraw.Draw(img)

    # Draw mowing areas
    for area_id, area in map_data["mowingAreas"]["value"]:
        points = [(int((p["x"] - boundary["x1"]) * scale + width*0.05),
                    int((p["y"] - boundary["y1"]) * scale + height*0.05))
                   for p in area["path"]]
        draw.polygon(points, fill=(144, 238, 144))

    # Draw forbidden areas
    for area_id, area in map_data["forbiddenAreas"]["value"]:
        points = [(int((p["x"] - boundary["x1"]) * scale + width*0.05),
                    int((p["y"] - boundary["y1"]) * scale + height*0.05))
                   for p in area["path"]]
        draw.polygon(points, fill=(255, 0, 0, 128))

    # Draw mowing path
    if path_data:
        # Parse path coordinates and draw lines
        pass

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
```

### Properties via `iotstatus/props` (Correct Endpoint for Mova)

Instead of the non-existent `sendCommand`, use `iotstatus/props`:

```python
def get_properties_mova(self, siid_piid_list: list[str]) -> list[dict]:
    """Get current property values via iotstatus/props.

    Args:
        siid_piid_list: List of "siid.piid" strings, e.g. ["2.1", "3.1"]

    Returns:
        List of {"key": "2.1", "value": "1", "updateDate": 123456789}
    """
    keys_str = ",".join(siid_piid_list)
    response = self._api_call(
        f"{self._strings[23]}/{self._strings[25]}/{self._strings[41]}",
        {"did": str(self._did), "keys": keys_str}
    )
    if response and response.get("code") == 0:
        return response.get("data", [])
    return []
```

---

## 13. Summary: What Needs to Change in the Integration

### protocol.py
1. Add `get_device_user_data()` method using `iotuserdata/getDeviceData`
2. Add `get_properties_mova()` method using `iotstatus/props`
3. Fix or replace `sendCommand` calls — endpoint doesn't exist for Mova

### device.py
1. On startup, call `get_device_user_data()` to fetch map + settings
2. Use `get_properties_mova()` for property polling instead of broken `sendCommand`
3. Parse `SETTINGS` data for mower configuration
4. Parse `SCHEDULE_TASK` for schedule entities

### map.py (or new mova_map.py)
1. New map parser for Mova JSON format (polygon-based, not raster)
2. Chunk reassembly logic (`MAP.0-N` + `MAP.info`)
3. Path reassembly logic (`M_PATH.0-N` + `M_PATH.info`)
4. PNG renderer using PIL (draw polygons + paths)

### camera.py
1. Use new Mova map renderer instead of `DreameMowerMapOptimizer`
2. Periodic refresh via `getDeviceData` (map updates during mowing)

### Estimated Effort
- **Properties via iotstatus/props:** 2-3 hours (protocol change + device.py adaptation)
- **Map data fetch + parse:** 2-3 hours (new endpoint + chunk reassembly)
- **Map renderer:** 4-6 hours (polygon rendering, path drawing, coordinate scaling)
- **Camera entity integration:** 2-3 hours (wire renderer to camera entity)
- **Total:** ~12-15 hours of focused development

*Last updated: 2026-03-14 22:00*
*Author: Claude (assisted by Nils)*
