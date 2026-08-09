"""Einstiegspunkt: Logging-Setup und Start der GUI."""

from __future__ import annotations

import logging
import tkinter as tk

from tia_wincc_alarm_export.gui import App


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    root = tk.Tk()
    root.title("TIA/WinCC Störarchiv Export")
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
