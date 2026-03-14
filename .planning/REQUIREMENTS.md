# Requirements: Mova 600 Plus HA Integration

**Defined:** 2026-03-14
**Core Value:** Users can see their Mova 600 Plus on a live map in Home Assistant and control it with reliable status feedback.

## v1 Requirements

Requirements for initial working release. Each maps to roadmap phases.

### Foundation

- [x] **FOUND-01**: Integration installs without errors on current HA (2025.x+) with all dependencies resolved
- [x] **FOUND-02**: Dead `py-mini-racer` dependency replaced with `mini-racer`
- [x] **FOUND-03**: All dependency versions pinned in manifest.json
- [x] **FOUND-04**: paho-mqtt v2.0 callback API compatibility verified

### Connectivity

- [ ] **CONN-01**: User can add Mova 600 Plus via config flow using MOVAhome account credentials
- [ ] **CONN-02**: Integration discovers and pairs with Mova 600 Plus device (model ID confirmed)
- [ ] **CONN-03**: Cloud MQTT protocol maintains stable connection to Mova 600 Plus
- [x] **CONN-04**: Unknown property IDs from Mova 600 Plus do not crash the integration (fix #46)

### Control

- [x] **CTRL-01**: User can start mowing from HA
- [x] **CTRL-02**: User can pause mowing from HA
- [x] **CTRL-03**: User can send mower to dock from HA without breaking device schedules (fix #35)

### Sensors

- [x] **SENS-01**: Battery level displayed as percentage sensor
- [x] **SENS-02**: Mower state sensor shows current activity (mowing, docked, paused, returning, charging, error)
- [x] **SENS-03**: Error state sensor shows error description when mower has a fault
- [x] **SENS-04**: Online/connectivity binary sensor shows cloud connection status
- [x] **SENS-05**: Mowing progress sensor shows percentage of area completed
- [x] **SENS-06**: Area mowed sensor shows square meters mowed in current session
- [x] **SENS-07**: Blade usage sensor shows wear percentage or hours remaining
- [x] **SENS-08**: Blade consumable reset button available

### Map

- [ ] **MAP-01**: Live map camera entity renders mower position on garden map
- [ ] **MAP-02**: Map shows mowed vs unmowed areas during a session
- [ ] **MAP-03**: Map data parsing does not crash (fix #39)
- [ ] **MAP-04**: Camera entity has required HA attributes without errors (fix #42)

### Cleanup

- [x] **CLEAN-01**: Vacuum-specific entities (suction, mop, carpet, dust bin) are not exposed for mower devices
- [x] **CLEAN-02**: Config flow deprecation warnings resolved (fix #41)

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Zone Management

- **ZONE-01**: User can see named zones on the map
- **ZONE-02**: User can select specific zones to mow from HA
- **ZONE-03**: User can toggle no-go zones on/off from HA

### Enhanced Controls

- **ENHC-01**: User can select mowing pattern/mode (standard, efficient, edge)
- **ENHC-02**: User can enable/disable mowing schedule via switch
- **ENHC-03**: Mowing schedule exposed as HA calendar entity

### Advanced Sensors

- **ADVS-01**: Firmware version sensor
- **ADVS-02**: WiFi signal strength (RSSI) sensor
- **ADVS-03**: Total lifetime mowing time sensor
- **ADVS-04**: Mowing history with map snapshots

## Out of Scope

| Feature | Reason |
|---------|--------|
| Local/non-cloud protocol | Mova 600 Plus has no local API; massive reverse-engineering effort |
| Remote joystick control | Latency-sensitive over cloud; safety risk for outdoor machinery |
| OTA firmware updates | Safety-critical; must go through manufacturer app |
| Obstacle photo display | Mova 600 Plus has no camera, only LiDAR |
| Voice pack installation | Vacuum-specific feature, mowers don't talk |
| Multi-floor map support | Mower has one garden, not multiple floors |
| Custom Lovelace card | Use existing vacuum map cards; card development is separate project |
| Room/zone name editing | Edit in MOVAhome app; read-only in HA is sufficient |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| FOUND-01 | Phase 1: Stabilize and Connect | Complete |
| FOUND-02 | Phase 1: Stabilize and Connect | Complete |
| FOUND-03 | Phase 1: Stabilize and Connect | Complete |
| FOUND-04 | Phase 1: Stabilize and Connect | Complete |
| CONN-01 | Phase 1: Stabilize and Connect | Pending |
| CONN-02 | Phase 1: Stabilize and Connect | Pending |
| CONN-03 | Phase 1: Stabilize and Connect | Pending |
| CONN-04 | Phase 1: Stabilize and Connect | Complete |
| CLEAN-02 | Phase 1: Stabilize and Connect | Complete |
| CTRL-01 | Phase 2: Control and Sensors | Complete |
| CTRL-02 | Phase 2: Control and Sensors | Complete |
| CTRL-03 | Phase 2: Control and Sensors | Complete |
| SENS-01 | Phase 2: Control and Sensors | Complete |
| SENS-02 | Phase 2: Control and Sensors | Complete |
| SENS-03 | Phase 2: Control and Sensors | Complete |
| SENS-04 | Phase 2: Control and Sensors | Complete |
| SENS-05 | Phase 2: Control and Sensors | Complete |
| SENS-06 | Phase 2: Control and Sensors | Complete |
| SENS-07 | Phase 2: Control and Sensors | Complete |
| SENS-08 | Phase 2: Control and Sensors | Complete |
| CLEAN-01 | Phase 2: Control and Sensors | Complete |
| MAP-01 | Phase 3: Live Map | Pending |
| MAP-02 | Phase 3: Live Map | Pending |
| MAP-03 | Phase 3: Live Map | Pending |
| MAP-04 | Phase 3: Live Map | Pending |

**Coverage:**
- v1 requirements: 25 total
- Mapped to phases: 25
- Unmapped: 0

---
*Requirements defined: 2026-03-14*
*Last updated: 2026-03-14 after 02-02 completion (SENS-01/03/05/06/07/08, CLEAN-01)*
