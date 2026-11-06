"""Pannello operativo grafico Senalox: riusa gli script CLI esistenti."""
from __future__ import annotations

import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk, filedialog

ROOT = Path(__file__).resolve().parent
OPS = "analysis.laboratory.trigger_patterns.operational"


class OperationalPanel(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Senalox - Strumenti operativi NEW MODE")
        self.geometry("1000x700")
        self.minsize(760, 540)
        self.events = queue.Queue()
        self.running = False
        self.buttons = []
        self._build()
        self.after(100, self._drain)

    def _build(self):
        outer = ttk.Frame(self, padding=14)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="SENALOX | Strumenti operativi NEW MODE",
                  font=("Arial", 16, "bold")).pack(anchor="w", pady=(0, 12))
        controls = ttk.Frame(outer)
        controls.pack(fill="x")
        self._section(controls, "Archivio", [
            ("Aggiorna estrazioni", lambda: self._run(["update_estrazioni.py"], script=True)),
        ])
        self._section(controls, "Trigger", [
            ("Trigger attivi", lambda: self._run([OPS + ".active_triggers"])),
            ("Performance annuali (tutti gli anni)", lambda: self._run([OPS + ".performance_by_year"])),
            ("Performance anno selezionato", self._performance),
            ("Ranking attivi (anno / 4 mesi)", self._ranking),
        ])
        self._section(controls, "Risultati e sestine", [
            ("Controlla ultime estrazioni", self._check),
            ("Genera sestine", self._generate),
        ])
        params = ttk.LabelFrame(outer, text="Parametri", padding=10)
        params.pack(fill="x", pady=(10, 8))
        self.year = tk.StringVar(value=str(__import__("datetime").date.today().year))
        self.draws = tk.StringVar(value="1")
        self.count = tk.StringVar(value="3")
        self.period = tk.StringVar(value="auto")
        ttk.Label(params, text="Anno").grid(row=0, column=0, padx=4)
        ttk.Entry(params, textvariable=self.year, width=8).grid(row=0, column=1, padx=4)
        ttk.Label(params, text="Ultime estrazioni").grid(row=0, column=2, padx=4)
        ttk.Entry(params, textvariable=self.draws, width=7).grid(row=0, column=3, padx=4)
        ttk.Label(params, text="Sestine").grid(row=0, column=4, padx=4)
        ttk.Entry(params, textvariable=self.count, width=7).grid(row=0, column=5, padx=4)
        ttk.Label(params, text="Periodo ranking").grid(row=0, column=6, padx=4)
        ttk.Combobox(params, textvariable=self.period, values=("auto", "anno", "4mesi"),
                     state="readonly", width=8).grid(row=0, column=7, padx=4)
        bar = ttk.Frame(outer)
        bar.pack(fill="x", pady=(4, 6))
        self.status = tk.StringVar(value="Pronto")
        ttk.Label(bar, textvariable=self.status).pack(side="left")
        ttk.Button(bar, text="Salva output...", command=self._save).pack(side="right", padx=4)
        ttk.Button(bar, text="Pulisci", command=lambda: self.output.delete("1.0", "end")).pack(side="right")
        frame = ttk.Frame(outer)
        frame.pack(fill="both", expand=True)
        self.output = tk.Text(frame, wrap="none", font=("Consolas", 10), state="normal")
        yscroll = ttk.Scrollbar(frame, command=self.output.yview)
        xscroll = ttk.Scrollbar(frame, orient="horizontal", command=self.output.xview)
        self.output.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        self.output.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

    def _section(self, parent, title, items):
        frame = ttk.LabelFrame(parent, text=title, padding=8)
        frame.pack(side="left", fill="both", expand=True, padx=(0, 7))
        for name, callback in items:
            btn = ttk.Button(frame, text=name, command=callback)
            btn.pack(fill="x", pady=3)
            self.buttons.append(btn)

    def _positive(self, value, label):
        try:
            number = int(value)
            if number < 1:
                raise ValueError
            return number
        except ValueError:
            messagebox.showerror("Parametro non valido", f"{label}: inserire un intero positivo.")
            return None

    def _check(self):
        n = self._positive(self.draws.get(), "Ultime estrazioni")
        if n is not None:
            self._run([OPS + ".check_draws", "-x", str(n)])

    def _performance(self):
        year = self._positive(self.year.get(), "Anno")
        if year is not None:
            self._run([OPS + ".trigger_performance", "--year", str(year)])

    def _ranking(self):
        # Stesso ranking utilizzato dal generatore, senza estrarre sestine.
        self._run([OPS + ".generate_sestine", "-n", "1", "--periodo", self.period.get(), "--ranking-only"])

    def _generate(self):
        n = self._positive(self.count.get(), "Numero sestine")
        if n is not None:
            self._run([OPS + ".generate_sestine", "-n", str(n), "--periodo", self.period.get()])

    def _run(self, args, script=False):
        if self.running:
            return
        command = [sys.executable] + ([str(ROOT / args[0])] if script else ["-m", args[0]]) + args[1:]
        self.running = True
        for btn in self.buttons:
            btn.configure(state="disabled")
        self.output.delete("1.0", "end")
        self.status.set("Esecuzione in corso...")
        self.output.insert("end", "Comando: " + " ".join(command[1:]) + "\n\n")
        threading.Thread(target=self._worker, args=(command,), daemon=True).start()

    def _worker(self, command):
        try:
            env = os.environ.copy()
            env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
            env["PYTHONIOENCODING"] = "utf-8"
            proc = subprocess.Popen(command, cwd=ROOT, env=env, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                                    errors="replace", bufsize=1)
            for line in proc.stdout:
                self.events.put(("line", line))
            code = proc.wait()
            self.events.put(("done", code))
        except Exception as exc:
            self.events.put(("error", str(exc)))

    def _drain(self):
        try:
            while True:
                kind, data = self.events.get_nowait()
                if kind == "line":
                    self.output.insert("end", data)
                    self.output.see("end")
                else:
                    self.running = False
                    for btn in self.buttons:
                        btn.configure(state="normal")
                    if kind == "error":
                        self.output.insert("end", "\nERRORE: " + data + "\n")
                        self.status.set("Errore")
                    else:
                        self.status.set("Completato" if data == 0 else f"Errore (codice {data})")
        except queue.Empty:
            pass
        self.after(100, self._drain)

    def _save(self):
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Testo", "*.txt"), ("Tutti", "*.*")])
        if path:
            Path(path).write_text(self.output.get("1.0", "end-1c"), encoding="utf-8")


if __name__ == "__main__":
    OperationalPanel().mainloop()
