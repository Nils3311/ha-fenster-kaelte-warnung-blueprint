# Bayesian Room Occupancy — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Deploy Bayesian room occupancy detection for all 10 rooms, sync to existing `input_boolean.*_belegt` helpers, and filter the Aktiv dashboard tab to show only occupied rooms.

**Architecture:** Template binary_sensors convert door/window events into 3-min activity signals. Bayesian binary_sensors fuse activity, motion, and media signals into occupancy probability. A blueprint automation syncs each Bayesian sensor to its `input_boolean.*_belegt` helper. The Aktiv dashboard tab wraps room cards in conditional cards.

**Tech Stack:** Home Assistant YAML config (Samba share at `/Volumes/config/`), HA MCP tools for dashboard edits, HA blueprints for automation.

**Design doc:** `docs/plans/2026-02-16-bayesian-room-occupancy-design.md` — full architecture, probability math, and AI instructions for adding future sensors.

---

## Critical Context

- **HA config volume:** `/Volumes/config/` (Samba share, writable)
- **Dashboard:** `new-home` (storage mode, edit via MCP `ha_config_set_dashboard`)
- **Existing helpers:** `input_boolean.*_belegt` (10 rooms, all currently `off`)
- **MCP python_transform rules:** No `replace()`, no builtins (`len`, `range`, `str`), no f-strings. Only allowed methods: `append, clear, count, endswith, extend, get, index, insert, items, join, keys, lower, pop, remove, reverse, setdefault, sort, split, startswith, strip, update, upper, values`
- **Blueprint already in repo:** `occupancy_sync_blueprint.yaml` at repo root
- **`configuration.yaml`** currently has NO `binary_sensor:` key — needs to be added
- **No `binary_sensors/` directory** exists yet — needs to be created
- **Blueprints go in:** `/Volumes/config/blueprints/automation/Nils3311/`

---

## Task 1: Create activity sensors YAML

**Files:**
- Create: `/Volumes/config/binary_sensors/room_activity.yaml`

**Step 1: Create the binary_sensors directory**

```bash
mkdir -p /Volumes/config/binary_sensors
```

**Step 2: Write the activity sensors file**

Create `/Volumes/config/binary_sensors/room_activity.yaml` with this exact content:

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

**Step 3: Verify file was written**

```bash
ls -la /Volumes/config/binary_sensors/room_activity.yaml
```

Expected: file exists, non-zero size.

---

## Task 2: Create Bayesian occupancy sensors YAML

**Files:**
- Create: `/Volumes/config/binary_sensors/room_occupancy.yaml`

**Step 1: Write the Bayesian sensors file**

Create `/Volumes/config/binary_sensors/room_occupancy.yaml` with this exact content:

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
  # No sensors yet — add motion/door sensors here later

- platform: bayesian
  name: "Arbeitszimmer oben Raumnutzung"
  prior: 0.25
  probability_threshold: 0.7
  observations: []
  # No sensors yet — add motion/door sensors here later

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

**Step 2: Verify file was written**

```bash
ls -la /Volumes/config/binary_sensors/room_occupancy.yaml
```

---

## Task 3: Update configuration.yaml

**Files:**
- Modify: `/Volumes/config/configuration.yaml`

**Step 1: Read the current configuration.yaml**

Read `/Volumes/config/configuration.yaml` to find the exact content.

**Step 2: Add binary_sensor include**

Add this line after the existing includes (`automation:`, `script:`, `scene:`):

```yaml
binary_sensor: !include_dir_merge_list binary_sensors/
```

**Important:** Do NOT modify the existing `template:` section (which has the "Anyone Home" binary sensor). The `binary_sensor:` key is separate from `template:`.

**Step 3: Verify the change**

Read `/Volumes/config/configuration.yaml` back and confirm the new line exists.

**Step 4: Validate HA config before restart**

Use MCP tool `ha_check_config` to validate the configuration is correct. If it fails, fix the YAML before proceeding.

---

## Task 4: Deploy the sync blueprint

**Files:**
- Create: `/Volumes/config/blueprints/automation/Nils3311/occupancy_sync_blueprint.yaml`

**Step 1: Copy the blueprint**

The blueprint source is at `/Users/nilshoffmann/Documents/Programmieren/hass/occupancy_sync_blueprint.yaml`.

Copy it to: `/Volumes/config/blueprints/automation/Nils3311/occupancy_sync_blueprint.yaml`

```bash
cp /Users/nilshoffmann/Documents/Programmieren/hass/occupancy_sync_blueprint.yaml /Volumes/config/blueprints/automation/Nils3311/occupancy_sync_blueprint.yaml
```

**Step 2: Verify the file exists**

```bash
ls -la /Volumes/config/blueprints/automation/Nils3311/occupancy_sync_blueprint.yaml
```

---

## Task 5: Restart Home Assistant

