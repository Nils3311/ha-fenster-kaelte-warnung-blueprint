# Architecture Patterns

**Domain:** Home Assistant custom integration for Dreame/Mova robotic lawn mowers
**Researched:** 2026-03-14
**Confidence:** HIGH (based on direct codebase analysis of bhuebschen/dreame-mower v0.0.5-alpha)

## System Overview

The integration is a layered system forked from Tasshack/dreame-vacuum with vacuum-to-mower adaptations. The architecture has 4 distinct layers, each with clear responsibilities:

```
[Home Assistant Core]
        |
  [HA Platform Layer]     lawn_mower.py, camera.py, sensor.py, switch.py, ...
        |
  [Coordinator Layer]     coordinator.py -- bridges async HA world to sync device world
        |
  [Device Layer]          dreame/device.py -- state machine, property management, actions
        |
  [Protocol Layer]        dreame/protocol.py -- cloud MQTT + local MiIO transport
        |
  [Map Subsystem]         dreame/map.py -- map manager, decoder, renderer (semi-independent)
        |
  [Type Definitions]      dreame/types.py, dreame/const.py -- enums, model capabilities
        |
  [Resources]             dreame/resources.py -- compressed model definitions, images
```

## Component Boundaries

| Component | File(s) | Responsibility | Communicates With |
|-----------|---------|---------------|-------------------|
| **Config Flow** | `config_flow.py` | Device discovery, account login (Dreame/Mova/local), setup UI | Protocol (for login/discovery) |
| **Coordinator** | `coordinator.py` | HA DataUpdateCoordinator, bridges async HA to sync Device, fires events/notifications | Device, HA Core |
| **Entity Base** | `entity.py` | Base entity class with property-driven pattern, dynamic name/icon/availability | Coordinator |
| **Lawn Mower Entity** | `lawn_mower.py` | Start/pause/dock actions, HA services (zone clean, segment clean, map ops), state mapping | Coordinator, Device (via coordinator) |
| **Camera Entity** | `camera.py` | Map image serving via custom CameraViews, map renderer initialization, history/obstacle/recovery map endpoints | Coordinator, Map Renderer |
| **Sensor Entities** | `sensor.py` | Battery, blade wear, area mowed, state, status, cleaning time, consumables | Coordinator |
| **Other Entities** | `switch.py`, `select.py`, `number.py`, `button.py`, `time.py` | DND, child lock, cleaning mode, volume, map saving, etc. | Coordinator |
| **Device** | `dreame/device.py` | Central state machine: property polling, action dispatch, status computation, capability detection, map manager lifecycle | Protocol, Map Manager, Types |
| **Protocol** | `dreame/protocol.py` | Transport abstraction: `DreameMowerProtocol` facade wrapping cloud (MQTT) and local (MiIO) protocols | Dreame/Mova cloud APIs, device LAN |
| **Map Manager** | `dreame/map.py` (DreameMapMowerMapManager) | Map data acquisition from cloud, frame processing, map list management | Protocol (cloud), Map Decoder |
| **Map Editor** | `dreame/map.py` (DreameMapMowerMapEditor) | Optimistic edits to map data (zone settings, segment names, cleaning config) | Map Manager |
| **Map Decoder** | `dreame/map.py` (DreameMowerMapDecoder) | Decodes compressed/encrypted map frames into MapData objects | None (pure transform) |
| **Map Renderer** | `dreame/map.py` (DreameMowerMapRenderer) | Renders MapData to PNG images with layers (walls, paths, segments, robot position) | Map Decoder output |
| **Map JSON Renderer** | `dreame/map.py` (DreameMowerMapDataJsonRenderer) | Renders MapData to JSON for Valetudo-compatible map cards | Map Decoder output |
| **Map Optimizer** | `dreame/map.py` (DreameMowerMapOptimizer) | Post-processing on map data (path smoothing, segment optimization) | Map Manager |
| **Types** | `dreame/types.py` | All enums (Property, Action, State, Error, Status), dataclasses (MapData, Segment, Path), property/action mappings, PIID/DIID helpers, model capability definitions | Everyone (imported everywhere) |
| **Constants** | `dreame/const.py` | String mappings, error descriptions, model capability definitions (compressed), map parameter names | Types, Device |
| **Resources** | `dreame/resources.py` | Compressed/base64 model definitions, error images, consumable images | Device (capability detection), Coordinator (notifications) |

