---
phase: 01-stabilize-and-connect
plan: 01
subsystem: integration
tags: [dreame-mower, mini-racer, paho-mqtt, ha-custom-component, manifest, bugfix]

# Dependency graph
requires:
  - phase: none
    provides: "First plan in project"
provides:
  - "Installable dreame_mower integration with all dependencies resolved"
  - "Crash-free property handling for unknown Mova 600 Plus IDs"
  - "Working OptionsFlow without 500 errors"
  - "Camera entity init without AttributeError"
  - "Safe map result parsing (dict type guard at 5 locations)"
affects: [01-02, 02-control-and-sensors, 03-live-map]

# Tech tracking
tech-stack:
  added: [mini-racer>=0.12.0]
  patterns: ["FORK comment convention for all surgical fixes", "try/except ValueError guard for enum lookups"]

key-files:
  created: []
  modified:
    - custom_components/dreame_mower/manifest.json
    - custom_components/dreame_mower/dreame/map.py
    - custom_components/dreame_mower/dreame/device.py
    - custom_components/dreame_mower/config_flow.py
    - custom_components/dreame_mower/camera.py
    - custom_components/dreame_mower/dreame/protocol.py

key-decisions:
  - "Pin all dependency versions with >= floors rather than exact pins for HA compatibility"
  - "Store unknown property values in self.data[did] for future reference instead of dropping silently"
  - "Use model_map.get() with device model string as fallback rather than 'Unknown'"

patterns-established:
  - "FORK comment: Every change to upstream code marked with # FORK: Fix #NN / REQ-ID - description"
  - "Pre-validate enum lookups: try/except ValueError before using enum value in multiple places"

requirements-completed: [FOUND-01, FOUND-02, FOUND-03, FOUND-04, CONN-04, CLEAN-02]

# Metrics
duration: 3min
completed: 2026-03-14
---

# Phase 1 Plan 1: Fix Blocking Bugs Summary

**7 surgical fixes to manifest, imports, crash handlers, deprecation, and type guards making dreame-mower installable and crash-free on modern HA**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-14T15:50:40Z
- **Completed:** 2026-03-14T15:53:58Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Replaced dead py-mini-racer with mini-racer and pinned all 8 manifest dependencies
- Fixed 5 distinct crash/error bugs across device.py, config_flow.py, camera.py, map.py
- Verified paho-mqtt v2.0 compatibility already handled; documented with FORK comment
- Every change marked with FORK comment for traceability back to upstream

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix manifest.json and map.py import** - `9f13180` (fix)
2. **Task 2: Apply 5 surgical bug fixes** - `7b452d6` (fix)

## Files Created/Modified
- `manifest.json` - Pinned 8 deps, replaced py-mini-racer, valid semver, updated codeowners/URLs
- `dreame/map.py` - Fixed import to mini_racer; added isinstance(result, dict) guard at 5 locations
- `dreame/device.py` - try/except ValueError for unknown property IDs from Mova 600 Plus
- `config_flow.py` - Removed deprecated OptionsFlow __init__; model_map.get() safety
- `camera.py` - Set _webrtc_provider = None before super().__init__()
- `dreame/protocol.py` - FORK comment confirming paho-mqtt v2.0 VERSION1 compatibility

## Decisions Made
- Pinned dependencies with >= floors (not exact pins) for maximum HA compatibility
- Unknown property values stored in self.data[did] for future debugging, not silently dropped
- model_map fallback uses the raw device model string (informative) rather than generic "Unknown"

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Integration should now install cleanly on HA 2025.x+
- Ready for 01-02: live device pairing with Mova 600 Plus via config flow
- HA restart required before pairing to load the fixed integration

## Self-Check: PASSED

- All 6 modified files exist on disk
- Commit 9f13180 (Task 1) found in git log
- Commit 7b452d6 (Task 2) found in git log
- SUMMARY.md created successfully

---
*Phase: 01-stabilize-and-connect*
*Completed: 2026-03-14*
