from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

import pytest

from tia_wincc_alarm_export import core

DDL = """
CREATE TABLE logdata (
    Time_ms DOUBLE,
    MsgProc INT,
    StateAfter INT,
    MsgClass INT,
    MsgNumber INT,
    Var1 TEXT,
    Var2 TEXT,
    Var3 TEXT,
    Var4 TEXT,
    Var5 TEXT,
    Var6 TEXT,
    Var7 TEXT,
    Var8 TEXT,
    TimeString TEXT,
    MsgText TEXT,
    PLC TEXT
)
"""


def _make_rdb(path: Path, rows: list[tuple]) -> None:
    """Legt eine SQLite-DB mit dem Zielschema an path an und fügt rows ein."""
    conn = sqlite3.connect(path)
    try:
        conn.execute(DDL)
        placeholders = ", ".join("?" for _ in core.COLUMNS)
        conn.executemany(
            f"INSERT INTO logdata VALUES ({placeholders})", rows
        )
        conn.commit()
    finally:
        conn.close()


def _row(time_ms: float, msg_text: str = "Testmeldung", plc: str = "PLC1") -> tuple:
    return (
        time_ms,
        1,
        1,
        3,
        110001,
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        "",
        None,
        msg_text,
        plc,
    )


def test_find_rdb_files_returns_only_rdb(tmp_path: Path) -> None:
    (tmp_path / "a.rdb").touch()
    (tmp_path / "b.rdb").touch()
    (tmp_path / "notes.txt").touch()

    result = core.find_rdb_files(tmp_path)

    assert [p.name for p in result] == ["a.rdb", "b.rdb"]


def test_read_rdb_file_reads_all_columns_in_order(tmp_path: Path) -> None:
    path = tmp_path / "one.rdb"
    _make_rdb(path, [_row(100.0, msg_text="Hallo")])

    rows = core.read_rdb_file(path)

    assert rows == [
        (100.0, 1, 1, 3, 110001, "", "", "", "", "", "", "", "", None, "Hallo", "PLC1")
    ]


def test_read_rdb_file_empty_table(tmp_path: Path) -> None:
    path = tmp_path / "empty.rdb"
    _make_rdb(path, [])

    assert core.read_rdb_file(path) == []


def test_read_rdb_file_missing_table_raises_schema_error(tmp_path: Path) -> None:
    path = tmp_path / "wrong.rdb"
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE other (id INT)")
    conn.commit()
    conn.close()

    with pytest.raises(core.SchemaError):
        core.read_rdb_file(path)


def test_read_rdb_file_missing_column_raises_schema_error(tmp_path: Path) -> None:
    path = tmp_path / "incomplete.rdb"
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE logdata (Time_ms DOUBLE, MsgProc INT)")
    conn.commit()
    conn.close()

    with pytest.raises(core.SchemaError, match="PLC"):
        core.read_rdb_file(path)


def test_merge_and_sort_orders_by_time_ms_across_files() -> None:
    file_a = [_row(300.0), _row(100.0)]
    file_b = [_row(200.0)]

    result = core.merge_and_sort([file_a, file_b])

    assert [row[0] for row in result] == [100.0, 200.0, 300.0]


def test_merge_and_sort_handles_empty_lists() -> None:
    file_a: list[tuple] = []
    file_b = [_row(50.0)]

    result = core.merge_and_sort([file_a, file_b])

    assert [row[0] for row in result] == [50.0]


def test_write_csv_utf8_sig_and_umlauts(tmp_path: Path) -> None:
    output_path = tmp_path / "out.csv"
    rows = [_row(1.0, msg_text="License Key nicht verfügbar!")]

    core.write_csv(rows, output_path)

    with output_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        data_row = next(reader)

    assert tuple(header) == core.COLUMNS
    assert "verfügbar" in data_row[core.COLUMNS.index("MsgText")]


def test_export_end_to_end_multiple_files(tmp_path: Path) -> None:
    _make_rdb(tmp_path / "Stoerarchiv0.rdb", [_row(300.0)])
    _make_rdb(tmp_path / "Stoerarchiv1.rdb", [])
    _make_rdb(tmp_path / "Stoerarchiv2.rdb", [_row(100.0), _row(200.0)])

    output_path = tmp_path / "output" / "alarms.csv"
    row_count = core.export(tmp_path, output_path)

    assert row_count == 3

    with output_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        next(reader)  # header
        time_values = [float(row[0]) for row in reader]

    assert time_values == [100.0, 200.0, 300.0]


def test_export_raises_when_no_rdb_files(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        core.export(tmp_path, tmp_path / "out.csv")