## Data Flow

### 1. Startup Sequence

```
HA calls async_setup_entry()
  -> Creates DreameMowerDataUpdateCoordinator
  -> Coordinator creates DreameMowerDevice(name, host, token, username, password, country, ...)
     -> Device creates DreameMowerProtocol (facade)
        -> Protocol creates DreameMowerDreameHomeCloudProtocol (MQTT client)
     -> Device creates DreameMapMowerMapManager (if cloud available)
        -> MapManager creates DreameMapMowerMapEditor
        -> MapManager creates DreameMowerMapOptimizer
  -> Coordinator calls async_config_entry_first_refresh()
     -> Calls _async_update_data() (runs ONCE)
        -> Runs device.update() in executor thread (blocking I/O)
           -> device.connect_device()
              -> protocol.connect() -- MQTT login, subscribe to device topic
              -> protocol._request_properties() -- initial property fetch via cloud
           -> device._handle_properties() -- parses response into device.data dict
           -> device.capability.refresh() -- determines device capabilities from properties
           -> device.schedule_update() -- starts periodic Timer-based polling
  -> HA creates platform entities (lawn_mower, camera, sensor, etc.)
```

### 2. Periodic Update Cycle (After Startup)

```
Device._update_timer fires (every 10-30s depending on state)
  -> device.update()
     -> protocol.get_properties([STATE, ERROR, BATTERY, STATUS, ...])
        -> cloud.send("get_properties", params) via MQTT
        <- Response arrives via MQTT callback
     -> device._handle_properties(results)
        -> For each property: compare to previous value
        -> If changed: fire _property_update_callback[property]
           -> Individual handlers: _task_status_changed, _status_changed, etc.
        -> Fire _update_callback (general update)
           -> coordinator.set_updated_data()
              -> HA entities receive async_write_ha_state()
     -> If cloud connection: map_manager.update() runs in parallel
        -> Fetches MAP_DATA and OBJECT_NAME properties from cloud
        -> Decodes partial map frames via DreameMowerMapDecoder
        -> Merges into current MapData
        -> Fires map_changed callback
           -> camera entities re-render via DreameMowerMapRenderer
```

### 3. Map Data Flow (Detail)

```
Cloud MQTT
  -> DreameMapMowerMapManager._request_map_from_cloud()
     -> protocol.cloud.get_device_property(MAP_DATA, count=20, start_time=...)
     <- Returns list of timestamped map data entries
     -> For each entry: _decode_map_partial(json_data, timestamp)
        -> DreameMowerMapDecoder.decode_map(raw_data)
           -> AES decrypt (if encrypted)
           -> zlib decompress
           -> Parse binary pixel data, paths, segments, obstacles
           -> Returns MapDataPartial
     -> _add_cloud_map_data(partials, object_name, timestamp)
        -> Merge I-frames (full) and P-frames (delta) into MapData
        -> Update robot position, charger position, paths
        -> Fire _update_callback
  -> DreameMowerMapRenderer.render(map_data, config)
     -> Renders pixel grid to numpy array
     -> Draws layers: floor, walls, segments (colored), no-go zones, virtual walls
     -> Draws paths: cleaning path, predicted path
     -> Draws entities: robot, charger, obstacles
     -> Returns PNG bytes via PIL
  -> Camera entity serves PNG via /api/camera_proxy/{entity_id}
```

### 4. Action Flow (User Command)

```
User calls lawn_mower.start_mowing
  -> DreameMower.async_start_mowing()
     -> coordinator.device.start() (or start_custom, clean_segment, etc.)
        -> device._protocol.action(siid, aiid, params)
           -> cloud.send("action", {...}) via MQTT
           <- Action acknowledgement
        -> device._dirty_data[property] = DirtyData(value, timeout)
           (optimistic update: immediately reflect expected state)
        -> Fire _update_callback -> coordinator -> entities update
```

### 5. Cloud MQTT Message Flow

