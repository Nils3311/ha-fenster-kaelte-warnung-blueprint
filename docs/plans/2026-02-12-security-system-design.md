# Home Assistant Security System Design

**Date:** 2026-02-12
**Version:** 1.0
**Status:** Ready for Implementation

## Overview

Smart security system for Home Assistant with automatic arming based on presence detection, multiple security modes, and integration with existing Reolink doorbell camera. The system protects the home using existing door/window contact sensors and motion sensors, with plans for future camera expansion.

## Design Goals

- **Automatic operation**: Arm/disarm based on presence (iPhone detection)
- **Flexible modes**: Different protection levels for away, night, and enhanced security
- **Smart notifications**: German-language notifications with progressive warnings
- **False alarm prevention**: Grace periods, phone detection bypass, bedroom exclusions
- **Future-ready**: Integration with existing Reolink doorbell, expandable for more cameras

## System Modes

### Mode Overview

| Mode | Trigger | Active Sensors | Entry Delays |
|------|---------|----------------|--------------|
| **Away** | Everyone leaves (5 min delay) | All doors, windows, motion | Entry doors: 60s, Windows: 15s |
| **Home** (Nachtschutz) | 22:00 + someone home | Ground floor perimeter only | Entry doors: 60s, Windows: 15s |
| **Erweiterte Sicherheit** | Manual activation | All sensors including motion | Entry doors: 60s, Windows: 15s |
| **Disarmed** | 07:00 + someone home, or arrival | None | - |

### Mode Details

#### Away Mode (armed_away)
- **Activation**: Automatically when `binary_sensor.anyone_home` = off for 5 minutes
- **Sensors**: All perimeter sensors (doors/windows) + all motion sensors
- **Use case**: Everyone has left the house
- **Deactivation**: Automatically when someone arrives (iPhone detected)

#### Home Mode / Nachtschutz (armed_home)
- **Activation**: Automatically at 22:00 if someone home
- **Sensors**: Ground floor doors and windows only, motion sensors disabled
- **Upper floor windows**: Disabled (allows ventilation in bedrooms)
- **Use case**: Night protection while sleeping
- **Deactivation**: Automatically at 07:00 if someone still home

#### Erweiterte Sicherheit (armed_custom_bypass)
- **Activation**: Manual via dashboard button
- **Sensors**: All sensors including motion (except upper floor windows)
- **Use case**: One person home alone, wants full protection
- **Deactivation**: Manual via dashboard

#### Disarmed
- **Default state**: When someone home during daytime (07:00 - 22:00)
- **No protection active**

## Presence Detection & Automatic Arming

### Presence Tracking

**Entities:**
```yaml
binary_sensor.iphone_nils_focus          # Nils' iPhone presence
binary_sensor.iphone_[girlfriend]        # Girlfriend's iPhone (future)
binary_sensor.anyone_home                # Template: OR of both iPhones
```

### Automatic Arming Logic

**Away Mode Activation:**
```yaml
Trigger: binary_sensor.anyone_home changes to 'off'
Wait: 5 minutes (grace period for quick returns)
Condition: binary_sensor.anyone_home still 'off'
Action:
  - Arm to 'armed_away'
  - Notification: "🏠 Sicherheitssystem ist SCHARF (Abwesend). Alle Sensoren aktiv."
```

**Automatic Disarm on Arrival:**
```yaml
Trigger: binary_sensor.anyone_home changes to 'on'
Condition: Alarm is 'armed_away'
Action:
  - Disarm immediately (trusted presence = no entry delay needed)
  - Notification: "✅ Sicherheitssystem DEAKTIVIERT. Willkommen zu Hause!"
```

**Night Mode Activation:**
```yaml
Trigger: Time = 22:00
Condition: binary_sensor.anyone_home = 'on'
Action:
  - Arm to 'armed_home'
  - Notification: "🌙 Nachtschutz AKTIVIERT (22:00). Außensensoren überwachen."
```

