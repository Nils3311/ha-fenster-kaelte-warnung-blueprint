# Mova 600 Plus — Home Assistant Integration

## What This Is

A Home Assistant custom integration for the Mova 600 Plus robotic lawn mower, forked from bhuebschen/dreame-mower (v0.0.5-alpha). Provides live map display, mowing controls, progress tracking, and device sensors. Installed via HACS from a personal GitHub fork, developed and tested directly in HA's custom_components/ directory against a real Mova 600 Plus device.

## Core Value

Users can see their Mova 600 Plus on a live map in Home Assistant and control it (start/stop/dock) with reliable status feedback — turning HA into the single interface for the mower instead of the MOVAhome app.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Start, stop, and dock the mower from Home Assistant
- [ ] Display a live map showing the mower's position and mowed area
- [ ] Show mowing progress as a percentage sensor
- [ ] Expose battery level, blade wear, error state, and area mowed as sensors
- [ ] Confirm Mova 600 Plus connectivity via Dreame/MOVAhome cloud protocol
- [ ] Fix known map rendering bugs (issues #39, #42 in upstream)
- [ ] Fix dock command breaking schedules (issue #35 in upstream)

### Out of Scope

- Zone selection for targeted mowing — complexity too high for v1, defer to v2
- Local-only (non-cloud) communication — Mova 600 Plus requires cloud protocol
- Multi-floor/multi-map support — single garden, single map
- Lovelace custom card development — use existing vacuum map cards
- Voice assistant integration — basic HA entity exposure is sufficient
- MOVAhome app replacement — integration complements the app, doesn't replace it

## Context

### Upstream Codebase (bhuebschen/dreame-mower v0.0.5-alpha)

- Forked from Tasshack/dreame-vacuum (mature, 1800+ stars, full map support)
- Already adapted from vacuum to lawn_mower platform
- Map rendering code exists (415KB map.py) but has bugs (#39 data parsing, #42 camera entity)
- Cloud protocol works via Dreame/MOVAhome MQTT (protocol.py, 33KB)
- Supports Dreame A1, A1 Pro, A2 models — Mova 600 Plus not yet confirmed
- 5 contributors, actively maintained (last commit March 2026)

### Mova 600 Plus Device

- Model identifier: likely `mova.mower.*` prefix (needs confirmation from device)
- Navigation: 3D-LiDAR (UltraView), no camera
- Cloud: MOVAhome app account (Dreame subsidiary)
- Protocol: Expected to use same MQTT cloud protocol as other Dreame/Mova mowers

### Development Setup

- Fork cloned into `/Volumes/config/custom_components/dreame_mower/`
- Direct live testing against real Mova 600 Plus
- GitHub fork for version control and HACS distribution
- HA instance accessible for restart/reload during development

### Key Files in Upstream

| File | Size | Purpose |
|------|------|---------|
| `dreame/device.py` | 247 KB | Device control, properties, actions |
| `dreame/map.py` | 415 KB | Map rendering, PNG generation |
| `dreame/protocol.py` | 33 KB | Cloud + local communication |
| `dreame/types.py` | 100 KB | Enums, data structures |
| `dreame/const.py` | 52 KB | Constants, error mappings |
| `dreame/resources.py` | 19.2 MB | Compressed model definitions |
| `config_flow.py` | ~600 lines | Device discovery, setup UI |
| `lawn_mower.py` | Main entity | Start/stop/dock actions |
| `camera.py` | Map entity | Camera entities for map display |
| `sensor.py` | Sensors | Battery, wear, area, progress |

### Known Upstream Bugs to Fix

- **#35**: `lawn_mower.dock` breaks Dreame schedules (bad state after dock)
- **#39**: Map data parsing error ("list indices must be integers")
- **#42**: Camera entity missing `_webrtc_provider` attribute
- **#41**: Config flow 500 error (deprecated `self.config_entry`)
- **#46**: Mova Lidax Ultra 800 property validation errors (may affect Mova 600 Plus)

## Constraints

- **Cloud dependency**: Mova 600 Plus has no local API — must use Dreame/MOVAhome cloud MQTT
- **Device access**: Need physical Mova 600 Plus for testing (owner has one)
- **Upstream stability**: Base code is alpha (v0.0.5) — expect rough edges
- **HA compatibility**: Must work with current HA version (2025.x+)
- **HACS compliance**: Must pass HACS validation for distribution

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Fork bhuebschen/dreame-mower (not Tasshack vacuum or PaoloCappellari fork) | Already adapted vacuum→mower, active community, map code present but buggy | — Pending |
| Hybrid dev: clone into custom_components/ | Direct live testing against real device, GitHub for version control | — Pending |
| Cloud-only protocol | Mova 600 Plus has no local API, cloud protocol already implemented | — Pending |
| Fix upstream bugs before adding features | Stable base needed before building on top | — Pending |

---
*Last updated: 2026-03-14 after initialization*