**Step 1: Ask the user for confirmation before restarting**

IMPORTANT: Always ask the user before restarting HA. Say: "Ready to restart HA to load the new sensors and blueprint. OK to proceed?"

**Step 2: Restart HA**

Use MCP tool `ha_restart` to restart Home Assistant.

**Step 3: Wait for HA to come back online**

Wait ~60 seconds, then use MCP tool `ha_get_system_health` to verify HA is running.

**Step 4: Verify new entities exist**

Use MCP tool `ha_search_entities` to search for:
- `aktivitaet` — should find 8 activity sensors
- `raumnutzung` — should find 10 Bayesian sensors

If any entities are missing, check HA logs via MCP for YAML errors.

---

## Task 6: Create 10 sync automations from blueprint

**Context:** HA doesn't have an MCP tool to create automations from blueprints. Instead, create them by writing directly to `/Volumes/config/automations.yaml`.

**Step 1: Read the current automations.yaml**

Read `/Volumes/config/automations.yaml` to see the existing automations format.

**Step 2: Append 10 new automations**

Add 10 automation entries to `automations.yaml`. Each follows this pattern:

```yaml
- id: 'occupancy_sync_wohnbereich'
  alias: 'Raumbelegung Sync: Wohnbereich'
  use_blueprint:
    path: Nils3311/occupancy_sync_blueprint.yaml
    input:
      occupancy_sensor: binary_sensor.wohnbereich_raumnutzung
      occupancy_helper: input_boolean.wohnbereich_belegt
      off_delay: 2
```

The full list of 10 automations:

| id | alias | sensor | helper |
|----|-------|--------|--------|
| `occupancy_sync_wohnbereich` | Raumbelegung Sync: Wohnbereich | `binary_sensor.wohnbereich_raumnutzung` | `input_boolean.wohnbereich_belegt` |
| `occupancy_sync_kueche` | Raumbelegung Sync: Küche | `binary_sensor.kuche_raumnutzung` | `input_boolean.kuche_belegt` |
| `occupancy_sync_flur` | Raumbelegung Sync: Flur | `binary_sensor.flur_raumnutzung` | `input_boolean.flur_belegt` |
| `occupancy_sync_hwr` | Raumbelegung Sync: HWR | `binary_sensor.hwr_raumnutzung` | `input_boolean.hwr_belegt` |
| `occupancy_sync_az_unten` | Raumbelegung Sync: Arbeitszimmer unten | `binary_sensor.arbeitszimmer_unten_raumnutzung` | `input_boolean.arbeitszimmer_unten_belegt` |
| `occupancy_sync_bad_unten` | Raumbelegung Sync: Badezimmer unten | `binary_sensor.badezimmer_unten_raumnutzung` | `input_boolean.badezimmer_unten_belegt` |
| `occupancy_sync_schlafzimmer` | Raumbelegung Sync: Schlafzimmer | `binary_sensor.schlafzimmer_raumnutzung` | `input_boolean.schlafzimmer_belegt` |
| `occupancy_sync_kinderzimmer` | Raumbelegung Sync: Kinderzimmer | `binary_sensor.kinderzimmer_raumnutzung` | `input_boolean.kinderzimmer_belegt` |
| `occupancy_sync_az_oben` | Raumbelegung Sync: Arbeitszimmer oben | `binary_sensor.arbeitszimmer_oben_raumnutzung` | `input_boolean.arbeitszimmer_oben_belegt` |
| `occupancy_sync_bad_oben` | Raumbelegung Sync: Badezimmer oben | `binary_sensor.badezimmer_oben_raumnutzung` | `input_boolean.badezimmer_oben_belegt` |

All use `off_delay: 2`.

**Step 3: Reload automations**

Use MCP tool `ha_reload_core` with target `automation` to reload without full restart.

**Step 4: Verify automations exist**

Use MCP tool `ha_deep_search` to search for `occupancy_sync` and confirm 10 automations are loaded.

---

## Task 7: Test the occupancy system

**Step 1: Test HWR (has motion sensor)**

Use MCP tool `ha_get_state` to check:
- `binary_sensor.hwr_bewegung` — current state
- `binary_sensor.hwr_aktivitaet` — should exist
- `binary_sensor.hwr_raumnutzung` — should exist, check `probability` attribute
- `input_boolean.hwr_belegt` — current state

Report all states to the user.

**Step 2: Test a door/window room (Wohnbereich)**

Use MCP tool `ha_get_state` to check:
- `binary_sensor.wohnbereich_aktivitaet` — should exist
- `binary_sensor.wohnbereich_raumnutzung` — check probability attribute
- `input_boolean.wohnbereich_belegt` — current state

**Step 3: Test an empty room (Kinderzimmer)**

Use MCP tool `ha_get_state` to check:
- `binary_sensor.kinderzimmer_raumnutzung` — should exist with probability = prior (0.25)

