# Home Assistant Security System Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement automated security system for Home Assistant with presence-based arming, multiple security modes, and camera integration.

**Architecture:** Manual Alarm Control Panel with template-based presence detection, automated mode switching via time/presence triggers, progressive notification system, and centralized alarm actions via scripts. Designed for single-person use with easy expansion for second person.

**Tech Stack:** Home Assistant Core, Manual Alarm Control Panel integration, Jinja2 templates, Reolink camera integration, Sonos media player, YAML automations/scripts

---

## Task 1: Create Light Security Group

**Files:**
- Verify: Check existing lights via MCP
- Create: Light group via `ha_call_service`

**Step 1: Verify existing light entities**

Use MCP to confirm available lights:
```python
ha_search_entities(query="", domain_filter="light")
```

Expected entities:
- `light.aussenlicht`
- `light.hwr_deckenlampe`

**Step 2: Create security lights group**

```python
ha_call_service(
    domain="group",
    service="set",
    data={
        "object_id": "security_lights",
        "name": "Security Lights",
        "entities": [
            "light.aussenlicht",
            "light.hwr_deckenlampe"
        ]
    }
)
```

**Step 3: Verify group creation**

```python
ha_get_state(entity_id="group.security_lights")
```

Expected: State object with entity_id "group.security_lights", members listed in attributes

**Step 4: Test group control**

```python
ha_call_service(domain="light", service="turn_on", entity_id="group.security_lights")
```

Expected: Both lights turn on

```python
ha_call_service(domain="light", service="turn_off", entity_id="group.security_lights")
```

Expected: Both lights turn off

**Step 5: Document group for future expansion**

Note: User can add more lights to this group as they install them. Group will automatically control all member lights.

---

## Task 2: Create Anyone Home Template Sensor

**Files:**
- Create: Template binary sensor configuration via MCP

**Step 1: Verify iPhone presence entity**

```python
ha_get_state(entity_id="binary_sensor.iphone_nils_focus")
```

Expected: State object exists (on/off)

**Step 2: Design template logic**

Template should:
- Return "on" when iPhone Nils is home
- Return "off" when iPhone Nils is away
- Be easily extensible for second phone (OR condition)

Template code:
```jinja2
{{ is_state('binary_sensor.iphone_nils_focus', 'on') }}
```

**Step 3: Test template evaluation**

```python
ha_eval_template(template="{{ is_state('binary_sensor.iphone_nils_focus', 'on') }}")
```

Expected: Returns "True" or "False" based on current phone state

**Step 4: Create helper for anyone_home sensor**

```python
ha_call_service(
    domain="input_boolean",
    service="create",
    data={
        "name": "Anyone Home Override",
        "icon": "mdi:home-account"
    }
)
```

Note: We'll create the actual template sensor using a configuration-based approach in the next step.

**Step 5: Create template binary sensor via helper**

Search for existing helper creation tool or use automation to maintain state:

```python
ha_config_set_automation(config={
    "alias": "Update Anyone Home Status",
    "description": "Template sensor replacement - updates anyone_home status based on iPhone presence",
    "mode": "restart",
    "trigger": [
        {
            "platform": "state",
            "entity_id": "binary_sensor.iphone_nils_focus"
        }
    ],
    "action": [
        {
            "choose": [
                {
                    "conditions": [
                        {
                            "condition": "state",
                            "entity_id": "binary_sensor.iphone_nils_focus",
                            "state": "on"
                        }
                    ],
                    "sequence": [
                        {
                            "service": "input_boolean.turn_on",
                            "target": {
                                "entity_id": "input_boolean.anyone_home_override"
                            }
                        }
                    ]
                }
            ],
            "default": [
                {
                    "service": "input_boolean.turn_off",
                    "target": {
                        "entity_id": "input_boolean.anyone_home_override"
                    }
                }
            ]
        }
    ]
})
```

**Alternative Step 5: Use helper creation API**

```python
ha_create_config_entry_helper(
    domain="template",
    data={
        "template_type": "binary_sensor",
        "name": "Anyone Home",
        "state": "{{ is_state('binary_sensor.iphone_nils_focus', 'on') }}",
        "device_class": "presence"
    }
)
```

**Step 6: Verify template sensor**

```python
ha_get_state(entity_id="binary_sensor.anyone_home")
```

Expected: State matches iPhone Nils focus state

**Step 7: Test state changes**

Monitor that sensor updates when iPhone presence changes. Document that to add second person later, change template to:
```jinja2
{{ is_state('binary_sensor.iphone_nils_focus', 'on') or is_state('binary_sensor.iphone_girlfriend', 'on') }}
```

---

## Task 3: Create Notification Group

**Files:**
- Create: Notification group via configuration

**Step 1: Find iPhone notification service name**

```python
ha_list_services(domain="notify")
```

Expected: Find service like "notify.mobile_app_iphone_nils" or similar

**Step 2: Test notification service**

```python
ha_call_service(
    domain="notify",
    service="mobile_app_iphone_nils",
    data={
        "title": "Test",
        "message": "Security system setup test"
    }
)
```

Expected: Notification received on iPhone

**Step 3: Create notification group via automation (workaround)**

Since notification groups require configuration.yaml, create a script that sends to all users:

```python
ha_config_set_script(
    script_id="notify_all_users",
    config={
        "alias": "Notify All Users",
        "description": "Send notification to all household members",
        "fields": {
            "title": {
                "description": "Notification title",
                "example": "Security Alert"
            },
            "message": {
                "description": "Notification message",
                "example": "Alarm triggered"
            },
            "data": {
                "description": "Additional notification data (optional)",
                "example": {}
            }
        },
        "sequence": [
            {
                "service": "notify.mobile_app_iphone_nils",
                "data": {
                    "title": "{{ title }}",
                    "message": "{{ message }}",
                    "data": "{{ data | default({}) }}"
                }
            }
        ]
    }
)
```

**Step 4: Test notification script**

```python
ha_call_service(
    domain="script",
    service="notify_all_users",
    data={
        "title": "Test Alert",
        "message": "Testing notification system"
    }
)
```

