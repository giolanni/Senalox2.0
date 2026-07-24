import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from datetime import date, datetime
from shared import data_loader as loader
from src.core import analyzer, generator
from src.gui.components.strategies_tab import StrategyTab


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Senalox 2.0")
        self.geometry("1200x800")
        self.estrazioni = []
        self.estrazioni_filtered = []
        self.analyzer = None
        self.generatore = None
        self.current_mode = None

        # Variabili grafiche condivise dai controlli e dall'indicatore.
        self.mode_var = tk.StringVar(value="")
        self.mode_status_var = tk.StringVar(
            value="MODALITÀ ATTIVA: nessuna modalità selezionata"
        )

        self.create_interface()
        self.load_initial_data()
    
    def create_interface(self):
        # Indicatore sempre visibile, anche quando si cambia scheda.
        status_frame = ttk.Frame(self, padding=(10, 8))
        status_frame.pack(fill=tk.X)

        ttk.Label(
            status_frame,
            textvariable=self.mode_status_var,
            font=("Arial", 11, "bold"),
        ).pack()

        self.notebook = ttk.Notebook(self)

        # Tab Home
        home_frame = ttk.Frame(self.notebook)
        self.create_home_tab(home_frame)
        self.notebook.add(home_frame, text="Home")
        
        self.notebook.pack(expand=True, fill=tk.BOTH)
    
    def create_home_tab(self, frame):
        ttk.Label(frame, text="Modalità Operativa", font=('Arial', 14)).pack(pady=20)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10)
        
        ttk.Radiobutton(
            btn_frame,
            text="OVERALL (FULL)",
            variable=self.mode_var,
            value="FULL",
            command=lambda: self.set_mode("FULL"),
        ).pack(side=tk.LEFT, padx=10)

        ttk.Radiobutton(
            btn_frame,
            text="NEW MODE (2009+)",
            variable=self.mode_var,
            value="2009",
            command=lambda: self.set_mode("2009"),
        ).pack(side=tk.LEFT, padx=10)

        ttk.Label(
            frame,
            text=(
                "OVERALL usa tutte le estrazioni disponibili; "
                "NEW MODE usa quelle dal 01/07/2009."
            ),
        ).pack(pady=(10, 0))
    
    def set_mode(self, mode):
        """Imposta il dataset operativo e aggiorna l'indicatore visibile."""
        self.current_mode = mode
        self.mode_var.set(mode)

        self.estrazioni_filtered = loader.filtra_per_data(
            self.estrazioni,
            2009 if mode == "2009" else None,
        )

        if mode == "2009":
            description = "NEW MODE (2009+) - estrazioni dal 01/07/2009"
        else:
            description = "OVERALL (FULL) - tutte le estrazioni disponibili"

        self.mode_status_var.set(
            f"MODALITÀ ATTIVA: {description} | "
            f"Estrazioni caricate: {len(self.estrazioni_filtered)}"
        )
        self.title(f"Senalox 2.0 - {description}")

        self.analyzer = analyzer.Analyzer(self.estrazioni_filtered)
        self.generatore = generator.GeneratorePesato(self.analyzer)
        self.create_strategy_tabs()
    
    def create_strategy_tabs(self):
    """
    Ricrea i tab delle strategie usando la modalità dati attualmente attiva.
    """

    # Rimuove tutti i vecchi tab, mantenendo soltanto la Home.
    for tab in self.notebook.tabs()[1:]:
        self.notebook.forget(tab)

    # Costruisce il testo della modalità attualmente selezionata.
    if self.current_mode == "2009":
        dataset_label = "NEW MODE — dal 01/07/2009"
    else:
        dataset_label = "OVERALL — archivio completo"

    extraction_count = len(self.estrazioni_filtered)

    # Crea un tab per ciascuna strategia registrata nel generatore.
    for name in self.generatore.strategie.keys():

        tab = StrategyTab(
            parent=self.notebook,
            name=name,
            generator=lambda n=name: self.generatore.strategie[n][0].generate(),
            description=get_algorithm_description(name),
            dataset_label=dataset_label,
            extraction_count=extraction_count,
        )

        self.notebook.add(
            tab,
            text=name,
        )

    # Tab della strategia combinata pesata.
    pesata_tab = StrategyTab(
        parent=self.notebook,
        name="Pesata",
        generator=self.generatore.genera_sestina_pesata,
        description=get_algorithm_description("Pesata"),
        dataset_label=dataset_label,
        extraction_count=extraction_count,
    )

    self.notebook.add(
        pesata_tab,
        text="Combinata Pesata",
    )
    
    def load_initial_data(self):
        try:
            self.estrazioni = loader.load_estrazioni_multifile()
        except Exception as e:
            messagebox.showerror("Errore", str(e))