```
Dreame/Mova Cloud
  -> MQTT broker at {country}apigw.{strings}.com:{port}
  -> Device publishes property changes to /{topic}/{did}/{uid}/{model}/{country}/
  -> Integration subscribes to same topic
  -> DreameMowerDreameHomeCloudProtocol._on_message()
     -> Decrypts payload (ARC4 with session key)
     -> Parses JSON property updates
     -> Fires message_callback -> device handles property changes
```

## Key Architectural Insights

### The "God Object" Problem: device.py

`dreame/device.py` is 5,387 lines containing three classes:
- `DreameMowerDevice` (~3,800 lines) -- the entire device abstraction
- `DreameMowerDeviceStatus` (~1,300 lines) -- status helpers
- `DreameMowerDeviceInfo` (~65 lines) -- device metadata

`DreameMowerDevice` handles: protocol management, property polling, property change callbacks, action dispatch, status computation, capability detection, map manager lifecycle, cleaning history, dirty data (optimistic updates), timers, cloud connectivity, and more. This is the hardest component to modify safely.

**Recommendation for fork:** Do NOT refactor device.py significantly. Make surgical fixes. The complexity is inherited from upstream (Tasshack/dreame-vacuum) and refactoring risks breaking the property/action callback chain that everything depends on.

### The Map Subsystem: map.py

`dreame/map.py` is 9,322 lines containing 7 classes. It is semi-independent -- it communicates only with:
- `DreameMowerProtocol` (for fetching map data from cloud)
- `dreame/types.py` (for MapData, Segment, Path dataclasses)

