"""Gestione Git per Senalox. Operazioni esplicite, senza shell e senza force."""
from __future__ import annotations

import os
import queue
import subprocess
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

ROOT = Path(__file__).resolve().parent


class RepositoryPanel(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Senalox | Gestione repository Git")
        self.geometry("900x680")
        self.minsize(740, 560)
        self.running = False
        self.events = queue.Queue()
        self.buttons = []
        self.message = tk.StringVar(value="")
        self.status = tk.StringVar(value="Pronto")
        self._build()
        self.after(100, self._drain)
        self.refresh()

    def _build(self):
        root = ttk.Frame(self, padding=16)
        root.pack(fill="both", expand=True)
        ttk.Label(root, text="Gestione repository", font=("Arial", 17, "bold")).pack(anchor="w")
        ttk.Label(root, text=f"Cartella locale: {ROOT}", wraplength=830).pack(anchor="w", pady=(3, 12))
        actions = ttk.LabelFrame(root, text="Operazioni Git", padding=12)
        actions.pack(fill="x")
        for label, command in [
            ("1. Controlla stato", self.refresh),
            ("2. Scarica aggiornamenti (Pull)", self.pull),
            ("3. Prepara commit", self.commit),
            ("4. Pubblica su GitHub (Push)", self.push),
        ]:
            button = ttk.Button(actions, text=label, command=command)
            button.pack(side="left", padx=(0, 7), pady=3)
            self.buttons.append(button)
        info = ttk.LabelFrame(root, text="Commit locale", padding=10)
        info.pack(fill="x", pady=(12, 8))
        ttk.Label(info, text="Messaggio del commit (obbligatorio):").pack(anchor="w")
        ttk.Entry(info, textvariable=self.message).pack(fill="x", pady=(5, 5))
        ttk.Label(info, text="Prepara commit include i file modificati, nuovi e rimossi, esclusi quelli ignorati da Git.").pack(anchor="w")
        ttk.Label(root, textvariable=self.status).pack(anchor="w", pady=(4, 5))
        ttk.Label(root, text="Risultato dei comandi", font=("Arial", 10, "bold")).pack(anchor="w")
        output_frame = ttk.Frame(root)
        output_frame.pack(fill="both", expand=True)
        self.output = tk.Text(output_frame, font=("Consolas", 10), wrap="none")
        vbar = ttk.Scrollbar(output_frame, orient="vertical", command=self.output.yview)
        hbar = ttk.Scrollbar(output_frame, orient="horizontal", command=self.output.xview)
        self.output.configure(yscrollcommand=vbar.set, xscrollcommand=hbar.set)
        self.output.grid(row=0, column=0, sticky="nsew")
        vbar.grid(row=0, column=1, sticky="ns")
        hbar.grid(row=1, column=0, sticky="ew")
        output_frame.rowconfigure(0, weight=1)
        output_frame.columnconfigure(0, weight=1)
        ttk.Label(root, text="Pull: solo fast-forward. Push: mai forzato. Eventuali conflitti vanno risolti manualmente.",
                  wraplength=830).pack(anchor="w", pady=(8, 0))

    def _git(self, *args):
        result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                                text=True, encoding="utf-8", errors="replace",
                                stdin=subprocess.DEVNULL, timeout=120,
                                env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
        return result.returncode, (result.stdout + result.stderr).strip()

    def _ensure_repo(self):
        code, value = self._git("rev-parse", "--show-toplevel")
        if code or Path(value).resolve() != ROOT.resolve():
            raise RuntimeError("La cartella corrente non è la radice del repository Git atteso.")

    def _status_text(self):
        self._ensure_repo()
        _, branch = self._git("branch", "--show-current")
        _, remote = self._git("remote", "-v")
        _, changes = self._git("status", "--short")
        _, tracking = self._git("status", "-sb")
        return (f"Branch: {branch or '(non disponibile)'}\n\n"
                f"Tracking: {tracking}\n\nRemote:\n{remote or '(nessuno)'}\n\n"
                f"File modificati:\n{changes or '(nessuna modifica)'}")

    def refresh(self):
        self._run("Stato repository", self._status_text)

    def pull(self):
        if not messagebox.askyesno("Conferma Pull", "Scaricare gli aggiornamenti dal remote?\n"
                                   "L'operazione usa --ff-only e non crea merge automatici.", parent=self):
            return
        def action():
            self._ensure_repo()
            code, branch = self._git("branch", "--show-current")
            if code or not branch:
                raise RuntimeError("Impossibile individuare il branch corrente.")
            code, changes = self._git("status", "--porcelain")
            if code or changes:
                raise RuntimeError("Ci sono modifiche locali: esegui prima un commit o sistemale manualmente.")
            code, result = self._git("pull", "--ff-only")
            if code:
                raise RuntimeError(result or "Pull non riuscito.")
            return result + "\n\n" + self._status_text()
        self._run("Pull", action)

    def commit(self):
        message = self.message.get().strip()
        if not message:
            messagebox.showwarning("Messaggio mancante", "Scrivi un messaggio per il commit.", parent=self)
            return
        if not messagebox.askyesno("Conferma commit", "Preparare un commit locale con TUTTE le modifiche "
                                   "(file nuovi, modificati e rimossi)?\n\n"
                                   "Controlla prima l'elenco con «Controlla stato».", parent=self):
            return
        def action():
            self._ensure_repo()
            code, changes = self._git("status", "--porcelain")
            if code or not changes:
                raise RuntimeError("Non ci sono modifiche da registrare.")
            code, result = self._git("add", "-A")
            if code:
                raise RuntimeError(result or "Git add non riuscito.")
            code, result = self._git("commit", "-m", message)
            if code:
                raise RuntimeError(result or "Commit non riuscito.")
            return result + "\n\n" + self._status_text()
        self._run("Commit", action)

    def push(self):
        if not messagebox.askyesno("Conferma Push", "Pubblicare i commit locali sul branch remoto configurato?\n"
                                   "Non verrà eseguito alcun force push.", parent=self):
            return
        def action():
            self._ensure_repo()
            code, branch = self._git("branch", "--show-current")
            if code or not branch:
                raise RuntimeError("Nessun branch corrente valido.")
            code, upstream = self._git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}")
            if code or not upstream:
                raise RuntimeError("Nessun upstream configurato. Configuralo manualmente prima del push.")
            code, result = self._git("push")
            if code:
                raise RuntimeError(result or "Push non riuscito.")
            return result + "\n\n" + self._status_text()
        self._run("Push", action)

    def _run(self, label, action):
        if self.running:
            return
        self.running = True
        self.status.set(f"{label}: in corso...")
        self.output.delete("1.0", "end")
        for button in self.buttons:
            button.configure(state="disabled")
        def worker():
            try:
                result = action()
                self.events.put(("done", label, result))
            except Exception as exc:
                self.events.put(("error", label, str(exc)))
        threading.Thread(target=worker, daemon=True).start()

    def _drain(self):
        try:
            while True:
                kind, label, result = self.events.get_nowait()
                self.running = False
                for button in self.buttons:
                    button.configure(state="normal")
                self.output.insert("end", result + "\n")
                self.status.set(f"{label}: {'completato' if kind == 'done' else 'errore'}")
                if kind == "error":
                    messagebox.showerror("Operazione Git non riuscita", result, parent=self)
        except queue.Empty:
            pass
        if self.winfo_exists():
            self.after(100, self._drain)


if __name__ == "__main__":
    app = tk.Tk()
    app.withdraw()
    RepositoryPanel(app)
    app.mainloop()
