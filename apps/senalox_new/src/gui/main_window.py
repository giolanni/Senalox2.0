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
        self.analyzer = None
        self.generatore = None
        
        self.create_interface()
        self.load_initial_data()
    
    def create_interface(self):
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
        
        ttk.Button(btn_frame, text="FULL", command=lambda: self.set_mode('FULL')).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="2009+", command=lambda: self.set_mode('2009')).pack(side=tk.LEFT, padx=10)
    
    def set_mode(self, mode):
        self.current_mode = mode
        
        self.estrazioni_filtered = loader.filtra_per_data(
            self.estrazioni, 
            2009 if mode == '2009' else None
        )
        self.analyzer = analyzer.Analyzer(self.estrazioni_filtered)
        self.generatore = generator.GeneratorePesato(self.analyzer)
        self.create_strategy_tabs()
    
    def create_strategy_tabs(self):
        # Rimuovi vecchi tab
        for tab in self.notebook.tabs()[1:]:
            self.notebook.forget(tab)
        
        # Aggiungi tab per ogni strategia
        for name in self.generatore.strategie.keys():
            tab = StrategyTab(
                self.notebook,
                name,
                lambda n=name: self.generatore.strategie[n][0].generate()
            )
            self.notebook.add(tab, text=name)
        
        # Aggiungi tab generazione pesata
        pesata_tab = StrategyTab(
            self.notebook,
            "Pesata",
            self.generatore.genera_sestina_pesata
        )
        self.notebook.add(pesata_tab, text="Combinata Pesata")
    
    def load_initial_data(self):
        try:
            self.estrazioni = loader.load_estrazioni_multifile()
        except Exception as e:
            messagebox.showerror("Errore", str(e))
