# Domain Pitfalls

**Domain:** Home Assistant custom integration for Dreame/Mova robotic lawn mowers (fork maintenance)
**Researched:** 2026-03-14
**Confidence:** HIGH (based on direct codebase analysis and upstream issue investigation)

## Critical Pitfalls

Mistakes that cause integration crashes, data loss, or require rewrites.

### Pitfall 1: Unknown Property Enum Values Crash the Integration

**What goes wrong:** When a new Dreame/Mova model returns properties not defined in the `DreameMowerProperty` IntEnum, `device.py:409` calls `DreameMowerProperty(did)` which raises `ValueError` and crashes the entire integration. No entities load. Issue #46 demonstrates this with the Mova Lidax Ultra 800.

**Why it happens:** The upstream code (from Tasshack/dreame-vacuum) assumes all properties are known. Each new device model can introduce new MiOT properties with unknown integer IDs. The integration treats this as fatal rather than graceful degradation.

**Consequences:** Integration completely non-functional for the device. No sensors, no map, no control. User sees "Config flow could not be loaded" or coordinator startup failure.

**Prevention:** Wrap `DreameMowerProperty(did)` in `_handle_properties()` with a try/except that logs unknown property IDs and skips them. This is the single most important fix for supporting any new model.

```python
# In device.py _handle_properties():
try:
    prop = DreameMowerProperty(did)
except ValueError:
    _LOGGER.debug("Unknown property ID %s, skipping", did)
    continue
```

**Detection:** Integration fails to start; error log contains `ValueError: XXXXXXX is not a valid DreameMowerProperty`.

### Pitfall 2: Map Data Response Type Mismatch

**What goes wrong:** `DreameMapMowerMapManager._request_i_map()` at line 308 accesses `result[MAP_PARAMETER_CODE]` assuming `result` is a dict. Some cloud API responses return a list instead of a dict, causing `TypeError: list indices must be integers or slices, not str`. Issue #39.

**Why it happens:** The `_request_map()` method returns the raw protocol response, which varies by cloud server version and account type (Dreame vs Mova). The mower fork inherited vacuum code that was tested against specific Dreame cloud responses.

**Consequences:** Map updates fail silently. The map freezes at the last successfully parsed frame. Integration continues running but map display shows stale data.

**Prevention:** Type-check the response before accessing it as a dict:
```python
if result and isinstance(result, dict) and MAP_PARAMETER_CODE in result and result[MAP_PARAMETER_CODE] == 0:
```

**Detection:** Log error "Map update Failed: TypeError: list indices must be integers or slices, not str" from `dreame/map.py`.

### Pitfall 3: HA Breaking Changes in Camera Base Class

**What goes wrong:** Home Assistant 2025.x changed the `Camera` base class to require a `_webrtc_provider` attribute. The `DreameMowerCameraEntity` initializes entity description before calling `Camera.__init__()`, and the HA framework accesses `_webrtc_provider` during `async_refresh_providers()` before the Camera init runs. Issue #42.

**Why it happens:** The entity initialization order in `camera.py` was inherited from the vacuum integration, which was written before the HA Camera refactor.

**Consequences:** Camera entity fails to register. No map display at all.

**Prevention:** Add `self._webrtc_provider = None` before calling `Camera.__init__(self)` in the entity constructor. Always test against the latest HA version after updates.

**Detection:** Error log: `AttributeError: 'DreameMowerCameraEntity' object has no attribute '_webrtc_provider'`.

### Pitfall 4: Modifying Compressed Model Capability Blobs

**What goes wrong:** `DREAME_MODEL_CAPABILITIES` in `const.py` is a ~19KB gzip+base64 compressed Python data structure. Attempting to decompress, edit, and recompress it can corrupt the data or change the structure subtly, breaking capability detection for all models.

**Why it happens:** The upstream integration compresses large data structures to reduce file size and load time. The format is not documented.

**Consequences:** Capability detection fails silently (returns None for model lookup, falls back to generic detection). Or worse, misdetects capabilities causing entities to appear/disappear incorrectly.

**Prevention:** Do NOT edit the compressed blobs directly. For Mova 600 Plus support, rely on the property-based capability detection fallback path in `DreameMowerDeviceCapability.refresh()`. Only modify the blob if specific capabilities are being incorrectly auto-detected.

**Detection:** Unexpected entities appearing or missing; capability list not matching device features.

## Moderate Pitfalls

### Pitfall 5: Dock Command Not Ending Mowing Session

**What goes wrong:** Calling `lawn_mower.dock` sends the mower back to dock but doesn't properly end the mowing session in Dreame's cloud state machine. The Dreame app still shows the session as active, preventing scheduled mowing from working. Issue #35.

**Why it happens:** The dock action likely sends only a CHARGE action without a preceding STOP action. The Dreame cloud expects a specific state transition sequence: PAUSE -> STOP -> CHARGE to properly terminate a session.

**Prevention:** Implement the dock command as a sequence: pause first (if mowing), then stop, then charge. Match the state transition sequence that the Dreame app uses.

**Detection:** After docking via HA, the Dreame app shows "Continue" / "End" / "Return to dock" buttons instead of the idle state.

### Pitfall 6: Options Flow Deprecated API (HA 2025.12+)

