# Phase 1: Stabilize and Connect - Research

**Researched:** 2026-03-14
**Domain:** Home Assistant custom integration bug fixes, dependency repair, and cloud device pairing
**Confidence:** HIGH

## Summary

Phase 1 requires fixing five known bugs, replacing one dead dependency, pinning all dependency versions, and pairing the integration with a real Mova 600 Plus device. The codebase has been inspected file-by-file; all bugs have been located at exact line numbers and verified against the actual source at `/Volumes/config/custom_components/dreame_mower_repo/`.

The paho-mqtt v2.0 compatibility issue is **already resolved** in the current codebase -- `CallbackAPIVersion.VERSION1` is explicitly specified on line 252 of `protocol.py`, and all three callback signatures (`_on_client_connect`, `_on_client_disconnect`, `_on_client_message`) match the VERSION1 convention. The remaining fixes are: (1) replace `py-mini-racer` with `mini-racer` (2 files), (2) remove deprecated `self.config_entry` assignment in `config_flow.py` line 71, (3) add `_webrtc_provider = None` to camera entity init, (4) wrap `DreameMowerProperty(did)` in try/except in `device.py`, (5) add type-checking to `result[MAP_PARAMETER_CODE]` access in `map.py` (5 locations), and (6) pin all manifest.json dependency versions.

Additionally, `config_flow.py` line 462 has a `KeyError` risk: `model_map[device["model"]]` will crash for any model not in the hardcoded `model_map` dict (only 4 Dreame models listed). This affects the Dreamehome account path but not the Mova account path.

