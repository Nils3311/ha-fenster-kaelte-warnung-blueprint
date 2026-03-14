---
phase: 1
slug: stabilize-and-connect
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-14
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x with pytest-homeassistant-custom-component |
| **Config file** | `tests/conftest.py` (Wave 0 creates) |
| **Quick run command** | `cd /Volumes/config/custom_components/dreame_mower_repo && python -m pytest tests/ -x -q` |
| **Full suite command** | `cd /Volumes/config/custom_components/dreame_mower_repo && python -m pytest tests/ -v` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run quick test command
- **After every plan wave:** Run full suite command
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 0 | FOUND-01 | unit | `pytest tests/test_manifest.py` | ❌ W0 | ⬜ pending |
| 01-01-02 | 01 | 1 | FOUND-02 | unit | `pytest tests/test_manifest.py` | ❌ W0 | ⬜ pending |
| 01-01-03 | 01 | 1 | FOUND-03 | unit | `pytest tests/test_manifest.py` | ❌ W0 | ⬜ pending |
| 01-01-04 | 01 | 1 | FOUND-04 | unit | `pytest tests/test_protocol.py` | ❌ W0 | ⬜ pending |
| 01-02-01 | 02 | 1 | CONN-04 | unit | `pytest tests/test_device.py` | ❌ W0 | ⬜ pending |
| 01-02-02 | 02 | 1 | CLEAN-02 | unit | `pytest tests/test_config_flow.py` | ❌ W0 | ⬜ pending |
| 01-02-03 | 02 | 2 | CONN-01..03 | manual | HA config flow test | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/__init__.py` — test package init
- [ ] `tests/conftest.py` — shared fixtures (mock HA, mock device)
- [ ] `tests/test_manifest.py` — manifest validation stubs
- [ ] `tests/test_protocol.py` — protocol compatibility stubs
- [ ] `tests/test_device.py` — device property handling stubs
- [ ] `tests/test_config_flow.py` — config flow stubs
- [ ] `pytest` + `pytest-homeassistant-custom-component` — install if not present

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Config flow UI works with MOVAhome credentials | CONN-01 | Requires live HA + cloud API | 1. Go to Settings > Integrations > Add 2. Search "Dreame Mower" 3. Enter MOVAhome credentials 4. Verify device appears |
| Mova 600 Plus discovered and paired | CONN-02 | Requires real device on network | 1. Complete config flow 2. Check device info for model ID 3. Verify entity creation |
| Stable MQTT connection maintained | CONN-03 | Requires sustained cloud connection | 1. Add integration 2. Wait 30+ minutes 3. Check logs for disconnection errors |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