**Morning Auto-Disarm:**
```yaml
Trigger: Time = 07:00
Conditions:
  - Alarm state = 'armed_home'
  - AND binary_sensor.anyone_home = 'on' (prevents disarm when on vacation)
Action:
  - Disarm
  - Notification: "☀️ Nachtschutz DEAKTIVIERT (07:00). Guten Morgen!"
```

**Manual Erweiterte Sicherheit:**
```yaml
Trigger: Dashboard button pressed
Action: Arm to 'armed_custom_bypass'
Notification: "🔒 Erweiterte Sicherheit AKTIVIERT. Alle Sensoren aktiv."
```

## Sensor Configuration

### Current Sensors

**Door/Window Contact Sensors (Perimeter):**
1. Haupteingang Tür (main entrance)
2. HWR Tür Seite (side entry - utility room)
3. Wohnzimmer Fenster klein
4. Wohnzimmer Tür groß (large patio door)
5. Esszimmer Tür groß (large patio door)
6. Esszimmer Fenster klein
7. Küche Fenster
8. Badezimmer unten Fenster
9. Arbeitszimmer unten Fenster vorne
10. Arbeitszimmer unten Fenster Seite
11. Badezimmer oben Fenster vorne
12. Badezimmer oben Fenster Seite
13. Schlafzimmer Tür groß (large patio door)
14. Schlafzimmer Fenster klein
15. MYGGBETT door/window sensor Tür (x2)

**Motion Sensors:**
1. HWR Bewegung Belegung (utility room)
2. Badezimmer unten Bewegung (downstairs bathroom)
3. (More to be added later)

### Sensor Behavior by Zone

#### Entry Doors (Main Entries)
**Sensors:** Haupteingang Tür, HWR Tür Seite

**Behavior:**
- 60 second entry delay when armed
- **iPhone detection bypass**: If iPhone detected on WiFi/Bluetooth → skip delay, auto-disarm
- If iPhone NOT detected → full 60s entry delay with countdown notifications

**Notifications during entry delay:**
```yaml
60s: "⚠️ Eingang erkannt! Bitte innerhalb 60 Sekunden deaktivieren!"
30s: "⚠️ WARNUNG: Noch 30 Sekunden zum Deaktivieren!"
10s: "🚨 DRINGEND: Sofort deaktivieren!"
Priority: Critical (bypasses Do Not Disturb)
Action button: "Jetzt deaktivieren"
```

#### Ground Floor Windows & Doors
**Sensors:** All Wohnzimmer, Esszimmer, Küche, Badezimmer unten, Arbeitszimmer unten, HWR windows/doors

**Behavior:**
- 15 second grace period when opened
- Notification: "⚠️ [Sensor Name] geöffnet! 10 Sek zum Schließen!"
- If not closed within 15s → Full alarm triggers
- Active in: Away, Home, Erweiterte Sicherheit modes

#### Upper Floor Windows
**Sensors:** Schlafzimmer, Arbeitszimmer oben, Badezimmer oben windows

**Behavior:**
- **Away mode**: 15s grace period (same as ground floor)
  - Rationale: If opened when everyone gone = intrusion (requires ladder)
- **Home mode**: Disabled
  - Rationale: Allow opening for ventilation at night without alarm
- **Erweiterte Sicherheit**: 15s grace period

#### Motion Sensors

**Behavior:**
- **Away mode**: Active, instant trigger
- **Home mode**: Disabled (prevent false alarms while moving at night)
- **Erweiterte Sicherheit**: Active, instant trigger

## Alarm Actions

### When Alarm Triggers

**Trigger Conditions:**
- Entry delay countdown reaches 0 without disarm
- Instant trigger sensors (windows opened, motion detected when armed)
- Second sensor trigger within 5 minutes

**Actions:**

**1. Sonos Audio Alarm**
```yaml
Entity: media_player.wohnzimmer (Sonos)
Action: Play alarm sound file
Volume: 80-90%
Mode: Loop until disarmed
```

