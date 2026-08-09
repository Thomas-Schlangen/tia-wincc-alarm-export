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

`Time_ms` ist kein Unix-Timestamp und kein Windows-FILETIME, sondern ein
**OLE Automation Date, skaliert mit 1.000.000** (laut Siemens Dok-ID
109747174): Ganzzahlteil von `Time_ms / 1.000.000` = Tage seit der
OLE-Epoche 30.12.1899, Nachkommastellen = Tagesbruchteil (Uhrzeit). WinCC
Advanced speichert in Lokalzeit des Panels, es ist keine UTC-Konvertierung
nötig. `Time_ms` bleibt unverändert als Rohwert in der CSV erhalten (u.a.
als Sortierschlüssel für die chronologische Reihenfolge) und wird
zusätzlich um eine berechnete Spalte `Timestamp` (lesbares Datum) ergänzt.

Die Umrechnung (`core.timestamp_to_datetime`) ist gegen echte Paneldaten
verifiziert (`Time_ms 46243611628.69` → `09.08.2026 14:40:44`,
`Time_ms 46243561204.19` → `09.08.2026 13:28:08` — deckt sich exakt mit den
Datei-Zeitstempeln der zugehörigen `.rdb`-Backups) und ist panelunabhängig,
da die OLE-Epoche fest ist und nicht kalibriert werden muss.

## Tests

```
pytest
```
