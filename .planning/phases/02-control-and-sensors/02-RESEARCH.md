# Phase 2: Control and Sensors - Research

**Researched:** 2026-03-14
**Domain:** Home Assistant lawn_mower entity controls, sensor/button entity platform, vacuum-to-mower entity pruning
**Confidence:** HIGH

## Summary

Phase 2 must ensure the three core lawn_mower controls (start/pause/dock) work correctly with the Mova 600 Plus, expose all mower-relevant sensors (battery, state, error, progress, blade wear), add a blade consumable reset button, create an online/connectivity binary sensor, and remove vacuum-specific ghost entities that the unpruned fork creates.

The codebase already has most of the infrastructure in place. The `lawn_mower.py` entity maps to `LawnMowerActivity` states, the `sensor.py` has definitions for battery, state, error, cleaning progress, blade wear (BLADES_LEFT, BLADES_TIME_LEFT), and area mowed. The `button.py` has a RESET_BLADES action. The primary work is: (1) verifying controls actually dispatch commands correctly for the Mova 600 Plus, (2) fixing the state mapping to use `LawnMowerActivity.RETURNING` (now available in HA), (3) investigating the dock-breaks-schedules issue, (4) adding a missing `binary_sensor` platform for connectivity, and (5) surgically removing vacuum-only sensor/switch/button/number/select entity descriptions.

**Primary recommendation:** Start with a verification pass of what already works with the live device, then fix the state mapping, investigate dock behavior, add the binary_sensor platform, and finally prune vacuum entities -- in that order.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CTRL-01 | User can start mowing from HA | lawn_mower.py `async_start_mowing()` calls `device.start()` which dispatches `DreameMowerAction.START_MOWING` (action 1). Already implemented. Needs live verification. |
| CTRL-02 | User can pause mowing from HA | lawn_mower.py `async_pause()` calls `device.pause()` which dispatches `DreameMowerAction.PAUSE` (action 2). Already implemented. Needs live verification. |
| CTRL-03 | User can dock without breaking schedules | lawn_mower.py `async_dock()` calls `device.dock()` which dispatches `DreameMowerAction.DOCK` (action 3) directly without STOP first. Issue #35 concern: may need STOP then DOCK sequence. See Pitfall 1. |
| SENS-01 | Battery level percentage sensor | sensor.py has `BATTERY_LEVEL` description with `SensorDeviceClass.BATTERY`. Already implemented. Needs live verification. |
| SENS-02 | Mower state sensor shows activity | sensor.py has `STATE` description + lawn_mower.py has `STATE_CODE_TO_STATE` mapping. RETURNING is mapped to MOWING but HA now has `LawnMowerActivity.RETURNING`. Fix needed. |
| SENS-03 | Error state sensor with description | sensor.py has `ERROR` description with `attrs_fn` exposing error value, faults, and description. Already implemented. Needs live verification. |
| SENS-04 | Online/connectivity binary sensor | No `binary_sensor.py` exists. Must create new platform. `device.device_connected` property exists (checks `protocol.connected`). |
| SENS-05 | Mowing progress percentage | sensor.py has `CLEANING_PROGRESS` description with `UNIT_PERCENT`. Already implemented. Needs live verification that Mova 600 Plus reports this property. |
| SENS-06 | Area mowed sensor (sq meters) | sensor.py has `CLEANED_AREA` description with `UNIT_AREA`. Already implemented. Needs live verification. |
| SENS-07 | Blade usage/wear sensor | sensor.py has `BLADES_LEFT` (percent) and `BLADES_TIME_LEFT` (hours) descriptions. Already implemented. Needs live verification. |
| SENS-08 | Blade consumable reset button | button.py has `RESET_BLADES` action description with `exists_fn` checking `device.status.blades_life is not None`. Already implemented. |
| CLEAN-01 | Remove vacuum-specific entities | sensor.py, switch.py, button.py, select.py, number.py, coordinator.py all contain vacuum-only entity descriptions. Must identify and remove/gate. See "Vacuum Entity Pruning" section. |
</phase_requirements>

## Standard Stack