Expected: Notification received

**Step 5: Document expansion**

Note: To add girlfriend's notifications later, add another service call in the sequence:
```yaml
- service: notify.mobile_app_iphone_girlfriend
  data:
    title: "{{ title }}"
    message: "{{ message }}"
```

---

## Task 4: Create Manual Alarm Control Panel

**Files:**
- Create: Manual alarm control panel helper

**Step 1: Check if manual alarm integration is available**

```python
ha_get_integration(integration="manual")
```

Expected: Integration details or availability info

**Step 2: Create manual alarm control panel helper**

```python
ha_create_config_entry_helper(
    domain="manual",
    data={
        "name": "Home Security",
        "code": None,  # No code required for arming/disarming
        "delay_time": 60,  # Entry delay for doors
        "arming_time": 5,  # Time to leave after arming
        "disarm_after_trigger": False,  # Requires manual disarm
        "trigger_time": 600  # Alarm sounds for 10 minutes
    }
)
```

**Alternative Step 2: Create via automation/configuration**

If helper API not available, document that user needs to add to configuration.yaml:

```yaml
alarm_control_panel:
  - platform: manual
    name: Home Security
    code_arm_required: false
    code_disarm_required: false
    arming_time: 5
    delay_time: 60
    trigger_time: 600
    disarmed:
      trigger_time: 0
    armed_home:
      arming_time: 0
      delay_time: 60
    armed_away:
      arming_time: 5
      delay_time: 60
    armed_custom_bypass:
      arming_time: 0
      delay_time: 60
```

Then reload configuration:
```python
ha_call_service(domain="homeassistant", service="reload_config_entry")
```

**Step 3: Verify alarm panel creation**

```python
ha_search_entities(query="", domain_filter="alarm_control_panel")
```

Expected: Find `alarm_control_panel.home_security`

**Step 4: Test alarm states**

Test arming to away:
```python
ha_call_service(
    domain="alarm_control_panel",
    service="alarm_arm_away",
    entity_id="alarm_control_panel.home_security"
)
```

Wait 5 seconds (arming_time), then check:
```python
ha_get_state(entity_id="alarm_control_panel.home_security")
```

Expected: State is "armed_away"

**Step 5: Test disarming**

```python
ha_call_service(
    domain="alarm_control_panel",
    service="alarm_disarm",
    entity_id="alarm_control_panel.home_security"
)
```

Expected: State is "disarmed"

**Step 6: Test other modes**

Test armed_home:
```python
ha_call_service(
    domain="alarm_control_panel",
    service="alarm_arm_home",
    entity_id="alarm_control_panel.home_security"
)
```

Test armed_custom_bypass:
```python
ha_call_service(
    domain="alarm_control_panel",
    service="alarm_arm_custom_bypass",
    entity_id="alarm_control_panel.home_security"
)
```

Disarm after tests:
```python
ha_call_service(
    domain="alarm_control_panel",
    service="alarm_disarm",
    entity_id="alarm_control_panel.home_security"
)
```

---

## Task 5: Create Security Control Scripts

**Files:**
- Create: 6 scripts for alarm control and actions

**Step 1: Create script - Arm Away**

```python
ha_config_set_script(
    script_id="security_arm_away",
    config={
        "alias": "Security: Arm Away",
        "description": "Arm security system to Away mode - all sensors active",
        "icon": "mdi:shield-lock",
        "sequence": [
            {
                "service": "alarm_control_panel.alarm_arm_away",
                "target": {
                    "entity_id": "alarm_control_panel.home_security"
                }
            },
            {
                "service": "script.notify_all_users",
                "data": {
                    "title": "🏠 Sicherheitssystem",
                    "message": "System ist SCHARF (Abwesend). Alle Sensoren aktiv."
                }
            }
        ]
    }
)
```

**Step 2: Create script - Arm Home (Night Mode)**

```python
ha_config_set_script(
    script_id="security_arm_home",
    config={
        "alias": "Security: Arm Home (Nachtschutz)",
        "description": "Arm security system to Home mode - ground floor sensors only",
        "icon": "mdi:shield-home",
        "sequence": [
            {
                "service": "alarm_control_panel.alarm_arm_home",
                "target": {
                    "entity_id": "alarm_control_panel.home_security"
                }
            },
            {
                "service": "script.notify_all_users",
                "data": {
                    "title": "🌙 Nachtschutz",
                    "message": "Nachtschutz AKTIVIERT. Außensensoren überwachen."
                }
            }
        ]
    }
)
```

**Step 3: Create script - Arm Enhanced Security**

```python
ha_config_set_script(
    script_id="security_arm_enhanced",
    config={
        "alias": "Security: Erweiterte Sicherheit",
        "description": "Arm with all sensors including motion - for when home alone",
        "icon": "mdi:shield-alert",
        "sequence": [
            {
                "service": "alarm_control_panel.alarm_arm_custom_bypass",
                "target": {
                    "entity_id": "alarm_control_panel.home_security"
                }
            },
            {
                "service": "script.notify_all_users",
                "data": {
                    "title": "🔒 Erweiterte Sicherheit",
                    "message": "Erweiterte Sicherheit AKTIVIERT. Alle Sensoren aktiv."
                }
            }
        ]
    }
)
```

**Step 4: Create script - Disarm**

```python
ha_config_set_script(
    script_id="security_disarm",
    config={
        "alias": "Security: Disarm",
        "description": "Disarm security system",
        "icon": "mdi:shield-off",
        "sequence": [
            {
                "service": "alarm_control_panel.alarm_disarm",
                "target": {
                    "entity_id": "alarm_control_panel.home_security"
                }
            },
            {
                "service": "script.notify_all_users",
                "data": {
                    "title": "✅ Sicherheitssystem",
                    "message": "System DEAKTIVIERT."
                }
            }
        ]
    }
)
```

**Step 5: Create script - Trigger Alarm Actions**