**What goes wrong:** `DreameMowerOptionsFlowHandler.__init__()` explicitly sets `self.config_entry = config_entry` which is deprecated in HA 2025.12+. Results in 500 Internal Server Error when opening integration settings. Issue #41.

**Why it happens:** HA 2025.12 changed `OptionsFlow` to manage `config_entry` internally. Explicitly setting it conflicts with the new base class behavior.

**Prevention:** Remove line 71 in `config_flow.py`. The base `OptionsFlow` class now handles `self.config_entry` automatically.

**Detection:** 500 error when clicking the gear icon on the integration in HA settings.

### Pitfall 7: Diverging from Upstream Makes Merges Painful

**What goes wrong:** Restructuring files, renaming classes, or reorganizing modules in the fork creates merge conflicts when trying to incorporate Tasshack/dreame-vacuum upstream fixes.

**Why it happens:** The fork (bhuebschen/dreame-mower) is a rename+adapt of Tasshack/dreame-vacuum. The core `dreame/` library is structurally identical. Tasshack continues to fix bugs and add features for the vacuum that may also apply to the mower.

**Prevention:** Keep structural changes minimal. Use `# FORK: reason` comments for every change. Prefer additive changes (new code) over modification of existing lines. When fixing shared bugs, consider contributing upstream.

**Detection:** git diff against upstream shows massive changes in files that should be similar.

### Pitfall 8: Thread Safety in Device Update Loop

**What goes wrong:** The device uses a `threading.Timer` for periodic updates and background thread queues for MQTT callbacks. The coordinator's `set_updated_data` bridges from these threads to HA's asyncio event loop via `hass.loop.call_soon_threadsafe()`. Race conditions can occur if device properties are being modified while the coordinator is reading them.

**Why it happens:** The protocol layer uses synchronous HTTP requests and MQTT callbacks in background threads. The device object is shared between the polling thread and the HA async context.

**Prevention:** Don't add new shared mutable state to the device object. Use the existing `_dirty_data` mechanism for optimistic updates. Don't bypass `call_soon_threadsafe()` when communicating from device threads to HA.

**Detection:** Intermittent `RuntimeError: dictionary changed size during iteration` or inconsistent state readings.

## Minor Pitfalls

### Pitfall 9: Vacuum-Specific Entities Appearing on Mower

**What goes wrong:** Sensors for mop pad humidity, tank filter, silver ion, squeegee, and other vacuum-specific consumables may appear as entities if the mower reports any related properties (even with value 0 or -1).

**Why it happens:** The `exists_fn` default only checks if the property key exists in `device.data`. If the cloud API returns a value (even 0) for a vacuum-only property, the entity gets created.

**Prevention:** Add explicit `exists_fn` checks that verify the property is both present AND relevant to the device type. Or simply remove vacuum-only sensor descriptions from `sensor.py`.

**Detection:** Extra entities with 0% or "Unknown" values in HA device page.

### Pitfall 10: py_mini_racer Dependency Issues

**What goes wrong:** `map.py` imports `py_mini_racer` (a V8 JavaScript engine) for executing JavaScript-based map decryption from the Dreame app. This package can fail to install on certain architectures (ARM32, unusual Linux distros).

**Why it happens:** py_mini_racer bundles the V8 engine as a native binary. Not all HA installation types (especially HassOS on older Raspberry Pi) have compatible binaries.

**Prevention:** Verify py_mini_racer works in the target HA environment before relying on map decryption features. Consider making it optional with a fallback.

**Detection:** Import error on `from py_mini_racer import MiniRacer` during integration load.

### Pitfall 11: Large resources.py Slows Integration Load

**What goes wrong:** `dreame/resources.py` is 19.2 MB (compressed data blobs). Importing it at module level adds noticeable delay to integration startup and increases memory usage.

**Why it happens:** The upstream integration bundles all model-specific images, error icons, and capability definitions in a single Python file as base64-encoded constants.

**Prevention:** Accept this for now. The data is loaded once and stays in memory. Lazy loading would require significant refactoring of the import chain.

**Detection:** Slow integration startup (5-10s on lower-powered hardware).

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Bug fixes | Fix #39 but break something else in map.py's 9,322 lines | Test with real device map data; don't change code paths you don't fully understand |
| Bug fixes | Fix #42 but incompatible with older HA versions | Check minimum HA version requirement in manifest.json; decide on supported versions |
| Mova 600 Plus support | Model returns unexpected property structure | Fix #46 first (property validation), then pair device to discover actual properties |
| Mova 600 Plus support | MQTT subscription topic format differs for Mova | Check MOVA_STRINGS vs DREAME_STRINGS decoded values; test with Mova account type |
| Vacuum pruning | Remove a "vacuum" property that the mower actually uses | Pair device first, capture full property dump, compare against existing enum before removing anything |
| Vacuum pruning | Break exists_fn logic that prevents vacuum entities from appearing | Test entity creation with and without pruning; verify no extra entities appear |

## Sources

- bhuebschen/dreame-mower issues #35, #39, #41, #42, #46 -- direct issue analysis via GitHub API
- Codebase analysis of dreame/device.py (5,387 lines), dreame/map.py (9,322 lines), dreame/protocol.py, dreame/types.py
- HA 2025.12 deprecation of explicit config_entry in OptionsFlow -- confirmed by issue #41 reporter fix
- HA Camera component breaking change -- confirmed by issue #42 traceback
