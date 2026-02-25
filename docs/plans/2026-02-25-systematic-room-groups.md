# Systematic Per-Room Domain Groups — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` to implement this plan task-by-task.

**Goal:** Replace ad-hoc mixed-domain HA groups with consistent per-room, per-domain groups in `configuration.yaml` — persistent, automation-ready, and used as single source of truth across all dashboards.

**Architecture:** Option A — YAML groups for persistence (survive HA restart). Groups created for all rooms × domains where entities exist. Dashboard room_cards updated to use domain-specific groups (no empty groups in UI). Existing mixed-domain `_alle` groups kept but deprioritized.

**Tech Stack:** Home Assistant YAML groups, HA MCP tools (`ha_config_set_group`, `ha_reload_core`, `ha_config_set_dashboard` python_transform), Samba share at `/Volumes/config/configuration.yaml`.

---

## Critical Context (read before starting)

### Infrastructure
- **YAML config**: `/Volumes/config/configuration.yaml` — Samba share, may not always be mounted
- **Check mount first**: `ls /Volumes/config/` — if fails, mount via Finder → Go → Connect to Server
- **MCP tools**: All HA writes go via MCP (`home-assistant` server). Never edit `.storage/` files directly.
- **After YAML edits**: Always reload with `ha_reload_core("groups")` via MCP
- **python_transform constraints** (critical, violations cause silent failure):
  - NO `replace()` — use `"new".join(s.split("old"))`
  - NO builtins: `len()`, `range()`, `str()`, `int()`, `list()`, `dict()`
  - NO negative indices: `[-1]` → count manually and use `[N]`
  - NO f-strings, `def`, `class`, `try/except`
  - YES: `for`, `while`, `if/else`, `append`, `insert`, `pop`, `get`, `items`, `keys`, `values`

### Reference Files
- **Entity reference**: `~/.claude/skills/home-assistant/reference/home-setup.md` — all rooms and entity IDs
- **Memory**: `~/.claude/projects/.../memory/MEMORY.md` — architecture notes

### Existing Groups (in YAML already — do not duplicate)
```
group.alle_lichter         — all lights house-wide
group.security_lights      — lights used in alarm
group.wohnzimmer_alle      — MIXED (lights+covers+media) — KEEP, but not used for Licht button
group.schlafzimmer_alle    — MIXED (lights+covers+media) — KEEP
group.tueren_sicherheit    — all-house doors (keep as-is)
group.fenster_sicherheit   — all-house windows (keep as-is)
group.bewohner             — persons
```

### Runtime-only group (needs YAML persistence — high priority)
```
group.wohnzimmer_lichter   — currently runtime only via MCP, will be lost on HA restart
```

### Dashboard Room-Card Structure
Views 1–4 contain `conditional` cards wrapping `custom:decluttering-card` (template: `room_card`).
Each card has a `variables` list; last entry is `room_devices` — a list of `custom:button-card` entries.
The Licht device uses `template: kohbo_room_card_device`, `name: "Licht"`, `tap_action: toggle`.

---

## Groups to Create

### EG (Erdgeschoss)

**Wohnzimmer** (note: vitrine/Esszimmer included since Wohnbereich = combined room):
```yaml
wohnzimmer_lichter:
  name: "Wohnzimmer Lichter"
  icon: mdi:lightbulb-group
  entities:
    - light.regal_wohnzimmer
    - light.wohnzimmer_stehlampe_oben
    - light.wohnzimmer_stehlampe_mitte
    - light.wohnzimmer_stehlampe_unten
    - light.vitrine

wohnzimmer_rollos:
  name: "Wohnzimmer Rollos"
  icon: mdi:blinds
  entities:
    - cover.wohnzimmer_rollo_gross
    - cover.wohnzimmer_rollo_klein

wohnzimmer_fenster:
  name: "Wohnzimmer Fenster"
  icon: mdi:window-closed-variant
  entities:
    - binary_sensor.wohnzimmer_fenster_klein

wohnzimmer_tueren:
  name: "Wohnzimmer Türen"
  icon: mdi:door-closed
  entities:
    - binary_sensor.wohnzimmer_tur_gross
```

**Esszimmer** (separate covers/sensors for fine-grained control):
```yaml
esszimmer_rollos:
  name: "Esszimmer Rollos"
  icon: mdi:blinds
  entities:
    - cover.esszimmer_rollo_gross
    - cover.esszimmer_rollo_klein

esszimmer_fenster:
  name: "Esszimmer Fenster"
  icon: mdi:window-closed-variant
  entities:
    - binary_sensor.esszimmer_fenster_klein

esszimmer_tueren:
  name: "Esszimmer Türen"
  icon: mdi:door-closed
  entities:
    - binary_sensor.esszimmer_tur_gross
```