```python
ha_config_set_script(
    script_id="security_alarm_trigger",
    config={
        "alias": "Security: Trigger Alarm",
        "description": "Execute all alarm trigger actions - siren, lights, notifications",
        "icon": "mdi:alarm-light",
        "mode": "single",
        "sequence": [
            {
                "parallel": [
                    {
                        "sequence": [
                            {
                                "service": "media_player.volume_set",
                                "target": {
                                    "entity_id": "media_player.wohnzimmer"
                                },
                                "data": {
                                    "volume_level": 0.85
                                }
                            },
                            {
                                "service": "media_player.play_media",
                                "target": {
                                    "entity_id": "media_player.wohnzimmer"
                                },
                                "data": {
                                    "media_content_type": "music",
                                    "media_content_id": "https://www.soundjay.com/misc/sounds/bell-ringing-05.mp3"
                                }
                            }
                        ]
                    },
                    {
                        "service": "siren.turn_on",
                        "target": {
                            "entity_id": "siren.kamera_vordertur_sirene"
                        }
                    },
                    {
                        "service": "light.turn_on",
                        "target": {
                            "entity_id": "group.security_lights"
                        },
                        "data": {
                            "brightness": 255
                        }
                    },
                    {
                        "service": "script.notify_all_users",
                        "data": {
                            "title": "🚨 ALARM AUSGELÖST!",
                            "message": "Sicherheitsalarm um {{ now().strftime('%H:%M:%S') }} ausgelöst!",
                            "data": {
                                "push": {
                                    "sound": {
                                        "name": "default",
                                        "critical": 1,
                                        "volume": 1.0
                                    }
                                }
                            }
                        }
                    }
                ]
            }
        ]
    }
)
```

**Step 6: Create script - Stop Alarm**

```python
ha_config_set_script(
    script_id="security_alarm_stop",
    config={
        "alias": "Security: Stop Alarm",
        "description": "Stop all alarm actions and restore previous states",
        "icon": "mdi:alarm-off",
        "mode": "single",
        "sequence": [
            {
                "parallel": [
                    {
                        "service": "media_player.media_stop",
                        "target": {
                            "entity_id": "media_player.wohnzimmer"
                        }
                    },
                    {
                        "service": "siren.turn_off",
                        "target": {
                            "entity_id": "siren.kamera_vordertur_sirene"
                        }
                    },
                    {
                        "service": "light.turn_off",
                        "target": {
                            "entity_id": "group.security_lights"
                        }
                    },
                    {
                        "service": "script.notify_all_users",
                        "data": {
                            "title": "✅ Alarm Deaktiviert",
                            "message": "Alarm gestoppt um {{ now().strftime('%H:%M:%S') }}"
                        }
                    }
                ]
            }
        ]
    }
)
```

**Step 7: Test each script**

Test arm away:
```python
ha_call_service(domain="script", service="security_arm_away")
```

Wait for notification, verify alarm state.

Test disarm:
```python
ha_call_service(domain="script", service="security_disarm")
```

Test trigger alarm (WARNING: Will be loud!):
```python
ha_call_service(domain="script", service="security_alarm_trigger")
```

Immediately stop:
```python
ha_call_service(domain="script", service="security_alarm_stop")
```

Test other modes similarly.

---

## Task 6: Create Presence-Based Auto Arming Automations

**Files:**
- Create: Automations for automatic arming/disarming based on presence

**Step 1: Create automation - Auto Arm Away**

```python
ha_config_set_automation(config={
    "alias": "Security: Auto Arm Away",
    "description": "Automatically arm to Away mode when everyone leaves (5 min delay)",
    "mode": "restart",
    "trigger": [
        {
            "platform": "state",
            "entity_id": "binary_sensor.anyone_home",
            "to": "off",
            "for": {
                "minutes": 5
            }
        }
    ],
    "condition": [
        {
            "condition": "state",
            "entity_id": "alarm_control_panel.home_security",
            "state": "disarmed"
        }
    ],
    "action": [
        {
            "service": "script.security_arm_away"
        }
    ]
})
```

**Step 2: Verify auto arm away automation**

```python
ha_search_entities(query="auto arm away", domain_filter="automation")
```

Expected: Find automation entity

Check configuration:
```python
ha_config_get_automation(identifier="automation.security_auto_arm_away")
```

**Step 3: Create automation - Auto Disarm on Arrival**

```python
ha_config_set_automation(config={
    "alias": "Security: Auto Disarm on Arrival",
    "description": "Automatically disarm when someone arrives home",
    "mode": "restart",
    "trigger": [
        {
            "platform": "state",
            "entity_id": "binary_sensor.anyone_home",
            "to": "on"
        }
    ],
    "condition": [
        {
            "condition": "state",
            "entity_id": "alarm_control_panel.home_security",
            "state": "armed_away"
        }
    ],
    "action": [
        {
            "service": "script.security_disarm"
        },
        {
            "service": "script.notify_all_users",
            "data": {
                "title": "✅ Willkommen zu Hause!",
                "message": "Sicherheitssystem automatisch deaktiviert."
            }
        }
    ]
})
```

**Step 4: Test arrival/departure logic**

Test by manually toggling the iPhone presence (or input_boolean if using that approach):

Simulate leaving:
```python
ha_call_service(
    domain="input_boolean",
    service="turn_off",
    entity_id="binary_sensor.anyone_home"  # Or the underlying input_boolean
)
```

Wait 5+ minutes, verify alarm arms.

Simulate arriving:
```python
ha_call_service(
    domain="input_boolean",
    service="turn_on",
    entity_id="binary_sensor.anyone_home"
)
```

Verify alarm disarms immediately.

---

## Task 7: Create Time-Based Night Mode Automations

**Files:**
- Create: Automations for automatic night mode activation/deactivation

**Step 1: Create automation - Night Mode Activation**

```python
ha_config_set_automation(config={
    "alias": "Security: Night Mode Activation",
    "description": "Activate Nachtschutz at 22:00 if someone is home",
    "mode": "single",
    "trigger": [
        {
            "platform": "time",
            "at": "22:00:00"
        }
    ],
    "condition": [
        {
            "condition": "state",
            "entity_id": "binary_sensor.anyone_home",
            "state": "on"
        },
        {
            "condition": "state",
            "entity_id": "alarm_control_panel.home_security",
            "state": "disarmed"
        }
    ],
    "action": [
        {
            "service": "script.security_arm_home"
        }
    ]
})
```

