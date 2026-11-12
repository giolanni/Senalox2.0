"""Pannello operativo Senalox: navigazione laterale, comandi e console."""
from __future__ import annotations

import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from datetime import date, datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

ROOT = Path(__file__).resolve().parent
OPS = "analysis.laboratory.trigger_patterns.operational"
BG = "#f3f6fb"
NAV = "#17263d"
ACCENT = "#2563eb"
TEXT = "#19283b"
MUTED = "#64748b"


class OperationalPanel(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Senalox | Pannello operativo")
        self.geometry("1120x760")
        self.minsize(900, 630)
        self.configure(bg=BG)
        self.events = queue.Queue()
        self.running = False
        self.buttons = []
        self.nav_buttons = {}
        self.page = None
        self.year = tk.StringVar(value=str(date.today().year))
        self.draws = tk.StringVar(value="1")
        self.count = tk.StringVar(value="3")
        self.period = tk.StringVar(value="auto")
        self.date_from = tk.StringVar()
        self.date_to = tk.StringVar()
        self.status = tk.StringVar(value="Pronto")
        self._style()
        self._build()
        self._show("Archivio")
        self.after(100, self._drain)

    def _style(self):
        style = ttk.Style(self)
        style.configure("App.TFrame", background=BG)
        style.configure("Card.TFrame", background="#ffffff")
        style.configure("Card.TLabel", background="#ffffff", foreground=TEXT, font=("Segoe UI", 10))
        style.configure("Heading.TLabel", background=BG, foreground=TEXT, font=("Segoe UI", 19, "bold"))
        style.configure("Muted.TLabel", background=BG, foreground=MUTED, font=("Segoe UI", 10))
        style.configure("Action.TButton", font=("Segoe UI", 10), padding=(14, 10))
        style.configure("App.TEntry", padding=5)
        style.configure("App.TCombobox", padding=5)

    def _build(self):
        nav = tk.Frame(self, bg=NAV, width=228)
        nav.pack(side="left", fill="y")
        nav.pack_propagate(False)
        tk.Label(nav, text="SENALOX", bg=NAV, fg="white",
                 font=("Segoe UI", 19, "bold"), anchor="w").pack(fill="x", padx=22, pady=(28, 2))
        tk.Label(nav, text="PANNELLO OPERATIVO", bg=NAV, fg="#9db1cc",
                 font=("Segoe UI", 9), anchor="w").pack(fill="x", padx=22, pady=(0, 32))
        for name in ("Archivio", "Trigger", "Risultati", "Sestine", "Repository Git"):
            btn = tk.Button(nav, text=name, anchor="w", relief="flat", bd=0,
                            padx=20, pady=13, cursor="hand2",
                            bg=NAV, fg="#dbe6f5", activebackground="#284466",
                            activeforeground="white", font=("Segoe UI", 11),
                            command=lambda n=name: self._show(n))
            btn.pack(fill="x", padx=9, pady=3)
            self.nav_buttons[name] = btn
        tk.Label(nav, text="Git e analisi in un unico posto", bg=NAV, fg="#8da2bd",
                 font=("Segoe UI", 9), wraplength=180, justify="left").pack(side="bottom", anchor="w", padx=22, pady=25)

        main = ttk.Frame(self, style="App.TFrame", padding=(24, 20))
        main.pack(side="left", fill="both", expand=True)
        self.heading = ttk.Label(main, style="Heading.TLabel")
        self.heading.pack(anchor="w")
        self.description = ttk.Label(main, style="Muted.TLabel")
        self.description.pack(anchor="w", pady=(4, 16))
        self.panel = ttk.Frame(main, style="Card.TFrame", padding=16)
        self.panel.pack(fill="x")
        toolbar = ttk.Frame(main, style="App.TFrame")
        toolbar.pack(fill="x", pady=(18, 8))
        ttk.Label(toolbar, text="Risultati operazione", style="Heading.TLabel",
                  font=("Segoe UI", 12, "bold")).pack(side="left")
        ttk.Button(toolbar, text="Salva testo", command=self._save).pack(side="right", padx=(8, 0))
        ttk.Button(toolbar, text="Pulisci", command=self._clear).pack(side="right")
        console = ttk.Frame(main, style="App.TFrame")
        console.pack(fill="both", expand=True)
        self.output = tk.Text(console, wrap="none", bg="#ffffff", fg=TEXT,
                              font=("Consolas", 10), relief="flat", padx=12, pady=12)
        y = ttk.Scrollbar(console, command=self.output.yview)
        x = ttk.Scrollbar(console, orient="horizontal", command=self.output.xview)
        self.output.configure(yscrollcommand=y.set, xscrollcommand=x.set)
        self.output.grid(row=0, column=0, sticky="nsew")
        y.grid(row=0, column=1, sticky="ns")
        x.grid(row=1, column=0, sticky="ew")
        console.columnconfigure(0, weight=1)
        console.rowconfigure(0, weight=1)
        footer = ttk.Frame(main, style="App.TFrame")
        footer.pack(fill="x", pady=(9, 0))
        ttk.Label(footer, textvariable=self.status, style="Muted.TLabel").pack(side="left")

    def _show(self, name):
        self.page = name
        for label, button in self.nav_buttons.items():
            button.configure(bg=ACCENT if label == name else NAV,
                             fg="white" if label == name else "#dbe6f5")
        for child in self.panel.winfo_children():
            child.destroy()
        self.buttons = []
        descriptions = {
            "Archivio": "Aggiorna l'archivio delle estrazioni.",
            "Trigger": "Controlla trigger attivi, performance e classifiche.",
            "Risultati": "Verifica gli esiti delle ultime estrazioni o di un intervallo.",
            "Sestine": "Genera combinazioni dai trigger selezionati dal ranking.",
            "Repository Git": "Controlla le modifiche e sincronizza il progetto con GitHub.",
        }
        self.heading.configure(text=name)
        self.description.configure(text=descriptions[name])
        if name == "Archivio":
            self._action("Aggiorna estrazioni", lambda: self._run(["update_estrazioni.py"], script=True))
            self._hint("L'aggiornamento scarica le estrazioni disponibili e aggiorna i dati locali.")
        elif name == "Trigger":
            self._action("Visualizza trigger attivi", lambda: self._run([OPS + ".active_triggers"]))
            self._action("Performance di tutti gli anni", lambda: self._run([OPS + ".performance_by_year"]))
            row = self._fields()
            self._field(row, "Anno", self.year, 10)
            self._action("Performance anno selezionato", self._performance)
            self._field(row, "Periodo ranking", self.period, 12, choices=("auto", "anno", "4mesi"))
            self._action("Ranking dei trigger attivi", self._ranking)
        elif name == "Risultati":
            row = self._fields()
            self._field(row, "Numero ultime estrazioni", self.draws, 12)
            self._action("Controlla ultime N estrazioni", self._check)
            row = self._fields()
            self._field(row, "Dal (GG/MM/AAAA)", self.date_from, 16)
            self._field(row, "Al (GG/MM/AAAA)", self.date_to, 16)
            self._action("Controlla intervallo di date", self._check_dates)
        elif name == "Sestine":
            row = self._fields()
            self._field(row, "Numero sestine", self.count, 10)
            self._field(row, "Periodo ranking", self.period, 12, choices=("auto", "anno", "4mesi"))
            self._action("Genera sestine", self._generate)
        else:
            self._hint("La gestione Git si apre in una finestra dedicata. Le operazioni che modificano i dati richiedono conferma.")
            self._action("Apri gestione repository Git", self._open_repository)
        if self.running:
            for button in self.buttons:
                button.configure(state="disabled")

    def _fields(self):
        row = ttk.Frame(self.panel, style="Card.TFrame")
        row.pack(fill="x", pady=(4, 10))
        return row

    def _field(self, parent, label, variable, width, choices=None):
        item = ttk.Frame(parent, style="Card.TFrame")
        item.pack(side="left", padx=(0, 20))
        ttk.Label(item, text=label, style="Card.TLabel").pack(anchor="w", pady=(0, 4))
        if choices:
            ttk.Combobox(item, textvariable=variable, values=choices, width=width,
                         state="readonly", style="App.TCombobox").pack(anchor="w")
        else:
            ttk.Entry(item, textvariable=variable, width=width,
                      style="App.TEntry").pack(anchor="w")

    def _action(self, label, callback):
        button = ttk.Button(self.panel, text=label, command=callback, style="Action.TButton")
        button.pack(anchor="w", pady=5)
        self.buttons.append(button)

    def _hint(self, text):
        ttk.Label(self.panel, text=text, style="Card.TLabel", wraplength=700).pack(anchor="w", pady=9)

    def _open_repository(self):
        from repository_gui import RepositoryPanel
        if getattr(self, "_repository_window", None) and self._repository_window.winfo_exists():
            self._repository_window.lift()
            self._repository_window.focus_force()
        else:
            self._repository_window = RepositoryPanel(self)

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

    def _check_dates(self):
        start, end = self.date_from.get().strip(), self.date_to.get().strip()
        try:
            a = datetime.strptime(start, "%d/%m/%Y").date()
            b = datetime.strptime(end, "%d/%m/%Y").date()
            if a > b:
                raise ValueError
        except ValueError:
            messagebox.showerror("Date non valide", "Indica Dal e Al in formato GG/MM/AAAA, in ordine cronologico.")
            return
        self._run([OPS + ".check_draws", "--dal", start, "--al", end])

    def _performance(self):
        year = self._positive(self.year.get(), "Anno")
        if year is not None:
            self._run([OPS + ".trigger_performance", "--year", str(year)])

    def _ranking(self):
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
        for button in self.buttons:
            button.configure(state="disabled")
        self._clear()
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
            self.events.put(("done", proc.wait()))
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
                    for button in self.buttons:
                        button.configure(state="normal")
                    if kind == "error":
                        self.output.insert("end", "\nERRORE: " + data + "\n")
                        self.status.set("Errore")
                    else:
                        self.status.set("Completato" if data == 0 else f"Errore (codice {data})")
        except queue.Empty:
            pass
        self.after(100, self._drain)

    def _clear(self):
        self.output.delete("1.0", "end")

    def _save(self):
        path = filedialog.asksaveasfilename(defaultextension=".txt",
                                            filetypes=[("Testo", "*.txt"), ("Tutti", "*.*")])
        if path:
            Path(path).write_text(self.output.get("1.0", "end-1c"), encoding="utf-8")


if __name__ == "__main__":
    OperationalPanel().mainloop()
