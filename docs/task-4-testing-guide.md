# Task 4: Manual Alarm Control Panel - Testing Guide

## Prerequisites

Before running these tests, ensure you have:
1. Added the manual alarm configuration to `configuration.yaml` (see `manual-alarm-configuration.md`)
2. Restarted Home Assistant
3. Verified that `alarm_control_panel.home_security` entity exists

## Test 1: Verify Entity Exists

**Goal**: Confirm the alarm control panel entity was created successfully.

**Method**: Use Home Assistant Developer Tools > States

1. Navigate to Developer Tools > States
2. Search for "alarm_control_panel"
3. Look for entity: `alarm_control_panel.home_security`

**Expected Result**:
- Entity exists with state "disarmed"
- Attributes show:
  - `code_arm_required: false`
  - `code_disarm_required: false`

**Status**: ☐ Pass ☐ Fail

---

## Test 2: Arm to Away Mode

**Goal**: Test arming to Away mode with 5-second arming delay.

**Method**: Use Developer Tools > Services

1. Go to Developer Tools > Services
2. Select service: `alarm_control_panel.alarm_arm_away`
3. Enter target:
   ```yaml
   entity_id: alarm_control_panel.home_security
   ```
4. Click "Call Service"
5. Immediately check entity state (should be "arming" or "pending")
6. Wait 5 seconds
7. Check entity state again (should be "armed_away")

**Expected Results**:
- Immediately after service call: State = "arming" or "pending"
- After 5 seconds: State = "armed_away"
- No errors in Home Assistant logs

**Actual State After 5s**: _________________

**Status**: ☐ Pass ☐ Fail

---

## Test 3: Disarm from Away Mode

**Goal**: Test disarming the system.

**Method**: Use Developer Tools > Services

1. Ensure system is in "armed_away" state (from Test 2)
2. Go to Developer Tools > Services
3. Select service: `alarm_control_panel.alarm_disarm`
4. Enter target:
   ```yaml
   entity_id: alarm_control_panel.home_security
   ```
5. Click "Call Service"
6. Check entity state immediately

**Expected Result**:
- State changes to "disarmed" immediately
- No errors

**Actual State**: _________________

**Status**: ☐ Pass ☐ Fail

---

## Test 4: Arm to Home Mode (Night Mode)

**Goal**: Test arming to Home mode with no arming delay.

**Method**: Use Developer Tools > Services

1. Ensure system is disarmed
2. Go to Developer Tools > Services
3. Select service: `alarm_control_panel.alarm_arm_home`
4. Enter target:
   ```yaml
   entity_id: alarm_control_panel.home_security
   ```
5. Click "Call Service"
6. Immediately check entity state

**Expected Result**:
- State changes to "armed_home" immediately (no arming delay)
- No pending/arming state

**Actual State**: _________________

**Status**: ☐ Pass ☐ Fail

---

## Test 5: Arm to Custom Bypass Mode (Enhanced Security)

**Goal**: Test arming to Enhanced Security mode.

**Method**: Use Developer Tools > Services

1. Disarm system first
2. Go to Developer Tools > Services
3. Select service: `alarm_control_panel.alarm_arm_custom_bypass`
4. Enter target:
   ```yaml
   entity_id: alarm_control_panel.home_security
   ```
5. Click "Call Service"
6. Check entity state

**Expected Result**:
- State changes to "armed_custom_bypass" immediately
- No arming delay (arming_time: 0)

**Actual State**: _________________

**Status**: ☐ Pass ☐ Fail

---

## Test 6: Manual Trigger Test

**Goal**: Test manual alarm triggering (warning: may be loud if scripts are set up).

**Method**: Use Developer Tools > Services

1. Arm system to any mode
2. Go to Developer Tools > Services
3. Select service: `alarm_control_panel.alarm_trigger`
4. Enter target:
   ```yaml
   entity_id: alarm_control_panel.home_security
   ```