**Step 2: Create automation - Morning Disarm**

```python
ha_config_set_automation(config={
    "alias": "Security: Morning Auto-Disarm",
    "description": "Disarm Nachtschutz at 07:00 if someone is home",
    "mode": "single",
    "trigger": [
        {
            "platform": "time",
            "at": "07:00:00"
        }
    ],
    "condition": [
        {
            "condition": "state",
            "entity_id": "binary_sensor.anyone_home",
            "state": "on"
        },
        {
            "condition": "state",
            "entity_id": "alarm_control_panel.home_security",
            "state": "armed_home"
        }
    ],
    "action": [
        {
            "service": "script.security_disarm"
        },
        {
            "service": "script.notify_all_users",
            "data": {
                "title": "☀️ Guten Morgen!",
                "message": "Nachtschutz automatisch deaktiviert (07:00)."
            }
        }
    ]
})
```

**Step 3: Test night mode logic**

Test by manually triggering the automation:

```python
ha_call_service(
    domain="automation",
    service="trigger",
    target={
        "entity_id": "automation.security_night_mode_activation"
    }
)
```

Verify:
- Alarm state changes to armed_home
- Notification received

Test morning disarm similarly:
```python
ha_call_service(
    domain="automation",
    service="trigger",
    target={
        "entity_id": "automation.security_morning_auto_disarm"
    }
)
```

---

## Task 8: Create Sensor Monitoring Automations

**Files:**
- Create: Automations for door/window sensor monitoring with grace periods

**Step 1: Define sensor groups for monitoring**

Entry doors (60s delay):
- `binary_sensor.haupteingang_tur`
- `binary_sensor.hwr_tur_seite`

Ground floor windows/doors (15s grace):
- `binary_sensor.wohnzimmer_fenster_klein`
- `binary_sensor.wohnzimmer_tur_gross`
- `binary_sensor.esszimmer_tur_gross`
- `binary_sensor.esszimmer_fenster_klein`
- `binary_sensor.kuche_fenster`
- `binary_sensor.badezimmer_unten_fenster`
- `binary_sensor.arbeitszimmer_unten_fenster_vorne`
- `binary_sensor.arbeitszimmer_unten_fenster_seite`

Upper floor windows (conditional):
- `binary_sensor.badezimmer_oben_fenster_vorne`
- `binary_sensor.badezimmer_oben_fenster_seite`
- `binary_sensor.schlafzimmer_tur_gross`
- `binary_sensor.schlafzimmer_fenster_klein`

**Step 2: Create automation - Entry Door Monitoring**

```python
ha_config_set_automation(config={
    "alias": "Security: Entry Door Delay",
    "description": "60 second entry delay for main doors with progressive warnings",
    "mode": "restart",
    "trigger": [
        {
            "platform": "state",
            "entity_id": [
                "binary_sensor.haupteingang_tur",
                "binary_sensor.hwr_tur_seite"
            ],
            "to": "on"
        }
    ],
    "condition": [
        {
            "condition": "or",
            "conditions": [
                {
                    "condition": "state",
                    "entity_id": "alarm_control_panel.home_security",
                    "state": "armed_away"
                },
                {
                    "condition": "state",
                    "entity_id": "alarm_control_panel.home_security",
                    "state": "armed_home"
                },
                {
                    "condition": "state",
                    "entity_id": "alarm_control_panel.home_security",
                    "state": "armed_custom_bypass"
                }
            ]
        },
        {
            "condition": "template",
            "value_template": "{{ trigger.to_state.state == 'on' }}"
        }
    ],
    "action": [
        {
            "service": "script.notify_all_users",
            "data": {
                "title": "⚠️ Eingang erkannt!",
                "message": "{{ trigger.to_state.attributes.friendly_name }} geöffnet! 60 Sekunden zum Deaktivieren.",
                "data": {
                    "actions": [
                        {
                            "action": "DISARM_NOW",
                            "title": "Jetzt deaktivieren"
                        }
                    ]
                }
            }
        },
        {
            "delay": {
                "seconds": 30
            }
        },
        {
            "if": [
                {
                    "condition": "or",
                    "conditions": [
                        {
                            "condition": "state",
                            "entity_id": "alarm_control_panel.home_security",
                            "state": "armed_away"
                        },
                        {
                            "condition": "state",
                            "entity_id": "alarm_control_panel.home_security",
                            "state": "armed_home"
                        },
                        {
                            "condition": "state",
                            "entity_id": "alarm_control_panel.home_security",
                            "state": "armed_custom_bypass"
                        }
                    ]
                }
            ],
            "then": [
                {
                    "service": "script.notify_all_users",
                    "data": {
                        "title": "⚠️ WARNUNG",
                        "message": "Noch 30 Sekunden zum Deaktivieren!",
                        "data": {
                            "push": {
                                "sound": {
                                    "name": "default",
                                    "critical": 1
                                }
                            }
                        }
                    }
                }
            ]
        },
        {
            "delay": {
                "seconds": 20
            }
        },
        {
            "if": [
                {
                    "condition": "or",
                    "conditions": [
                        {
                            "condition": "state",
                            "entity_id": "alarm_control_panel.home_security",
                            "state": "armed_away"
                        },
                        {
                            "condition": "state",
                            "entity_id": "alarm_control_panel.home_security",
                            "state": "armed_home"
                        },
                        {
                            "condition": "state",
                            "entity_id": "alarm_control_panel.home_security",
                            "state": "armed_custom_bypass"
                        }
                    ]
                }
            ],
            "then": [
                {
                    "service": "script.notify_all_users",
                    "data": {
                        "title": "🚨 DRINGEND",
                        "message": "10 Sekunden! Sofort deaktivieren!",
                        "data": {
                            "push": {
                                "sound": {
                                    "name": "default",
                                    "critical": 1,
                                    "volume": 1.0
                                }
                            }
                        }
                    }
                }
            ]
        },
        {
            "delay": {
                "seconds": 10
            }
        },
        {
            "if": [
                {
                    "condition": "or",
                    "conditions": [
                        {
                            "condition": "state",
                            "entity_id": "alarm_control_panel.home_security",
                            "state": "armed_away"
                        },
                        {
                            "condition": "state",
                            "entity_id": "alarm_control_panel.home_security",
                            "state": "armed_home"
                        },
                        {
                            "condition": "state",
                            "entity_id": "alarm_control_panel.home_security",
                            "state": "armed_custom_bypass"
                        }
                    ]
                }
            ],
            "then": [
                {
                    "service": "script.security_alarm_trigger"
                }
            ]
        }
    ]
})
```

