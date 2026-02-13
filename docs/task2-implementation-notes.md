# Task 2 Implementation: Anyone Home Template Sensor

## Implementation Date
2026-02-13

## What Was Implemented

Created a presence detection system using an `input_boolean` helper synchronized with iPhone presence sensor via automation.

### Components Created

1. **Helper: `input_boolean.anyone_home`**
   - Name: "Anyone Home"
   - Icon: `mdi:home-account`
   - Purpose: Tracks whether anyone is home based on iPhone presence
   - Current State: `off` (synchronized with iPhone Nils Focus)

2. **Automation: `automation.update_anyone_home_status`**
   - Alias: "Update Anyone Home Status"
   - Trigger: State change of `binary_sensor.iphone_nils_focus`
   - Action: Updates `input_boolean.anyone_home` to match iPhone state
   - Mode: `restart` (cancels previous run if triggered again)

## Verified Entities

- **iPhone Presence Sensor**: `binary_sensor.iphone_nils_focus` ✓ (exists, currently "off")
- **Anyone Home Helper**: `input_boolean.anyone_home` ✓ (created successfully)
- **Update Automation**: `automation.update_anyone_home_status` ✓ (created and triggered successfully)

## Testing Results

### Test 1: Entity Verification
- ✓ iPhone presence sensor exists and is accessible
- ✓ Current state: "off"

### Test 2: Template Evaluation
- ✓ Template `{{ is_state('binary_sensor.iphone_nils_focus', 'on') }}` evaluates correctly
- ✓ Returns `False` when iPhone is not home

### Test 3: Helper Creation
- ✓ `input_boolean.anyone_home` created successfully
- ✓ Initial state: "off"
- ✓ Icon set correctly: `mdi:home-account`

### Test 4: Automation Creation
- ✓ Automation created with correct configuration
- ✓ Trigger configured for iPhone state changes
- ✓ Choose/default logic implemented correctly

### Test 5: Automation Trigger Test
- ✓ Manual trigger executed successfully
- ✓ State synchronization confirmed (both sensors "off")

## Expansion Instructions for Second Person

To add a second person (girlfriend) to the presence detection system:

### Step 1: Verify Second iPhone Sensor
```python
ha_get_state(entity_id="binary_sensor.iphone_girlfriend_focus")
```

### Step 2: Update Automation Logic
Modify the automation to use OR logic for multiple people:

```yaml
automation:
  alias: "Update Anyone Home Status"
  trigger:
    - platform: state
      entity_id: binary_sensor.iphone_nils_focus
    - platform: state
      entity_id: binary_sensor.iphone_girlfriend_focus
  action:
    - choose:
        - conditions:
            - condition: or
              conditions:
                - condition: state
                  entity_id: binary_sensor.iphone_nils_focus
                  state: "on"
                - condition: state
                  entity_id: binary_sensor.iphone_girlfriend_focus
                  state: "on"
          sequence:
            - service: input_boolean.turn_on
              target:
                entity_id: input_boolean.anyone_home
      default:
        - service: input_boolean.turn_off
          target:
            entity_id: input_boolean.anyone_home
```

### Alternative: Template Binary Sensor (for reference)
If template sensors were used instead, the template would be:
```jinja2
{{ is_state('binary_sensor.iphone_nils_focus', 'on') or
   is_state('binary_sensor.iphone_girlfriend_focus', 'on') }}
```

## Technical Notes

- Used `input_boolean` + automation approach instead of pure template sensor because it's more reliable and easier to debug
- Automation uses `restart` mode to ensure state consistency if multiple rapid changes occur
- The `choose` action with `default` provides clean if/else logic
- Description field added to automation for future reference about expansion

## Files Modified

None (all changes applied directly to Home Assistant via MCP API)

## Next Steps

This sensor (`input_boolean.anyone_home`) will be used by:
- Task 6: Presence-Based Auto Arming Automations (auto arm when everyone leaves)
- Task 7: Time-Based Night Mode Automations (night mode only when someone home)
- Other security automations requiring presence detection