### Core (Already in Place)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| homeassistant.components.lawn_mower | HA 2025.1+ | LawnMowerEntity base class | Native HA platform; provides START_MOWING, PAUSE, DOCK features and MOWING/DOCKED/PAUSED/RETURNING/ERROR activities |
| homeassistant.components.sensor | HA 2025.1+ | SensorEntity for battery, state, error, progress, blade wear | Standard HA sensor platform with device_class, state_class, unit support |
| homeassistant.components.binary_sensor | HA 2025.1+ | BinarySensorEntity for connectivity | Standard HA binary_sensor with BinarySensorDeviceClass.CONNECTIVITY |
| homeassistant.components.button | HA 2025.1+ | ButtonEntity for blade reset | Standard HA button platform for one-shot actions |

### No New Dependencies
This phase requires NO new pip packages. All work is within the existing integration code.

## Architecture Patterns

### Recommended Project Structure Changes
```
custom_components/dreame_mower/
  __init__.py          # ADD: Platform.BINARY_SENSOR to PLATFORMS tuple
  binary_sensor.py     # NEW: Connectivity binary sensor
  sensor.py            # MODIFY: Remove vacuum-only sensor descriptions
  button.py            # MODIFY: Remove vacuum-only button descriptions
  switch.py            # MODIFY: Remove vacuum-only switch descriptions
  select.py            # MODIFY: Remove vacuum-only select descriptions
  number.py            # MODIFY: Remove vacuum-only number descriptions
  lawn_mower.py        # MODIFY: Fix state mapping for RETURNING; investigate dock
  coordinator.py       # MODIFY: Remove vacuum-only consumable checks
  const.py             # MODIFY: Remove vacuum-only consumable constants
  dreame/device.py     # MODIFY: Potentially fix dock() to stop+dock sequence
```

### Pattern 1: Property-Driven Entity Registration (Existing)
**What:** Every entity description uses `exists_fn` callback to determine creation based on device capabilities and reported properties.
**When to use:** Every entity modification in this phase.
**Key insight:** The `exists_fn` on `DreameMowerEntityDescription` defaults to checking if `description.property_key.value` exists in `device.data`. If the Mova 600 Plus does not report a property (returns None or property not in data dict), the entity silently is not created. This means vacuum-specific entities whose properties the mower does not report will NOT appear. But some vacuum properties might share SIID/PIID numbers with mower properties, creating ghost entities.

```python
# Source: entity.py lines 44-64
exists_fn: Callable[[object, object], bool] = lambda description, device: bool(
    (description.action_key is not None and description.action_key in device.action_mapping)
    or description.property_key is None
    or (
        isinstance(description.property_key, DreameMowerProperty)
        and description.property_key.value in device.data
    )
    # ... also checks AutoSwitchProperty, StrAIProperty, AIProperty
)
```

### Pattern 2: Adding a New Platform (binary_sensor)
**What:** Register the platform in `__init__.py` PLATFORMS tuple and create the platform file.
**When to use:** Adding the connectivity binary sensor (SENS-04).
**Example:**
```python
# __init__.py: Add Platform.BINARY_SENSOR to PLATFORMS tuple
PLATFORMS = (
    Platform.LAWN_MOWER,
    Platform.SENSOR,
    Platform.BINARY_SENSOR,  # NEW
    Platform.SWITCH,
    Platform.BUTTON,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.CAMERA,
    Platform.TIME,
)
```

```python
# binary_sensor.py (new file)
# Source: HA binary_sensor developer docs
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)

# Use device.device_connected property for connectivity state
```

### Pattern 3: State Mapping Fix
**What:** The current `STATE_CODE_TO_STATE` maps `DreameMowerState.RETURNING` to `LawnMowerActivity.MOWING`, but HA now supports `LawnMowerActivity.RETURNING`.
**When to use:** Fixing SENS-02.
**Example:**
```python
# lawn_mower.py line 119 -- BEFORE:
DreameMowerState.RETURNING: LawnMowerActivity.MOWING,

# AFTER:
DreameMowerState.RETURNING: LawnMowerActivity.RETURNING,
```

