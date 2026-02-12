# Home Assistant Blueprint: Fenster/Tür offen bei Kälte Warnung

Ein Blueprint für Home Assistant, der benachrichtigt, wenn ein Fenster oder eine Tür zu lange bei niedrigen Außentemperaturen offen ist.

## Beschreibung

Dieser Blueprint ermöglicht es, für jedes Fenster und jede Tür eine individuelle Automation zu erstellen, die eine Benachrichtigung sendet, wenn:
- Das Fenster/die Tür für eine konfigurierbare Zeit geöffnet ist
- Die Außentemperatur unter einem konfigurierbaren Schwellenwert liegt

## Features

- ✅ Individuell konfigurierbare Dauer pro Fenster/Tür (1-120 Minuten)
- ✅ Individuell konfigurierbare Temperatur-Schwelle pro Fenster/Tür (-20 bis 30°C)
- ✅ Flexible Wetter-Entity Auswahl
- ✅ Anpassbarer Benachrichtigungsdienst
- ✅ Keine Helper (input_number) erforderlich

## Installation

### Methode 1: Direkt Import in Home Assistant

1. Gehe zu **Einstellungen** → **Automationen & Szenen** → **Blueprints**
2. Klicke auf **Blueprint importieren**
3. Füge diese URL ein:
   ```
   https://github.com/DEIN_USERNAME/REPO_NAME/blob/main/cold_window_alert_blueprint.yaml
   ```

### Methode 2: Manuelle Installation

1. Kopiere `cold_window_alert_blueprint.yaml` nach:
   ```
   <config>/blueprints/automation/cold_window_alert_blueprint.yaml
   ```
2. Starte Home Assistant neu oder lade die Automationen neu

## Verwendung

1. Gehe zu **Einstellungen** → **Automationen & Szenen**
2. Klicke auf **Automation erstellen** → **Mit Blueprint beginnen**
3. Wähle "Fenster/Tür offen bei Kälte Warnung"
4. Konfiguriere:
   - **Fenster/Tür Sensor**: Wähle deinen Binary Sensor (z.B. `binary_sensor.wohnzimmer_fenster`)
   - **Dauer**: Wie lange soll das Fenster offen sein? (Standard: 10 Minuten)
   - **Temperatur Schwelle**: Bei welcher Temperatur warnen? (Standard: 15°C)
   - **Wetter Entity**: Wetter-Sensor (Standard: `weather.forecast_home`)
   - **Benachrichtigungsdienst**: z.B. `notify.notify`

## Beispiel

Für ein Wohnzimmerfenster könnte die Konfiguration so aussehen:
- Sensor: `binary_sensor.wohnzimmer_fenster_klein`
- Dauer: 15 Minuten
- Temperatur: 10°C
- Wetter: `weather.forecast_home`
- Benachrichtigung: `notify.notify`

→ Du erhältst eine Benachrichtigung, wenn das Wohnzimmerfenster länger als 15 Minuten offen ist und es draußen unter 10°C hat.

## Lizenz

MIT License - Frei verwendbar

## Changelog

### v1.0.0 (2026-02-12)
- Initiales Release
- Unterstützung für individuelle Fenster/Tür-Konfigurationen
- Keine Helper erforderlich
