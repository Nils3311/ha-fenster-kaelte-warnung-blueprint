# Security System Verification Checklist

**Date:** 2026-02-13
**Status:** ⚠️ 3 CRITICAL ISSUES FOUND - FIXES REQUIRED BEFORE LIVE USE

---

## Remote Verification Results ✅

### Core Components

- [x] Alarm control panel created (alarm_control_panel.home_security)
- [x] Presence detection working (binary_sensor.anyone_home)
- [x] Notification system working (script.notify_all_users)
- [ ] ⚠️ **Security lights group MISSING** (group.security_lights)

### Scripts (6/6)

- [x] script.security_arm_away
- [x] script.security_arm_home
- [x] script.security_arm_enhanced
- [x] script.security_disarm
- [x] script.security_alarm_trigger
- [x] script.security_alarm_stop

### Automations (12/12)

**Presence-Based:**
- [x] automation.security_auto_arm_away
- [x] automation.security_auto_disarm_on_arrival

**Time-Based:**
- [x] automation.security_night_mode_activation
- [x] automation.security_morning_auto_disarm

**Sensor Monitoring:**
- [x] automation.security_entry_door_delay
- [ ] ⚠️ **automation.security_window_grace_period (BROKEN)**
- [ ] ⚠️ **automation.security_upper_floor_windows_away_mode (BROKEN)**
- [x] automation.security_motion_sensor_alert

**Camera Integration:**
- [x] automation.security_person_at_door_alert
- [x] automation.security_package_detected
- [x] automation.security_doorbell_alert

**Notification Handler:**
- [x] automation.security_handle_notification_disarm

### Sensor Coverage

- [x] 2 entry doors verified
- [x] 8 ground floor windows/doors verified
- [x] 4 upper floor windows/doors verified
- [x] 2 motion sensors verified
- [x] 5 camera AI sensors verified

### Alarm Devices

- [x] Sonos speaker verified (media_player.wohnzimmer)
- [x] Camera siren verified (siren.kamera_vordertur_sirene)
- [ ] ⚠️ **Security lights group MISSING**

---

## Critical Issues Found 🚨

### Issue 1: Security Lights Group Missing
**Severity:** HIGH
**Impact:** Alarm trigger/stop scripts will fail on light control

**Fix:**
```yaml
# Add to configuration.yaml:
group:
  security_lights:
    name: Security Lights
    entities:
      - light.aussenlicht
      - light.hwr_deckenlampe
```

### Issue 2: Window Grace Period Broken
**Severity:** CRITICAL
**Impact:** No warning before alarm triggers, defeats purpose of grace period

**Problem:** Uses `for: {seconds: 15}` trigger instead of `wait_for_trigger`

**Fix:** Replace both window automations with corrected implementation (see testing guide Section 3)

### Issue 3: Alarm Panel Code Requirement
**Severity:** MEDIUM (workaround available)
**Impact:** UI requires code to arm/disarm

**Workaround:** Use scripts instead of UI controls

**Fix:**
```yaml
# Edit configuration.yaml:
alarm_control_panel:
  - platform: manual
    code_arm_required: false  # Change from true
    code_disarm_required: false
```

---

## Manual Testing Required ⏳

**Priority 1 (Test Immediately):**
- [ ] Test 2: Script-based arming/disarming
- [ ] Test 3: Entry door delay (60s countdown)
- [ ] Test 9: Full alarm trigger (LOUD - daytime only)

**Priority 2 (After Fixes Applied):**
- [ ] Test 4: Window grace period (after fix)
- [ ] Test 6: Away mode with upper floor (after fix)
- [ ] Test 7: Motion sensor instant trigger

**Priority 3 (Optional/Long-Duration):**
- [ ] Test 10: Presence-based auto-arming (10+ min)
- [ ] Test 11: Time-based night mode (wait until 22:00)
- [ ] Test 12: Camera AI integration
- [ ] Test 13: Actionable notification button

---

## System Readiness Status

### Current: ⚠️ NOT READY FOR LIVE USE

**Blockers:**
- ❌ Security lights group missing
- ❌ Window grace period broken (critical safety issue)

### After Fixes: ✅ READY FOR TESTING

**Working Features:**
- ✅ Core arming/disarming (via scripts)
- ✅ Entry door 60s delay with progressive warnings
- ✅ Motion sensor instant alarm
- ✅ Presence-based auto-arming
- ✅ Time-based night mode
- ✅ Camera AI notifications
- ✅ Actionable notification disarm button

