"""
SENALOX - Launcher unificato
============================

Questo programma costituisce l'unico punto di ingresso del progetto.

Permette di:

1. avviare Senalox 1.0, mantenuta come versione stabile;
2. avviare New Senalox, mantenuta come versione sperimentale;
3. eseguire le due applicazioni come processi separati;
4. rendere disponibile la cartella principale del progetto agli import Python;
5. mostrare eventuali errori di avvio senza chiudere il launcher.

La cartella principale del progetto viene aggiunta alla variabile PYTHONPATH
dei processi avviati.

Questo permette alle applicazioni contenute in:

    apps/senalox_legacy
    apps/senalox_new

di importare correttamente moduli condivisi come:

    shared.data_loader
    shared.models.estrazione
    shared.paths
"""

from __future__ import annotations

import os
import subprocess
import sys
import tkinter as tk

from pathlib import Path
from tkinter import messagebox, ttk

from shared.paths import LEGACY_DIR, NEW_DIR, PROJECT_ROOT


class SenaloxLauncher(tk.Tk):
    """
    Finestra principale da cui avviare le due versioni di Senalox.
    """

    def __init__(self) -> None:
        """
        Inizializza la finestra principale del launcher.
        """

        super().__init__()

        self.title("Senalox")
        self.geometry("620x390")
        self.minsize(620, 390)

        self._configure_style()
        self._create_widgets()

    def _configure_style(self) -> None:
        """
        Configura lo stile grafico dei widget del launcher.
        """

        style = ttk.Style(self)

        style.configure(
            "Title.TLabel",
            font=("Arial", 22, "bold"),
        )

        style.configure(
            "Subtitle.TLabel",
            font=("Arial", 11),
        )

        style.configure(
            "Version.TButton",
            font=("Arial", 12, "bold"),
            padding=12,
        )

        style.configure(
            "Status.TLabel",
            font=("Arial", 9),
        )

    def _create_widgets(self) -> None:
        """
        Costruisce l'interfaccia grafica del launcher.
        """

        container = ttk.Frame(
            self,
            padding=28,
        )

        container.pack(
            expand=True,
            fill="both",
        )

        ttk.Label(
            container,
            text="SENALOX",
            style="Title.TLabel",
        ).pack(
            pady=(0, 4),
        )

        ttk.Label(
            container,
            text="Un unico accesso alla versione stabile e alla nuova evoluzione",
            style="Subtitle.TLabel",
        ).pack(
            pady=(0, 28),
        )

        # ------------------------------------------------------------------
        # Sezione Senalox 1.0
        # ------------------------------------------------------------------

        legacy_box = ttk.LabelFrame(
            container,
            text="Versione stabile",
            padding=16,
        )

        legacy_box.pack(
            fill="x",
            pady=(0, 16),
        )

        ttk.Button(
            legacy_box,
            text="Avvia Senalox 1.0",
            style="Version.TButton",
            command=self._launch_legacy,
        ).pack(
            fill="x",
        )

        ttk.Label(
            legacy_box,
            text="Applicazione storica da preservare e usare normalmente.",
            style="Status.TLabel",
        ).pack(
            pady=(8, 0),
        )

        # ------------------------------------------------------------------
        # Sezione New Senalox
        # ------------------------------------------------------------------

        new_box = ttk.LabelFrame(
            container,
            text="Versione sperimentale",
            padding=16,
        )

        new_box.pack(
            fill="x",
        )

        ttk.Button(
            new_box,
            text="Avvia New Senalox",
            style="Version.TButton",
            command=self._launch_new,
        ).pack(
            fill="x",
        )

        ttk.Label(
            new_box,
            text="Area di sviluppo isolata: può evolvere senza compromettere la 1.0.",
            style="Status.TLabel",
        ).pack(
            pady=(8, 0),
        )

    def _launch_legacy(self) -> None:
        """
        Avvia Senalox 1.0.
        """

        self._launch(
            working_dir=LEGACY_DIR,
            script_name="senalox_GUI.py",
            label="Senalox 1.0",
        )

    def _launch_new(self) -> None:
        """
        Avvia New Senalox.
        """

        self._launch(
            working_dir=NEW_DIR,
            script_name="exec_gui.py",
            label="New Senalox",
        )

    def _build_process_environment(self) -> dict[str, str]:
        """
        Costruisce l'ambiente da passare ai processi avviati.

        Il punto fondamentale è l'aggiunta di PROJECT_ROOT a PYTHONPATH.

        Senza questa modifica, quando Python esegue uno script dentro:

            apps/senalox_legacy
            apps/senalox_new

        non riesce necessariamente a trovare la cartella:

            shared

        che si trova invece nella radice del progetto.
        """

        # Copia tutte le variabili d'ambiente attuali.
        environment = os.environ.copy()

        # Legge l'eventuale PYTHONPATH già configurato sul computer.
        existing_pythonpath = environment.get("PYTHONPATH", "")

        # Converte il percorso principale del progetto in stringa.
        project_root_text = str(PROJECT_ROOT)

        if existing_pythonpath:
            # Mantiene il PYTHONPATH esistente e aggiunge Senalox all'inizio.
            environment["PYTHONPATH"] = (
                project_root_text
                + os.pathsep
                + existing_pythonpath
            )
        else:
            # Se PYTHONPATH non esiste, usa soltanto la radice di Senalox.
            environment["PYTHONPATH"] = project_root_text

        return environment

    def _launch(
        self,
        working_dir: Path,
        script_name: str,
        label: str,
    ) -> None:
        """
        Avvia una versione di Senalox in un processo Python indipendente.

        Parameters
        ----------
        working_dir
            Cartella di lavoro dell'applicazione.

        script_name
            Nome dello script Python da eseguire.

        label
            Nome leggibile dell'applicazione, usato nei messaggi di errore.
        """

        # Costruisce il percorso completo dello script da avviare.
        script_path = working_dir / script_name

        # Verifica che lo script esista davvero.
        if not script_path.exists():
            messagebox.showerror(
                "File non trovato",
                (
                    f"Impossibile avviare {label}.\n\n"
                    f"File mancante:\n{script_path}"
                ),
            )

            return

        try:
            # Prepara l'ambiente con PROJECT_ROOT inserito nel PYTHONPATH.
            process_environment = self._build_process_environment()

            # Avvia l'applicazione come processo separato.
            subprocess.Popen(
                [
                    sys.executable,
                    str(script_path),
                ],
                cwd=str(working_dir),
                env=process_environment,
            )

        except Exception as exc:
            messagebox.showerror(
                "Errore di avvio",
                (
                    f"Impossibile avviare {label}.\n\n"
                    f"{exc}"
                ),
            )


if __name__ == "__main__":
    app = SenaloxLauncher()
    app.mainloop()