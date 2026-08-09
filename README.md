# tia-wincc-alarm-export

## Zweck

Führt mehrere WinCC/TIA-Portal-Störarchiv-Dateien (SQLite-Datenbanken, Endung
`.rdb`) aus einem Ordner chronologisch sortiert (nach `Time_ms`) zu einer
einzigen CSV-Datei zusammen.

## Installation

Voraussetzung: Python >= 3.12

```
pip install -e .[dev]
```

## Nutzung

```
tia-wincc-alarm-export
```

oder ohne Installation:

```
python -m tia_wincc_alarm_export.main
```

Es öffnet sich eine GUI: Eingabeordner mit `.rdb`-Dateien wählen, Ausgabepfad
bestätigen oder ändern (Default: `output/alarms.csv`), Export starten.

## Datenformat

Jede `.rdb`-Datei enthält eine Tabelle `logdata` mit den Spalten `Time_ms,
MsgProc, StateAfter, MsgClass, MsgNumber, Var1..Var8, TimeString, MsgText,
PLC`. `TimeString` ist auf dem Panel immer leer/`None` und wird nicht
verwendet. Die CSV wird als UTF-8 mit BOM (`utf-8-sig`) geschrieben, damit
Excel Umlaute korrekt anzeigt.

### Zeitstempel (Time_ms / Timestamp)

`Time_ms` ist kein Unix-Timestamp und kein Windows-FILETIME, sondern
Millisekunden seit einer **gerätespezifischen Epoche**, die beim ersten Start
des Panels gesetzt wird und nicht vorhersagbar ist. `Time_ms` bleibt
unverändert als Rohwert in der CSV erhalten (u.a. als Sortierschlüssel für
die chronologische Reihenfolge) und wird zusätzlich um eine berechnete Spalte
`Timestamp` (lesbares Datum) ergänzt.

Die Epoche ist in `core.EPOCH` fest kodiert und wurde für das Testpanel
dieses Projekts anhand eines bekannten Referenzpunkts kalibriert
(`Time_ms 46243611628.69` → `09.08.2026 14:44:32`). **Diese Epoche gilt nur
für dieses Panel.** Bei einem anderen Panel oder nach dessen
Neuinitialisierung ändert sie sich und `core.EPOCH` muss neu kalibriert
werden (z.B. anhand eines Ereignisses mit bekanntem Zeitpunkt).

## Tests

```
pytest
```