**Step 3: Create automation - Window/Door Grace Period**

```python
ha_config_set_automation(config={
    "alias": "Security: Window Grace Period",
    "description": "15 second grace period for windows/doors when armed",
    "mode": "parallel",
    "max": 10,
    "trigger": [
        {
            "platform": "state",
            "entity_id": [
                "binary_sensor.wohnzimmer_fenster_klein",
                "binary_sensor.wohnzimmer_tur_gross",
                "binary_sensor.esszimmer_tur_gross",
                "binary_sensor.esszimmer_fenster_klein",
                "binary_sensor.kuche_fenster",
                "binary_sensor.badezimmer_unten_fenster",
                "binary_sensor.arbeitszimmer_unten_fenster_vorne",
                "binary_sensor.arbeitszimmer_unten_fenster_seite"
            ],
            "to": "on"
        }
    ],
    "condition": [
        {
            "condition": "or",
            "conditions": [
                {
                    "condition": "state",
                    "entity_id": "alarm_control_panel.home_security",
                    "state": "armed_away"
                },
                {
                    "condition": "state",
                    "entity_id": "alarm_control_panel.home_security",
                    "state": "armed_home"
                },
                {
                    "condition": "state",
                    "entity_id": "alarm_control_panel.home_security",
                    "state": "armed_custom_bypass"
                }
            ]
        }
    ],
    "action": [
        {
            "service": "script.notify_all_users",
            "data": {
                "title": "⚠️ Sensor ausgelöst",
                "message": "{{ trigger.to_state.attributes.friendly_name }} geöffnet! 15 Sekunden zum Schließen."
            }
        },
        {
            "wait_for_trigger": [
                {
                    "platform": "state",
                    "entity_id": "{{ trigger.entity_id }}",
                    "to": "off"
                }
            ],
            "timeout": {
                "seconds": 15
            }
        },
        {
            "if": [
                {
                    "condition": "template",
                    "value_template": "{{ wait.trigger is none }}"
                }
            ],
            "then": [
                {
                    "service": "script.security_alarm_trigger"
                }
            ]
        }
    ]
})
```

**Step 4: Create automation - Upper Floor Window Monitoring (Away Mode Only)**

```python
ha_config_set_automation(config={
    "alias": "Security: Upper Floor Windows (Away Mode)",
    "description": "Monitor upper floor windows only in Away and Enhanced modes",
    "mode": "parallel",
    "max": 5,
    "trigger": [
        {
            "platform": "state",
            "entity_id": [
                "binary_sensor.badezimmer_oben_fenster_vorne",
                "binary_sensor.badezimmer_oben_fenster_seite",
                "binary_sensor.schlafzimmer_tur_gross",
                "binary_sensor.schlafzimmer_fenster_klein"
            ],
            "to": "on"
        }
    ],
    "condition": [
        {
            "condition": "or",
            "conditions": [
                {
                    "condition": "state",
                    "entity_id": "alarm_control_panel.home_security",
                    "state": "armed_away"
                },
                {
                    "condition": "state",
                    "entity_id": "alarm_control_panel.home_security",
                    "state": "armed_custom_bypass"
                }
            ]
        }
    ],
    "action": [
        {
            "service": "script.notify_all_users",
            "data": {
                "title": "⚠️ Obergeschoss Sensor",
                "message": "{{ trigger.to_state.attributes.friendly_name }} geöffnet! 15 Sekunden zum Schließen."
            }
        },
        {
            "wait_for_trigger": [
                {
                    "platform": "state",
                    "entity_id": "{{ trigger.entity_id }}",
                    "to": "off"
                }
            ],
            "timeout": {
                "seconds": 15
            }
        },
        {
            "if": [
                {
                    "condition": "template",
                    "value_template": "{{ wait.trigger is none }}"
                }
            ],
            "then": [
                {
                    "service": "script.security_alarm_trigger"
                }
            ]
        }
    ]
})
```

**Step 5: Create automation - Motion Sensor Monitoring**

```python
ha_config_set_automation(config={
    "alias": "Security: Motion Sensor Alert",
    "description": "Instant trigger on motion when armed (Away/Enhanced modes only)",
    "mode": "parallel",
    "max": 5,
    "trigger": [
        {
            "platform": "state",
            "entity_id": [
                "binary_sensor.hwr_bewegung",
                "binary_sensor.badezimmer_unten_bewegung"
            ],
            "to": "on"
        }
    ],
    "condition": [
        {
            "condition": "or",
            "conditions": [
                {
                    "condition": "state",
                    "entity_id": "alarm_control_panel.home_security",
                    "state": "armed_away"
                },
                {
                    "condition": "state",
                    "entity_id": "alarm_control_panel.home_security",
                    "state": "armed_custom_bypass"
                }
            ]
        }
    ],
    "action": [
        {
            "service": "script.security_alarm_trigger"
        },
        {
            "service": "script.notify_all_users",
            "data": {
                "title": "🚨 BEWEGUNG ERKANNT!",
                "message": "{{ trigger.to_state.attributes.friendly_name }} - Alarm ausgelöst!"
            }
        }
    ]
})
```

**Step 6: Test sensor monitoring**

IMPORTANT: Be prepared to quickly disarm!

Test entry door delay:
```python
# Arm system
ha_call_service(domain="script", service="security_arm_away")

# Wait 10 seconds for arming

# Manually trigger door sensor (or physically open door)
# Should receive progressive notifications at 60s, 30s, 10s marks
# Disarm before 60s expires:
ha_call_service(domain="script", service="security_disarm")
```