**Küche:**
```yaml
kueche_lichter:
  name: "Küche Lichter"
  icon: mdi:lightbulb-group
  entities:
    - light.arbeitsplatte

kueche_rollos:
  name: "Küche Rollos"
  icon: mdi:blinds
  entities:
    - cover.kuche_rollo

kueche_fenster:
  name: "Küche Fenster"
  icon: mdi:window-closed-variant
  entities:
    - binary_sensor.kuche_fenster
```

**Flur:**
```yaml
flur_tueren:
  name: "Flur Türen"
  icon: mdi:door-closed
  entities:
    - binary_sensor.haupteingang_tur
```

**Arbeitszimmer unten:**
```yaml
arbeitszimmer_unten_rollos:
  name: "Arbeitszimmer unten Rollos"
  icon: mdi:blinds
  entities:
    - cover.arbeitszimmer_unten_rollo_vorne
    - cover.arbeitszimmer_unten_rollo_seite

arbeitszimmer_unten_fenster:
  name: "Arbeitszimmer unten Fenster"
  icon: mdi:window-closed-variant
  entities:
    - binary_sensor.arbeitszimmer_unten_fenster_vorne
    - binary_sensor.arbeitszimmer_unten_fenster_seite
```

**Badezimmer unten:**
```yaml
badezimmer_unten_lichter:
  name: "Badezimmer unten Lichter"
  icon: mdi:lightbulb-group
  entities:
    - light.deckenlampe_badezimmer_unten

badezimmer_unten_rollos:
  name: "Badezimmer unten Rollos"
  icon: mdi:blinds
  entities:
    - cover.bad_unten_rollo

badezimmer_unten_fenster:
  name: "Badezimmer unten Fenster"
  icon: mdi:window-closed-variant
  entities:
    - binary_sensor.badezimmer_unten_fenster
```

**HWR:**
```yaml
hwr_lichter:
  name: "HWR Lichter"
  icon: mdi:lightbulb-group
  entities:
    - light.hwr_deckenlampe

hwr_tueren:
  name: "HWR Türen"
  icon: mdi:door-closed
  entities:
    - binary_sensor.hwr_tur_seite
```

### OG (Obergeschoss)

**Schlafzimmer:**
```yaml
schlafzimmer_lichter:
  name: "Schlafzimmer Lichter"
  icon: mdi:lightbulb-group
  entities:
    - light.schlafzimmer_decke
    - light.bett_links
    - light.bett_rechts
    - light.nachtlicht

schlafzimmer_rollos:
  name: "Schlafzimmer Rollos"
  icon: mdi:blinds
  entities:
    - cover.schlafzimmer_rollo

schlafzimmer_fenster:
  name: "Schlafzimmer Fenster"
  icon: mdi:window-closed-variant
  entities:
    - binary_sensor.schlafzimmer_fenster_klein

schlafzimmer_tueren:
  name: "Schlafzimmer Türen"
  icon: mdi:door-closed
  entities:
    - binary_sensor.schlafzimmer_tur_gross
```

**Kinderzimmer:**
```yaml
kinderzimmer_lichter:
  name: "Kinderzimmer Lichter"
  icon: mdi:lightbulb-group
  entities:
    - light.schirmlampe_wohnzimmer

kinderzimmer_rollos:
  name: "Kinderzimmer Rollos"
  icon: mdi:blinds
  entities:
    - cover.kinderzimmer_rollo
```

**Arbeitszimmer oben:**
```yaml
arbeitszimmer_oben_rollos:
  name: "Arbeitszimmer oben Rollos"
  icon: mdi:blinds
  entities:
    - cover.arbeitszimmer_oben_rollo
```

**Badezimmer oben:**
```yaml
badezimmer_oben_fenster:
  name: "Badezimmer oben Fenster"
  icon: mdi:window-closed-variant
  entities:
    - binary_sensor.badezimmer_oben_fenster_vorne
    - binary_sensor.badezimmer_oben_fenster_seite
```

---

## Dashboard Room-Cards: Which Licht Entity to Use

After groups are created, update these room_cards (in views 1–4) to use domain groups:

