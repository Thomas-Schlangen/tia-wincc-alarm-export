"""Kernlogik zum Einlesen, Zusammenführen und Exportieren von WinCC-Störarchiven."""

from __future__ import annotations

import csv
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

# Time_ms ist kein Unix-Timestamp und kein Windows-FILETIME, sondern ein
# OLE Automation Date (Tage seit 30.12.1899, Nachkommastellen = Tagesbruchteil
# für die Uhrzeit), skaliert mit 1.000.000 (laut Siemens Dok-ID 109747174).
# WinCC Advanced speichert in Lokalzeit des Panels, keine UTC-Konvertierung
# nötig. Wichtig: Epoche ist der 30.12.1899, nicht der 31.12.1899.
OLE_EPOCH = datetime(1899, 12, 30)

COLUMNS: tuple[str, ...] = (
    "Time_ms",
    "MsgProc",
    "StateAfter",
    "MsgClass",
    "MsgNumber",
    "Var1",
    "Var2",
    "Var3",
    "Var4",
    "Var5",
    "Var6",
    "Var7",
    "Var8",
    "TimeString",
    "MsgText",
    "PLC",
)
CSV_COLUMNS: tuple[str, ...] = (*COLUMNS, "Timestamp")
TABLE_NAME = "logdata"


class SchemaError(Exception):
    """Wird ausgelöst, wenn eine .rdb-Datei nicht das erwartete logdata-Schema hat."""


def timestamp_to_datetime(time_ms: float) -> datetime:
    """Konvertiert einen Time_ms-Rohwert (OLE Automation Date * 1.000.000) in datetime.

    Verifiziert gegen echte Paneldaten:
    - time_ms 46243611628.69 -> 09.08.2026 14:40:44
    - time_ms 46243561204.19 -> 09.08.2026 13:28:08
    """
    ole_date = time_ms / 1_000_000
    return OLE_EPOCH + timedelta(days=ole_date)


def find_rdb_files(folder: Path) -> list[Path]:
    """Alle *.rdb-Dateien direkt in folder, alphabetisch sortiert."""
    return sorted(folder.glob("*.rdb"))


def _verify_schema(conn: sqlite3.Connection, path: Path) -> None:
    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    if TABLE_NAME not in tables:
        raise SchemaError(f"{path}: Tabelle '{TABLE_NAME}' nicht gefunden.")

    existing_columns = {
        row[1] for row in conn.execute(f"PRAGMA table_info({TABLE_NAME})").fetchall()
    }
    missing = [c for c in COLUMNS if c not in existing_columns]
    if missing:
        raise SchemaError(
            f"{path}: Tabelle '{TABLE_NAME}' fehlen erwartete Spalten: {', '.join(missing)}"
        )


def read_rdb_file(path: Path) -> list[tuple]:
    """Liest alle Zeilen aus logdata, in COLUMNS-Reihenfolge, read-only."""
    uri = f"{path.resolve().as_uri()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    try:
        _verify_schema(conn, path)
        select_columns = ", ".join(COLUMNS)
        cursor = conn.execute(f"SELECT {select_columns} FROM {TABLE_NAME}")
        return cursor.fetchall()
    finally:
        conn.close()


def merge_and_sort(rows_per_file: list[list[tuple]]) -> list[tuple]:
    """Flacht alle Zeilenlisten ab und sortiert aufsteigend nach Time_ms (Index 0)."""
    all_rows = [row for rows in rows_per_file for row in rows]
    all_rows.sort(key=lambda row: row[0])
    return all_rows


def write_csv(rows: list[tuple], output_path: Path) -> None:
    """Schreibt CSV_COLUMNS als Header + rows (samt berechneter Timestamp-Spalte)
    nach output_path (UTF-8 mit BOM). Time_ms bleibt unverändert als Rohwert erhalten."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(CSV_COLUMNS)
        for row in rows:
            timestamp = timestamp_to_datetime(row[0]).isoformat(sep=" ", timespec="milliseconds")
            writer.writerow((*row, timestamp))


def export(input_folder: Path, output_path: Path) -> int:
    """Liest alle .rdb-Dateien aus input_folder, mergt/sortiert sie chronologisch
    und schreibt sie nach output_path. Gibt die Anzahl geschriebener Zeilen zurück."""
    rdb_files = find_rdb_files(input_folder)
    if not rdb_files:
        raise FileNotFoundError(f"Keine .rdb-Dateien gefunden in: {input_folder}")

    rows_per_file = [read_rdb_file(path) for path in rdb_files]
    rows = merge_and_sort(rows_per_file)
    write_csv(rows, output_path)
    return len(rows)