**2. Light Activation**
```yaml
Action: Turn on all lights EXCEPT Schlafzimmer
Areas included:
  - Wohnzimmer, Esszimmer, Küche
  - Flur, HWR
  - Arbeitszimmer (oben/unten)
  - Badezimmer (oben/unten)
Excluded: Kinderzimmer, Schlafzimmer (don't wake son)
Brightness: 100%
State management: Save previous states before turning on
```

**3. Camera Siren**
```yaml
Entity: siren.kamera_vordertur_sirene
Action: Turn on
Duration: Until alarm disarmed
```

**4. Critical Notification**
```yaml
Service: notify.all_users
Message: "🚨 ALARM AUSGELÖST! [Sensor Name] - [Time]"
Priority: Critical
Include: Which sensor triggered, timestamp
```

### When Alarm Stops (Disarmed)

**Actions:**
```yaml
1. Stop Sonos playback
2. Restore previous Sonos state
3. Turn off camera siren
4. Restore previous light states (on/off, brightness, colors)
5. Notification: "✅ Alarm deaktiviert um [Time]"
```

## Camera Integration

### Current Setup: Reolink Doorbell

**Camera Entity:** `camera.kamera_vordertur_standardauflosung`

**Available Sensors:**
- `binary_sensor.kamera_vordertur_person` (Person detection)
- `binary_sensor.kamera_vordertur_fahrzeug` (Vehicle detection)
- `binary_sensor.kamera_vordertur_paket` (Package detection)
- `binary_sensor.kamera_vordertur_besucher` (Visitor button press)
- `binary_sensor.kamera_vordertur_haustier` (Pet detection)
- `binary_sensor.kamera_vordertur_bewegung` (Motion detection)

**Siren:** `siren.kamera_vordertur_sirene`

### Division of Responsibilities

#### What Reolink Handles (Automatically)
- ✅ Video recording when triggers detected
- ✅ Storage to SD card/NVR
- ✅ Doorbell chime sounds (visitor button)
- ✅ Reolink app notifications
- ✅ AI detection processing

#### What Home Assistant Adds

**1. Person Detected at Door (Standing Outside)**
```yaml
Trigger: binary_sensor.kamera_vordertur_person = on
Condition: Alarm armed (any mode)
Action:
  - Info notification: "ℹ️ Person an Haustür (System scharf)"
  - Include: Snapshot from camera
  - Priority: Normal

Note: NO entry delay - person is just outside
Note: Reolink already recording
```

**2. Package Detected**
```yaml
Trigger: binary_sensor.kamera_vordertur_paket = on
Action: Notification: "📦 Paket an Haustür erkannt"
Include: Snapshot
No alarm triggered (informational only)
```

**3. Visitor Doorbell Press**
```yaml
Trigger: binary_sensor.kamera_vordertur_besucher = on
If armed: Notification with snapshot "🔔 Türklingel! [Snapshot]"
If disarmed: Reolink handles chime automatically
```

**4. Door Opens + Enhanced Detection**
```yaml
Trigger: binary_sensor.haupteingang_tur opens
Condition: Alarm armed
Base action: Start 60s entry delay

Enhancement (optional):
  If person detected at same time: Normal behavior
  If NO person detected: Suspicious, send immediate warning
    "⚠️ Tür geöffnet aber keine Person erkannt!"
```

**5. Camera Siren Integration**
```yaml
Trigger: Full alarm triggered (after entry delay expires)
Action: Turn on siren.kamera_vordertur_sirene
Along with: Sonos alarm + lights
```

### Future Camera Expansion

When additional Reolink cameras are added:

**Snapshot on Any Trigger:**
```yaml
When: Any sensor triggers while armed
Action:
  - Take snapshot from nearest camera
  - Include in notification
  - Save to: /config/www/security/snapshots/
  - Filename: YYYY-MM-DD_HH-MM-SS_[sensor]_[camera].jpg
```