### Anti-Patterns to Avoid
- **Removing property enums from types.py:** Even if a property is vacuum-only, removing it from `DreameMowerProperty` will break the SIID/PIID mapping tables and any code that references it by name. Leave enums intact; only remove entity descriptions.
- **Removing action enums from types.py:** Same reason. `DreameMowerAction.RESET_FILTER` etc. must stay in the enum even if we remove the corresponding button entities.
- **Modifying device.py status methods:** The `DreameMowerDeviceStatus` class (1,300 lines) has tightly coupled conditional chains. Do not modify status computation methods to "clean up" vacuum references -- they are harmless and deeply interconnected.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Connectivity tracking | Custom MQTT ping mechanism | `device.device_connected` property (already checks `protocol.connected`) | Protocol layer already tracks MQTT connection state; just expose it |
| Battery icon | Custom battery icon logic | `icon_for_battery_level()` from HA helpers | lawn_mower.py already imports and uses this (line 14, 629) |
| State mapping | Custom state machine | `LawnMowerActivity` enum from HA | HA provides the canonical state enum; just map Dreame states to it |
| Consumable reset | Custom action dispatch | `device.call_action(DreameMowerAction.RESET_BLADES)` via button.py pattern | button.py already has the infrastructure; action dispatches through protocol layer |

## Common Pitfalls

### Pitfall 1: Dock Command Breaking Schedules (Issue #35)
**What goes wrong:** Calling `device.dock()` dispatches `DreameMowerAction.DOCK` (action 3, SIID 5 AIID 3) directly. This tells the mower to return home, but the Dreame cloud may not see the current session as "completed" -- it sees it as "interrupted." When the next scheduled mow triggers, the cloud may try to resume the interrupted session rather than starting a fresh one, effectively breaking the schedule.
**Why it happens:** The `stop()` method (action 5) explicitly sets `DreameMowerTaskStatus.COMPLETED` + `DreameMowerStatus.STANDBY` before calling `DreameMowerAction.STOP`. The `dock()` method does NOT set COMPLETED status -- it only sets BACK_HOME + RETURNING. The cloud-side schedule handler may depend on the session being explicitly completed.
**How to avoid:** The fix likely requires sending STOP first (to mark session as completed), then DOCK (to physically return). Compare with `stop()` method at line 2449 which calls `_update_status(COMPLETED, STANDBY)`. The dock method should probably call `stop()` first if `status.started` is true, then dispatch DOCK. However, this needs live testing -- the STOP action alone may already trigger return-to-base on some models.
**Warning signs:** After docking via HA, next scheduled mow doesn't trigger, or mower tries to resume from where it stopped instead of starting fresh.
**Research confidence:** MEDIUM -- this is a hypothesis based on code analysis. Live testing needed to confirm.

### Pitfall 2: Ghost Entities from Shared Property IDs
**What goes wrong:** Vacuum-specific properties (SIDE_BRUSH_LEFT, FILTER_LEFT, TANK_FILTER_LEFT, SILVER_ION_LEFT, SQUEEGEE_LEFT, LENSBRUSH_LEFT) are defined in `DreameMowerProperty` with SIID/PIID mappings in types.py. If the Mova 600 Plus happens to report data at the same SIID/PIID combinations (which is unlikely but possible), ghost entities appear.
**Why it happens:** The `exists_fn` default checks `description.property_key.value in device.data`. If the protocol fetches properties and the device responds with data for those SIID/PIID combos, the values end up in `device.data` and the entities get created.
**How to avoid:** The safest approach is to add mower-specific `exists_fn` guards on vacuum-only sensor descriptions. For entities that definitely should never appear for mowers, either remove the description entirely from the SENSORS/BUTTONS/etc. tuples, or add `exists_fn=lambda desc, dev: False` to disable them.
**Warning signs:** Entities named "Mova 600 Plus Side Brush Left", "Mova 600 Plus Filter Left", etc. appearing in HA.

### Pitfall 3: LawnMowerActivity.RETURNING Availability
**What goes wrong:** The `LawnMowerActivity.RETURNING` state was added to HA in 2024.12. If the minimum HA version for this integration is set too low, the import will fail on older HA versions.
**Why it happens:** The integration's hacs.json currently specifies `"homeassistant": "2025.1.0"` (from Phase 1). RETURNING was added in HA 2024.12, so the floor version is already safe.
**How to avoid:** Verify `LawnMowerActivity.RETURNING` exists in the HA version we target. Since we target >=2025.1.0, this is confirmed safe.
**Warning signs:** `ImportError` or `AttributeError` when loading the integration.

### Pitfall 4: Removing Entities That Already Exist in User's HA
**What goes wrong:** If the user already paired the Mova 600 Plus in Phase 1 and vacuum-specific entities were created (e.g., sensor.momo_side_brush_left), removing the entity descriptions from code won't automatically clean up the entity registry. Orphaned entities remain visible.
**Why it happens:** HA entity registry persists entities by unique_id. Removing code that creates an entity doesn't remove the registry entry. The entity just becomes "unavailable."
**How to avoid:** After removing entity descriptions, the user needs to either: (a) remove the integration and re-add it, or (b) manually delete orphaned entities from the entity registry. Document this as a known migration step.
**Warning signs:** Entities showing as "unavailable" after the code update.