Test window grace period similarly with shorter timeout.

---

## Task 9: Create Camera Integration Automations

**Files:**
- Create: Automations for camera AI detection integration

**Step 1: Create automation - Person at Door (Informational)**

```python
ha_config_set_automation(config={
    "alias": "Security: Person at Door Alert",
    "description": "Notify when person detected at door while armed (informational)",
    "mode": "single",
    "trigger": [
        {
            "platform": "state",
            "entity_id": "binary_sensor.kamera_vordertur_person",
            "to": "on"
        }
    ],
    "condition": [
        {
            "condition": "or",
            "conditions": [
                {
                    "condition": "state",
                    "entity_id": "alarm_control_panel.home_security",
                    "state": "armed_away"
                },
                {
                    "condition": "state",
                    "entity_id": "alarm_control_panel.home_security",
                    "state": "armed_home"
                },
                {
                    "condition": "state",
                    "entity_id": "alarm_control_panel.home_security",
                    "state": "armed_custom_bypass"
                }
            ]
        }
    ],
    "action": [
        {
            "service": "script.notify_all_users",
            "data": {
                "title": "ℹ️ Person an Haustür",
                "message": "Person erkannt (System scharf) - {{ now().strftime('%H:%M:%S') }}",
                "data": {
                    "entity_id": "camera.kamera_vordertur_standardauflosung"
                }
            }
        }
    ]
})
```

**Step 2: Create automation - Package Detected**

```python
ha_config_set_automation(config={
    "alias": "Security: Package Detected",
    "description": "Notify when package detected at door",
    "mode": "single",
    "trigger": [
        {
            "platform": "state",
            "entity_id": "binary_sensor.kamera_vordertur_paket",
            "to": "on"
        }
    ],
    "action": [
        {
            "service": "script.notify_all_users",
            "data": {
                "title": "📦 Paket erkannt",
                "message": "Paket an Haustür erkannt - {{ now().strftime('%H:%M:%S') }}",
                "data": {
                    "entity_id": "camera.kamera_vordertur_standardauflosung"
                }
            }
        }
    ]
})
```

**Step 3: Create automation - Doorbell Pressed**

```python
ha_config_set_automation(config={
    "alias": "Security: Doorbell Alert",
    "description": "Enhanced notification when doorbell pressed while armed",
    "mode": "single",
    "trigger": [
        {
            "platform": "state",
            "entity_id": "binary_sensor.kamera_vordertur_besucher",
            "to": "on"
        }
    ],
    "condition": [
        {
            "condition": "or",
            "conditions": [
                {
                    "condition": "state",
                    "entity_id": "alarm_control_panel.home_security",
                    "state": "armed_away"
                },
                {
                    "condition": "state",
                    "entity_id": "alarm_control_panel.home_security",
                    "state": "armed_home"
                },
                {
                    "condition": "state",
                    "entity_id": "alarm_control_panel.home_security",
                    "state": "armed_custom_bypass"
                }
            ]
        }
    ],
    "action": [
        {
            "service": "script.notify_all_users",
            "data": {
                "title": "🔔 Türklingel!",
                "message": "Besucher an der Tür (System scharf) - {{ now().strftime('%H:%M:%S') }}",
                "data": {
                    "entity_id": "camera.kamera_vordertur_standardauflosung"
                }
            }
        }
    ]
})
```

**Step 4: Test camera automations**

Test person detection:
```python
# Trigger by walking in front of camera, or simulate:
# (Note: Cannot easily simulate Reolink AI detection via MCP)
# Verify notification received with camera snapshot
```

Test similarly for package and doorbell.

---

## Task 10: Create Actionable Notification Handler

**Files:**
- Create: Automation to handle notification actions (disarm button)

**Step 1: Create automation - Handle Disarm Action**

```python
ha_config_set_automation(config={
    "alias": "Security: Handle Notification Disarm",
    "description": "Handle disarm action from notification button",
    "mode": "single",
    "trigger": [
        {
            "platform": "event",
            "event_type": "mobile_app_notification_action",
            "event_data": {
                "action": "DISARM_NOW"
            }
        }
    ],
    "action": [
        {
            "service": "script.security_disarm"
        }
    ]
})
```

**Step 2: Test actionable notification**

This requires actual notification with action button. Test during entry delay:

1. Arm system
2. Open entry door
3. Receive notification with "Jetzt deaktivieren" button
4. Press button
5. Verify system disarms

---

## Task 11: Create Security Dashboard

**Files:**
- Create: Lovelace dashboard for security system control and monitoring

**Step 1: Create new dashboard**

```python
ha_config_set_dashboard(
    url_path="security-system",
    title="Sicherheitssystem",
    icon="mdi:shield-home",
    config={
        "views": [
            {
                "title": "Sicherheit",
                "type": "sections",
                "sections": [
                    {
                        "title": "Status",
                        "type": "grid",
                        "cards": [
                            {
                                "type": "alarm-panel",
                                "entity": "alarm_control_panel.home_security",
                                "name": "Sicherheitssystem",
                                "states": [
                                    "arm_away",
                                    "arm_home",
                                    "arm_custom_bypass"
                                ]
                            },
                            {
                                "type": "entity",
                                "entity": "binary_sensor.anyone_home",
                                "name": "Anwesenheit",
                                "icon": "mdi:home-account"
                            }
                        ]
                    },
                    {
                        "title": "Schnellaktionen",
                        "type": "grid",
                        "cards": [
                            {
                                "type": "button",
                                "name": "Abwesend",
                                "icon": "mdi:shield-lock",
                                "tap_action": {
                                    "action": "call-service",
                                    "service": "script.security_arm_away"
                                },
                                "entity": "script.security_arm_away"
                            },
                            {
                                "type": "button",
                                "name": "Nachtschutz",
                                "icon": "mdi:shield-home",
                                "tap_action": {
                                    "action": "call-service",
                                    "service": "script.security_arm_home"
                                },
                                "entity": "script.security_arm_home"
                            },
                            {
                                "type": "button",
                                "name": "Erweitert",
                                "icon": "mdi:shield-alert",
                                "tap_action": {
                                    "action": "call-service",
                                    "service": "script.security_arm_enhanced"
                                },
                                "entity": "script.security_arm_enhanced"
                            },
                            {
                                "type": "button",
                                "name": "Deaktivieren",
                                "icon": "mdi:shield-off",
                                "tap_action": {
                                    "action": "call-service",
                                    "service": "script.security_disarm"
                                },
                                "entity": "script.security_disarm"
                            }
                        ]
                    }
                ]
            }
        ]
    }
)
```

