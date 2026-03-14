# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-14)

**Core value:** Users can see their Mova 600 Plus on a live map in Home Assistant and control it with reliable status feedback.
**Current focus:** Phase 2: Control and Sensors

## Current Position

Phase: 2 of 3 (Control and Sensors)
Plan: 2 of 2 in current phase (awaiting checkpoint)
Status: Checkpoint -- awaiting HA restart and entity verification
Last activity: 2026-03-14 -- Completed 02-02 Tasks 1-2 (Vacuum Entity Cleanup), Task 3 checkpoint pending

Progress: [██████░░░░] 55%

## Performance Metrics

**Velocity:**
- Total plans completed: 3.5 (01-02 partial, 02-02 checkpoint pending)
- Average duration: 3 min
- Total execution time: 0.18 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-stabilize-and-connect | 1/2 | 3 min | 3 min |
| 02-control-and-sensors | 2/2 | 7 min | 3.5 min |

**Recent Trend:**
- Last 5 plans: 01-01 (3 min), 01-02 (1 min, partial), 02-01 (3 min), 02-02 (4 min)
- Trend: consistent

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Roadmap]: Coarse granularity -- 3 phases merging bug fixes + device validation into Phase 1, control + sensors into Phase 2, live map as Phase 3
- [Roadmap]: Map bug fixes (#39, #42) assigned to Phase 1 (stabilize) even though map feature is Phase 3, because they are crash-prevention fixes not feature work
- [01-01]: Pin dependencies with >= floors (not exact pins) for maximum HA compatibility
- [01-01]: Store unknown property values in self.data[did] for future debugging reference
- [01-01]: Use raw device model string as model_map fallback rather than generic "Unknown"
- [01-02]: Task 2 (live pairing) deferred as pending checkpoint -- requires user to restart HA and complete config flow UI
- [02-01]: Stop-before-dock calls device.stop() then device.dock() to mark session COMPLETED and prevent cloud schedule breakage
- [02-01]: Connectivity binary sensor reads device_connected (protocol.connected) rather than a Dreame property
- [02-02]: Remove vacuum descriptions entirely rather than guarding with exists_fn -- mower hardware never has these properties
- [02-02]: Keep DreameMowerAIProperty import since AI_OBSTACLE_DETECTION (LiDAR) is valid for mowers

### Pending Todos

None yet.

### Blockers/Concerns

- Mova 600 Plus model ID unknown until device pairing (Phase 1 must discover empirically)
- ARM64 mini-racer wheel availability unverified (may affect HA OS on RPi)
- paho-mqtt v2.0 callback API audit needed in protocol.py (Phase 1 scope)

## Session Continuity

Last session: 2026-03-14
Stopped at: 02-02-PLAN.md Task 3 checkpoint (awaiting HA restart and entity verification)
Resume file: .planning/phases/02-control-and-sensors/02-02-SUMMARY.md
Next action: User restarts HA, verifies entities, then Phase 2 complete -- proceed to Phase 3
