---
phase: 02-control-and-sensors
plan: 01
subsystem: mower-controls
tags: [lawn-mower, state-mapping, binary-sensor, connectivity, dock-fix]

# Dependency graph
requires:
  - phase: 01-stabilize-and-connect
    provides: Working integration that installs and connects to cloud
provides:
  - Correct RETURNING state mapping in lawn_mower entity
  - Safe stop-before-dock behavior preventing schedule breakage
  - Connectivity binary sensor (device_connected)
  - Cleaned vacuum references from lawn_mower.py
affects: [02-02-PLAN, 03-live-map]

# Tech tracking
tech-stack:
  added: []
  patterns: [stop-before-dock for clean session termination, binary sensor from device property]

key-files:
  created:
    - custom_components/dreame_mower/binary_sensor.py
  modified:
    - custom_components/dreame_mower/lawn_mower.py
    - custom_components/dreame_mower/__init__.py

key-decisions:
  - "Stop-before-dock calls device.stop() then device.dock() to mark session COMPLETED and prevent cloud schedule breakage"
  - "Connectivity binary sensor reads device_connected (protocol.connected) rather than a Dreame property"

patterns-established:
  - "Binary sensor pattern: DreameMowerBinarySensorEntityDescription with value_fn lambda for device-level properties"
  - "FORK comment convention for all mower-specific changes (FORK: CTRL-03, SENS-02, SENS-04, CLEAN-01)"

requirements-completed: [CTRL-01, CTRL-02, CTRL-03, SENS-02, SENS-04]

# Metrics
duration: 3min
completed: 2026-03-14
---

# Phase 2 Plan 1: Mower Controls and Connectivity Summary

**Fixed RETURNING state mapping, stop-before-dock to prevent schedule breakage, connectivity binary sensor, and vacuum code cleanup in lawn_mower.py**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-14T16:54:06Z
- **Completed:** 2026-03-14T16:57:36Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- RETURNING state now correctly shows as LawnMowerActivity.RETURNING instead of MOWING
- Dock command calls stop() first when mowing to mark session COMPLETED, preventing cloud schedule breakage (Fix #35)
- Connectivity binary sensor exposes cloud connection status as a diagnostic entity
- Removed vacuum-only imports, voice pack service, fan speed dead code, and vacuum consumable reset entries

## Task Commits

Each task was committed atomically:

1. **Task 1: Fix state mapping, dock behavior, and clean vacuum refs** - `e32d70d` (feat)
2. **Task 2: Create connectivity binary sensor and register platform** - `89e73c6` (feat)

## Files Created/Modified
- `custom_components/dreame_mower/lawn_mower.py` - Fixed RETURNING mapping, stop-before-dock, removed vacuum refs
- `custom_components/dreame_mower/binary_sensor.py` - New connectivity binary sensor entity
- `custom_components/dreame_mower/__init__.py` - Added Platform.BINARY_SENSOR to PLATFORMS

## Decisions Made
- Stop-before-dock pattern: calling stop() sets DreameMowerTaskStatus.COMPLETED which tells the cloud the session ended cleanly, then dock() sends the physical return command
- Connectivity binary sensor uses device.device_connected (reads protocol.connected) with no property_key, relying on the default exists_fn allowing property_key=None entities

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Verification assertion for SERVICE_INSTALL_VOICE_PACK checked comments too -- adjusted comment wording to avoid false positive. Trivial, no impact.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- lawn_mower.py controls are correct and clean, ready for 02-02 entity description cleanup
- binary_sensor.py pattern established for future binary sensors
- Platform.BINARY_SENSOR registered, will be discovered by HA on next restart

## Self-Check: PASSED

- [x] binary_sensor.py exists in live directory
- [x] binary_sensor.py exists in git repo
- [x] 02-01-SUMMARY.md exists
- [x] Commit e32d70d (Task 1) exists
- [x] Commit 89e73c6 (Task 2) exists

---
*Phase: 02-control-and-sensors*
*Completed: 2026-03-14*
