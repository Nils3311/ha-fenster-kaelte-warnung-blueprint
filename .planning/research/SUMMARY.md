# Project Research Summary

**Project:** Mova 600 Plus -- Home Assistant Integration
**Domain:** Home Assistant custom integration (brownfield fork of bhuebschen/dreame-mower v0.0.5-alpha)
**Researched:** 2026-03-14
**Confidence:** HIGH

## Executive Summary

This project forks an existing but buggy HA custom integration for Dreame robotic mowers to make it work reliably with the Mova 600 Plus. The upstream codebase (bhuebschen/dreame-mower) is itself a fork of the mature Tasshack/dreame-vacuum integration, which means the core architecture -- protocol handling, map rendering, entity patterns -- is proven and functional. The work is not building from scratch; it is stabilizing, pruning vacuum leftovers, and validating against a specific device. Five open bugs (#35, #39, #41, #42, #46) block basic functionality and must be fixed before anything else.

The recommended approach is strictly surgical: fix the five known bugs in dependency order, replace the dead `py-mini-racer` dependency with the maintained `mini-racer`, validate the integration against the real Mova 600 Plus device, prune clearly irrelevant vacuum entities, and then focus on making the live map camera entity work reliably -- this is the integration's only real differentiator over generic MQTT setups. The stack is well-understood (all dependencies are HA-blessed except for the one critical `py-mini-racer` swap), and the architecture should not be refactored. The codebase has 5 files over 1,000 lines each, inherited from upstream, and restructuring them would destroy the ability to cherry-pick future upstream fixes.

The key risks are: (1) the dead `py-mini-racer` dependency will fail on modern Python/HA and must be replaced immediately, (2) unknown property IDs from the Mova 600 Plus will crash the integration unless the property enum is made resilient first, and (3) the 9,322-line map.py is where the most valuable feature lives (live map) and also where the hardest bugs are. All three risks have clear, documented mitigations.

## Key Findings

### Recommended Stack

The integration runs on HA Core >=2025.1.0 with Python 3.12-3.14. All major dependencies (Pillow, numpy, paho-mqtt, pycryptodome, requests) are HA Core-bundled and low-risk. Two dependencies need immediate action: `py-mini-racer` must be replaced with `mini-racer` (the old package is dead since 2021 and won't install on Python 3.12+), and all dependencies in `manifest.json` need version pins (currently bare package names with no constraints). `python-miio` is the highest-risk ongoing dependency -- it is inactive with no releases in 12+ months -- but the miIO protocol handshake code it provides is small enough to inline if it breaks. See STACK.md for full version table and target manifest.json.

**Core technologies:**
- `mini-racer` (>=0.12.0): V8 JS engine for Dreame cloud auth -- replaces dead `py-mini-racer` (P0 fix)
- `paho-mqtt` (>=2.0.0): Cloud MQTT transport -- v2.0 callback API must be audited in protocol.py
- `pillow` + `numpy`: Map PNG rendering pipeline -- HA Core-bundled, stable
- `pycryptodome`: AES encryption for Dreame protocol -- stable, no changes needed
- `python-miio` (>=0.5.12): Xiaomi device discovery -- inactive upstream, pin working version
- `ruff` + `pytest-homeassistant-custom-component`: Dev tooling -- HA standard

### Expected Features

The feature landscape is shaped by what other mower integrations provide (Husqvarna, Landroid, Bosch Indego) and what the Tasshack/dreame-vacuum lineage uniquely enables. See FEATURES.md for the full feature matrix with complexity ratings and dependency chains.

**Must have (table stakes):**
- lawn_mower entity (start/pause/dock) -- already partially working in upstream
- Battery level, mower state/status, error state sensors -- basic monitoring
- Online/connectivity binary sensor -- debug cloud connection issues
- Mowing progress (area, time), blade usage sensor -- maintenance tracking

**Should have (differentiators):**
- Live map camera entity -- the killer feature; no other mower integration has this
- Mowing pattern/mode select -- Mova 600 Plus supports creative patterns
- Mowing history with map snapshots -- inherited from vacuum infrastructure
- Schedule enable/disable switch -- simple but high-value UX

**Defer (v2+):**
- Zone/area management (switches, zone-specific mowing services)
- Schedule calendar entity
- Cutting height control (may not be software-controllable on Mova 600 Plus)
- No-go zone switches
- Override schedule actions

**Anti-features (never build):**
- Vacuum-specific sensors (mop pad, tank filter, suction level)
- Remote joystick control (latency-sensitive, dangerous for outdoor machinery)
- OTA firmware updates (safety risk)
- Local API reverse engineering (Mova 600 Plus requires cloud)

### Architecture Approach

The integration is a 4-layer system: HA platform entities at the top, a DataUpdateCoordinator bridging async HA to sync device code, a central Device state machine (the "god object" at 5,387 lines), and a Protocol layer handling cloud MQTT and local MiIO transport. A semi-independent Map subsystem (9,322 lines, 7 classes) handles map acquisition, decoding, and PNG rendering. The critical architectural insight is: do not refactor. The large files mirror the upstream Tasshack/dreame-vacuum structure, and structural changes destroy merge compatibility. All changes should be surgical with `# FORK: reason` comments. See ARCHITECTURE.md for complete component boundaries and data flow diagrams.

**Major components:**
1. **Protocol layer** (protocol.py) -- Cloud MQTT + local MiIO transport; handles both Dreame and Mova accounts; working, do not touch
2. **Device state machine** (device.py, 5,387 lines) -- Property polling, action dispatch, capability detection; make surgical fixes only
3. **Map subsystem** (map.py, 9,322 lines) -- Map acquisition, decoding, PNG rendering; contains the hardest bugs (#39) and the highest-value feature (live map)
4. **Entity layer** (lawn_mower.py, camera.py, sensor.py, etc.) -- Property-driven entity registration with `exists_fn` pattern; add/remove entity descriptions here
5. **Type definitions** (types.py, const.py) -- All enums, property mappings, model capabilities; change first when adding new model support

### Critical Pitfalls

The top 5 pitfalls, ordered by severity. See PITFALLS.md for all 11 with code-level prevention strategies.

1. **Unknown property enum crash (#46)** -- New Mova models return properties not in `DreameMowerProperty` IntEnum, crashing the entire integration. Fix: wrap in try/except, skip unknown properties. This is the single most important fix for any new model support.
2. **Dead `py-mini-racer` dependency** -- Won't install on Python 3.12+. Fix: replace with `mini-racer` in manifest.json and all imports. Tasshack/dreame-vacuum already did this.
3. **Map data type mismatch (#39)** -- Cloud returns a list where code expects a dict, breaking map updates. Fix: add `isinstance(result, dict)` type check.
4. **Camera entity HA breaking change (#42)** -- Missing `_webrtc_provider` attribute crashes camera entity registration. Fix: one-line attribute initialization.
5. **Dock command breaks schedules (#35)** -- Dock action doesn't properly end the mowing session in Dreame's cloud state machine. Fix: implement pause-stop-charge sequence.

## Implications for Roadmap

Based on the combined research, the project naturally breaks into 5 phases driven by dependency order, risk mitigation, and feature value.

### Phase 1: Stabilize the Fork

**Rationale:** Nothing else works until the five known bugs are fixed. These bugs affect all users and all device models. Fixing them requires no new features, no device pairing, and no architectural changes. This phase also replaces the dead `py-mini-racer` dependency and adds version pins -- both P0 blockers.

**Delivers:** A fork that installs, starts, and runs without crashing on HA 2025.1+. Config flow works (#41), property parsing is resilient (#46), camera entity loads (#42), and manifest.json has proper dependency pins.

**Addresses features:** None directly (prerequisite for all features).

**Avoids pitfalls:** #1 (property crash), #3 (camera crash), #6 (options flow crash), #10 (py-mini-racer install failure).

**Bug fix order (dependency-driven):**
1. Replace `py-mini-racer` with `mini-racer` + add version pins to manifest.json
2. Fix #41 config_flow options (one-line removal)
3. Fix #46 property enum resilience (try/except wrapper)
4. Fix #42 camera entity `_webrtc_provider` (one-line addition)
5. Fix #39 map data type check (type guard)
6. Fix #35 dock command state sequence (pause-stop-charge)

### Phase 2: Mova 600 Plus Device Validation

**Rationale:** With bugs fixed, pair the real Mova 600 Plus and capture its actual property set, model ID, and cloud behavior. This phase is empirical -- it discovers what the device actually reports rather than guessing from vacuum code. Must come before feature work because the device may expose unexpected properties or missing ones.

**Delivers:** Confirmed Mova 600 Plus model registration in config_flow, documented property dump, verified cloud MQTT connectivity via Mova account type, and validated basic controls (start/pause/dock).

**Addresses features:** lawn_mower entity, battery sensor, state sensor, online sensor.

**Avoids pitfalls:** #1 (property enum crash -- already fixed in Phase 1, validated here), #5 (dock command -- verified against real device).

### Phase 3: Core Sensors and Entity Cleanup

**Rationale:** With the device paired and basic controls validated, add the table-stakes sensors that every mower integration provides, and prune vacuum-specific phantom entities. This phase makes the integration feel like a real mower integration rather than a relabeled vacuum.

**Delivers:** Complete sensor suite (battery, state, error, progress, blade wear, WiFi, firmware), consumable reset buttons, and clean entity list with no vacuum ghosts.

**Addresses features:** All table-stakes sensors from FEATURES.md Phase 1 and Phase 2 lists. Vacuum entity pruning from anti-features list.

**Avoids pitfalls:** #9 (phantom vacuum entities -- removed here), #7 (upstream divergence -- only additive changes to sensor descriptions, no structural refactoring).

### Phase 4: Live Map Camera Entity

**Rationale:** The live map is the integration's only true differentiator. With #39 (map parsing) and #42 (camera entity) already fixed in Phase 1, this phase focuses on validating map rendering with real Mova 600 Plus data, fixing any rendering issues specific to outdoor mower maps, and ensuring the map updates reliably during mowing sessions.

**Delivers:** Working live map camera entity showing mower position, mowed area, dock location, and path history. Mowing history map snapshots.

**Addresses features:** Live map camera entity (top differentiator), mowing history statistics.

**Avoids pitfalls:** #2 (map data type mismatch -- fixed in Phase 1, stress-tested here), #4 (compressed blob corruption -- rely on property-based detection, don't edit blobs).

### Phase 5: Enhanced Controls and Polish

**Rationale:** With core functionality solid, add the quality-of-life features that elevate the integration: mowing mode selection, schedule switch, diagnostic sensors. These are independent of each other and can be implemented in any order.

**Delivers:** Mowing pattern/mode select entity, schedule enable/disable switch, diagnostic sensors (LiDAR status, wheel temps, collision count), CI/CD pipeline (hassfest + HACS validation + ruff).

**Addresses features:** Mowing pattern/mode select, schedule enable/disable, diagnostic sensors, firmware version sensor.

**Avoids pitfalls:** #8 (thread safety -- use existing dirty data mechanism for new controls), #7 (upstream divergence -- additive entity descriptions only).

### Phase Ordering Rationale

- **Phase 1 before everything:** All five bugs are blocking bugs. The integration literally crashes without these fixes. The `py-mini-racer` swap is a hard blocker on modern HA.
- **Phase 2 before Phase 3:** You cannot write correct sensor entities without knowing what properties the Mova 600 Plus actually reports. Empirical device validation prevents building against assumptions.
- **Phase 3 before Phase 4:** Sensors are simpler and higher-certainty than map rendering. Getting basic sensors working builds confidence in the property pipeline before tackling the complex map subsystem.
- **Phase 4 before Phase 5:** The live map is the highest-value feature. Polish features (mode select, schedule switch) are nice-to-have but don't justify the integration's existence the way the map does.
- **Phase 5 is optional for v1:** The integration is shippable after Phase 4. Phase 5 is enhancement.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 2 (Device Validation):** Requires physical device pairing and empirical property capture. Cannot be fully planned from code analysis alone. The Mova 600 Plus model ID, supported properties, and MQTT topic format must be discovered.
- **Phase 4 (Live Map):** The map subsystem is 9,322 lines and the most complex component. Map rendering for outdoor mower contexts (GPS-less, large areas, irregular shapes) may differ from indoor vacuum maps. Research the Mova 600 Plus map data format specifically.

Phases with standard patterns (skip research-phase):
- **Phase 1 (Bug Fixes):** All fixes are documented with exact file locations, line numbers, and code snippets. No research needed.
- **Phase 3 (Sensors):** Property-driven entity registration is a well-documented HA pattern. The sensor descriptions follow the existing codebase pattern exactly.
- **Phase 5 (Polish):** Select entities, switch entities, and CI/CD are standard HA patterns with official documentation.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All dependencies verified against HA Core constraints and PyPI. `py-mini-racer` to `mini-racer` migration confirmed by Tasshack/dreame-vacuum. |
| Features | HIGH | Feature landscape cross-referenced against 5 competing mower integrations (Husqvarna, Landroid, Bosch Indego, Mammotion) and upstream Tasshack/dreame-vacuum. |
| Architecture | HIGH | Based on direct codebase analysis of all major files with line counts and class inventories. Data flow traced through all layers. |
| Pitfalls | HIGH | All critical pitfalls traced to specific GitHub issues with confirmed reproduction steps. Code-level fixes verified against HA source and upstream patterns. |

**Overall confidence:** HIGH

### Gaps to Address

- **Mova 600 Plus model ID:** The exact model string (e.g., "mova.mower.xxx") is unknown until device pairing. Phase 2 must discover this empirically.
- **Cutting height controllability:** Uncertain whether the Mova 600 Plus exposes cutting height as a software-settable property (it has a physical dial). LOW confidence -- defer to Phase 5 or v2.
- **paho-mqtt v2.0 callback audit:** The STACK.md flags that protocol.py must be audited for paho-mqtt v2.0 callback API compatibility. This has not been done yet. Must be part of Phase 1.
- **ARM64 `mini-racer` wheel availability:** V8 engine binaries may not have wheels for all HA OS architectures (RPi3/4 ARM). Needs validation in Phase 1.
- **Mova vs Dreame cloud API differences:** The protocol layer handles both account types, but subtle API response differences (like the list-vs-dict in #39) may exist specifically for Mova accounts. Phase 2 must validate.
- **Map rendering for outdoor context:** The map renderer was designed for indoor vacuum maps (rooms, furniture, carpets). Outdoor mower maps (lawns, irregular boundaries, weather) may need rendering adjustments. Phase 4 must validate.

## Sources

### Primary (HIGH confidence)
- [bhuebschen/dreame-mower](https://github.com/bhuebschen/dreame-mower) -- direct codebase analysis, issues #35, #39, #41, #42, #46
- [Tasshack/dreame-vacuum](https://github.com/Tasshack/dreame-vacuum) v1.0.8 -- upstream reference, confirmed `mini-racer` migration
- [HA Developer Docs](https://developers.home-assistant.io/) -- lawn_mower, camera, sensor platform APIs; manifest.json spec; DataUpdateCoordinator pattern
- [HA Core package_constraints.txt](https://github.com/home-assistant/core/blob/dev/homeassistant/package_constraints.txt) -- bundled library versions
- [paho-mqtt migration docs](https://eclipse.dev/paho/files/paho.mqtt.python/html/migrations.html) -- v2.0 breaking changes
- [PyPI: py-mini-racer](https://pypi.org/project/py-mini-racer/) (last release 0.6.0, 2021) and [mini-racer](https://pypi.org/project/mini-racer/) (v0.14.1, 2026)

### Secondary (MEDIUM confidence)
- [Husqvarna Automower HA integration](https://www.home-assistant.io/integrations/husqvarna_automower/) -- feature reference (gold standard official mower integration)
- [Landroid Cloud](https://github.com/MTrab/landroid_cloud), [Bosch Indego](https://github.com/sander1988/Indego), [Mammotion](https://github.com/mikey0000/Mammotion-HA) -- community mower integration feature comparison
- [HA Community Dreame mower thread](https://community.home-assistant.io/t/dreame-a1-a1-pro-a2-mova-600-1000-integration/749593) -- user reports and device compatibility
- [HACS Publishing Requirements](https://www.hacs.xyz/docs/publish/integration/) -- validation checklist
- [pytest-homeassistant-custom-component](https://github.com/MatthewFlamm/pytest-homeassistant-custom-component) -- v0.13.317 targeting HA 2026.3.1

### Tertiary (LOW confidence)
- Mova 600 Plus cutting height software control -- unverified, needs device testing
- ARM64 `mini-racer` wheel availability -- unverified, needs target platform testing

---
*Research completed: 2026-03-14*
*Ready for roadmap: yes*
