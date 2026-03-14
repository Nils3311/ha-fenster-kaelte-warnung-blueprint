---
phase: 02-control-and-sensors
plan: 02
subsystem: integration
tags: [dreame-mower, entity-cleanup, sensor, button, switch, select, consumable]

# Dependency graph
requires:
  - phase: 02-control-and-sensors/01
    provides: "Fixed lawn_mower controls, connectivity binary sensor, vacuum service cleanup"
provides:
  - "Clean entity platform files with only mower-relevant descriptions"
  - "Coordinator checking only blade consumable"
  - "Const.py without vacuum constants"
affects: [03-live-map]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "FORK: CLEAN-01 comment markers on all pruned sections for traceability"

key-files:
  created: []
  modified:
    - "custom_components/dreame_mower/sensor.py"
    - "custom_components/dreame_mower/button.py"
    - "custom_components/dreame_mower/switch.py"
    - "custom_components/dreame_mower/select.py"
    - "custom_components/dreame_mower/coordinator.py"
    - "custom_components/dreame_mower/const.py"

key-decisions:
  - "Remove all 15 vacuum sensor descriptions rather than guarding with exists_fn -- cleaner codebase since mower will never have these properties"
  - "Remove DreameMowerStrAIProperty import from switch.py since only user was AI_HUMAN_DETECTION (removed)"
  - "Remove floor material imports and icon dicts from select.py since both segment selects using them were removed"

patterns-established:
  - "FORK: CLEAN-01 comment pattern marks all vacuum-to-mower pruning for future upstream comparison"

requirements-completed: [SENS-01, SENS-03, SENS-05, SENS-06, SENS-07, SENS-08, CLEAN-01]

# Metrics
duration: 4min
completed: 2026-03-14
---

# Phase 2 Plan 02: Vacuum Entity Cleanup Summary

**Removed 36 vacuum-only entity descriptions, 7 consumable checks, and 18 constants from 6 files -- only mower-relevant entities remain**

## Performance

- **Duration:** 4 min
- **Started:** 2026-03-14T17:01:22Z
- **Completed:** 2026-03-14T17:05:35Z
- **Tasks:** 2 completed, 1 pending checkpoint
- **Files modified:** 6

## Accomplishments
- Removed 15 vacuum sensor descriptions (side brush, filter, tank filter, silver ion, lensbrush, squeegee, sensor dirty, stream status) from sensor.py
- Removed 6 vacuum reset buttons, 13 camera/vacuum switches, 2 floor material segment selects from button/switch/select.py
- Pruned coordinator.py to only check blade consumable (removed 6 vacuum consumable checks)
- Cleaned const.py of 7 vacuum consumable constants, 7 vacuum notification IDs, and 4 fan speed constants
- Cross-file import consistency verified: no file references any removed symbol

## Task Commits

Each task was committed atomically:

1. **Task 1: Remove vacuum entity descriptions from sensor.py, button.py, switch.py, select.py** - `1aa7406` (feat)
2. **Task 2: Prune vacuum consumable checks from coordinator.py and constants from const.py** - `027cedb` (feat)
3. **Task 3: Verify all Phase 2 entities in Home Assistant** - PENDING (checkpoint:human-verify)

## Files Created/Modified
- `sensor.py` - Removed 15 vacuum sensor descriptions, kept battery/state/error/progress/blades/etc.
- `button.py` - Removed 6 vacuum reset buttons, kept RESET_BLADES/CLEAR_WARNING/mapping buttons
- `switch.py` - Removed 13 camera/vacuum switches (AI image, pet detection, stain avoidance, etc.)
- `select.py` - Removed 2 floor material segment selects and associated imports/dicts
- `coordinator.py` - _check_consumables only checks BLADES, removed 12 vacuum imports from const
- `const.py` - Removed 7 consumable constants, 7 notification IDs, 4 fan speed constants

## Decisions Made
- Removed descriptions entirely rather than guarding with exists_fn -- mower hardware never has these properties
- Kept DreameMowerAIProperty import in switch.py because AI_OBSTACLE_DETECTION (LiDAR-based) is a valid mower feature
- Removed DreameMowerStrAIProperty import since its only user (AI_HUMAN_DETECTION) was removed

## Deviations from Plan
None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required. User must restart HA to see entity changes (Task 3 checkpoint).

## Next Phase Readiness
- All Phase 2 code changes complete (Plans 01 + 02)
- Awaiting HA restart and entity verification (Task 3 checkpoint)
- After verification, Phase 3 (Live Map) can begin

---
*Phase: 02-control-and-sensors*
*Completed: 2026-03-14*
