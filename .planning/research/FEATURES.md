# Feature Landscape

**Domain:** Home Assistant robotic mower integration (Dreame/Mova)
**Researched:** 2026-03-14

## Table Stakes

Features users expect from any HA mower integration. Missing = users stay on the manufacturer app.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **lawn_mower entity (start/pause/dock)** | HA's native lawn_mower platform provides these three actions; every mower integration implements them. Husqvarna, Landroid, Mammotion, Bosch Indego all expose them. | Low | Already working in upstream dreame-mower. Uses `LawnMowerEntityFeature` flags: `START_MOWING`, `PAUSE`, `DOCK`. |
| **Battery level sensor** | Universal across all mower integrations. Users need to know charge state for automations (e.g., "don't start if battery < 20%"). | Low | Upstream vacuum code already exposes battery sensors. Map to mower context. |
| **Mower state/status sensor** | Must show current activity: mowing, docked, paused, returning, charging, error. Husqvarna exposes detailed sub-states (leaving dock, searching). Landroid and Bosch Indego both expose state + detailed state. | Low | lawn_mower platform provides: MOWING, DOCKED, PAUSED, RETURNING, ERROR. Map Dreame protocol status codes to these. |
| **Error state sensor with codes** | Users need to know *why* the mower stopped: stuck, lifted, tilted, trapped, blade blocked, boundary lost. Husqvarna fires error events with severity + GPS coordinates. Landroid exposes error sensor. | Med | Dreame protocol has error codes in types.py/const.py. Must map mower-specific errors (not vacuum errors like "dust bin full"). |
| **Mowing progress/area mowed sensor** | Bosch Indego: "lawn mowed" percentage. Husqvarna: systematic mowing progress per zone. Users want to see "how done is it?" | Med | Dreame protocol reports cleaned_area and cleaning_time. Adapt from vacuum context. Need to verify Mova 600 Plus reports this. |
| **Total mowing time sensor** | Bosch Indego, Landroid both expose total work time. Useful for maintenance tracking. | Low | Already in upstream vacuum code (total cleaning time). Rename for mower context. |
| **Blade usage/wear sensor** | Husqvarna: blade usage time + reset button. Landroid: blade work time sensor. Mova 600 Plus uses replaceable blades (81-pack included). Users need maintenance reminders. | Med | Upstream vacuum tracks consumables (filter, brush). Adapt to mower consumables (blades). Verify Dreame protocol exposes blade hours for mowers. |
| **Online/connectivity sensor** | Bosch Indego: online sensor. Users need to know if cloud connection is active, especially for cloud-dependent integrations. | Low | Protocol.py handles MQTT connection state. Expose as binary_sensor. |
| **Signal strength (RSSI/WiFi)** | Landroid: RSSI sensor. Mammotion: connection type sensor. Important for debugging connectivity issues in gardens where WiFi is weak. | Low | Dreame protocol likely reports WiFi RSSI. |

## Differentiators