## Code Examples

### Existing Control Flow (Already Working)
```python
# Source: lawn_mower.py lines 644-666
# Start mowing
async def async_start_mowing(self) -> None:
    await self._try_command("Unable to call start: %s", self.device.start)

# Pause
async def async_pause(self) -> None:
    await self._try_command("Unable to call pause: %s", self.device.pause)

# Dock
async def async_dock(self, **kwargs) -> None:
    await self._try_command("Unable to call return_to_base: %s", self.device.dock)
```

### Existing Blade Sensor (Already Working)
```python
# Source: sensor.py lines 131-143
DreameMowerSensorEntityDescription(
    property_key=DreameMowerProperty.BLADES_LEFT,
    icon="mdi:car-turbocharger",
    native_unit_of_measurement=UNIT_PERCENT,
    entity_category=EntityCategory.DIAGNOSTIC,
),
DreameMowerSensorEntityDescription(
    property_key=DreameMowerProperty.BLADES_TIME_LEFT,
    icon="mdi:car-turbocharger",
    native_unit_of_measurement=UNIT_HOURS,
    entity_category=EntityCategory.DIAGNOSTIC,
),
```

### Existing Blade Reset Button (Already Working)
```python
# Source: button.py lines 39-47
DreameMowerButtonEntityDescription(
    action_key=DreameMowerAction.RESET_BLADES,
    icon="mdi:car-turbocharger",
    entity_category=EntityCategory.DIAGNOSTIC,
    exists_fn=lambda description, device: bool(
        DreameMowerEntityDescription().exists_fn(description, device)
        and device.status.blades_life is not None
    ),
),
```

### New Binary Sensor Pattern
```python
# Source: HA binary_sensor developer docs + existing entity.py pattern
from homeassistant.components.binary_sensor import (
    ENTITY_ID_FORMAT,
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)

@dataclass
class DreameMowerBinarySensorEntityDescription(
    DreameMowerEntityDescription, BinarySensorEntityDescription
):
    """Describes Dreame Mower Binary Sensor entity."""

BINARY_SENSORS: tuple[DreameMowerBinarySensorEntityDescription, ...] = (
    DreameMowerBinarySensorEntityDescription(
        key="online",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        value_fn=lambda value, device: device.device_connected,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)
```

## Vacuum Entity Pruning (CLEAN-01)

### Entities to Remove (Vacuum-Only)

#### sensor.py -- Remove These Descriptions
| Property Key | Name | Why Remove |
|-------------|------|-----------|
| SIDE_BRUSH_LEFT | Side Brush Left | Mowers have no side brush |
| SIDE_BRUSH_TIME_LEFT | Side Brush Time Left | Mowers have no side brush |
| FILTER_LEFT | Filter Left | Mowers have no HEPA filter |
| FILTER_TIME_LEFT | Filter Time Left | Mowers have no HEPA filter |
| TANK_FILTER_LEFT | Tank Filter Left | Mowers have no water tank |
| TANK_FILTER_TIME_LEFT | Tank Filter Time Left | Mowers have no water tank |
| SILVER_ION_LEFT | Silver Ion Left | Mowers have no silver-ion sterilizer |
| SILVER_ION_TIME_LEFT | Silver Ion Time Left | Mowers have no silver-ion sterilizer |
| LENSBRUSH_LEFT | Lens Brush Left | Mowers have no camera lens brush |
| LENSBRUSH_TIME_LEFT | Lens Brush Time Left | Mowers have no camera lens brush |
| SQUEEGEE_LEFT | Squeegee Left | Mowers have no squeegee |
| SQUEEGEE_TIME_LEFT | Squeegee Time Left | Mowers have no squeegee |
| STREAM_STATUS | Stream Status | Mova 600 Plus has no camera streaming |
| SENSOR_DIRTY_LEFT | Sensor Dirty Left | Review: mowers may have LiDAR sensor cleaning |
| SENSOR_DIRTY_TIME_LEFT | Sensor Dirty Time Left | Review: same |

