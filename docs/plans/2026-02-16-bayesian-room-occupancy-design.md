# Bayesian Room Occupancy System

> Design document for room-level occupancy detection using HA Bayesian sensors.
> Created: 2026-02-16

---

## Overview

Detect which rooms are currently "in use" for dashboard filtering (Aktiv tab).
Uses Home Assistant's built-in `bayesian` binary sensor platform to fuse multiple
signal sources per room into a single occupancy probability.

**Definition of "occupied":** The room is being actively used. Sonos playing in
Wohnzimmer means it's occupied even if you stepped into the kitchen briefly.
Not strict real-time presence, not 15-minute sticky either.

---

## Architecture

```
Layer 1: Activity Sensors (template binary_sensor)
  Door/window open events → 3-minute delay_off signal
         │
Layer 2: Bayesian Sensors (binary_sensor.bayesian)
  Combines motion, media, activity → probability → on/off
         │
Layer 3: Sync Automation (blueprint, one instance per room)
  Bayesian on  → immediately set input_boolean.*_belegt ON
  Bayesian off → wait 2 min, confirm, set input_boolean.*_belegt OFF
         │
Layer 4: Dashboard
  room_card reads input_boolean.*_belegt for opacity + status text
  Aktiv tab uses conditional cards to show only occupied rooms
```

Manual override: toggling `input_boolean.*_belegt` directly still works.
The sync automation only reacts to Bayesian sensor changes.

---

## File Structure

All files on HA config volume (`/Volumes/config/`):

| File | Purpose |
|------|---------|
| `binary_sensors/room_activity.yaml` | Template sensors for door/window events |
| `binary_sensors/room_occupancy.yaml` | Bayesian sensors (one per room) |
| `blueprints/automation/occupancy_sync.yaml` | Sync blueprint |
| `configuration.yaml` | Include directive |

The blueprint is also in the GitHub repo at `occupancy_sync_blueprint.yaml`.

### configuration.yaml include

```yaml
binary_sensor: !include_dir_merge_list binary_sensors/
```

---

## Layer 1: Activity Sensors

Template binary_sensors that convert door/window open/close events into a
3-minute "someone was here" signal. The Bayesian sensor reads these instead
of raw contact sensors.

### Why not use raw contact sensors directly?

A door being "open" is a state. It could be open all day (ventilation).
The *act of opening* is the signal. The activity sensor captures the event
and provides a 3-minute window for the Bayesian sensor to use.

### Configuration: `binary_sensors/room_activity.yaml`

```yaml
- platform: template
  sensors:
    wohnbereich_aktivitaet:
      friendly_name: "Wohnbereich Aktivität"
      delay_off: "00:03:00"
      value_template: >
        {{ is_state('binary_sensor.wohnzimmer_fenster_klein', 'on')
           or is_state('binary_sensor.wohnzimmer_tur_gross', 'on')
           or is_state('binary_sensor.esszimmer_fenster_klein', 'on')
           or is_state('binary_sensor.esszimmer_tur_gross', 'on') }}

    kueche_aktivitaet:
      friendly_name: "Küche Aktivität"
      delay_off: "00:03:00"
      value_template: >
        {{ is_state('binary_sensor.kuche_fenster', 'on') }}

    flur_aktivitaet:
      friendly_name: "Flur Aktivität"
      delay_off: "00:03:00"
      value_template: >
        {{ is_state('binary_sensor.haupteingang_tur', 'on') }}

    hwr_aktivitaet:
      friendly_name: "HWR Aktivität"
      delay_off: "00:03:00"
      value_template: >
        {{ is_state('binary_sensor.hwr_tur_seite', 'on') }}

    schlafzimmer_aktivitaet:
      friendly_name: "Schlafzimmer Aktivität"
      delay_off: "00:03:00"
      value_template: >
        {{ is_state('binary_sensor.schlafzimmer_fenster_klein', 'on')
           or is_state('binary_sensor.schlafzimmer_tur_gross', 'on') }}

    arbeitszimmer_unten_aktivitaet:
      friendly_name: "Arbeitszimmer unten Aktivität"
      delay_off: "00:03:00"
      value_template: >
        {{ is_state('binary_sensor.arbeitszimmer_unten_fenster_vorne', 'on')
           or is_state('binary_sensor.arbeitszimmer_unten_fenster_seite', 'on') }}

    badezimmer_unten_aktivitaet:
      friendly_name: "Badezimmer unten Aktivität"
      delay_off: "00:03:00"
      value_template: >
        {{ is_state('binary_sensor.badezimmer_unten_fenster', 'on') }}

    badezimmer_oben_aktivitaet:
      friendly_name: "Badezimmer oben Aktivität"
      delay_off: "00:03:00"
      value_template: >
        {{ is_state('binary_sensor.badezimmer_oben_fenster_vorne', 'on')
           or is_state('binary_sensor.badezimmer_oben_fenster_seite', 'on') }}
```