Features that set this integration apart. Not universally expected, but valued -- especially things the Dreame/Tasshack vacuum lineage makes possible that other mower integrations lack.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Live map via camera entity** | The killer feature inherited from Tasshack/dreame-vacuum. No other mower integration provides a live rendered map inside HA showing the mower's position and mowed area in real-time. Husqvarna only has a GPS device_tracker dot on a map. Mammotion has no map. This is a vacuum-class feature applied to mowers -- unique in the mower space. | High | map.py (415KB) renders PNG maps. Known bugs #39 (data parsing) and #42 (camera entity missing attribute). Fixing these is a prerequisite. Camera entity refreshes dynamically during mowing. |
| **Zone/area management in HA** | Mova 600 Plus supports multiple lawn zones, no-go areas, and pathways via the MOVAhome app. Exposing zone switches in HA (like Husqvarna's work area switches) lets users automate which zones get mowed. E.g., "mow front yard on Monday, back yard on Wednesday." | High | Upstream vacuum has room/segment cleaning services. Must adapt zone concepts from vacuum rooms to mower zones. Currently out of scope per PROJECT.md (v2), but this is the #1 differentiator to plan for. |
| **Cutting height control** | Mova 600 Plus: 20-60mm adjustable. Husqvarna exposes cutting height as a number entity (1-9). Very few mower integrations expose this. Allows automations like "lower cut height in summer." | Med | Need to verify if Dreame protocol exposes cutting height as a settable property. Mova 600 Plus has physical rotary dial -- may not be software-controllable. If not settable, expose as read-only sensor. LOW confidence. |
| **Mowing pattern/mode select** | Mova 600 Plus supports: standard, efficient, edge, spot, manual control, plus creative patterns (hearts, geometric). No other HA mower integration exposes mowing mode selection. | Med | Dreame protocol likely has mode properties. Upstream vacuum has cleaning mode selects. Adapt for mower modes. |
| **Schedule calendar entity** | Husqvarna is the only integration providing a native HA calendar entity for mowing schedules. Mova 600 Plus supports dual seasonal schedules via app. Exposing this in HA calendar is premium UX. | High | Husqvarna uses their API's schedule data. Would need to read Dreame schedule data from protocol and create calendar entity. Bug #35 (dock breaks schedules) must be fixed first. |
| **Schedule enable/disable switch** | Husqvarna provides a schedule switch. Simple but very useful -- "disable mowing schedule during vacation" as a single toggle. | Low | Should be straightforward if schedule data is accessible via protocol. |
| **No-go zone switches** | Husqvarna: switch per stay-out zone. Toggle zones on/off without editing the map. E.g., "deactivate the pool zone no-go area in winter." | High | Requires reading zone configuration from Dreame protocol and creating dynamic switch entities. Upstream vacuum has restricted_zone services. |
| **Mowing history/statistics** | Upstream Tasshack vacuum provides cleaning history maps. Applying this to mowers gives users session-by-session mowing history with area covered, time taken, and map snapshots. No other mower integration provides this depth. | Med | Vacuum code already has history infrastructure. Adapt rendering for mower context (green coverage instead of vacuumed paths). |
| **Device tracker entity** | Husqvarna: GPS-based device tracker (when available). Mova 600 Plus uses LiDAR positioning, not GPS, so true lat/lng isn't available. Could expose position on the map coordinate system instead. | Med | LiDAR position is relative to map, not GPS coordinates. Device tracker expects lat/lng. May need to use map-relative positioning or skip this. Not directly comparable to GPS mowers. |
| **Consumable reset buttons** | Upstream vacuum: 7+ consumable reset buttons. Mower equivalent: blade reset button (like Husqvarna). Simple maintenance UX. | Low | Upstream infrastructure exists. Filter to mower-relevant consumables only. |
| **Override schedule action** | Husqvarna: "mow for X minutes regardless of schedule" or "park for X hours overriding schedule." Powerful for ad-hoc control. | Med | Need custom service calls mapped to Dreame protocol commands. |
| **Rain delay / weather awareness** | Landroid has built-in rain sensor + delay. Mova 600 Plus is IPX6 rated but has no rain sensor. HA can fill this gap with weather integration automations -- but exposing a rain delay number entity (like Landroid) from the device side would be valuable if supported. | Low | This is better handled as HA automation using weather entities, not integration code. Only expose if Dreame protocol has native rain delay. |
| **Firmware version sensor** | Landroid exposes firmware version. Useful for tracking updates and debugging. | Low | Dreame protocol likely reports firmware version in device properties. |
| **Diagnostic sensors** | Upstream vacuum: 40+ sensors. For mowers, relevant diagnostics include: LiDAR status, wheel motor temps, total distance driven, charge cycles, collision count, orientation (yaw/roll/pitch). | Med | Cherry-pick from vacuum sensor list. Only expose what's relevant to mowers and what the Mova 600 Plus actually reports. |

## Anti-Features

Features to explicitly NOT build. Either inherited from vacuum that don't apply, or complexity traps.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Vacuum-specific consumable sensors** | Upstream code has: filter left, side brush left, main brush left, mop pad, water tank, dust bin, tank filter. None of these exist on a mower. Exposing them creates confusing ghost entities. | Strip vacuum consumables entirely. Only expose blade-related consumables. |
| **Suction level / water volume controls** | Vacuum concepts with no mower equivalent. Select entities for suction modes and water volume would be meaningless. | Remove these entity types. Replace with mower-specific controls (cutting height, mowing pattern). |
| **Mopping / carpet detection** | Carpet boost switches, no-mopping zones, mop mode selects -- all vacuum-only. | Remove entirely. No mower equivalent. |
| **Room/segment name editing** | Upstream vacuum lets you rename rooms from HA. Mower zones are typically named in the manufacturer app and rarely changed. Adding this complexity is not worth it for v1. | Read-only zone names. Editing via MOVAhome app. |
| **Multi-floor map support** | Upstream vacuum supports multiple saved floor plans. A mower has one garden. Dual map on Mova 600 Plus is for two separate areas (front/back yard), not "floors." | Support dual map as dual zone if the protocol treats them this way. Don't build floor-switching UI. |
| **Obstacle photo display** | Upstream vacuum shows photos of detected obstacles. Mova 600 Plus uses LiDAR (no camera). There are no obstacle photos to display. | Remove obstacle photo entities. LiDAR obstacle data could be shown on the map instead. |
| **Voice pack installation** | Vacuum-specific feature for voice prompts. Mowers don't talk. | Remove the `install_voice_pack` service. |
| **Remote joystick control from HA** | Upstream vacuum has `remote_control_move` service. While Mova 600 Plus supports "manual control" mode, exposing real-time joystick control through HA is latency-sensitive and cloud-dependent -- a recipe for the mower hitting something. | Leave manual control to the MOVAhome app which has direct, low-latency connection. |
| **OTA firmware updates via HA** | Firmware updates should go through manufacturer app/cloud for safety. A bad update to outdoor heavy machinery is dangerous. No mower integration provides this. Mammotion has a restart button but not OTA. | Expose firmware version as read-only sensor. Updates via MOVAhome app. |
| **Local API / non-cloud protocol** | Mova 600 Plus requires cloud protocol. Investing in reverse-engineering a local API is massive effort for uncertain gain. | Accept cloud dependency. Document it clearly. Monitor community for local protocol discoveries. |

## Feature Dependencies

```
Battery sensor ──────────────────────> lawn_mower entity (state machine needs battery info)
Error state sensor ──────────────────> lawn_mower entity (ERROR state requires error details)
Cloud protocol connection ───────────> All entities (everything depends on working MQTT)
                                       |
Map data parsing (fix #39) ──────────> Live map camera entity
Camera entity fix (#42) ─────────────> Live map camera entity
                                       |
Live map camera entity ──────────────> Zone visualization
                                       > Mowing history maps
                                       > Mowing progress overlay
                                       |
Schedule data access ────────────────> Calendar entity
Dock command fix (#35) ──────────────> Schedule enable/disable switch
                                       |
Zone data from protocol ─────────────> Zone switches
                                       > Zone-specific mowing service
                                       > No-go zone switches
```

## MVP Recommendation

Prioritize (Phase 1 -- get working):
1. **lawn_mower entity** (start/pause/dock) -- already mostly works
2. **Battery level sensor** -- basic monitoring
3. **Mower state/status sensor** -- know what it's doing
4. **Error state sensor** -- know when something's wrong
5. **Online/connectivity binary sensor** -- debug connection issues

Prioritize (Phase 2 -- essential sensors):
6. **Mowing progress sensor** (area mowed, time)
7. **Blade usage sensor + reset button**
8. **Total mowing time sensor**
9. **WiFi signal strength sensor**
10. **Firmware version sensor**

Prioritize (Phase 3 -- the differentiator):
11. **Live map camera entity** (fix bugs #39, #42) -- this is the integration's unique value
12. **Mowing history statistics**

Defer to v2:
- Zone/area management (switches, services)
- Schedule calendar entity
- Cutting height control
- Mowing pattern/mode selection
- No-go zone switches
- Override schedule actions

**Rationale:** The MVP must match what every mower integration provides (basic controls + sensors). The live map is what makes this integration worth choosing over generic MQTT setups -- prioritize fixing map bugs over adding new features. Zone management is explicitly out of scope for v1 per PROJECT.md constraints.

## Sources

- [Husqvarna Automower HA integration](https://www.home-assistant.io/integrations/husqvarna_automower/) -- gold standard official integration, MEDIUM-HIGH confidence
- [HA lawn_mower platform developer docs](https://developers.home-assistant.io/docs/core/entity/lawn-mower/) -- authoritative, HIGH confidence
- [Bosch Indego HA integration](https://github.com/sander1988/Indego) -- community integration, MEDIUM confidence
- [Landroid Cloud HA integration](https://github.com/MTrab/landroid_cloud) -- community integration, MEDIUM confidence
- [Mammotion HA integration](https://github.com/mikey0000/Mammotion-HA) -- community integration, MEDIUM confidence
- [Tasshack/dreame-vacuum](https://github.com/Tasshack/dreame-vacuum) -- upstream parent (100+ entities), HIGH confidence
- [bhuebschen/dreame-mower](https://github.com/bhuebschen/dreame-mower) -- fork base, MEDIUM confidence (alpha)
- [Dreame/Mova mower community thread](https://community.home-assistant.io/t/dreame-a1-a1-pro-a2-mova-600-1000-integration/749593) -- user reports, MEDIUM confidence
- [Mova 600 review](https://basic-tutorials.com/reviews/gadget-reviews/mova-600/) -- device capabilities, HIGH confidence
- [Lawn Mower Card](https://github.com/cociweb/lawn-mower-card) -- dashboard card compatibility, MEDIUM confidence
- [Husqvarna Automower community thread](https://community.home-assistant.io/t/husqvarna-automower-integration/778547) -- reference integration patterns, MEDIUM confidence