#### button.py -- Remove These Descriptions
| Action Key | Name | Why Remove |
|-----------|------|-----------|
| RESET_SIDE_BRUSH | Reset Side Brush | No side brush on mowers |
| RESET_FILTER | Reset Filter | No HEPA filter on mowers |
| RESET_SENSOR | Reset Sensor | Review: mowers may need sensor reset |
| RESET_SILVER_ION | Reset Silver Ion | No silver-ion on mowers |
| RESET_LENSBRUSH | Reset Lens Brush | No lens brush on Mova 600 Plus |
| RESET_SQUEEGEE | Reset Squeegee | No squeegee on mowers |
| RESET_TANK_FILTER | Reset Tank Filter | No tank filter on mowers |

#### switch.py -- Remove These Descriptions
| Property Key | Name | Why Remove |
|-------------|------|-----------|
| AI_OBSTACLE_IMAGE_UPLOAD | AI Obstacle Image Upload | No camera on Mova 600 Plus |
| AI_OBSTACLE_PICTURE | AI Obstacle Picture | No camera |
| AI_PET_DETECTION | AI Pet Detection | Camera-based feature |
| AI_HUMAN_DETECTION | AI Human Detection | Camera-based feature |
| FUZZY_OBSTACLE_DETECTION | Fuzzy Obstacle Detection | Camera-based feature |
| AI_PET_AVOIDANCE | AI Pet Avoidance | Camera-based feature |
| PET_PICTURE | Pet Picture | Camera-based feature |
| PET_FOCUSED_DETECTION | Pet Focused Detection | Camera-based feature |
| STAIN_AVOIDANCE | Stain Avoidance | Indoor vacuum feature |
| FLOOR_DIRECTION_CLEANING | Floor Direction Cleaning | Indoor vacuum feature |
| PET_FOCUSED_CLEANING | Pet Focused Cleaning | Camera-based feature |
| STREAMING_VOICE_PROMPT | Streaming Voice Prompt | No camera streaming |
| camera_light_brightness_auto | Camera Light Auto | No camera on Mova 600 Plus |

#### number.py -- Review
The only number entity is VOLUME (slider 0-100%). This is legitimate for mowers that have speakers. Keep it, but verify the Mova 600 Plus reports this property.

The segment number entities are dynamically created from map data -- these are fine for mowers.

#### select.py -- Review
| Property Key | Name | Keep/Remove |
|-------------|------|-------------|
| CLEANING_MODE | Cleaning Mode | Keep -- mowers have mowing modes |
| VOICE_ASSISTANT_LANGUAGE | Voice Assistant Language | Review -- does Mova 600 Plus have voice assistant? |
| CLEANING_ROUTE | Cleaning Route | Keep -- mowers have route options |
| CLEANGENIUS | CleanGenius | Review -- vacuum-specific AI cleaning? |
| map_rotation | Map Rotation | Keep -- valid for mowers |
| selected_map | Selected Map | Keep -- valid for dual-map mowers |

Segment selects (CLEANING_MODE, cleaning_times, CLEANING_ROUTE, order, floor_material, floor_material_direction, visibility, name): Keep CLEANING_MODE, cleaning_times, CLEANING_ROUTE, order, visibility, name. Remove floor_material and floor_material_direction (indoor vacuum concepts).

#### coordinator.py -- Remove Vacuum Consumable Checks
The `_check_consumables()` method checks all consumables including SIDE_BRUSH, FILTER, TANK_FILTER, SENSOR_DIRTY, SQUEEGEE, LENSBRUSH. Remove checks for consumables that don't apply to mowers. Keep BLADES check.

#### const.py -- Remove Vacuum Constants
Remove vacuum-only consumable constants: `CONSUMABLE_SIDE_BRUSH`, `CONSUMABLE_FILTER`, `CONSUMABLE_TANK_FILTER`, `CONSUMABLE_SENSOR`, `CONSUMABLE_SILVER_ION`, `CONSUMABLE_LENSBRUSH`, `CONSUMABLE_SQUEEGEE` and their notification IDs. Keep `CONSUMABLE_BLADES`.

Also remove vacuum-only services from const.py and lawn_mower.py:
- `SERVICE_INSTALL_VOICE_PACK` -- mowers don't install voice packs
- Related `INPUT_LANGUAGE_ID`, `INPUT_URL`, `INPUT_MD5`, `INPUT_SIZE` if only used by voice pack

