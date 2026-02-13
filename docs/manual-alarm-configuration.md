# Manual Alarm Control Panel Configuration

## Overview
The Manual Alarm Control Panel integration must be configured via YAML in Home Assistant's `configuration.yaml` file. It cannot be created through the UI or API.

## Required Configuration

Add the following to your Home Assistant `configuration.yaml` file:

```yaml
alarm_control_panel:
  - platform: manual
    name: Home Security
    code_arm_required: false
    code_disarm_required: false
    arming_time: 5
    delay_time: 60
    trigger_time: 600
    disarmed:
      trigger_time: 0
    armed_home:
      arming_time: 0
      delay_time: 60
    armed_away:
      arming_time: 5
      delay_time: 60
    armed_custom_bypass:
      arming_time: 0
      delay_time: 60
```

## Configuration Parameters

- **name**: "Home Security" - The display name for the alarm control panel
- **code_arm_required**: false - No PIN code required to arm the system
- **code_disarm_required**: false - No PIN code required to disarm the system
- **arming_time**: 5 seconds - Time delay when arming (gives you time to leave)
- **delay_time**: 60 seconds - Entry delay for doors (time to disarm after trigger)
- **trigger_time**: 600 seconds (10 minutes) - How long the alarm sounds
- **disarmed**: No trigger time when disarmed
- **armed_home**: No arming delay, 60s entry delay (for night mode)
- **armed_away**: 5s arming delay, 60s entry delay (for leaving home)
- **armed_custom_bypass**: No arming delay, 60s entry delay (for enhanced security)

## Installation Steps

1. **Edit Configuration File**
   - Access your Home Assistant configuration directory
   - Open `configuration.yaml` in a text editor
   - Add the above YAML configuration

2. **Check Configuration**
   - In Home Assistant UI, go to Developer Tools > YAML
   - Click "Check Configuration" to validate syntax
   - Fix any errors if reported

3. **Restart Home Assistant**
   - Go to Settings > System > Restart
   - Wait for Home Assistant to fully restart (1-2 minutes)

4. **Verify Installation**
   - Check that entity `alarm_control_panel.home_security` exists
   - Go to Developer Tools > States
   - Search for "alarm_control_panel"
   - You should see `alarm_control_panel.home_security` with state "disarmed"

## Entity Information

After installation, the following entity will be available:
- **Entity ID**: `alarm_control_panel.home_security`
- **Initial State**: disarmed
- **Available States**:
  - disarmed
  - armed_away
  - armed_home
  - armed_custom_bypass
  - pending (transitioning state during arming_time)
  - arming (alternative pending state)
  - triggered (alarm is sounding)

## Services

Once configured, the following services will be available:

- `alarm_control_panel.alarm_arm_away` - Arm to Away mode
- `alarm_control_panel.alarm_arm_home` - Arm to Home mode
- `alarm_control_panel.alarm_arm_custom_bypass` - Arm to Enhanced Security mode
- `alarm_control_panel.alarm_disarm` - Disarm the system
- `alarm_control_panel.alarm_trigger` - Manually trigger the alarm

## Next Steps

After configuring and verifying the manual alarm control panel:

1. Test all alarm states (see testing section below)
2. Proceed to Task 5: Create Security Control Scripts
3. Continue with remaining security system tasks

## Testing Commands

Use Home Assistant's Developer Tools > Services to test:

```yaml
# Test arming to away
service: alarm_control_panel.alarm_arm_away
target:
  entity_id: alarm_control_panel.home_security

# Wait 5 seconds, then check state
# Expected: state should be "armed_away"

# Test disarming
service: alarm_control_panel.alarm_disarm
target:
  entity_id: alarm_control_panel.home_security

# Expected: state should be "disarmed"
```

## Troubleshooting

**Issue**: Entity not appearing after restart
- **Solution**: Check YAML syntax errors in Developer Tools > YAML > Check Configuration

**Issue**: "Unknown error" when arming/disarming
- **Solution**: Verify entity_id is exactly `alarm_control_panel.home_security`

**Issue**: Want to add PIN code protection
- **Solution**: Set `code_arm_required: true` and `code_disarm_required: true`, then add `code: "1234"` parameter to the configuration

## References

- [Home Assistant Manual Alarm Documentation](https://www.home-assistant.io/integrations/manual/)
- [Alarm Control Panel Services](https://www.home-assistant.io/integrations/alarm_control_panel/)