**Primary recommendation:** Fix bugs in dependency order (manifest first, then types/device, then map, then camera/config_flow), then pair the real Mova 600 Plus device to discover its model ID and property set.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| FOUND-01 | Integration installs without errors on current HA (2025.x+) with all dependencies resolved | Replace `py-mini-racer` with `mini-racer` in manifest.json and map.py import; fix version format in manifest.json |
| FOUND-02 | Dead `py-mini-racer` dependency replaced with `mini-racer` | Exact files identified: `manifest.json` line 18, `dreame/map.py` line 16 and line 9153 |
| FOUND-03 | All dependency versions pinned in manifest.json | Target manifest with version floors provided in STACK.md; current manifest has zero pins |
| FOUND-04 | paho-mqtt v2.0 callback API compatibility verified | Already resolved: `CallbackAPIVersion.VERSION1` on protocol.py line 252; all callbacks match VERSION1 signatures |
| CONN-01 | User can add Mova 600 Plus via config flow using MOVAhome account credentials | Config flow has Mova account path (lines 492-576); KeyError bug on line 462 only affects Dreame path |
| CONN-02 | Integration discovers and pairs with Mova 600 Plus device (model ID confirmed) | `DREAME_MODELS` list (line 49-52) already includes `"mova.mower."` prefix; model_map needs Mova 600 Plus entry for Dreame path |
| CONN-03 | Cloud MQTT protocol maintains stable connection to Mova 600 Plus | Protocol.py uses MOVA_STRINGS for Mova account type (line 286); MQTT connect/subscribe/reconnect logic is model-agnostic |
| CONN-04 | Unknown property IDs from Mova 600 Plus do not crash the integration (fix #46) | Crash at `DreameMowerProperty(did)` in device.py lines 370, 402, 409, 414, 421; needs try/except wrapper |
| CLEAN-02 | Config flow deprecation warnings resolved (fix #41) | Remove `self.config_entry = config_entry` at config_flow.py line 71; also update `async_get_options_flow` to not pass config_entry |
</phase_requirements>

## Standard Stack

### Core (Already in codebase -- fix versions only)

| Library | Pin | Purpose | Current State |
|---------|-----|---------|---------------|
| `mini-racer` | >=0.12.0 | V8 JS engine for map optimizer | **Must replace** `py-mini-racer` (dead since 2021) |
| `pillow` | >=12.0.0 | Map PNG rendering | In manifest, no pin |
| `numpy` | >=2.0.0 | Map pixel buffer processing | In manifest, no pin |
| `paho-mqtt` | >=2.0.0 | Dreame/Mova cloud MQTT | In manifest, no pin; v2.0 compat already done |
| `pycryptodome` | >=3.20.0 | AES encryption for cloud protocol | In manifest, no pin |
| `python-miio` | >=0.5.12 | Xiaomi MiIO protocol handshake | In manifest, no pin |
| `pybase64` | >=1.4.0 | Fast base64 for map data | In manifest, no pin |
| `requests` | >=2.31.0 | HTTP client for cloud API | In manifest, no pin |

### Development Tools

| Tool | Version | Purpose |
|------|---------|---------|
| `pytest` | >=8.0.0 | Test runner |
| `pytest-homeassistant-custom-component` | >=0.13.300 | HA test fixtures |
| `pytest-asyncio` | >=0.23.0 | Async test support |
| `ruff` | >=0.15.0 | Linting + formatting |

## Architecture Patterns

### Project Structure (Existing -- Do Not Reorganize)

```
custom_components/dreame_mower/
├── __init__.py              # Entry point: async_setup_entry, platform forwarding
├── config_flow.py           # Dreame/Mova/Local account setup, device discovery
├── coordinator.py           # DataUpdateCoordinator, notification dispatch
├── entity.py                # Base entity class, property-driven registration
├── camera.py                # Map camera entities, custom CameraViews
├── lawn_mower.py            # LawnMowerEntity, start/pause/dock actions
├── sensor.py                # Battery, blade, area, state sensors
├── switch.py / select.py / number.py / button.py / time.py  # Other entities
├── const.py                 # Integration-level constants, notification strings
├── recorder.py              # Unrecorded attributes for camera
└── dreame/                  # Core library (model-agnostic)
    ├── protocol.py          # MQTT + MiIO transport (DreameMowerProtocol facade)
    ├── device.py            # Central state machine (5,387 lines -- DO NOT refactor)
    ├── map.py               # Map subsystem (9,322 lines -- surgical fixes only)
    ├── types.py             # All enums, dataclasses, PIID/DIID mappings
    ├── const.py             # String mappings, model capabilities blob
    ├── resources.py         # Compressed model definitions (19.2 MB)
    └── exceptions.py        # Custom exception classes
```

### Pattern: Surgical Fixes with FORK Comments

**What:** Every code change in the fork should be marked with a `# FORK:` comment explaining why.

**When:** Always, for every change.

**Example:**
```python
# FORK: Fix #46 - unknown property IDs from new Mova models
try:
    prop = DreameMowerProperty(did)
except ValueError:
    _LOGGER.debug("Unknown property ID %s with value %s, skipping", did, value)
    self.data[did] = value  # Still store for future reference
    continue
```

### Pattern: Safe Dict Access for Protocol Responses

**What:** The `_request_map()` method returns `self._protocol.action(...)` which can return a dict, a list, or None depending on cloud server version and account type.

**When:** Every access to `result[MAP_PARAMETER_CODE]` in map.py.

**Example:**
```python
# FORK: Fix #39 - cloud may return list instead of dict
if result and isinstance(result, dict) and result.get(MAP_PARAMETER_CODE) == 0:
```

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| V8 JavaScript execution | Custom JS interpreter | `mini-racer` | Map optimizer JS is complex; V8 binary handles it correctly |
| MiIO protocol | Own implementation | `python-miio` | Protocol framing, token exchange is fiddly; library handles it |
| MQTT reconnection | Custom reconnect logic | paho-mqtt's `reconnect_delay_set` + `loop_start` | Already built into paho-mqtt; current code uses it correctly |
| Map decoding | Manual binary parser | Existing `DreameMowerMapDecoder` | 1,400 lines of working decoder; inherited from upstream |

## Common Pitfalls

### Pitfall 1: DreameMowerProperty(did) ValueError Crash

**What goes wrong:** Unknown property IDs from new Mova models crash the entire integration at `device.py:370,402,409,414,421`.
**Root cause:** `DreameMowerProperty` is an IntEnum. `DreameMowerProperty(-115360139)` raises `ValueError`.
**How to avoid:** Wrap in try/except at the top of the property processing loop (line 360-361 area). Log unknown IDs at debug level and skip.
**Exact locations in device.py that call `DreameMowerProperty(did).name`:** Lines 370, 402, 409, 414, 421.
**Warning signs:** Error log: `ValueError: XXXXXXX is not a valid DreameMowerProperty`.

### Pitfall 2: Map Result Type Mismatch (5 Locations)

**What goes wrong:** `result[MAP_PARAMETER_CODE]` assumes `result` is a dict. Cloud can return a list.
**Root cause:** `_request_map()` returns `self._protocol.action(...)` raw output, which varies by cloud server.
**How to avoid:** Check `isinstance(result, dict)` before dict-key access at all 5 locations.
**Exact locations in map.py:** Lines 308, 384, 401, 433, 1351.
**Warning signs:** `TypeError: list indices must be integers or slices, not str`.

### Pitfall 3: Camera Entity Missing _webrtc_provider

**What goes wrong:** `Camera.__init__()` sets `_webrtc_provider = None` since HA 2024.11. If MRO doesn't reach `Camera.__init__()`, the attribute is missing.
**Root cause:** `DreameMowerCameraEntity(DreameMowerEntity, Camera)` -- the `super().__init__(coordinator, description)` on line 444 follows MRO through DreameMowerEntity -> CoordinatorEntity -> Entity. Camera is in the MRO but its `__init__` expects no positional args beyond `self`, so it may or may not be called depending on how the chain is wired.
**How to avoid:** Add `self._webrtc_provider = None` explicitly before line 444 or ensure `Camera.__init__()` is called.
**Warning signs:** `AttributeError: 'DreameMowerCameraEntity' object has no attribute '_webrtc_provider'`.

### Pitfall 4: model_map KeyError on Dreame Account Path

**What goes wrong:** `config_flow.py:462` does `model = model_map[device["model"]]` which raises `KeyError` for any model not in the 4-entry `model_map` dict.
**Root cause:** `model_map` only has 4 Dreame model strings. Any new model (including Mova models via Dreame path) crashes.
**How to avoid:** Use `model_map.get(device["model"], device["model"])` to fall back to the raw model string.
**Note:** The Mova account path (line 549) already uses `model = device["model"]` directly and does NOT have this bug.

### Pitfall 5: OptionsFlow config_entry Deprecation (HA 2025.12+)

**What goes wrong:** `config_flow.py:71` sets `self.config_entry = config_entry` explicitly, which was deprecated in HA 2025.1 and **errors** in HA 2025.12+ (`property 'config_entry' has no setter`).
**How to avoid:** Remove the `__init__` method entirely from `DreameMowerOptionsFlowHandler` (or just remove line 71). Also update `async_get_options_flow` on line 162-166 to not pass `config_entry`.
**Warning signs:** 500 Internal Server Error when opening integration settings.

### Pitfall 6: manifest.json Version Format

**What goes wrong:** Current `manifest.json` has `"version": "v0.0.5-alpha"` -- the `v` prefix and `-alpha` suffix may not be valid semver for HACS validation.
**How to avoid:** Use clean semver: `"version": "0.1.0"`.

## Code Examples

### Fix 1: Replace py-mini-racer with mini-racer

**manifest.json** (line 18):
```json
// BEFORE:
"py-mini-racer",
// AFTER:
"mini-racer>=0.12.0",
```

**dreame/map.py** (line 16):
```python
# BEFORE:
from py_mini_racer import MiniRacer
# AFTER:  FORK: Fix FOUND-02 - py-mini-racer is dead, use mini-racer
from mini_racer import MiniRacer
```

### Fix 2: Pin All Dependency Versions (manifest.json)

```json
{
  "domain": "dreame_mower",
  "name": "Dreame Mower",
  "codeowners": ["@nilshoffmann"],
  "config_flow": true,
  "documentation": "https://github.com/nilshoffmann/dreame-mower",
  "iot_class": "cloud_polling",
  "issue_tracker": "https://github.com/nilshoffmann/dreame-mower/issues",
  "requirements": [
    "pillow>=12.0.0",
    "numpy>=2.0.0",
    "pybase64>=1.4.0",
    "requests>=2.31.0",
    "pycryptodome>=3.20.0",
    "python-miio>=0.5.12",
    "mini-racer>=0.12.0",
    "paho-mqtt>=2.0.0"
  ],
  "version": "0.1.0"
}
```

### Fix 3: OptionsFlow Deprecation (config_flow.py)

```python
# BEFORE (lines 66-71):
class DreameMowerOptionsFlowHandler(OptionsFlow):
    """Handle Dreame Mower options."""
    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize Dreame Mower options flow."""
        self.config_entry = config_entry

# AFTER:  FORK: Fix #41 / CLEAN-02 - HA 2025.12 deprecated explicit config_entry
class DreameMowerOptionsFlowHandler(OptionsFlow):
    """Handle Dreame Mower options."""
    # No __init__ needed -- base class manages config_entry automatically

# Also update async_get_options_flow (lines 160-166):
# BEFORE:
@staticmethod
@callback
def async_get_options_flow(
    config_entry: ConfigEntry,
) -> DreameMowerOptionsFlowHandler:
    return DreameMowerOptionsFlowHandler(config_entry)

# AFTER:  FORK: Fix #41 - OptionsFlow no longer needs config_entry parameter
@staticmethod
@callback
def async_get_options_flow(
    config_entry: ConfigEntry,
) -> DreameMowerOptionsFlowHandler:
    return DreameMowerOptionsFlowHandler()
```

### Fix 4: Unknown Property Crash (device.py)

```python
# In _handle_properties(), around line 360:
# BEFORE:
did = int(prop["did"])
if prop["code"] == 0 and "value" in prop:
    value = prop["value"]
    if did in self._dirty_data:
        # ... DreameMowerProperty(did).name used without protection

# AFTER:  FORK: Fix #46 / CONN-04 - handle unknown property IDs from new models
did = int(prop["did"])
# Validate that this property ID is known before processing
try:
    prop_enum = DreameMowerProperty(did)
except ValueError:
    if prop["code"] == 0 and "value" in prop:
        _LOGGER.debug("Unknown property ID %s with value %s, skipping", did, prop["value"])
        self.data[did] = prop["value"]  # Store raw value
    continue

if prop["code"] == 0 and "value" in prop:
    value = prop["value"]
    # Now safe to use prop_enum.name in all subsequent logging
```

### Fix 5: Camera Entity _webrtc_provider (camera.py)

```python
# In DreameMowerCameraEntity.__init__(), before line 444:
def __init__(self, coordinator, description, ...):
    """Initialize a Dreame Mower Camera entity."""
    # FORK: Fix #42 / MAP-04 - HA 2024.11 requires _webrtc_provider attribute
    self._webrtc_provider = None
    super().__init__(coordinator, description)
    # ... rest of init
```

### Fix 6: Map Result Type Check (map.py)

```python
# BEFORE (5 locations: lines 308, 384, 401, 433, 1351):
if result and result[MAP_PARAMETER_CODE] == 0:

# AFTER:  FORK: Fix #39 - cloud may return list instead of dict
if result and isinstance(result, dict) and result.get(MAP_PARAMETER_CODE) == 0:
```

### Fix 7: model_map KeyError Protection (config_flow.py)

```python
# BEFORE (line 462):
model = model_map[device["model"]]

# AFTER:  FORK: Prevent KeyError for unknown models
model = model_map.get(device["model"], device["model"])
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `py-mini-racer` 0.6.0 | `mini-racer` 0.14.1 | 2022 (fork started) | Import path: `py_mini_racer` -> `mini_racer` |
| `paho-mqtt` v1.x callbacks | `paho-mqtt` v2.0 with `CallbackAPIVersion` | Feb 2024 | Already handled in codebase with `VERSION1` |
| OptionsFlow `self.config_entry = config_entry` | Base class manages automatically | HA 2025.1 (deprecated), 2025.12 (broken) | Remove manual assignment |
| Camera entity without `_webrtc_provider` | Camera.__init__ sets `_webrtc_provider` | HA 2024.11 | Must ensure attribute exists before Camera base init |

## paho-mqtt v2.0 Audit Results

**Status: ALREADY COMPATIBLE** (Confidence: HIGH)

The codebase already uses `CallbackAPIVersion.VERSION1` on `protocol.py` line 252:

```python
self._client = mqtt_client.Client(
    mqtt_client.CallbackAPIVersion.VERSION1,
    f"{self._strings[53]}{self._uid}...",
    clean_session=True,
    userdata=self,
)
```

Callback signatures match VERSION1 expectations:
- `_on_client_connect(client, self, flags, rc)` -- 4 params (client, userdata, flags, rc) -- CORRECT
- `_on_client_disconnect(client, self, rc)` -- 3 params (client, userdata, rc) -- CORRECT
- `_on_client_message(client, self, message)` -- 3 params (client, userdata, message) -- CORRECT

**No changes needed** for paho-mqtt compatibility. FOUND-04 can be verified by code review alone.

**Note:** Using VERSION1 emits deprecation warnings. A future improvement (not Phase 1 scope) would be migrating to VERSION2 callbacks, which have different signatures (flags becomes a `ConnectFlags` object, rc becomes a `ReasonCode` object). This is not urgent since VERSION1 remains functional.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest + pytest-homeassistant-custom-component |
| Config file | none -- see Wave 0 |
| Quick run command | `pytest tests/ -x -q` |
| Full suite command | `pytest tests/ -v --tb=short` |

### Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FOUND-01 | Integration loads without import errors | unit | `python -c "import custom_components.dreame_mower"` | No -- Wave 0 |
| FOUND-02 | mini-racer import works | unit | `python -c "from mini_racer import MiniRacer"` | No -- Wave 0 |
| FOUND-03 | manifest.json has version pins | unit | `pytest tests/test_manifest.py -x` | No -- Wave 0 |
| FOUND-04 | paho-mqtt v2.0 callbacks verified | manual-only | Code review (already compatible) | N/A |
| CONN-01 | Config flow Mova account step | integration | `pytest tests/test_config_flow.py::test_mova_flow -x` | No -- Wave 0 |
| CONN-02 | Device discovery returns model ID | integration | `pytest tests/test_config_flow.py::test_device_discovery -x` | No -- Wave 0 |
| CONN-03 | MQTT connection stable | manual-only | Live test with real device | N/A |
| CONN-04 | Unknown property IDs handled gracefully | unit | `pytest tests/test_device.py::test_unknown_property -x` | No -- Wave 0 |
| CLEAN-02 | OptionsFlow no deprecation warning | unit | `pytest tests/test_config_flow.py::test_options_flow -x` | No -- Wave 0 |

### Sampling Rate

- **Per task commit:** `python -c "import custom_components.dreame_mower"` (import smoke test)
- **Per wave merge:** `pytest tests/ -v --tb=short` (full suite)
- **Phase gate:** Full suite green + live device pairing verified

### Wave 0 Gaps

- [ ] `tests/` directory -- does not exist yet
- [ ] `tests/conftest.py` -- HA test fixtures
- [ ] `tests/test_manifest.py` -- validates manifest.json structure and version pins
- [ ] `tests/test_config_flow.py` -- config flow tests with mocked protocol
- [ ] `tests/test_device.py` -- device property handling tests including unknown properties
- [ ] Framework install: `pip install pytest pytest-homeassistant-custom-component pytest-asyncio`
- [ ] `pyproject.toml` or `setup.cfg` for test dependencies

## Open Questions

1. **Mova 600 Plus Model ID**
   - What we know: Mova models use prefix `mova.mower.` (already in `DREAME_MODELS` list at config_flow.py line 51)
   - What's unclear: The exact model string (e.g., `mova.mower.g2xxx`) is unknown until device pairing
   - Recommendation: Pair the device first using MOVAhome credentials, capture the model string from protocol logs, then add to `model_map` if needed

2. **Mova 600 Plus Property Set**
   - What we know: It will return MiOT properties via cloud MQTT just like Dreame mowers
   - What's unclear: Whether it returns properties with different PIID/SIID values or entirely new property IDs
   - Recommendation: Fix CONN-04 (unknown property handling) BEFORE pairing. Log all received properties at debug level to capture the full property set.

3. **Camera MRO and _webrtc_provider**
   - What we know: `DreameMowerCameraEntity(DreameMowerEntity, Camera)` has Camera in MRO. The issue is whether `Camera.__init__` is properly reached during `super().__init__()` chain.
   - What's unclear: Exact MRO behavior with `CoordinatorEntity` in the chain
   - Recommendation: Set `self._webrtc_provider = None` explicitly before `super().__init__()` -- safe regardless of MRO behavior.

4. **mini-racer ARM64 Wheel Availability**
   - What we know: mini-racer 0.14.1 provides wheels for common platforms
   - What's unclear: Whether ARM64 wheels are available for HA OS on Raspberry Pi
   - Recommendation: Not blocking for Phase 1 (dev environment is macOS). Document as known risk for production deployment on RPi.

## Sources

### Primary (HIGH confidence)
- Direct source inspection: `/Volumes/config/custom_components/dreame_mower_repo/` -- all files read and line numbers verified
- [HA Options Flow Deprecation Blog](https://developers.home-assistant.io/blog/2024/11/12/options-flow/) -- exact migration pattern
- [HA Camera Entity Breaking Change](https://github.com/home-assistant/core/issues/129532) -- `_webrtc_provider` requirement
- [paho-mqtt v2.0 Migration](https://eclipse.dev/paho/files/paho.mqtt.python/html/migrations.html) -- callback API version changes
- STACK.md, ARCHITECTURE.md, PITFALLS.md -- prior research documents

### Secondary (MEDIUM confidence)
- [LocalTuya OptionsFlow fix](https://github.com/rospogrigio/localtuya/issues/2132) -- confirms HA 2025.12 breaks `config_entry` setter
- [KartoffelToby/better_thermostat #1530](https://github.com/KartoffelToby/better_thermostat/issues/1530) -- confirms fix pattern

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- directly verified in source code and manifest.json
- Architecture: HIGH -- all bugs located at exact line numbers in actual source files
- Pitfalls: HIGH -- each pitfall verified against actual code; crash scenarios traced through call stack
- paho-mqtt audit: HIGH -- `CallbackAPIVersion.VERSION1` confirmed on line 252, all callback signatures verified
- Mova 600 Plus pairing: MEDIUM -- config flow supports Mova account type but model ID unknown until live test

**Research date:** 2026-03-14
**Valid until:** 2026-04-14 (stable domain; HA Camera/OptionsFlow APIs unlikely to change again soon)