**Step 4: Report results to user**

Tell the user: "All sensors are running. To test live: open a door in HWR and check if `input_boolean.hwr_belegt` turns on within a few seconds."

---

## Task 8: Wrap Aktiv tab room cards in conditional cards

**Context:** The Aktiv tab is views[1] (path `raeume`) in the `new-home` dashboard. Section 1 contains 10 room cards (decluttering-card) + 1 navbar-card. We need to wrap each room card (NOT the navbar) in a `conditional` card.

**Step 1: Read the dashboard to get current config**

Use MCP `ha_config_get_dashboard` with url_path `new-home` and `force_reload: true`. Note the `config_hash`. Identify the exact structure of `views[1].sections[1].cards` — confirm there are 10 room cards followed by 1 navbar-card.

**Step 2: Apply python_transform to wrap room cards**

The transform must wrap each of the 10 room cards (indices 0-9) in a conditional card, leaving the navbar-card (last card) untouched.

The occupancy entity mapping (in order of cards in section 1):

| Card Index | Room | Occupancy Entity |
|-----------|------|-----------------|
| 0 | Wohnbereich | `input_boolean.wohnbereich_belegt` |
| 1 | Küche | `input_boolean.kuche_belegt` |
| 2 | Schlafzimmer | `input_boolean.schlafzimmer_belegt` |
| 3 | Flur | `input_boolean.flur_belegt` |
| 4 | HWR | `input_boolean.hwr_belegt` |
| 5 | AZ unten | `input_boolean.arbeitszimmer_unten_belegt` |
| 6 | Bad unten | `input_boolean.badezimmer_unten_belegt` |
| 7 | AZ oben | `input_boolean.arbeitszimmer_oben_belegt` |
| 8 | Kinderzimmer | `input_boolean.kinderzimmer_belegt` |
| 9 | Bad oben | `input_boolean.badezimmer_oben_belegt` |

**IMPORTANT:** Verify the card order by reading the dashboard first! The order above is from the previous session and may be correct, but always confirm before transforming.

python_transform approach:

```python
occupancy_map = [
    "input_boolean.wohnbereich_belegt",
    "input_boolean.kuche_belegt",
    "input_boolean.schlafzimmer_belegt",
    "input_boolean.flur_belegt",
    "input_boolean.hwr_belegt",
    "input_boolean.arbeitszimmer_unten_belegt",
    "input_boolean.badezimmer_unten_belegt",
    "input_boolean.arbeitszimmer_oben_belegt",
    "input_boolean.kinderzimmer_belegt",
    "input_boolean.badezimmer_oben_belegt"
]

section = config['views'][1]['sections'][1]
new_cards = []
idx = 0
for card in section['cards']:
    if card.get('type') == 'custom:navbar-card':
        new_cards.append(card)
    else:
        wrapped = {
            "type": "conditional",
            "conditions": [{"entity": occupancy_map[idx], "state": "on"}],
            "card": card
        }
        new_cards.append(wrapped)
        idx += 1
section['cards'] = new_cards
```

**CAUTION with python_transform:** The above uses `get()` which is allowed. No builtins needed. Verify the card order matches before applying.

**Step 3: Verify the dashboard change**

Read the dashboard back with `force_reload: true`. Confirm:
- Each room card in views[1].sections[1] is now wrapped in a `conditional` card
- The navbar-card is NOT wrapped
- Each conditional references the correct `input_boolean.*_belegt` entity

**Step 4: Report to user**

Tell the user: "The Aktiv tab now filters by occupancy. Since all rooms are currently empty, the tab will show just the tab bar. Open a door or trigger motion to see rooms appear."

---

## Task 9: Final verification

**Step 1: Verify all entities**

Use MCP `ha_search_entities` to confirm:
- 8 `*_aktivitaet` binary sensors exist
- 10 `*_raumnutzung` binary sensors exist
- 10 `*_belegt` input_booleans exist
- 10 `occupancy_sync_*` automations exist

**Step 2: Verify dashboard structure**

Use MCP `ha_config_get_dashboard` to confirm:
- views[1] (raeume/Aktiv) has conditional-wrapped room cards
- views[2] (raeume-eg) has unwrapped room cards (no filtering)
- views[3] (raeume-og) has unwrapped room cards (no filtering)
- views[4] (raeume-draussen) has unwrapped cards (no filtering)

**Step 3: Report summary**

Report to user:
- Total new entities created
- All automations active
- Dashboard filtering in place
- Suggest testing: "Open the HWR door — within seconds the HWR room should appear on the Aktiv tab with full opacity"

---

## Commit

After all tasks pass, commit changes in the hass repo:

```bash
git add docs/plans/2026-02-16-occupancy-implementation-plan.md
git commit -m "Add Bayesian room occupancy implementation plan"
```