And the fan speed constants: `FAN_SPEED_SILENT`, `FAN_SPEED_STANDARD`, `FAN_SPEED_STRONG`, `FAN_SPEED_TURBO`.

#### lawn_mower.py -- Remove Vacuum-Only Services and Constants
Remove service registrations and handler methods for:
- `SERVICE_INSTALL_VOICE_PACK` / `async_install_voice_pack`
- Vacuum consumable entries in `CONSUMABLE_RESET_ACTION` (keep BLADES only)
- Fan speed references in `_set_attrs` (already no-op but confusing code)

### Pruning Strategy
**Approach:** Remove entity descriptions from the tuples (SENSORS, BUTTONS, SWITCHES, etc.) rather than modifying the underlying device.py properties. This is the safest approach because:
1. `device.py` status methods reference these properties internally (e.g., `blades_life`, `side_brush_life`). Removing the property accessor methods risks breaking internal status computation chains.
2. The enum values in `types.py` are referenced by SIID/PIID mapping tables. Removing enum values would require also removing mapping entries, which risks index misalignment.
3. Entity descriptions in sensor.py/button.py/switch.py are self-contained tuples with no cross-references.

**Mark every change with `# FORK: CLEAN-01 - removed vacuum entity` comments.**

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| LawnMowerActivity has 4 states (MOWING/DOCKED/PAUSED/ERROR) | 5 states: + RETURNING | HA 2024.12 | RETURNING should be mapped instead of treating it as MOWING |
| LawnMowerEntity.activity property | Same but with RETURNING support | HA 2024.12 | Update STATE_CODE_TO_STATE mapping |

**Deprecated/outdated:**
- Mapping `DreameMowerState.RETURNING` to `LawnMowerActivity.MOWING` -- incorrect; should map to `LawnMowerActivity.RETURNING`

## Open Questions

1. **Does dock-first-then-STOP work, or must it be STOP-then-DOCK?**
   - What we know: `dock()` only calls `DreameMowerAction.DOCK`. `stop()` calls `DreameMowerAction.STOP` with COMPLETED status. Issue #35 reports schedule breakage.
   - What's unclear: Whether the Mova 600 Plus specifically needs STOP before DOCK, or if DOCK alone properly terminates the session on this model.
   - Recommendation: Test dock behavior on live device. If schedules break, add STOP call before DOCK in the `dock()` method.

2. **Which vacuum properties does the Mova 600 Plus actually report?**
   - What we know: The device is paired as model g2552b. The protocol fetches all properties in the mapping table.
   - What's unclear: Which SIID/PIID combos actually return data vs returning -1/null. Some vacuum properties might overlap with mower properties at the protocol level.
   - Recommendation: Enable debug logging and capture a full property dump from the live device to identify which sensors will auto-create and which are truly phantom.

3. **Does SENSOR_DIRTY apply to mower LiDAR sensors?**
   - What we know: SENSOR_DIRTY_LEFT/SENSOR_DIRTY_TIME_LEFT were vacuum sensor cleaning reminders. Mova 600 Plus has LiDAR sensor that could need cleaning.
   - What's unclear: Whether the Mova 600 Plus reports these properties for its LiDAR sensor.
   - Recommendation: Check live device data. If it reports SENSOR_DIRTY properties, keep those sensors. If not, they won't be created due to `exists_fn`.

4. **Does CLEANING_PROGRESS work for mowers?**
   - What we know: Property ID 67 (CLEANING_PROGRESS) is defined. sensor.py has a description for it.
   - What's unclear: Whether the Mova 600 Plus populates this property during mowing sessions.
   - Recommendation: Check live device data during a mowing session. If not populated, SENS-05 may need an alternative approach (e.g., computing progress from cleaned_area / total_area).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.0+ with pytest-homeassistant-custom-component 0.13.300+ |
