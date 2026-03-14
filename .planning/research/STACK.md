# Technology Stack

**Project:** Mova 600 Plus -- Home Assistant Integration
**Researched:** 2026-03-14
**Mode:** Brownfield (forking bhuebschen/dreame-mower v0.0.5-alpha)

## Executive Summary

The upstream fork (bhuebschen/dreame-mower) has **two critical dependency problems** that must be fixed immediately: it uses `py-mini-racer` (abandoned since 2021, Python 2 era) instead of `mini-racer` (actively maintained, already adopted by Tasshack/dreame-vacuum v1.0.8), and it pins no versions in `manifest.json` -- risking breakage on any dependency update. The rest of the stack (Pillow for map PNG rendering, paho-mqtt for cloud MQTT, pycryptodome for Dreame protocol encryption) is sound and aligns with what HA Core bundles. No version pins in the manifest means HA installs whatever is current, which today happens to work but could break silently.

## Recommended Stack

### Core Platform

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| Home Assistant Core | >=2025.1.0 | Runtime platform | lawn_mower entity stable since 2023.6; setting floor at 2025.1 ensures modern config_flow, DataUpdateCoordinator, and Python 3.12+ | HIGH |
| Python | 3.12--3.14 | Language runtime | HA 2026.3 runs on Python 3.14; upstream code uses no syntax beyond 3.12 | HIGH |

### Integration Dependencies (manifest.json requirements)

These are installed by HA when the integration loads. **Use version pins** -- the upstream has none, which is a bug.

| Library | Pin | Purpose | Why This Version | Confidence |
|---------|-----|---------|------------------|------------|
| `pillow` | >=12.0.0 | Map PNG rendering (PIL.Image, PIL.ImageDraw) | HA Core bundles 12.1.1; floor at 12.0.0 avoids conflict. Map.py uses Image.new(), ImageDraw, putpixel, resize, paste -- all stable PIL APIs | HIGH |
| `numpy` | >=2.0.0 | Map data array processing | HA Core constraints pin 2.3.2; floor at 2.0 is safe. Used in map.py for pixel buffer manipulation and coordinate transforms | HIGH |
| `paho-mqtt` | >=2.0.0 | Dreame/MOVAhome cloud MQTT protocol | **Breaking change**: v2.0 requires `callback_api_version` parameter on `mqtt.Client()`. HA Core constraints pin 2.1.0. The upstream dreame-mower code must be audited for v2.0 callback compatibility | HIGH |
| `pycryptodome` | >=3.20.0 | AES encryption for Dreame cloud protocol | HA Core allows >=3.6.6; pin higher for security fixes. Used in protocol.py for AES-CBC and MD5 hashing | HIGH |
| `python-miio` | >=0.5.12 | Xiaomi device discovery and local communication | Legacy but still functional for miIO protocol handshake. Project is inactive (no release in 12+ months) but Dreame protocol.py depends on it for device token handling. No replacement available for this specific use case | MEDIUM |
| `mini-racer` | >=0.12.0 | V8 JavaScript engine for Dreame cloud API auth | **CRITICAL FIX**: upstream uses `py-mini-racer` which is DEAD (last release 0.6.0, April 2021, Python 2 era). Tasshack/dreame-vacuum already migrated to `mini-racer`. Import path changes from `py_mini_racer` to `mini_racer` | HIGH |
| `pybase64` | >=1.4.0 | Fast base64 encoding for map data | Performance-optimized base64 for large map payloads. Standard library `base64` would work but pybase64 is faster for the 100KB+ map buffers | MEDIUM |
| `requests` | >=2.31.0 | HTTP client for Dreame cloud API | HA Core bundles 2.32.5. Used in protocol.py for cloud authentication endpoints. Could be replaced with aiohttp long-term but not worth the churn now | HIGH |

### Development Tools

| Tool | Version | Purpose | Why |
|------|---------|---------|-----|
| `ruff` | >=0.15.0 | Linting + formatting | HA Core uses ruff. Replaces flake8+black+isort. Runs in <200ms on this codebase | HIGH |
| `pytest` | >=8.0.0 | Test runner | Standard for HA integrations | HIGH |
| `pytest-homeassistant-custom-component` | >=0.13.300 | HA test fixtures | Tracks HA core daily; provides `hass` fixture, `MockConfigEntry`, async test helpers. Version 0.13.317 targets HA 2026.3.1 | HIGH |
| `pytest-asyncio` | >=0.23.0 | Async test support | Required for testing HA async patterns (async_setup_entry, DataUpdateCoordinator) | HIGH |
| `pytest-cov` | >=5.0.0 | Coverage reporting | Track test coverage for map.py (415KB) and protocol.py (33KB) -- the most complex files | MEDIUM |

### CI/CD (GitHub Actions)

| Action | Usage | Purpose |
|--------|-------|---------|
| `home-assistant/actions/hassfest@master` | Push, PR, nightly | Validates manifest.json, ensures HA compatibility |
| `hacs/action@main` | Push, PR, nightly | Validates HACS compliance (structure, brands, hacs.json) |
| `astral-sh/ruff-action@v3` | Push, PR | Lint and format check |
| `actions/checkout@v4` | All workflows | Standard checkout |