| Room | Current Licht entity | New Licht entity |
|------|---------------------|-----------------|
| Wohnbereich | `group.wohnzimmer_alle` | `group.wohnzimmer_lichter` ✅ already done |
| Schlafzimmer | `group.schlafzimmer_alle` | `group.schlafzimmer_lichter` |
| Küche | unknown — verify | `group.kueche_lichter` |
| HWR | unknown — verify | `group.hwr_lichter` |
| Badezimmer unten | unknown — verify | `group.badezimmer_unten_lichter` |
| Kinderzimmer | `light.schirmlampe_wohnzimmer` | `group.kinderzimmer_lichter` |

---

## Tasks

---

### Task 1: Verify Samba mount and read current groups

**Step 1: Check if volume is mounted**
```bash
ls /Volumes/config/
```
Expected: lists HA config files. If fails → mount via Finder → Go → Connect to Server → smb://homeassistant.local

**Step 2: Read current groups section**
Use Read tool on `/Volumes/config/configuration.yaml` lines 159–250 (the `group:` section).
Confirm which groups already exist. Do NOT recreate `wohnzimmer_alle`, `schlafzimmer_alle`, `alle_lichter`, `security_lights`, `bewohner`, `tueren_sicherheit`, `fenster_sicherheit`.

**Step 3: Verify runtime group exists**
Via MCP: `ha_get_state("group.wohnzimmer_lichter")` — note that it currently only exists at runtime.

---

### Task 2: Add EG room groups to configuration.yaml

**Files:**
- Modify: `/Volumes/config/configuration.yaml` — insert new groups into the `group:` section

**Step 1: Insert all EG groups**

Find the line `  wohnzimmer_alle:` in configuration.yaml. Insert the new groups BEFORE it (so existing groups stay intact). Add all EG groups from the "Groups to Create" section above: `wohnzimmer_lichter`, `wohnzimmer_rollos`, `wohnzimmer_fenster`, `wohnzimmer_tueren`, `esszimmer_rollos`, `esszimmer_fenster`, `esszimmer_tueren`, `kueche_lichter`, `kueche_rollos`, `kueche_fenster`, `flur_tueren`, `arbeitszimmer_unten_rollos`, `arbeitszimmer_unten_fenster`, `badezimmer_unten_lichter`, `badezimmer_unten_rollos`, `badezimmer_unten_fenster`, `hwr_lichter`, `hwr_tueren`.

Use the Edit tool with the exact YAML from the "Groups to Create" section above.

**Step 2: Reload groups**
```python
ha_reload_core("groups")
```

**Step 3: Verify a sample of new groups**
```python
ha_get_state("group.wohnzimmer_lichter")   # expect: on or off (NOT unknown)
ha_get_state("group.kueche_lichter")        # expect: off (arbeitsplatte off)
ha_get_state("group.flur_tueren")           # expect: off (door closed)
```
All should return valid states. If `unknown` → group not loaded → check YAML syntax.

---

### Task 3: Add OG room groups to configuration.yaml

**Step 1: Insert all OG groups**

Insert after the last new EG group (before `wohnzimmer_alle`): `schlafzimmer_lichter`, `schlafzimmer_rollos`, `schlafzimmer_fenster`, `schlafzimmer_tueren`, `kinderzimmer_lichter`, `kinderzimmer_rollos`, `arbeitszimmer_oben_rollos`, `badezimmer_oben_fenster`.

Use exact YAML from the "Groups to Create" section above.

**Step 2: Reload**
```python
ha_reload_core("groups")
```

**Step 3: Verify**
```python
ha_get_state("group.schlafzimmer_lichter")   # expect: on or off
ha_get_state("group.kinderzimmer_lichter")    # expect: unavailable or off
ha_get_state("group.badezimmer_oben_fenster") # expect: off
```

---

### Task 4: Update dashboard room_cards to use domain-specific Licht groups

**Goal:** Every room_card Licht device must use a `_lichter` group, not a mixed `_alle` group.

**Step 1: Get fresh config_hash**
```python
ha_dashboard_find_card(url_path="new-home", entity_id="group.schlafzimmer_alle", include_config=True)
```
Note the config_hash and all locations where `group.schlafzimmer_alle` appears.

**Step 2: Update all room_cards in one python_transform**

Use `ha_config_set_dashboard` with python_transform to loop through all views and update any Licht device using `group.schlafzimmer_alle`:

```python
for view in config['views']:
    for section in view.get('sections', []):
        for card in section.get('cards', []):
            if card.get('type') == 'conditional':
                inner = card.get('card', {})
                if inner.get('type') == 'custom:decluttering-card':
                    for var in inner.get('variables', []):
                        devices = var.get('room_devices', None)
                        if devices is not None:
                            for device in devices:
                                if device.get('entity') == 'group.schlafzimmer_alle':
                                    device['entity'] = 'group.schlafzimmer_lichter'
```