**Step 2: Add sensor status section**

```python
ha_config_set_dashboard(
    url_path="security-system",
    python_transform="""
config['views'][0]['sections'].append({
    'title': 'Eingangstüren',
    'type': 'grid',
    'cards': [
        {
            'type': 'entity',
            'entity': 'binary_sensor.haupteingang_tur',
            'name': 'Haupteingang'
        },
        {
            'type': 'entity',
            'entity': 'binary_sensor.hwr_tur_seite',
            'name': 'HWR Seite'
        }
    ]
})
""",
    config_hash="<get from previous call>"
)
```

**Step 3: Add ground floor sensors section**

```python
ha_config_set_dashboard(
    url_path="security-system",
    python_transform="""
config['views'][0]['sections'].append({
    'title': 'Erdgeschoss Fenster/Türen',
    'type': 'grid',
    'cards': [
        {'type': 'entity', 'entity': 'binary_sensor.wohnzimmer_fenster_klein'},
        {'type': 'entity', 'entity': 'binary_sensor.wohnzimmer_tur_gross'},
        {'type': 'entity', 'entity': 'binary_sensor.esszimmer_tur_gross'},
        {'type': 'entity', 'entity': 'binary_sensor.esszimmer_fenster_klein'},
        {'type': 'entity', 'entity': 'binary_sensor.kuche_fenster'},
        {'type': 'entity', 'entity': 'binary_sensor.badezimmer_unten_fenster'},
        {'type': 'entity', 'entity': 'binary_sensor.arbeitszimmer_unten_fenster_vorne'},
        {'type': 'entity', 'entity': 'binary_sensor.arbeitszimmer_unten_fenster_seite'}
    ]
})
""",
    config_hash="<get from previous call>"
)
```

**Step 4: Add upper floor sensors section**

```python
ha_config_set_dashboard(
    url_path="security-system",
    python_transform="""
config['views'][0]['sections'].append({
    'title': 'Obergeschoss Fenster',
    'type': 'grid',
    'cards': [
        {'type': 'entity', 'entity': 'binary_sensor.badezimmer_oben_fenster_vorne'},
        {'type': 'entity', 'entity': 'binary_sensor.badezimmer_oben_fenster_seite'},
        {'type': 'entity', 'entity': 'binary_sensor.schlafzimmer_tur_gross'},
        {'type': 'entity', 'entity': 'binary_sensor.schlafzimmer_fenster_klein'}
    ]
})
""",
    config_hash="<get from previous call>"
)
```

**Step 5: Add motion sensors and camera section**

```python
ha_config_set_dashboard(
    url_path="security-system",
    python_transform="""
config['views'][0]['sections'].extend([
    {
        'title': 'Bewegungsmelder',
        'type': 'grid',
        'cards': [
            {'type': 'entity', 'entity': 'binary_sensor.hwr_bewegung'},
            {'type': 'entity', 'entity': 'binary_sensor.badezimmer_unten_bewegung'}
        ]
    },
    {
        'title': 'Kamera',
        'type': 'grid',
        'cards': [
            {
                'type': 'picture-entity',
                'entity': 'camera.kamera_vordertur_standardauflosung',
                'camera_image': 'camera.kamera_vordertur_standardauflosung',
                'name': 'Vordertür'
            },
            {
                'type': 'entities',
                'entities': [
                    'binary_sensor.kamera_vordertur_person',
                    'binary_sensor.kamera_vordertur_fahrzeug',
                    'binary_sensor.kamera_vordertur_paket',
                    'binary_sensor.kamera_vordertur_besucher'
                ]
            }
        ]
    }
])
""",
    config_hash="<get from previous call>"
)
```

**Step 6: Verify dashboard**

Open Home Assistant UI, navigate to: `http://homeassistant.local:8123/security-system`

Verify:
- Alarm panel shows current state
- All buttons work (test each mode)
- Sensor statuses display correctly
- Camera feed shows
- All sections render properly

---

## Task 12: End-to-End System Testing

**Files:**
- Test: Complete security system workflow

**Step 1: Test Away Mode Scenario**

Simulate leaving home:

```python
# 1. Ensure system is disarmed
ha_call_service(domain="script", service="security_disarm")

# 2. Simulate leaving (turn off presence)
# (Manual: Toggle iPhone presence off or wait for actual departure)

# 3. Wait 5 minutes (grace period)
# Expected: System automatically arms to Away mode
# Expected: Notification received

# 4. Verify alarm state
ha_get_state(entity_id="alarm_control_panel.home_security")
# Expected: State = "armed_away"
```

**Step 2: Test Entry Delay on Return**

```python
# 1. While armed away, simulate arrival
# (Manual: Toggle iPhone presence on or arrive home)

# Expected: System should auto-disarm immediately due to iPhone detection
# Expected: "Welcome home" notification

# Alternative test without phone present:
# Open entry door while armed
# Expected: 60s countdown with notifications at 60s, 30s, 10s
# Expected: Disarm before timeout to prevent full alarm
```

**Step 3: Test Night Mode Scenario**

```python
# 1. Ensure someone home during evening
# 2. Manually trigger night mode automation or wait for 22:00
ha_call_service(
    domain="automation",
    service="trigger",
    target={"entity_id": "automation.security_night_mode_activation"}
)

# Expected: System arms to Home mode
# Expected: Notification received

# 3. Verify upper floor windows don't trigger alarm
# (Manual: Open bedroom window)
# Expected: No alarm (upper floor excluded in Home mode)

# 4. Verify ground floor windows do trigger
# (Manual: Open living room window)
# Expected: 15s grace period warning
# Expected: Alarm if not closed

# 5. Disarm before testing next scenario
ha_call_service(domain="script", service="security_disarm")
```