## Critical Fixes Required in Fork

### 1. Replace `py-mini-racer` with `mini-racer` (P0)

**What:** `py-mini-racer` 0.6.0 was last released April 2021. It does not support Python 3.12+. The successor `mini-racer` (0.14.1, Feb 2026) is actively maintained with V8 12.6.

**Where to change:**
- `manifest.json`: `"py-mini-racer"` -> `"mini-racer>=0.12.0"`
- All Python imports: `from py_mini_racer import MiniRacer` -> `from mini_racer import MiniRacer`
- Verify in `protocol.py` or wherever V8 is used for cloud auth JavaScript execution

**Evidence:** Tasshack/dreame-vacuum v1.0.8 manifest already uses `mini-racer` (verified via GitHub raw content).

### 2. Add Version Pins to manifest.json (P0)

**What:** The current manifest lists bare package names with no version constraints. This means HA will install whatever pip resolves, which could be a breaking version.

**Fix:** Add minimum version floors as specified in the table above.

### 3. Audit paho-mqtt v2.0 Callback API (P1)

**What:** paho-mqtt 2.0 (Feb 2024) requires `callback_api_version=CallbackAPIVersion.VERSION2` in `mqtt.Client()` constructor. Old-style callbacks still work with `VERSION1` but emit deprecation warnings. HA Core already runs 2.1.0.

**Where:** `protocol.py` -- check all `mqtt.Client()` instantiations and callback registrations (`on_connect`, `on_message`, `on_disconnect`).

### 4. Update hacs.json Minimum HA Version (P2)

**What:** Current `hacs.json` specifies `"homeassistant": "2023.6.0"`. Should be updated to `"2025.1.0"` to align with the actual minimum version we support and test against.

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| JS Engine | `mini-racer` | `py-mini-racer` | Dead project, last release 2021, no Python 3.12+ support |
| JS Engine | `mini-racer` | `js2py` | Slower, incomplete ES6+ support, security concerns with arbitrary JS execution |
| MQTT | `paho-mqtt` | `asyncio-mqtt` / `aiomqtt` | Upstream protocol.py is built around paho's threading model; migration would be a rewrite. paho-mqtt 2.1.0 is stable and HA-blessed |
| HTTP | `requests` (keep) | `aiohttp` | Would be better (async, HA already bundles it) but protocol.py uses requests throughout; not worth the rewrite risk for v1 |
| Image | `pillow` | `opencv-python` | Massive dependency (100MB+), overkill for 2D map rendering. Pillow handles everything map.py needs |
| Base64 | `pybase64` | stdlib `base64` | pybase64 is 2-10x faster for the large map payloads; already a dependency in upstream |
| Crypto | `pycryptodome` | `cryptography` | Both work. pycryptodome is what upstream uses and provides the AES-CBC primitives directly. `cryptography` is HA core's choice but would require rewriting protocol.py |
| Miio | `python-miio` | Direct miIO implementation | python-miio handles device token exchange and miIO protocol framing. Writing our own would be 500+ lines for no benefit |
| Linting | `ruff` | `flake8` + `black` + `isort` | ruff does all three 100x faster. HA Core standard |
| Testing | `pytest-homeassistant-custom-component` | Plain pytest | Lose HA fixtures (`hass`, `MockConfigEntry`, entity registry helpers). Not worth it |

## What NOT to Use

| Technology | Why Avoid |
|------------|-----------|
| `py-mini-racer` | **Dead.** Last release April 2021. No Python 3.12+ wheels. Will fail to install on modern HA |
| `opencv-python` (cv2) | Bloated (100MB+), hard to build on ARM/HA OS, unnecessary for 2D map rendering |
| `asyncio-mqtt` / `aiomqtt` | Would require rewriting protocol.py's threading model. Not worth the risk for a fork |
| `mypy` (for type checking) | Upstream has no type annotations in 415KB map.py. Adding mypy would block all progress. Use ruff's type-checking rules instead |
| `black` / `flake8` / `isort` (separately) | Replaced by ruff. Slower, more config, fragmented |
| `tox` | Overkill for a single-HA-version custom integration. pytest + GitHub Actions is sufficient |

## manifest.json (Target)

```json
{
  "domain": "dreame_mower",
  "name": "Dreame Mower",
  "codeowners": ["@YOUR_GITHUB_USERNAME"],
  "config_flow": true,
  "documentation": "https://github.com/YOUR_USERNAME/dreame-mower",
  "iot_class": "cloud_polling",
  "issue_tracker": "https://github.com/YOUR_USERNAME/dreame-mower/issues",
  "requirements": [
    "pillow>=12.0.0",
    "numpy>=2.0.0",
    "pybase64>=1.4.0",
    "requests>=2.31.0",
    "pycryptodome>=3.20.0",
    "python-miio>=0.5.12",
    "mini-racer>=0.12.0",
    "paho-mqtt>=2.0.0"
  ],
  "version": "0.1.0"
}
```

## hacs.json (Target)