**Rooms without door/window sensors:** Kinderzimmer, Arbeitszimmer oben.
No activity sensor needed — they'll get observations when sensors are added.

---

## Layer 2: Bayesian Sensors

### Probability Weight Reference

| Source Type | prob_given_true | prob_given_false | Strength | Notes |
|-------------|----------------|-----------------|----------|-------|
| Motion sensor (PIR) | 0.90 | 0.05 | Very strong | Primary occupancy signal |
| Media player (playing) | 0.70 | 0.05 | Strong | Sonos/TV playing = someone listening |
| Door/window activity | 0.35 | 0.02 | Strong (ratio) | Someone MUST have been there to open it |
| Light (manual only) | 0.60 | 0.10 | Medium | Only for non-automated lights |
| Light (motion-automated) | 0.20 | 0.10 | Weak | Low weight to avoid circular dependency |

**Base parameters (all rooms):**
- `prior: 0.25` — conservative, avoids false positives
- `probability_threshold: 0.7` — 70% confidence to flip to occupied

### How the math works

Bayesian formula combines the prior with all active observations.

Example — HWR with motion on:
`P = (0.90 * 0.25) / (0.90 * 0.25 + 0.05 * 0.75) = 0.225 / 0.2625 = 0.857`
Result: 0.857 > 0.7 threshold → occupied.

Example — Küche with only window opened:
`P = (0.35 * 0.25) / (0.35 * 0.25 + 0.02 * 0.75) = 0.0875 / 0.1025 = 0.854`
Result: 0.854 > 0.7 → occupied (for 3 minutes via activity sensor delay_off).

Example — Motion-automated light on alone:
`P = (0.20 * 0.25) / (0.20 * 0.25 + 0.10 * 0.75) = 0.05 / 0.125 = 0.40`
Result: 0.40 < 0.7 → NOT occupied. No circular dependency.

### Configuration: `binary_sensors/room_occupancy.yaml`

```yaml
# === ERDGESCHOSS ===

- platform: bayesian
  name: "Wohnbereich Raumnutzung"
  prior: 0.25
  probability_threshold: 0.7
  observations:
    - entity_id: binary_sensor.wohnbereich_aktivitaet
      prob_given_true: 0.35
      prob_given_false: 0.02
      platform: state
      to_state: "on"
    - entity_id: media_player.wohnzimmer
      prob_given_true: 0.70
      prob_given_false: 0.05
      platform: state
      to_state: "playing"

- platform: bayesian
  name: "Küche Raumnutzung"
  prior: 0.25
  probability_threshold: 0.7
  observations:
    - entity_id: binary_sensor.kueche_aktivitaet
      prob_given_true: 0.35
      prob_given_false: 0.02
      platform: state
      to_state: "on"

- platform: bayesian
  name: "Flur Raumnutzung"
  prior: 0.25
  probability_threshold: 0.7
  observations:
    - entity_id: binary_sensor.flur_aktivitaet
      prob_given_true: 0.35
      prob_given_false: 0.02
      platform: state
      to_state: "on"

- platform: bayesian
  name: "HWR Raumnutzung"
  prior: 0.25
  probability_threshold: 0.7
  observations:
    - entity_id: binary_sensor.hwr_bewegung
      prob_given_true: 0.90
      prob_given_false: 0.05
      platform: state
      to_state: "on"
    - entity_id: binary_sensor.hwr_aktivitaet
      prob_given_true: 0.35
      prob_given_false: 0.02
      platform: state
      to_state: "on"

- platform: bayesian
  name: "Arbeitszimmer unten Raumnutzung"
  prior: 0.25
  probability_threshold: 0.7
  observations:
    - entity_id: binary_sensor.arbeitszimmer_unten_aktivitaet
      prob_given_true: 0.35
      prob_given_false: 0.02
      platform: state
      to_state: "on"

- platform: bayesian
  name: "Badezimmer unten Raumnutzung"
  prior: 0.25
  probability_threshold: 0.7
  observations:
    - entity_id: binary_sensor.badezimmer_unten_bewegung
      prob_given_true: 0.90
      prob_given_false: 0.05
      platform: state
      to_state: "on"
    - entity_id: binary_sensor.badezimmer_unten_aktivitaet
      prob_given_true: 0.35
      prob_given_false: 0.02
      platform: state
      to_state: "on"

# === OBERGESCHOSS ===

- platform: bayesian
  name: "Schlafzimmer Raumnutzung"
  prior: 0.25
  probability_threshold: 0.7
  observations:
    - entity_id: binary_sensor.schlafzimmer_aktivitaet
      prob_given_true: 0.35
      prob_given_false: 0.02
      platform: state
      to_state: "on"
    - entity_id: media_player.schlafzimmer
      prob_given_true: 0.70
      prob_given_false: 0.05
      platform: state
      to_state: "playing"

- platform: bayesian
  name: "Kinderzimmer Raumnutzung"
  prior: 0.25
  probability_threshold: 0.7
  observations: []
  # No sensors yet

- platform: bayesian
  name: "Arbeitszimmer oben Raumnutzung"
  prior: 0.25
  probability_threshold: 0.7
  observations: []
  # No sensors yet

- platform: bayesian
  name: "Badezimmer oben Raumnutzung"
  prior: 0.25
  probability_threshold: 0.7
  observations:
    - entity_id: binary_sensor.badezimmer_oben_aktivitaet
      prob_given_true: 0.35
      prob_given_false: 0.02
      platform: state
      to_state: "on"
```