**Known Limitations:**
- ⚠️ Alarm panel UI requires code (use scripts instead)
- ⚠️ Light group needed for full alarm functionality

### Estimated Time to Ready: 1 hour
- Apply 3 fixes: 30 min
- Complete priority tests: 30 min

---

## Quick Fix Commands

### Fix 1: Create Security Lights Group

**Via configuration.yaml:**
```yaml
group:
  security_lights:
    name: Security Lights
    entities:
      - light.aussenlicht
      - light.hwr_deckenlampe
```

**Or via UI:**
1. Settings → Devices & Services → Helpers
2. Create Group → Light Group
3. Name: "Security Lights"
4. Add: light.aussenlicht, light.hwr_deckenlampe

### Fix 2: Correct Window Grace Period

**Use MCP tool or configuration.yaml to replace:**
```python
ha_config_set_automation(
    identifier="automation.security_window_grace_period",
    config={
        "alias": "Security: Window Grace Period (Fixed)",
        "description": "15 second grace period for windows/doors when armed",
        "mode": "parallel",
        "max": 10,
        "trigger": [{
            "platform": "state",
            "entity_id": [
                "binary_sensor.wohnzimmer_fenster_klein",
                "binary_sensor.wohnzimmer_tur_gross",
                "binary_sensor.esszimmer_tur_gross",
                "binary_sensor.esszimmer_fenster_klein",
                "binary_sensor.kuche_fenster",
                "binary_sensor.badezimmer_unten_fenster",
                "binary_sensor.arbeitszimmer_unten_fenster_vorne",
                "binary_sensor.arbeitszimmer_unten_fenster_seite"
            ],
            "to": "on"
        }],
        "condition": [{
            "condition": "or",
            "conditions": [
                {"condition": "state", "entity_id": "alarm_control_panel.home_security", "state": "armed_away"},
                {"condition": "state", "entity_id": "alarm_control_panel.home_security", "state": "armed_home"},
                {"condition": "state", "entity_id": "alarm_control_panel.home_security", "state": "armed_custom_bypass"}
            ]
        }],
        "action": [
            {
                "service": "script.notify_all_users",
                "data": {
                    "title": "⚠️ Sensor ausgelöst",
                    "message": "{{ trigger.to_state.attributes.friendly_name }} geöffnet! 15 Sekunden zum Schließen."
                }
            },
            {
                "wait_for_trigger": [{
                    "platform": "state",
                    "entity_id": "{{ trigger.entity_id }}",
                    "to": "off"
                }],
                "timeout": {"seconds": 15}
            },
            {
                "if": [{
                    "condition": "template",
                    "value_template": "{{ wait.trigger is none }}"
                }],
                "then": [{"service": "script.security_alarm_trigger"}]
            }
        ]
    }
)
```

### Fix 3: Remove Code Requirement

**Edit configuration.yaml:**
```yaml
alarm_control_panel:
  - platform: manual
    name: Home Security
    code_arm_required: false
    code_disarm_required: false
    # ... rest of config unchanged
```

Then reload configuration.

---

## Success Criteria

System is ready for live use when:

- [ ] All 3 critical fixes applied
- [ ] Test 2 passes (script arming works)
- [ ] Test 3 passes (entry door delay + progressive warnings work)
- [ ] Test 4 passes (window grace period with warnings works)
- [ ] Test 9 passes (full alarm trigger works on all devices)
- [ ] No errors in Home Assistant logs
- [ ] User comfortable with system behavior

---

## Next Steps

1. **Apply fixes immediately** (30 min)
   - Create security lights group
   - Fix window grace period automations
   - (Optional) Remove alarm panel code requirement

2. **Run priority tests** (30 min)
   - Test script arming/disarming
   - Test entry door delay
   - Test full alarm trigger (LOUD!)

3. **Verify fixes** (15 min)
   - Test window grace period
   - Verify warning notifications
   - Verify light group works

4. **Go live** (if all tests pass)
   - Enable system for daily use
   - Monitor for 1 week
   - Schedule monthly tests

5. **Future enhancements**
   - Add girlfriend's iPhone
   - Add more security lights
   - Add video recording on alarm
   - Add battery monitoring