**Recording on Alarm:**
```yaml
When: Full alarm triggers
Action: Start recording on ALL cameras
Continue: Until disarmed + 2 minutes (capture aftermath)
Notification: Include live view links
```

**Reolink Siren Support:**
```yaml
If cameras have built-in sirens:
  - Trigger all camera sirens when alarm triggers
  - Along with Sonos and main doorbell siren
```

## Dashboard Integration

### Main Security Panel Card

**Status Display:**
```yaml
Large status badge with color coding:
  - 🔴 "SCHARF (Abwesend)" - Armed Away
  - 🟡 "SCHARF (Zuhause)" - Armed Home / Nachtschutz
  - 🟠 "Erweiterte Sicherheit" - Enhanced Security
  - 🟢 "DEAKTIVIERT" - Disarmed

Show: Current mode, time since last state change
```

**Quick Action Buttons:**
```yaml
[Deaktivieren] [Abwesend] [Erweiterte Sicherheit]
- Auto-hide based on current state
- Optional: Require PIN code for arming/disarming
```

**Sensor Status Overview (Collapsible):**
```yaml
"Eingangstüren (2)"
  ✅ Haupteingang - Geschlossen
  ✅ HWR Seite - Geschlossen

"Erdgeschoss Fenster/Türen (8)"
  ✅ Wohnzimmer Fenster - Geschlossen
  ⚠️ Küche Fenster - OFFEN (if any open)

"Obergeschoss Fenster (6)"
  ✅ Schlafzimmer - Geschlossen

"Bewegungsmelder (2)"
  🟢 HWR - Keine Bewegung

Color coding:
  - Green ✅ = Closed/No motion
  - Orange ⚠️ = Open but system disarmed
  - Red 🔴 = Open with system armed
```

**Recent Activity Log:**
```yaml
"Letzte Ereignisse:"
  - 14:32 - System deaktiviert (iPhone Nils erkannt)
  - 08:15 - Nachtschutz deaktiviert (07:00)
  - 22:00 - Nachtschutz aktiviert
  - Show last 10 events with timestamps
```

**Camera Section:**
```yaml
"Kamera-Ansichten"
  - Thumbnail: camera.kamera_vordertur_standardauflosung
  - Tap to view live stream
  - Recording indicator when alarm active
  - Last detection: "Person - 2 min ago"

(Expandable for future cameras)
```

## Notification System

### Notification Group

**Create notification group:**
```yaml
notify:
  - name: all_users
    platform: group
    services:
      - service: mobile_app_iphone_nils
      - service: mobile_app_[girlfriend_iphone]
```

### Notification Types

**1. Status Change Notifications (Normal Priority)**
- Armed to Away
- Disarmed on arrival
- Night mode activated
- Morning disarm
- Manual mode changes

**2. Entry Delay Notifications (Critical Priority)**
- Progressive countdown warnings
- Bypass Do Not Disturb
- Actionable "Disarm Now" button

**3. Alarm Notifications (Critical Priority)**
- Alarm triggered
- Which sensor
- Timestamp
- Camera snapshot (if available)

**4. Camera Detections (Normal/Info Priority)**
- Person detected while armed
- Package detected
- Doorbell pressed

**5. System Errors (High Priority)**
- Sensor offline
- Camera unavailable
- Automation failed

## Implementation Components

### Home Assistant Configuration

**Required Integrations:**
- ✅ Manual Alarm Control Panel
- ✅ Reolink Integration (already installed)
- ✅ iPhone Device Tracker / Companion App
- ✅ Notify services
- ✅ Sonos Integration

**Template Sensors to Create:**
```yaml
binary_sensor.anyone_home:
  - Combines presence of Nils + girlfriend
  - State: on if any phone home, off if both away
```

