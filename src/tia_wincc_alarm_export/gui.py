"""Tkinter-GUI: Ordner-/Dateiauswahl und Start des Exports."""

from __future__ import annotations

import logging
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from tia_wincc_alarm_export import core

logger = logging.getLogger(__name__)

DEFAULT_OUTPUT: Path = Path("output") / "alarms.csv"


class App(ttk.Frame):
    def __init__(self, master: tk.Tk) -> None:
        super().__init__(master, padding=12)
        self.master = master
        self.input_folder = tk.StringVar(value="")
        self.output_path = tk.StringVar(value=str(DEFAULT_OUTPUT))
        self.status = tk.StringVar(value="")

        self.pack(fill="both", expand=True)
        self._build_widgets()

    def _build_widgets(self) -> None:
        ttk.Label(self, text="Störarchiv-Ordner:").grid(row=0, column=0, sticky="w")
        ttk.Entry(self, textvariable=self.input_folder, width=60).grid(
            row=1, column=0, sticky="ew"
        )
        ttk.Button(self, text="Wählen...", command=self._choose_input_folder).grid(
            row=1, column=1, padx=(6, 0)
        )

        ttk.Label(self, text="Ausgabe-CSV:").grid(
            row=2, column=0, sticky="w", pady=(12, 0)
        )
        ttk.Entry(self, textvariable=self.output_path, width=60).grid(
            row=3, column=0, sticky="ew"
        )
        ttk.Button(self, text="Wählen...", command=self._choose_output_path).grid(
            row=3, column=1, padx=(6, 0)
        )

        ttk.Button(self, text="Exportieren", command=self._run_export).grid(
            row=4, column=0, columnspan=2, pady=(16, 0)
        )

        ttk.Label(self, textvariable=self.status, foreground="gray").grid(
            row=5, column=0, columnspan=2, sticky="w", pady=(12, 0)
        )

        self.columnconfigure(0, weight=1)

    def _choose_input_folder(self) -> None:
        path = filedialog.askdirectory(
            title="Störarchiv-Ordner wählen",
            initialdir=self.input_folder.get() or ".",
        )
        if path:
            self.input_folder.set(path)

    def _choose_output_path(self) -> None:
        current = Path(self.output_path.get() or DEFAULT_OUTPUT)
        path = filedialog.asksaveasfilename(
            title="CSV-Ausgabedatei wählen",
            defaultextension=".csv",
            filetypes=[("CSV-Datei", "*.csv"), ("Alle Dateien", "*.*")],
            initialfile=current.name,
            initialdir=str(current.parent) if str(current.parent) else ".",
        )
        if path:
            self.output_path.set(path)

    def _run_export(self) -> None:
        input_folder = Path(self.input_folder.get())
        output_path = Path(self.output_path.get())

        if not input_folder.is_dir():
            messagebox.showerror(
                "Fehler", f"Kein gültiger Ordner ausgewählt:\n{input_folder}"
            )
            return

        try:
            row_count = core.export(input_folder, output_path)
        except Exception as exc:  # noqa: BLE001 - letzte Instanz gegen rohe Tracebacks in der GUI
            logger.exception("Export fehlgeschlagen")
            messagebox.showerror("Fehler beim Export", str(exc))
            return

        self.status.set(f"{row_count} Zeilen exportiert nach {output_path}")
        messagebox.showinfo(
            "Export erfolgreich",
            f"{row_count} Zeilen wurden exportiert nach:\n{output_path}",
        )