### Current sensor availability

| Room | Motion | Media | Door/Window | Total Observations |
|------|--------|-------|-------------|-------------------|
| Wohnbereich | - | Sonos | 4 sensors | 2 |
| Küche | - | - | 1 sensor | 1 |
| Flur | - | - | 1 sensor | 1 |
| HWR | yes | - | 1 sensor | 2 |
| AZ unten | - | - | 2 sensors | 1 |
| Bad unten | yes | - | 1 sensor | 2 |
| Schlafzimmer | - | Sonos | 2 sensors | 2 |
| Kinderzimmer | - | - | - | 0 |
| AZ oben | - | - | - | 0 |
| Bad oben | - | - | 2 sensors | 1 |

---

## Layer 3: Sync Blueprint

File: `blueprints/automation/occupancy_sync.yaml`
(also in GitHub repo as `occupancy_sync_blueprint.yaml`)

### Blueprint inputs

| Input | Type | Default | Description |
|-------|------|---------|-------------|
| `occupancy_sensor` | binary_sensor | required | The Bayesian sensor for this room |
| `occupancy_helper` | input_boolean | required | The `*_belegt` helper |
| `off_delay` | number (min) | 2 | Delay before marking empty |

### Behavior

- **Mode: restart** — if sensor flickers, the off-delay resets
- **On detection:** immediately turns on `input_boolean`
- **On clear:** waits `off_delay` minutes, re-checks sensor is still off, then turns off `input_boolean`
- **Manual override:** toggling `input_boolean` directly still works

### Create 10 automations

One per room via HA UI: Settings → Automations → Create → From Blueprint.

| Automation | Sensor | Helper |
|------------|--------|--------|
| Wohnbereich Belegung | `binary_sensor.wohnbereich_raumnutzung` | `input_boolean.wohnbereich_belegt` |
| Küche Belegung | `binary_sensor.kuche_raumnutzung` | `input_boolean.kuche_belegt` |
| Flur Belegung | `binary_sensor.flur_raumnutzung` | `input_boolean.flur_belegt` |
| HWR Belegung | `binary_sensor.hwr_raumnutzung` | `input_boolean.hwr_belegt` |
| AZ unten Belegung | `binary_sensor.arbeitszimmer_unten_raumnutzung` | `input_boolean.arbeitszimmer_unten_belegt` |
| Bad unten Belegung | `binary_sensor.badezimmer_unten_raumnutzung` | `input_boolean.badezimmer_unten_belegt` |
| Schlafzimmer Belegung | `binary_sensor.schlafzimmer_raumnutzung` | `input_boolean.schlafzimmer_belegt` |
| Kinderzimmer Belegung | `binary_sensor.kinderzimmer_raumnutzung` | `input_boolean.kinderzimmer_belegt` |
| AZ oben Belegung | `binary_sensor.arbeitszimmer_oben_raumnutzung` | `input_boolean.arbeitszimmer_oben_belegt` |
| Bad oben Belegung | `binary_sensor.badezimmer_oben_raumnutzung` | `input_boolean.badezimmer_oben_belegt` |

---

## Layer 4: Dashboard — Aktiv Tab Filtering

The Aktiv tab (views[1], path `raeume`) wraps each room card in a `conditional` card:

```yaml
type: conditional
conditions:
  - entity: input_boolean.wohnbereich_belegt
    state: "on"
card:
  type: custom:decluttering-card
  template: room_card
  variables:
    # ... existing room card config, unchanged
```

- **EG, OG, Draußen tabs:** no filtering, always show all rooms on that floor
- **Empty Aktiv tab:** when no rooms are occupied, the tab shows just the tab bar — communicates "nothing active" clearly