**Automation Files to Create:**
1. `security_auto_arm_away.yaml` - Auto arm when everyone leaves
2. `security_auto_disarm_arrival.yaml` - Auto disarm when someone arrives
3. `security_night_mode.yaml` - Auto arm at 22:00 / disarm at 07:00
4. `security_entry_delay.yaml` - Entry delay countdown & notifications
5. `security_alarm_trigger.yaml` - Sonos, lights, siren, notifications
6. `security_alarm_disarm.yaml` - Stop alarm, restore states
7. `security_sensor_monitoring.yaml` - Monitor all sensors with delays
8. `security_camera_integration.yaml` - Person detection, snapshots

**Scripts to Create:**
1. `security_arm_away` - Manual arm to away
2. `security_arm_home` - Manual arm to home (night mode)
3. `security_arm_enhanced` - Manual arm to erweiterte sicherheit
4. `security_disarm` - Manual disarm
5. `security_alarm_trigger` - Centralized alarm action
6. `security_alarm_stop` - Centralized alarm stop

### Dashboard Configuration

**Lovelace Cards Needed:**
- Alarm Panel Card (custom or default)
- Entity cards for sensor status
- Camera card for doorbell
- History graph for events
- Button cards for manual arming

## Security Considerations

### Entry Delay Bypass
- iPhone presence detection prevents false alarms for authorized users
- Backup: Manual disarm via phone notification button
- Timeout: 60s is enough time without being too permissive

### False Alarm Prevention
1. **Grace periods**: 15s for windows allows accidental opening fix
2. **Bedroom exclusions**: Upper floor windows disabled at night
3. **Motion disabled in Home mode**: Prevents night movement false alarms
4. **5-minute departure delay**: Prevents re-arming if someone forgot something

### Privacy & Data
- Camera recordings stored locally (Reolink SD/NVR)
- HA snapshots stored locally (/config/www/)
- No cloud dependencies for alarm system
- Notifications use local HA notify service

## Future Enhancements

### Phase 2: Additional Cameras
- Add cameras for backyard, side yard, garage
- Expand snapshot/recording coverage
- Multi-camera views in dashboard

### Phase 3: Advanced Features
- Geofencing for faster presence detection
- Schedule-based mode switching (vacation mode)
- Integration with smart locks (future)
- Video doorbell two-way audio integration
- AI-based anomaly detection

### Phase 4: Monitoring
- Weekly security reports
- Sensor health monitoring
- Battery level tracking for wireless sensors
- Automation performance analytics

## Testing Plan

### Phase 1: Basic Functionality
1. Test presence detection (arrive/leave)
2. Test manual arming/disarming
3. Test entry delay with phone present/absent
4. Test notification delivery

### Phase 2: Alarm Triggers
1. Test each sensor type triggers correctly
2. Test grace periods work as expected
3. Test alarm actions (Sonos, lights, siren)
4. Test alarm stops correctly

### Phase 3: Mode Transitions
1. Test automatic mode switches (22:00, 07:00)
2. Test mode transitions when leaving/arriving
3. Test vacation scenario (away for multiple days)

### Phase 4: Camera Integration
1. Test person detection notifications
2. Test snapshot inclusion in notifications
3. Test camera siren activation
4. Test doorbell integration

## Maintenance

### Regular Tasks
- Monthly: Review sensor battery levels
- Monthly: Test alarm system end-to-end
- Quarterly: Update Reolink firmware
- Quarterly: Review and update notification preferences
- Yearly: Security audit of automations

### Monitoring
- Track false alarm rate
- Monitor notification delivery success
- Check automation execution logs
- Review sensor trigger patterns

---

## Approval & Next Steps

**Design Status:** ✅ Approved
**Ready for Implementation:** Yes

**Implementation Approach:**
1. Create notification group
2. Build template sensors (anyone_home)
3. Implement Away mode (auto arm/disarm)
4. Add entry delays and notifications
5. Implement alarm actions (Sonos, lights, siren)
6. Add Night mode automations
7. Integrate camera detection
8. Build dashboard
9. Test thoroughly
10. Deploy to production

**Estimated Implementation Time:** 2-3 hours for core functionality, additional time for dashboard polish and testing.