```json
{
  "name": "Dreame Mower",
  "homeassistant": "2025.1.0",
  "render_readme": true,
  "zip_release": true,
  "filename": "dreame_mower.zip"
}
```

## GitHub Actions Workflows

### .github/workflows/validate.yml

```yaml
name: Validate
on:
  push:
  pull_request:
  schedule:
    - cron: "0 0 * * *"
  workflow_dispatch:

permissions: {}

jobs:
  hassfest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: home-assistant/actions/hassfest@master

  hacs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: hacs/action@main
        with:
          category: integration

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/ruff-action@v3
```

## Installation (Development)

```bash
# Clone fork into custom_components
cd /Volumes/config/custom_components/
git clone https://github.com/YOUR_USERNAME/dreame-mower.git dreame_mower_dev

# Dev dependencies (on development machine, not HA)
pip install -e ".[dev]"
# Or individually:
pip install ruff pytest pytest-homeassistant-custom-component pytest-asyncio pytest-cov

# Run linting
ruff check custom_components/dreame_mower/
ruff format --check custom_components/dreame_mower/

# Run tests
pytest tests/ -v --cov=custom_components/dreame_mower
```

## Key HA Platform APIs Used

| Platform | Base Class | Key Methods |
|----------|-----------|-------------|
| `lawn_mower` | `LawnMowerEntity` | `async_start_mowing()`, `async_pause()`, `async_dock()`, `activity` property |
| `camera` | `Camera` | `async_camera_image(width, height) -> bytes` -- returns PNG bytes from Pillow |
| `sensor` | `SensorEntity` | `native_value`, `native_unit_of_measurement` -- battery, blade wear, area, progress |
| `config_flow` | `ConfigFlow` | `async_step_user()` -- cloud auth setup with Dreame account |
| coordinator | `DataUpdateCoordinator` | `_async_update_data()` -- polls Dreame cloud for device state |

## Dependency Risk Assessment

| Dependency | Risk | Mitigation |
|------------|------|------------|
| `python-miio` | HIGH -- inactive project, no releases in 12+ months | Pin working version. If it breaks, the miIO protocol handshake code is small enough to inline |
| `mini-racer` | MEDIUM -- V8 engine binary, platform-specific wheels | Verify ARM64 (HA OS on RPi) wheel availability. Fallback: cloud auth may work without JS eval on newer Dreame API versions |
| `paho-mqtt` | LOW -- stable, HA-blessed, v2.1.0 proven | Audit callback API version on fork |
| `pillow` | LOW -- HA Core dependency, always available | Floor version only, never ceiling |
| `numpy` | LOW -- HA Core constraints ensure compatible version | Floor version only |
| `pycryptodome` | LOW -- stable, mature, no breaking changes planned | Floor version for security fixes |

## Sources

- [HA Integration Manifest Docs](https://developers.home-assistant.io/docs/creating_integration_manifest/) -- manifest.json specification (HIGH confidence)
- [HA Camera Entity Docs](https://developers.home-assistant.io/docs/core/entity/camera/) -- camera platform API (HIGH confidence)
- [HA Lawn Mower Entity Docs](https://developers.home-assistant.io/docs/core/entity/lawn-mower/) -- lawn_mower platform API (HIGH confidence)
- [Tasshack/dreame-vacuum manifest.json](https://github.com/Tasshack/dreame-vacuum) -- verified mini-racer migration (HIGH confidence)
- [bhuebschen/dreame-mower manifest.json](https://github.com/bhuebschen/dreame-mower) -- verified py-mini-racer still in use (HIGH confidence)
- [HA Core package_constraints.txt](https://github.com/home-assistant/core/blob/dev/homeassistant/package_constraints.txt) -- bundled library versions (HIGH confidence)
- [paho-mqtt migration docs](https://eclipse.dev/paho/files/paho.mqtt.python/html/migrations.html) -- v2.0 breaking changes (HIGH confidence)
- [py-mini-racer on PyPI](https://pypi.org/project/py-mini-racer/) -- last release 0.6.0, April 2021 (HIGH confidence)
- [mini-racer on PyPI](https://pypi.org/project/mini-racer/) -- v0.14.1, Feb 2026 (HIGH confidence)
- [HACS Publishing Requirements](https://www.hacs.xyz/docs/publish/integration/) -- HACS validation checklist (HIGH confidence)
- [HACS GitHub Action](https://www.hacs.xyz/docs/publish/action/) -- CI validation (HIGH confidence)
- [pytest-homeassistant-custom-component](https://github.com/MatthewFlamm/pytest-homeassistant-custom-component) -- v0.13.317 targeting HA 2026.3.1 (HIGH confidence)
- [Ruff](https://docs.astral.sh/ruff/) -- v0.15.x, HA Core standard linter (HIGH confidence)
- [python-miio](https://github.com/rytilahti/python-miio) -- inactive, last significant release 0.5.12 (MEDIUM confidence on future viability)
- [HA 2026.3 Release](https://www.home-assistant.io/blog/2026/03/04/release-20263/) -- current HA version, Python 3.14 support (HIGH confidence)