The map subsystem has its own update timer and lifecycle, running in parallel to the main device update loop. This is the component most likely to need fixes (issues #39, #42).

**Key classes and their sizes:**
| Class | Lines (approx) | Purpose |
|-------|----------------|---------|
| DreameMapMowerMapManager | ~1,400 | Cloud map acquisition, frame merging |
| DreameMapMowerMapEditor | ~700 | Optimistic map edits |
| DreameMowerMapDecoder | ~1,400 | Binary frame decoding, AES/zlib |
| DreameMowerMapDataJsonRenderer | ~530 | JSON output for Valetudo cards |
| DreameMowerMapRenderer | ~3,500 | PNG rendering with PIL/numpy |
| DreameMowerMapOptimizer | ~1,500 | Path/segment post-processing |

### The Protocol Layer: Mova vs Dreame

`protocol.py` has a single cloud protocol class (`DreameMowerDreameHomeCloudProtocol`) that handles both Dreame and Mova accounts. The difference is controlled by `account_type` parameter ("dreame" vs "mova") which selects different API URL strings (stored compressed in `const.py` as `DREAME_STRINGS` vs `MOVA_STRINGS`).

The Mova 600 Plus should work through the "mova" account type path. The `config_flow.py` already has separate "Dreamehome Account" and "Mova Account" setup steps.

### The Model Support System

Model capabilities are determined at runtime via a two-step process:
1. Device properties are fetched from the cloud API
2. Model string (e.g., "dreame.mower.p2255") is matched against `DREAME_MODEL_CAPABILITIES` (a compressed lookup table in `const.py`)
3. Capabilities like `ai_detection`, `customized_cleaning`, `camera_streaming` are set as boolean flags

**Critical for Mova 600 Plus support:** The device capabilities table in `const.py` is a 19KB compressed blob. New models must be added here. If the model isn't found, capabilities fall back to property-detection only (which mostly works but may miss some features).

Issue #46 (Mova Lidax Ultra 800) shows what happens when a new model returns properties not in the `DreameMowerProperty` enum -- `ValueError: -115360139 is not a valid DreameMowerProperty`. The enum in `types.py` must be extended for any new model-specific properties.

### Vacuum Leftovers to Prune

The fork was a search-and-replace from vacuum to mower terminology, but significant vacuum-specific code remains:

| Area | Vacuum Leftover | Impact |
|------|-----------------|--------|
| `types.py` | Cleaning modes reference vacuum suction levels (SILENT, STANDARD, STRONG, TURBO) | Confusing but non-breaking |
| `types.py` | Furniture types, obstacle types designed for indoor vacuum | Unused for outdoor mower |
| `const.py` | Error codes for vacuum-specific hardware (mop, tank filter, dust collector) | Dead code, potentially confusing errors |
| `sensor.py` | Sensors for mop, filter, squeegee, silver ion, tank filter | Creates phantom entities |
| `lawn_mower.py` | Services for zone cleaning, segment cleaning, map editing still reference "cleaning" | Naming confusion |
| `device.py` | Properties for MOP_PAD_HUMIDITY, CLEANING_MODE suction levels | Non-functional properties |
| `map.py` | Furniture rendering, obstacle image cropping for camera-equipped vacuums | Dead code paths |
| `camera.py` | Obstacle image views, WiFi map views | May not apply to outdoor mowers |

**Recommendation:** Prune cautiously. Many vacuum properties are harmless (they simply return None and entities don't get created due to `exists_fn` checks). Focus on removing entities that actually appear incorrectly (phantom sensors) rather than gutting internal code paths.

## Recommended Architecture for Fork

### What to Keep Unchanged

1. **Protocol layer** (`dreame/protocol.py`) -- Working correctly for both Dreame and Mova accounts. The MQTT protocol is shared across all Dreame/Mova devices. No changes needed unless the Mova 600 Plus uses a different API version.

2. **Coordinator pattern** (`coordinator.py`) -- Standard HA DataUpdateCoordinator pattern. Only needs the event/notification code reviewed for mower-relevant events.

3. **Entity base class** (`entity.py`) -- Clean, generic pattern. No changes needed.

4. **Map decoder** (within `dreame/map.py`) -- The binary decoding is model-independent (same frame format across Dreame devices). The #39 bug is in the map manager, not the decoder.

### Where to Make Changes

#### Layer 1: Bug Fixes (No Architecture Changes)

| Bug | File | Fix |
|-----|------|-----|
| #39 Map parsing | `dreame/map.py:308` | `_request_i_map()` assumes `result` from `_request_map()` is a dict. Cloud can return a list. Add type check: `if result and isinstance(result, dict) and result.get(MAP_PARAMETER_CODE) == 0` |
| #42 Camera entity | `camera.py` | `DreameMowerCameraEntity` missing `_webrtc_provider` attribute. Add `self._webrtc_provider = None` before `Camera.__init__(self)` in constructor. This is a HA 2025.x breaking change in the Camera base class. |
| #41 Config flow | `config_flow.py:71` | Remove `self.config_entry = config_entry` from `DreameMowerOptionsFlowHandler.__init__()`. HA 2025.12 deprecated explicit config_entry setting on OptionsFlow -- the base class handles it automatically. |
| #35 Dock command | `dreame/device.py` | The `dock()` method likely calls only CHARGE_ACTION without first calling STOP_ACTION. Need to send stop + charge sequence to properly end the mowing session so Dreame cloud sees it as completed. |
| #46 Property enum | `dreame/types.py` | `DreameMowerProperty` enum doesn't include all properties returned by newer Mova models. Add a try/except around `DreameMowerProperty(did)` in `_handle_properties()` to skip unknown properties instead of crashing. |

#### Layer 2: Mova 600 Plus Support

| Change | File | Detail |
|--------|------|--------|
| Model registration | `config_flow.py` | Add `"mova.mower.xxx"` to `model_map` dict (exact model ID from device pairing) |
| Property mappings | `dreame/types.py` | May need new PIID/SIID mappings if Mova 600 Plus uses different MiOT spec IDs |
| Capability config | `dreame/const.py` | Add model entry to `DREAME_MODEL_CAPABILITIES` compressed blob (or bypass with property-based detection) |
| Error handling | `dreame/device.py` | Wrap `DreameMowerProperty(did)` lookups in try/except to handle unknown properties from new models |

#### Layer 3: Vacuum Pruning (Low Risk)

| Change | Files | Detail |
|--------|-------|--------|
| Remove phantom sensors | `sensor.py` | Remove or gate sensor descriptions for MOP_PAD, TANK_FILTER, SILVER_ION, SQUEEGEE if not applicable to any mower |
| Remove phantom consumable notifications | `coordinator.py` | Remove CONSUMABLE_LENSBRUSH, SQUEEGEE, SILVER_ION, TANK_FILTER notification handlers |
| Clean up state mappings | `const.py`, `types.py` | Remove vacuum-only error codes and state names |
| Remove dead services | `lawn_mower.py` | Remove services that make no sense for mowers (e.g., mop mode settings) |

### What NOT to Touch

1. **dreame/resources.py** (19.2 MB) -- Compressed binary blob. Don't try to "clean" it. It auto-detects what's relevant per model.

2. **DreameMowerDeviceStatus** class in device.py -- 1,300 lines of status computation logic ported from the Dreame mobile app. Complex conditional chains. Changing this risks breaking state detection.

3. **Map rendering internals** in DreameMowerMapRenderer -- 3,500 lines of PIL/numpy rendering code. Works for mowers already. Only touch if map visuals are wrong (not just data parsing).

4. **Protocol encryption/auth** -- ARC4 encryption, HMAC signatures, MQTT TLS. Security-sensitive code that works. Don't touch.

## Patterns to Follow

### Pattern 1: Property-Driven Entity Registration

**What:** Entities are defined declaratively using dataclass descriptions. The `exists_fn` callback determines whether an entity should be created based on device capabilities and available properties.

**When:** Adding any new sensor, switch, or select entity.

**Example:**
```python
DreameMowerSensorEntityDescription(
    property_key=DreameMowerProperty.BATTERY_LEVEL,
    device_class=SensorDeviceClass.BATTERY,
    native_unit_of_measurement=UNIT_PERCENT,
    state_class=SensorStateClass.MEASUREMENT,
    # exists_fn defaults to checking if property_key is in device.data
)
```

**Why this matters:** You never need to manually check model support. If the device doesn't report a property, the entity silently doesn't get created.

### Pattern 2: Optimistic Dirty Data Updates

**What:** When the user triggers an action (start, dock), the device immediately sets a "dirty" value for the affected properties with a timeout. The UI reflects the expected state before the cloud confirms it.

**When:** Any action that changes device state.

**Example from device.py:**
```python
def start(self):
    # Dispatch action to cloud
    self._protocol.action(siid, aiid, params)
    # Optimistically update local state
    self._dirty_data[DreameMowerProperty.STATE] = DirtyData(
        DreameMowerState.MOWING, timeout=self._discard_timeout
    )
    self._property_changed()  # Notify listeners immediately
```

### Pattern 3: Callback-Based Property Change Propagation

**What:** The Device maintains a dict of `_property_update_callback[property] = callback`. When a property changes, the specific callback fires, plus a general `_update_callback`. The coordinator registers its `set_updated_data` as the general callback.

**When:** Any new property that needs to trigger specific behavior on change.

```python
# In device.__init__:
self.listen(self._task_status_changed, DreameMowerProperty.TASK_STATUS)

# General callback reaches coordinator:
self._device.listen(self.set_updated_data)  # No property = general callback
```

## Anti-Patterns to Avoid

### Anti-Pattern 1: Refactoring the God Objects

**What:** Attempting to split `device.py` (5,387 lines) or `map.py` (9,322 lines) into smaller modules.

**Why bad:** These files mirror the upstream Tasshack/dreame-vacuum structure. Refactoring creates massive merge conflicts if you ever want to pull upstream changes. The internal coupling between methods is tight -- splitting requires understanding every callback chain.

**Instead:** Make surgical, well-commented changes. Use `# FORK: reason` comments for every change to make future merges easier.

### Anti-Pattern 2: Modifying the Compressed Resources

**What:** Trying to edit `DREAME_MODEL_CAPABILITIES` in `const.py` or model definitions in `resources.py`.

**Why bad:** These are compressed blobs (gzip + base64). Editing requires decompressing, modifying, recompressing. Easy to corrupt. The capability system falls back to property-detection when models aren't in the table.

**Instead:** For Mova 600 Plus, rely on property-based capability detection and only add to the capability table if specific capabilities are incorrectly detected.

### Anti-Pattern 3: Blocking I/O in the Coordinator

**What:** Adding synchronous network calls in coordinator methods that run on the HA event loop.

**Why bad:** The existing architecture carefully puts all blocking I/O (protocol.send, map fetching) in executor threads via `hass.async_add_executor_job`. The coordinator's `_async_update_data` only runs once; after that, the device's own Timer thread handles polling.

**Instead:** Always use `hass.async_add_executor_job()` for any new blocking operations.

## Dependency Graph and Build Order

```
Layer 0: dreame/types.py, dreame/const.py, dreame/exceptions.py
  No external dependencies. All other layers import from here.
  CHANGE FIRST: Add new properties/enums for Mova 600 Plus here.

Layer 1: dreame/protocol.py
  Depends on: types, const, exceptions
  External: paho-mqtt, miio, pycryptodome
  CHANGE SECOND (if needed): Only if Mova 600 Plus protocol differs.

Layer 2: dreame/map.py
  Depends on: types, const, protocol, resources
  External: PIL, numpy, py_mini_racer, cryptography
  CHANGE THIRD: Fix #39 map parsing bug here.

Layer 3: dreame/device.py
  Depends on: types, const, protocol, map, resources, exceptions
  CHANGE FOURTH: Fix #35 dock command, #46 property validation.

Layer 4: coordinator.py, entity.py
  Depends on: dreame/* (device, types, const)
  CHANGE FIFTH: Minor notification/event cleanup.

Layer 5: lawn_mower.py, camera.py, sensor.py, switch.py, etc.
  Depends on: coordinator, entity, dreame/*
  CHANGE LAST: Fix #42 camera entity, prune phantom sensors.
  config_flow.py also at this layer: Fix #41, add Mova 600 Plus model.
```

### Suggested Build Order for Phases

1. **Bug fixes in dependency order:** #41 config_flow (Layer 5) -> #46 property validation (Layer 3/types) -> #39 map parsing (Layer 2) -> #42 camera entity (Layer 5) -> #35 dock command (Layer 3)

2. **Mova 600 Plus support:** Pair device -> capture model ID -> add to config_flow model_map -> test property fetch -> fix any property enum gaps -> test map data -> test actions

3. **Vacuum pruning:** Remove phantom sensor descriptions -> clean up consumable notifications -> remove dead services -> clean up error code mappings

### Why This Order

- Bug fixes first because they affect all users, not just Mova 600 Plus
- #41 and #42 are trivial one-line fixes that immediately improve stability
- #46 (property validation) is needed before Mova 600 Plus work because new models will return unknown properties
- #39 (map parsing) blocks map display for everyone
- #35 (dock command) is functional but not blocking
- Mova 600 Plus support requires a working, stable base
- Vacuum pruning is lowest priority because the exists_fn pattern already hides most irrelevant entities

## Scalability Considerations

| Concern | Current State | At Fork Maturity |
|---------|---------------|------------------|
| Code maintainability | 5 files >1000 lines each, inherited from upstream | Accept large files; use `# FORK:` comments for traceability |
| Upstream sync | Fork diverges from Tasshack/dreame-vacuum | Cherry-pick relevant Tasshack bug fixes; bhuebschen tracks some automatically |
| Multi-model support | 4 models in config_flow model_map | Add Mova 600 Plus; capability detection handles differences |
| Map rendering perf | PIL/numpy rendering on each update (~100-500ms) | Acceptable for 10-30s update interval; low_resolution option exists |
| Cloud dependency | No fallback if cloud is down | By design -- Mova 600 Plus has no local API |

## Sources

- Direct codebase analysis: [bhuebschen/dreame-mower](https://github.com/bhuebschen/dreame-mower) v0.0.5-alpha (all files via GitHub API)
- Upstream reference: [Tasshack/dreame-vacuum](https://github.com/Tasshack/dreame-vacuum) v1.0.8
- Issue #35: [Dock command breaks schedules](https://github.com/bhuebschen/dreame-mower/issues/35) -- HIGH confidence
- Issue #39: [Map data parsing error](https://github.com/bhuebschen/dreame-mower/issues/39) -- HIGH confidence (bug confirmed in source)
- Issue #41: [Config flow 500 error](https://github.com/bhuebschen/dreame-mower/issues/41) -- HIGH confidence (fix confirmed by reporter)
- Issue #42: [Camera entity missing _webrtc_provider](https://github.com/bhuebschen/dreame-mower/issues/42) -- HIGH confidence (HA breaking change)
- Issue #46: [Mova Lidax Ultra 800 property errors](https://github.com/bhuebschen/dreame-mower/issues/46) -- HIGH confidence (traceback shows exact cause)
- HA Camera component breaking change (2025.x): `_webrtc_provider` attribute required -- MEDIUM confidence (inferred from error trace)
