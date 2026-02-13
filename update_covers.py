#!/usr/bin/env python3
import json

# Entity ID mappings
REPLACEMENTS = {
    "cover.esszimmer_gross_rollo": "cover.esszimmer_rollo_gross",
    "cover.esszimmer_klein_rollo": "cover.esszimmer_rollo_klein",
    "cover.arbeitszimmer_unten_vorne_rollo": "cover.arbeitszimmer_unten_rollo_vorne",
    "cover.arbeitszimmer_unten_seite_rollo": "cover.arbeitszimmer_unten_rollo_seite",
    "cover.wohnzimmer_gross_rollo": "cover.wohnzimmer_rollo_gross",
    "cover.wohnzimmer_klein_rollo": "cover.wohnzimmer_rollo_klein"
}

def replace_entity_ids(config):
    """Recursively replace entity IDs in config"""
    config_str = json.dumps(config)
    for old_id, new_id in REPLACEMENTS.items():
        config_str = config_str.replace(old_id, new_id)
    return json.loads(config_str)

# Sunrise automation config
sunrise_config = {"id":"1770750723106","alias":"🌅 Rollläden hochfahren bei Sonnenaufgang","description":"Rollläden fahren parallel hoch: Frühestens ab Schedule-Start UND Sonne ist auf (was später ist) + pro Rollladen 0-10 Min Zufall","mode":"single","trigger":[{"event":"sunrise","offset":"00:10:00","id":"sun_trigger","platform":"sun"},{"entity_id":"schedule.rolladen_zeitplan","to":"on","id":"schedule_trigger","platform":"state"}],"action":[{"choose":[{"conditions":[{"condition":"trigger","id":"sun_trigger"},{"condition":"state","entity_id":"schedule.rolladen_zeitplan","state":"on"}],"sequence":[{"parallel":[{"sequence":[{"delay":{"seconds":"{{ range(0, 600) | random }}"}},{"target":{"entity_id":"cover.esszimmer_gross_rollo"},"action":"cover.open_cover"}]},{"sequence":[{"delay":{"seconds":"{{ range(0, 600) | random }}"}},{"target":{"entity_id":"cover.esszimmer_klein_rollo"},"action":"cover.open_cover"}]},{"sequence":[{"delay":{"seconds":"{{ range(0, 600) | random }}"}},{"target":{"entity_id":"cover.arbeitszimmer_oben_rollo"},"action":"cover.open_cover"}]},{"sequence":[{"delay":{"seconds":"{{ range(0, 600) | random }}"}},{"target":{"entity_id":"cover.arbeitszimmer_unten_vorne_rollo"},"action":"cover.open_cover"}]},{"sequence":[{"delay":{"seconds":"{{ range(0, 600) | random }}"}},{"target":{"entity_id":"cover.arbeitszimmer_unten_seite_rollo"},"action":"cover.open_cover"}]},{"sequence":[{"delay":{"seconds":"{{ range(0, 600) | random }}"}},{"target":{"entity_id":"cover.wohnzimmer_gross_rollo"},"action":"cover.open_cover"}]},{"sequence":[{"delay":{"seconds":"{{ range(0, 600) | random }}"}},{"target":{"entity_id":"cover.wohnzimmer_klein_rollo"},"action":"cover.open_cover"}]},{"sequence":[{"delay":{"seconds":"{{ range(0, 600) | random }}"}},{"target":{"entity_id":"cover.bad_unten_rollo"},"action":"cover.open_cover"}]},{"sequence":[{"delay":{"seconds":"{{ range(0, 600) | random }}"}},{"target":{"entity_id":"cover.kinderzimmer_rollo"},"action":"cover.open_cover"}]},{"sequence":[{"delay":{"seconds":"{{ range(0, 600) | random }}"}},{"target":{"entity_id":"cover.kuche_rollo"},"action":"cover.open_cover"}]}]}]},{"conditions":[{"condition":"trigger","id":"schedule_trigger"},{"condition":"state","entity_id":"sun.sun","state":"above_horizon"}],"sequence":[{"parallel":[{"sequence":[{"delay":{"seconds":"{{ range(0, 600) | random }}"}},{"target":{"entity_id":"cover.esszimmer_gross_rollo"},"action":"cover.open_cover"}]},{"sequence":[{"delay":{"seconds":"{{ range(0, 600) | random }}"}},{"target":{"entity_id":"cover.esszimmer_klein_rollo"},"action":"cover.open_cover"}]},{"sequence":[{"delay":{"seconds":"{{ range(0, 600) | random }}"}},{"target":{"entity_id":"cover.arbeitszimmer_oben_rollo"},"action":"cover.open_cover"}]},{"sequence":[{"delay":{"seconds":"{{ range(0, 600) | random }}"}},{"target":{"entity_id":"cover.arbeitszimmer_unten_vorne_rollo"},"action":"cover.open_cover"}]},{"sequence":[{"delay":{"seconds":"{{ range(0, 600) | random }}"}},{"target":{"entity_id":"cover.arbeitszimmer_unten_seite_rollo"},"action":"cover.open_cover"}]},{"sequence":[{"delay":{"seconds":"{{ range(0, 600) | random }}"}},{"target":{"entity_id":"cover.wohnzimmer_gross_rollo"},"action":"cover.open_cover"}]},{"sequence":[{"delay":{"seconds":"{{ range(0, 600) | random }}"}},{"target":{"entity_id":"cover.wohnzimmer_klein_rollo"},"action":"cover.open_cover"}]},{"sequence":[{"delay":{"seconds":"{{ range(0, 600) | random }}"}},{"target":{"entity_id":"cover.bad_unten_rollo"},"action":"cover.open_cover"}]},{"sequence":[{"delay":{"seconds":"{{ range(0, 600) | random }}"}},{"target":{"entity_id":"cover.kinderzimmer_rollo"},"action":"cover.open_cover"}]},{"sequence":[{"delay":{"seconds":"{{ range(0, 600) | random }}"}},{"target":{"entity_id":"cover.kuche_rollo"},"action":"cover.open_cover"}]}]}]}],"default":[]}],"condition":[]}

updated_sunrise = replace_entity_ids(sunrise_config)
print(json.dumps(updated_sunrise, indent=2))
