---
phase: 1
slug: stabilize-and-connect
status: approved
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-14
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Ad-hoc `python3 -c` inline assertions (no pytest — this is a fork of an alpha integration; full test infrastructure is overkill for Phase 1 surgical fixes) |
| **Quick run command** | Inline `python3 -c` assertions in each task's `<automated>` verify block |
| **Full suite command** | N/A — each plan's `<verification>` section runs a comprehensive post-task check |
| **Estimated runtime** | ~2 seconds per verify block |

**Rationale:** Phase 1 applies 7 surgical fixes to a forked alpha integration. The fixes are verified by asserting file contents (presence of guard clauses, correct imports, removed deprecated code). pytest-homeassistant-custom-component would require mocking the entire Dreame cloud protocol stack for minimal additional confidence. The live device pairing in Plan 02 provides the real integration test.

---

## Wave 0 Requirements

None. Ad-hoc `python3 -c` verification requires no test infrastructure setup. Each task's `<automated>` verify command is self-contained.

---

## Sampling Rate

- **After every task commit:** Run the task's `<automated>` verify command
- **After every plan completes:** Run the plan's `<verification>` section comprehensive check
- **Before `/gsd:verify-work`:** All plan verification sections must pass
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Requirement | Verify Method | Automated Command | Status |
|---------|------|-------------|---------------|-------------------|--------|
| 01-01-T1 | 01 | FOUND-01, FOUND-02, FOUND-03 | file-content assertion | `python3 -c "import json; m=json.load(...);"` — checks version pins, mini-racer, semver | pending |
| 01-01-T2 | 01 | CONN-04, CLEAN-02, FOUND-04 | file-content assertion | `python3 -c "import ast; ..."` — checks ValueError handler, model_map.get, _webrtc_provider, isinstance checks, FORK comment in protocol.py | pending |
| 01-02-T1 | 02 | (prep for CONN-01..03) | file-content assertion | `python3 -c "..."` — checks FORK pairing comment present in __init__.py | pending |
| 01-02-T2 | 02 | CONN-01, CONN-02, CONN-03 | human checkpoint | Live config flow pairing with Mova 600 Plus device | pending |

*Status: pending / green / red / flaky*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Config flow UI works with MOVAhome credentials | CONN-01 | Requires live HA + cloud API | 1. Go to Settings > Integrations > Add 2. Search "Dreame Mower" 3. Enter MOVAhome credentials 4. Verify device appears |
| Mova 600 Plus discovered and paired | CONN-02 | Requires real device on network | 1. Complete config flow 2. Check device info for model ID 3. Verify entity creation |
| Stable MQTT connection maintained | CONN-03 | Requires sustained cloud connection | 1. Add integration 2. Wait 10+ minutes 3. Check logs for disconnection errors |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify commands (inline python3 -c assertions)
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 not needed — ad-hoc verification is self-contained
- [x] No watch-mode flags
- [x] Feedback latency < 15s (estimated ~2s per verify)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved