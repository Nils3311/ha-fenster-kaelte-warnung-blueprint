---
phase: 2
slug: control-and-sensors
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-14
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Ad-hoc `python3 -c` inline assertions + live HA entity state checks via MCP |
| **Quick run command** | Inline `python3 -c` assertions per task |
| **Full suite command** | MCP `ha_search_entities` + `ha_get_state` to verify entities exist and have correct states |
| **Estimated runtime** | ~5 seconds per verify block |

**Rationale:** Phase 2 modifies entity definitions and prunes vacuum code. Verification is best done by asserting file contents (entity descriptions present/absent) and checking live HA entity states via MCP after restart.

---

## Wave 0 Requirements

None. Ad-hoc verification is self-contained.

---

## Sampling Rate

- **After every task commit:** Run the task's `<automated>` verify command
- **After every plan completes:** Verify via MCP that expected entities exist in HA
- **Before `/gsd:verify-work`:** All entities must be present with correct states
- **Max feedback latency:** 5 seconds

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Start mowing from HA | CTRL-01 | Requires physical mower + lawn | Call lawn_mower.start_mowing, verify mower starts |
| Pause mowing from HA | CTRL-02 | Requires active mowing session | Call lawn_mower.pause, verify mower pauses |
| Dock without breaking schedules | CTRL-03 | Requires active session + schedule check | Call lawn_mower.dock, verify schedule intact in MOVAhome app |
| Mowing progress updates live | SENS-05 | Requires active mowing session | Start mowing, watch progress sensor update |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify commands
- [x] Sampling continuity maintained
- [x] Wave 0 not needed
- [x] No watch-mode flags
- [x] Feedback latency < 15s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved
