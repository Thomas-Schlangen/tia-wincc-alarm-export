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
PLC`. `Time_ms` wird unverändert als Rohwert übernommen (keine
Datumsumrechnung) und dient als alleiniges Sortierkriterium. Die CSV wird als
UTF-8 mit BOM (`utf-8-sig`) geschrieben, damit Excel Umlaute korrekt anzeigt.

## Tests

```
pytest
```
