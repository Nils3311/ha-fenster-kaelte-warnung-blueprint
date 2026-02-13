# Anyone Home Sensor Fix

## Problem
Task 2 created `input_boolean.anyone_home` but the security system plan expects `binary_sensor.anyone_home`. Future tasks (6, 7, 8) reference `binary_sensor.anyone_home` and will fail without this fix.

## Current State
- ✅ `input_boolean.anyone_home` exists and is maintained by automation
- ✅ `automation.update_anyone_home_status` keeps it in sync with iPhone presence
- ❌ `binary_sensor.anyone_home` does not exist yet

## Solution
Create a template binary sensor that wraps the input_boolean. This provides:
1. **Backward compatibility**: `input_boolean.anyone_home` continues to work
2. **Forward compatibility**: Future tasks can use `binary_sensor.anyone_home`
3. **Clean architecture**: Binary sensor is the public interface, input_boolean is internal state

## Implementation Steps

### Step 1: Add Template Sensor to Configuration

Add this to your Home Assistant `configuration.yaml` file:

```yaml
# Template Binary Sensor for Anyone Home Status
template:
  - binary_sensor:
      - name: "Anyone Home"
        unique_id: "anyone_home_presence"
        device_class: presence
        state: "{{ is_state('input_boolean.anyone_home', 'on') }}"
        icon: "mdi:home-account"
```

### Step 2: Restart Home Assistant

After adding the configuration, restart Home Assistant:
- Go to **Settings** → **System** → **Restart**
- Or use: **Developer Tools** → **YAML** → **Check Configuration** then **Restart**

### Step 3: Verify Both Entities Exist

After restart, verify both entities are working:

1. Check input_boolean (internal state keeper):
   - Navigate to **Developer Tools** → **States**
   - Search for `input_boolean.anyone_home`
   - Should show current presence state

2. Check binary_sensor (public interface):
   - Search for `binary_sensor.anyone_home`
   - Should show same state as input_boolean
   - Should update when input_boolean changes

### Step 4: Test the Integration

Test that the binary sensor updates correctly:

1. **Simulate leaving**:
   - Turn off `input_boolean.anyone_home` manually
   - Verify `binary_sensor.anyone_home` also turns off

2. **Simulate arriving**:
   - Turn on `input_boolean.anyone_home`
   - Verify `binary_sensor.anyone_home` also turns on

3. **Test automation**:
   - The existing automation will continue to maintain `input_boolean.anyone_home`
   - The template sensor will automatically reflect those changes

## Architecture

```
binary_sensor.iphone_nils_focus (iOS companion app)
           ↓
automation.update_anyone_home_status (state synchronizer)
           ↓
input_boolean.anyone_home (internal state keeper)
           ↓
binary_sensor.anyone_home (public interface via template)
           ↓
Future automations (Tasks 6, 7, 8)
```

## Benefits

1. **Separation of Concerns**:
   - Input boolean holds the state
   - Binary sensor provides the interface
   - Automation maintains the synchronization

2. **Easy Expansion**:
   - To add a second person, only modify the automation logic
   - All dependent automations continue to work unchanged

3. **Type Correctness**:
   - Binary sensors are the standard for presence detection
   - Matches Home Assistant best practices

## Alternative Approach (If Configuration Access Not Available)

If you cannot modify `configuration.yaml`, you can update all future task references:
- Change `binary_sensor.anyone_home` → `input_boolean.anyone_home`
- This works but is less semantically correct

## Verification Checklist

- [ ] Template sensor added to configuration.yaml
- [ ] Home Assistant restarted successfully
- [ ] `input_boolean.anyone_home` exists and shows current state
- [ ] `binary_sensor.anyone_home` exists and shows same state
- [ ] Test: Toggle input_boolean → binary_sensor updates
- [ ] Test: iPhone presence change → both entities update
- [ ] Ready to proceed with Tasks 6, 7, 8

## Related Files
- Configuration: `/config/configuration.yaml` (add template sensor here)
- Automation: `automation.update_anyone_home_status` (already configured)
- Plan: `docs/plans/2026-02-13-security-system-implementation.md`

## Next Steps

After implementing this fix:
1. Proceed with Task 3: Create Notification Group
2. Continue through remaining tasks normally
3. All references to `binary_sensor.anyone_home` will work correctly