**Step 4: Test Enhanced Security Mode**

```python
# 1. Manually arm to Enhanced mode
ha_call_service(domain="script", service="security_arm_enhanced")

# Expected: Notification received

# 2. Test motion sensor triggers alarm
# (Manual: Trigger motion sensor)
# Expected: Immediate alarm (no delay)

# 3. Stop alarm quickly
ha_call_service(domain="script", service="security_alarm_stop")

# 4. Disarm system
ha_call_service(domain="script", service="security_disarm")
```

**Step 5: Test Full Alarm Trigger**

WARNING: This will be loud! Prepare to stop quickly.

```python
# 1. Arm system
ha_call_service(domain="script", service="security_arm_away")

# 2. Open window without closing within grace period
# Expected: After 15 seconds, full alarm triggers
# Expected: Sonos plays alarm sound
# Expected: Camera siren activates
# Expected: Security lights turn on
# Expected: Critical notification sent

# 3. Immediately stop alarm
ha_call_service(domain="script", service="security_alarm_stop")

# Expected: All alarm actions stop
# Expected: Lights turn off
# Expected: Confirmation notification

# 4. Disarm system
ha_call_service(domain="script", service="security_disarm")
```

**Step 6: Test Camera Integration**

```python
# 1. Arm system
ha_call_service(domain="script", service="security_arm_away")

# 2. Trigger person detection at door
# (Manual: Walk in front of camera)
# Expected: Info notification with camera snapshot

# 3. Press doorbell
# (Manual: Press doorbell button)
# Expected: Doorbell notification with snapshot

# 4. Disarm system
ha_call_service(domain="script", service="security_disarm")
```

**Step 7: Test Actionable Notifications**

```python
# 1. Arm system
ha_call_service(domain="script", service="security_arm_away")

# 2. Open entry door to trigger countdown
# Expected: Notification with "Jetzt deaktivieren" button

# 3. Press notification action button
# Expected: System disarms immediately
# Expected: Confirmation notification
```

**Step 8: Verify Dashboard Functionality**

Open dashboard: `http://homeassistant.local:8123/security-system`

Manual testing:
1. Click "Abwesend" button → Verify arms to away
2. Click "Deaktivieren" button → Verify disarms
3. Click "Nachtschutz" button → Verify arms to home
4. Click "Erweitert" button → Verify arms to custom bypass
5. Check all sensor statuses display correctly
6. Verify camera feed shows live view

**Step 9: Document Expansion Instructions**

Create file: `docs/security-system-expansion.md`

```markdown
# Security System Expansion Guide

## Adding More Lights

1. Install new light in Home Assistant
2. Add to security lights group:
   ```python
   ha_call_service(
       domain="group",
       service="set",
       data={
           "object_id": "security_lights",
           "entities": [
               "light.aussenlicht",
               "light.hwr_deckenlampe",
               "light.new_light"  # Add here
           ]
       }
   )
   ```

## Adding Second Person Presence

1. Install Home Assistant app on girlfriend's iPhone
2. Find notification service:
   ```python
   ha_list_services(domain="notify")
   ```
3. Add to notification script:
   Edit `script.notify_all_users`, add second service call:
   ```yaml
   - service: notify.mobile_app_iphone_girlfriend
     data:
       title: "{{ title }}"
       message: "{{ message }}"
   ```

4. Update anyone_home template:
   Edit template to:
   ```jinja2
   {{ is_state('binary_sensor.iphone_nils_focus', 'on') or
      is_state('binary_sensor.iphone_girlfriend_focus', 'on') }}
   ```

## Adding More Cameras

When adding additional Reolink cameras:

1. Camera will auto-integrate via Reolink integration
2. Add camera to dashboard
3. Consider adding AI detection automations for new cameras
```

**Step 10: Final Verification Checklist**

Run through complete checklist:

- [ ] Light group created and controllable
- [ ] Anyone home sensor reflects iPhone presence
- [ ] Notification script sends to iPhone
- [ ] Alarm control panel created with all 4 modes
- [ ] All 6 scripts created and functional
- [ ] All 8+ automations created and enabled
- [ ] Dashboard renders correctly with all sections
- [ ] Away mode auto-arms after 5 min departure
- [ ] System auto-disarms on arrival
- [ ] Night mode activates at 22:00
- [ ] Morning disarm works at 07:00
- [ ] Entry doors trigger 60s countdown
- [ ] Windows trigger 15s grace period
- [ ] Motion sensors trigger instant alarm
- [ ] Camera detections send notifications
- [ ] Full alarm triggers all actions (Sonos, siren, lights)
- [ ] Alarm stop disables all actions
- [ ] Actionable notifications work
- [ ] Dashboard controls all modes
- [ ] Expansion documentation created

---

## Post-Implementation Notes

### Security Considerations

1. **Test regularly**: Monthly end-to-end alarm test
2. **Battery monitoring**: Check sensor batteries quarterly
3. **False alarm tracking**: Monitor false alarm rate, adjust grace periods if needed
4. **Backup codes**: Consider adding PIN code protection for dashboard controls

### Performance Monitoring

Monitor these metrics:
- Automation execution times (should be <1s)
- Notification delivery (should be instant)
- Camera response time
- Sensor battery levels

### Future Enhancements

Phase 2 improvements documented in design:
- Add more cameras (backyard, side yard)
- Geofencing for faster presence detection
- Video recording on alarm trigger
- Smart lock integration
- Weekly security reports

---

## Completion Criteria

System is complete when:
1. All automations execute correctly
2. Notifications arrive reliably
3. Dashboard controls work
4. End-to-end scenarios pass
5. Expansion documentation created
6. User can successfully arm/disarm all modes
7. System operates autonomously based on presence/time

**Estimated total implementation time:** 2-3 hours for core functionality + 1 hour testing + 30 min documentation = ~4 hours total