5. Click "Call Service"
6. Check entity state
7. Disarm immediately to stop alarm

**Expected Result**:
- State changes to "triggered"
- Alarm would sound for 600 seconds (10 minutes) if not disarmed
- Manual disarm stops the trigger

**Actual State**: _________________

**Status**: ☐ Pass ☐ Fail

**Note**: This test should only be run if you're prepared for alarm scripts to execute (sirens, lights, notifications). If scripts are not yet configured, this simply changes the entity state.

---

## Test 7: State Transition Verification

**Goal**: Verify all state transitions work correctly.

**Test Sequence**:

1. disarmed → armed_away → disarmed ☐
2. disarmed → armed_home → disarmed ☐
3. disarmed → armed_custom_bypass → disarmed ☐
4. armed_away → armed_home (mode switching) ☐
5. armed_home → armed_away (mode switching) ☐

**Expected Result**: All transitions complete without errors.

**Status**: ☐ Pass ☐ Fail

---

## Test 8: Configuration Values Verification

**Goal**: Verify timing values are correct.

**Method**: Check entity attributes in Developer Tools > States

1. Navigate to `alarm_control_panel.home_security`
2. View attributes

**Expected Attributes**:
- Delay time: 60 seconds
- Arming time (away): 5 seconds
- Arming time (home): 0 seconds
- Trigger time: 600 seconds
- Code required: false

**Actual Attributes**:
- Delay time: _________ seconds
- Arming time (away): _________ seconds
- Arming time (home): _________ seconds
- Trigger time: _________ seconds
- Code required: _________

**Status**: ☐ Pass ☐ Fail

---

## Test Summary

| Test | Status | Notes |
|------|--------|-------|
| 1. Entity Exists | ☐ | |
| 2. Arm Away | ☐ | |
| 3. Disarm | ☐ | |
| 4. Arm Home | ☐ | |
| 5. Arm Custom Bypass | ☐ | |
| 6. Manual Trigger | ☐ | |
| 7. State Transitions | ☐ | |
| 8. Config Values | ☐ | |

**Overall Result**: ☐ All Tests Pass ☐ Some Tests Fail

---

## Troubleshooting

### Issue: Entity doesn't exist after restart
**Solution**:
- Check YAML syntax in Developer Tools > YAML
- Review Home Assistant logs for errors
- Ensure indentation is correct in configuration.yaml

### Issue: Arming/disarming fails
**Solution**:
- Verify entity_id is exactly `alarm_control_panel.home_security`
- Check Home Assistant logs for specific error messages
- Ensure no conflicting automations are interfering

### Issue: Timing delays don't match expected values
**Solution**:
- Review configuration.yaml settings
- Restart Home Assistant after any config changes
- Check entity attributes to see actual configured values

---

## Next Steps After All Tests Pass

1. ✅ Mark Task 4 as complete
2. Proceed to Task 5: Create Security Control Scripts
3. Integrate alarm control panel with scripts and automations
4. Set up sensor monitoring (Task 8)
5. Create security dashboard (Task 11)

---

## API Testing Commands

For automated testing or script-based verification, use these Home Assistant MCP commands:

```python
# Check entity state
ha_get_state(entity_id="alarm_control_panel.home_security")

# Arm to away
ha_call_service(
    domain="alarm_control_panel",
    service="alarm_arm_away",
    entity_id="alarm_control_panel.home_security"
)

# Disarm
ha_call_service(
    domain="alarm_control_panel",
    service="alarm_disarm",
    entity_id="alarm_control_panel.home_security"
)

# Arm to home
ha_call_service(
    domain="alarm_control_panel",
    service="alarm_arm_home",
    entity_id="alarm_control_panel.home_security"
)

# Arm to custom bypass
ha_call_service(
    domain="alarm_control_panel",
    service="alarm_arm_custom_bypass",
    entity_id="alarm_control_panel.home_security"
)
```

---

## Test Completion Date

Date: ___________________

Tester: ___________________

Signature: ___________________