**Step 3: Update Kinderzimmer room_card**

The Kinderzimmer Licht device currently uses `light.schirmlampe_wohnzimmer` directly. Update to `group.kinderzimmer_lichter`:
```python
for view in config['views']:
    for section in view.get('sections', []):
        for card in section.get('cards', []):
            if card.get('type') == 'conditional':
                inner = card.get('card', {})
                if inner.get('type') == 'custom:decluttering-card':
                    for var in inner.get('variables', []):
                        devices = var.get('room_devices', None)
                        if devices is not None:
                            for device in devices:
                                if device.get('entity') == 'light.schirmlampe_wohnzimmer':
                                    if device.get('name') == 'Licht':
                                        device['entity'] = 'group.kinderzimmer_lichter'
```

**Step 4: Verify Küche, HWR, Badezimmer unten room_cards**

Check what entity each uses for Licht:
```python
ha_dashboard_find_card(url_path="new-home", entity_id="group.kueche_alle")  # or similar
```
If they use a mixed group, apply the same loop-transform to update to `group.kueche_lichter`, `group.hwr_lichter`, `group.badezimmer_unten_lichter`.

**Step 5: Verify result**
```python
ha_dashboard_find_card(url_path="new-home", entity_id="group.schlafzimmer_lichter", include_config=False)
```
Should find the card in views 2 or 3 (Räume EG/OG).

---

### Task 5: Update `group.alle_lichter` to include new lights correctly

**Context:** `group.alle_lichter` in YAML currently lists individual lights. The list may be incomplete or have duplicates after today's changes.

**Step 1: Read current `alle_lichter` group entities from configuration.yaml**

**Step 2: Verify all lights are included:**
Should contain: `light.aussenlicht`, `light.arbeitsplatte`, `light.hwr_deckenlampe`, `light.deckenlampe_badezimmer_unten`, `light.schirmlampe_wohnzimmer`, `light.regal_wohnzimmer`, `light.wohnzimmer_stehlampe_oben`, `light.wohnzimmer_stehlampe_mitte`, `light.wohnzimmer_stehlampe_unten`, `light.vitrine`, `light.schlafzimmer_decke`, `light.bett_links`, `light.bett_rechts`, `light.nachtlicht`

**Step 3: If anything is missing or wrong, update the list in YAML then reload.**

---

### Task 6: Update reference files

**Files:**
- Modify: `~/.claude/skills/home-assistant/reference/home-setup.md`
- Modify: `~/.claude/projects/.../memory/MEMORY.md`

**Step 1: Add "Groups" section to home-setup.md**

Add a new section listing all the new per-room groups:
```markdown
## Groups (per-room, per-domain)

| Group ID | Entities |
|----------|----------|
| `group.wohnzimmer_lichter` | regal, 3x stehlampe, vitrine |
| `group.wohnzimmer_rollos` | wohnzimmer_rollo_gross/klein |
| ... etc |
```

**Step 2: Update MEMORY.md**

Remove the `⚠️ Pending: configuration.yaml` note (if it exists) since the groups are now persisted.

Update the Wohnbereich Entities section to note that `group.wohnzimmer_lichter` is now in YAML.

**Step 3: Commit local file changes**
```bash
git add docs/plans/ ~/.claude/skills/home-assistant/reference/home-setup.md
git commit -m "docs: add systematic room groups plan and update reference"
```

---

## Verification Checklist

After all tasks complete:

- [ ] `ha_get_state("group.wohnzimmer_lichter")` returns `on`/`off` (not `unknown`)
- [ ] `ha_get_state("group.schlafzimmer_lichter")` returns correct state
- [ ] `ha_get_state("group.kinderzimmer_lichter")` returns correct state
- [ ] Wohnbereich room_card "Licht" shows correct state (not "Ein" when no lights on)
- [ ] Schlafzimmer room_card "Licht" shows correct state
- [ ] Kinderzimmer room_card "Licht" shows correct state
- [ ] HA restart test: after `ha_restart`, all new groups still exist (proves YAML persistence)

---

## Notes

- **Bewegungsmelder groups**: Intentionally not created (usually 1 sensor per room, no grouping needed)
- **Esszimmer Licht**: `light.vitrine` is included in `group.wohnzimmer_lichter` because Wohnbereich = Wohnzimmer + Esszimmer combined view
- **cover.wohnbereich_rollos**: This is a native HA cover group (not a generic `group:`), keep as-is for cover control
- **group.xxx_alle groups**: Keep for backward compatibility but don't use for single-domain display
- **Empty groups**: Not created — only rooms with actual entities get that domain group
