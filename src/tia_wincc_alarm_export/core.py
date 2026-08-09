"""Kernlogik zum Einlesen, Zusammenführen und Exportieren von WinCC-Störarchiven."""

from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

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
TABLE_NAME = "logdata"


class SchemaError(Exception):
    """Wird ausgelöst, wenn eine .rdb-Datei nicht das erwartete logdata-Schema hat."""


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
    """Schreibt COLUMNS als Header + rows nach output_path (UTF-8 mit BOM)."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(COLUMNS)
        writer.writerows(rows)


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