---

## AI Instructions: How to Add New Sensors

When the user adds new sensors to a room, follow these steps:

### Adding a motion sensor

1. **Identify the entity_id** of the new motion sensor (e.g., `binary_sensor.kuche_bewegung`)
2. **Add an observation** to the room's Bayesian sensor in `binary_sensors/room_occupancy.yaml`:
   ```yaml
   - entity_id: binary_sensor.kuche_bewegung
     prob_given_true: 0.90
     prob_given_false: 0.05
     platform: state
     to_state: "on"
   ```
3. **Restart HA** or reload binary_sensor integration

### Adding a light sensor

1. **Determine if the light is motion-automated or manual:**
   - **Manual only:** use weight `prob_given_true: 0.60, prob_given_false: 0.10`
   - **Motion-automated:** use weak weight `prob_given_true: 0.20, prob_given_false: 0.10` to avoid circular dependency
2. **Add observation** to the room's Bayesian sensor:
   ```yaml
   - entity_id: light.kuche_deckenlampe
     prob_given_true: 0.60  # or 0.20 if motion-automated
     prob_given_false: 0.10
     platform: state
     to_state: "on"
   ```

### Adding a door/window sensor to an existing activity sensor

1. **Add the entity** to the room's activity sensor `value_template` in `binary_sensors/room_activity.yaml`:
   ```yaml
   value_template: >
     {{ is_state('binary_sensor.existing_sensor', 'on')
        or is_state('binary_sensor.new_sensor', 'on') }}
   ```

### Adding a door/window sensor to a room WITHOUT an activity sensor

1. **Create a new activity sensor** in `binary_sensors/room_activity.yaml`:
   ```yaml
   kinderzimmer_aktivitaet:
     friendly_name: "Kinderzimmer Aktivität"
     delay_off: "00:03:00"
     value_template: >
       {{ is_state('binary_sensor.kinderzimmer_fenster', 'on') }}
   ```
2. **Add an observation** to the room's Bayesian sensor:
   ```yaml
   - entity_id: binary_sensor.kinderzimmer_aktivitaet
     prob_given_true: 0.35
     prob_given_false: 0.02
     platform: state
     to_state: "on"
   ```

### Adding a media player

1. **Add observation** with media weight:
   ```yaml
   - entity_id: media_player.kinderzimmer
     prob_given_true: 0.70
     prob_given_false: 0.05
     platform: state
     to_state: "playing"
   ```

### Adding a completely new sensor type

1. Determine two probabilities:
   - `prob_given_true`: "If someone IS in the room, how likely is this sensor active?" (0.0 to 1.0)
   - `prob_given_false`: "If nobody is in the room, how likely is this sensor active?" (0.0 to 1.0)
2. The ratio `prob_given_true / prob_given_false` determines signal strength:
   - Ratio > 10 = very strong signal (motion: 0.90/0.05 = 18x)
   - Ratio > 5 = strong signal (door activity: 0.35/0.02 = 17.5x)
   - Ratio > 3 = medium signal (manual light: 0.60/0.10 = 6x)
   - Ratio < 3 = weak signal (automated light: 0.20/0.10 = 2x)
3. Test with `Developer Tools → States` — check `binary_sensor.*_raumnutzung` attributes for current probability

### Probability tuning

If a room triggers too easily:
- Lower `prob_given_true` on weak signals
- Raise `prob_given_false` on noisy signals
- Lower the `prior` (e.g., 0.20 for rarely-used rooms)

If a room doesn't trigger when it should:
- Check that all sensors are reporting correctly in Developer Tools
- Raise `prob_given_true` for the primary sensor
- Raise the `prior` if the room is frequently used

The Bayesian sensor exposes its current probability as an attribute — check it in Developer Tools → States to debug.

---

## Implementation Checklist

1. [ ] Create `binary_sensors/room_activity.yaml` on HA config
2. [ ] Create `binary_sensors/room_occupancy.yaml` on HA config
3. [ ] Add `binary_sensor: !include_dir_merge_list binary_sensors/` to `configuration.yaml`
4. [ ] Copy blueprint to `blueprints/automation/occupancy_sync.yaml`
5. [ ] Restart HA
6. [ ] Create 10 automation instances from blueprint (one per room)
7. [ ] Test: open a door in HWR → check `binary_sensor.hwr_raumnutzung` turns on
8. [ ] Test: wait 3min + 2min → check `input_boolean.hwr_belegt` turns off
9. [ ] Wrap Aktiv tab room cards in conditional cards via dashboard python_transform
10. [ ] Verify Aktiv tab shows only occupied rooms