| Config file | none -- see Wave 0 |
| Quick run command | `pytest tests/ -x -q` |
| Full suite command | `pytest tests/ -v --cov=custom_components/dreame_mower` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CTRL-01 | start_mowing dispatches START_MOWING action | unit | `pytest tests/test_lawn_mower.py::test_start_mowing -x` | Wave 0 |
| CTRL-02 | pause dispatches PAUSE action | unit | `pytest tests/test_lawn_mower.py::test_pause -x` | Wave 0 |
| CTRL-03 | dock dispatches properly without breaking schedules | unit+manual | `pytest tests/test_lawn_mower.py::test_dock -x` | Wave 0 |
| SENS-01 | Battery sensor exists and reads from BATTERY_LEVEL property | unit | `pytest tests/test_sensor.py::test_battery_sensor -x` | Wave 0 |
| SENS-02 | State sensor maps all DreameMowerState values correctly | unit | `pytest tests/test_sensor.py::test_state_mapping -x` | Wave 0 |
| SENS-03 | Error sensor shows description when error present | unit | `pytest tests/test_sensor.py::test_error_sensor -x` | Wave 0 |
| SENS-04 | Connectivity binary sensor reflects device_connected | unit | `pytest tests/test_binary_sensor.py::test_connectivity -x` | Wave 0 |
| SENS-05 | Cleaning progress sensor reads CLEANING_PROGRESS | unit | `pytest tests/test_sensor.py::test_cleaning_progress -x` | Wave 0 |
| SENS-06 | Cleaned area sensor reads CLEANED_AREA | unit | `pytest tests/test_sensor.py::test_cleaned_area -x` | Wave 0 |
| SENS-07 | Blade sensors read BLADES_LEFT and BLADES_TIME_LEFT | unit | `pytest tests/test_sensor.py::test_blade_sensors -x` | Wave 0 |
| SENS-08 | Blade reset button dispatches RESET_BLADES action | unit | `pytest tests/test_button.py::test_blade_reset -x` | Wave 0 |
| CLEAN-01 | Vacuum-only sensors NOT created for mower device | unit | `pytest tests/test_sensor.py::test_no_vacuum_sensors -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/ -x -q`
- **Per wave merge:** `pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/` directory -- does not exist yet
- [ ] `tests/conftest.py` -- shared fixtures (mock DreameMowerDevice, mock coordinator)
- [ ] `tests/test_lawn_mower.py` -- lawn_mower entity tests
- [ ] `tests/test_sensor.py` -- sensor entity tests
- [ ] `tests/test_binary_sensor.py` -- binary sensor tests
- [ ] `tests/test_button.py` -- button entity tests
- [ ] Framework install: `pip install pytest pytest-homeassistant-custom-component pytest-asyncio`
- [ ] `pytest.ini` or `pyproject.toml` test configuration

Note: Given the complexity of mocking the Dreame protocol layer, unit tests should mock at the `DreameMowerDevice` / `DreameMowerDeviceStatus` level rather than attempting to mock MQTT protocol interactions.

## Sources

### Primary (HIGH confidence)
- Direct codebase analysis: `/Volumes/config/custom_components/dreame_mower/` -- all platform files (lawn_mower.py, sensor.py, button.py, switch.py, select.py, number.py, entity.py, coordinator.py, __init__.py, const.py)
- Direct codebase analysis: `/Volumes/config/custom_components/dreame_mower/dreame/` -- device.py (5,387 lines), types.py (property/action enums and mappings)
- [HA Lawn Mower Entity Developer Docs](https://developers.home-assistant.io/docs/core/entity/lawn-mower/) -- LawnMowerEntity API, LawnMowerActivity states including RETURNING (HIGH confidence)
- [HA Architecture Discussion #1123](https://github.com/home-assistant/architecture/discussions/1123) -- LawnMowerActivity.RETURNING added in HA 2024.12 (HIGH confidence)

### Secondary (MEDIUM confidence)
- [bhuebschen/dreame-mower issues](https://github.com/bhuebschen/dreame-mower) -- Issue #35 dock behavior analysis from code review (MEDIUM -- code analysis, not confirmed with live test)
- [Dreame/Mova community thread](https://community.home-assistant.io/t/dreame-a1-a1-pro-a2-mova-600-1000-integration/749593) -- User reports on entity behavior

### Tertiary (LOW confidence)
- Dock-breaks-schedules fix hypothesis (STOP then DOCK) -- based on code analysis of `stop()` vs `dock()` methods. Needs live device validation.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all platform APIs verified from HA developer docs
- Architecture: HIGH -- direct codebase analysis of all relevant files
- Pitfalls: MEDIUM -- dock/schedule issue is hypothesis; entity pruning impact is well-understood
- Vacuum pruning list: HIGH -- direct enumeration from source files

**Research date:** 2026-03-14
**Valid until:** 2026-04-14 (stable HA platform APIs; unlikely to change in 30 days)
