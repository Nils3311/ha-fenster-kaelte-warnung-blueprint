# Requirements: Mova 600 Plus HA Integration

**Defined:** 2026-03-14
**Core Value:** Users can see their Mova 600 Plus on a live map in Home Assistant and control it with reliable status feedback.

## v1 Requirements

Requirements for initial working release. Each maps to roadmap phases.

### Foundation

- [ ] **FOUND-01**: Integration installs without errors on current HA (2025.x+) with all dependencies resolved
- [ ] **FOUND-02**: Dead `py-mini-racer` dependency replaced with `mini-racer`
- [ ] **FOUND-03**: All dependency versions pinned in manifest.json
- [ ] **FOUND-04**: paho-mqtt v2.0 callback API compatibility verified

### Connectivity

- [ ] **CONN-01**: User can add Mova 600 Plus via config flow using MOVAhome account credentials
- [ ] **CONN-02**: Integration discovers and pairs with Mova 600 Plus device (model ID confirmed)
- [ ] **CONN-03**: Cloud MQTT protocol maintains stable connection to Mova 600 Plus
- [ ] **CONN-04**: Unknown property IDs from Mova 600 Plus do not crash the integration (fix #46)

### Control

- [ ] **CTRL-01**: User can start mowing from HA
- [ ] **CTRL-02**: User can pause mowing from HA
- [ ] **CTRL-03**: User can send mower to dock from HA without breaking device schedules (fix #35)

### Sensors

- [ ] **SENS-01**: Battery level displayed as percentage sensor
- [ ] **SENS-02**: Mower state sensor shows current activity (mowing, docked, paused, returning, charging, error)
- [ ] **SENS-03**: Error state sensor shows error description when mower has a fault
- [ ] **SENS-04**: Online/connectivity binary sensor shows cloud connection status
- [ ] **SENS-05**: Mowing progress sensor shows percentage of area completed
- [ ] **SENS-06**: Area mowed sensor shows square meters mowed in current session
- [ ] **SENS-07**: Blade usage sensor shows wear percentage or hours remaining
- [ ] **SENS-08**: Blade consumable reset button available

### Map

- [ ] **MAP-01**: Live map camera entity renders mower position on garden map
- [ ] **MAP-02**: Map shows mowed vs unmowed areas during a session
- [ ] **MAP-03**: Map data parsing does not crash (fix #39)
- [ ] **MAP-04**: Camera entity has required HA attributes without errors (fix #42)

### Cleanup

- [ ] **CLEAN-01**: Vacuum-specific entities (suction, mop, carpet, dust bin) are not exposed for mower devices
- [ ] **CLEAN-02**: Config flow deprecation warnings resolved (fix #41)

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
| FOUND-01 | Phase 1 | Pending |
| FOUND-02 | Phase 1 | Pending |
| FOUND-03 | Phase 1 | Pending |
| FOUND-04 | Phase 1 | Pending |
| CONN-01 | Phase 2 | Pending |
| CONN-02 | Phase 2 | Pending |
| CONN-03 | Phase 2 | Pending |
| CONN-04 | Phase 2 | Pending |
| CTRL-01 | Phase 2 | Pending |
| CTRL-02 | Phase 2 | Pending |
| CTRL-03 | Phase 2 | Pending |
| SENS-01 | Phase 3 | Pending |
| SENS-02 | Phase 3 | Pending |
| SENS-03 | Phase 3 | Pending |
| SENS-04 | Phase 3 | Pending |
| SENS-05 | Phase 3 | Pending |
| SENS-06 | Phase 3 | Pending |
| SENS-07 | Phase 3 | Pending |
| SENS-08 | Phase 3 | Pending |
| MAP-01 | Phase 4 | Pending |
| MAP-02 | Phase 4 | Pending |
| MAP-03 | Phase 4 | Pending |
| MAP-04 | Phase 4 | Pending |
| CLEAN-01 | Phase 3 | Pending |
| CLEAN-02 | Phase 1 | Pending |

**Coverage:**
- v1 requirements: 25 total
- Mapped to phases: 25
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-14*
*Last updated: 2026-03-14 after initial definition*
