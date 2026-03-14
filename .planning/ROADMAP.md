# Roadmap: Mova 600 Plus HA Integration

## Overview

This project stabilizes a forked Dreame mower integration, validates it against a real Mova 600 Plus device, exposes full control and sensor capabilities, and delivers a working live map -- turning Home Assistant into the single interface for the mower. Three phases move from "fork that installs and connects" through "mower you can control and monitor" to "live map on your dashboard."

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Stabilize and Connect** - Fix blocking bugs, replace dead dependencies, and pair with the real Mova 600 Plus
- [ ] **Phase 2: Control and Sensors** - Expose mower controls (start/pause/dock) and all monitoring sensors
- [ ] **Phase 3: Live Map** - Deliver the live map camera entity showing mower position and mowed area

## Phase Details

### Phase 1: Stabilize and Connect
**Goal**: The integration installs cleanly on modern HA, connects to the Mova 600 Plus via MOVAhome cloud, and runs without crashing
**Depends on**: Nothing (first phase)
**Requirements**: FOUND-01, FOUND-02, FOUND-03, FOUND-04, CONN-01, CONN-02, CONN-03, CONN-04, CLEAN-02
**Success Criteria** (what must be TRUE):
  1. Integration installs on HA 2025.x+ without dependency errors (no py-mini-racer failures, all versions pinned)
  2. User can add the Mova 600 Plus through the config flow UI using MOVAhome credentials without errors
  3. Integration discovers the Mova 600 Plus, confirms its model ID, and maintains a stable cloud MQTT connection
  4. Unknown property IDs from the Mova 600 Plus are silently skipped -- no crashes from unrecognized device data
  5. HA logs show no deprecation warnings from config flow (fix #41) and no startup errors
**Plans:** 2 plans

Plans:
- [x] 01-01-PLAN.md -- Fix all blocking bugs: manifest dependencies, mini-racer import, unknown property crash, OptionsFlow deprecation, camera _webrtc_provider, map result type checks, model_map KeyError
- [ ] 01-02-PLAN.md -- Live device pairing: restart HA, pair Mova 600 Plus via config flow, verify stable MQTT connection (Task 1 done, Task 2 pending user action)

### Phase 2: Control and Sensors
**Goal**: Users can control their mower and monitor all key metrics from Home Assistant
**Depends on**: Phase 1
**Requirements**: CTRL-01, CTRL-02, CTRL-03, SENS-01, SENS-02, SENS-03, SENS-04, SENS-05, SENS-06, SENS-07, SENS-08, CLEAN-01
**Success Criteria** (what must be TRUE):
  1. User can start, pause, and dock the mower from HA -- and docking does not break device schedules
  2. Battery level, mower state, error state, mowing progress, area mowed, and blade wear are all visible as HA sensors
  3. An online/connectivity binary sensor shows whether the cloud connection is active
  4. A blade consumable reset button is available and functional
  5. No vacuum-specific entities (suction, mop, carpet, dust bin) appear in the entity list
**Plans**: TBD

Plans:
- [ ] 02-01: TBD
- [ ] 02-02: TBD

### Phase 3: Live Map
**Goal**: Users can see their Mova 600 Plus on a live map in Home Assistant showing position and mowed area
**Depends on**: Phase 2
**Requirements**: MAP-01, MAP-02, MAP-03, MAP-04
**Success Criteria** (what must be TRUE):
  1. A camera entity renders the garden map with the mower's current position visible
  2. During a mowing session, the map updates to show mowed vs unmowed areas in real time
  3. Map data parsing handles all Mova 600 Plus responses without errors (no list-vs-dict crashes)
  4. The camera entity loads in HA without missing attribute errors (_webrtc_provider issue resolved)
**Plans**: TBD

Plans:
- [ ] 03-01: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Stabilize and Connect | 1.5/2 | Awaiting User Action (01-02 pairing checkpoint) | - |
| 2. Control and Sensors | 0/0 | Not started | - |
| 3. Live Map | 0/0 | Not started | - |
