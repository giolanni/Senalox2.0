import tkinter as tk
from tkinter import ttk, messagebox
from shared.data_loader import load_estrazioni_multifile
from src.core.generator import genera_sestina, STRATEGIES

class SenaloxGUI:
    def __init__(self, master):
        self.master = master
        master.title("Senalox 2.0")
        master.geometry("800x600")
        
        self.estrazioni = []
        self.create_widgets()
        self.load_data()

    def create_widgets(self):
        """Crea l'interfaccia utente"""
        self.notebook = ttk.Notebook(self.master)
        
        # Tab Generazione
        gen_frame = ttk.Frame(self.notebook)
        self._build_generation_tab(gen_frame)
        
        # Tab Statistiche
        stats_frame = ttk.Frame(self.notebook)
        self._build_stats_tab(stats_frame)
        
        self.notebook.add(gen_frame, text="Generazione")
        self.notebook.add(stats_frame, text="Statistiche")
        self.notebook.pack(expand=True, fill=tk.BOTH)

    def _build_generation_tab(self, frame):
        """Costruisci il tab di generazione"""
        ttk.Label(frame, text="Metodo di generazione:").pack(pady=10)
        
        self.method_var = tk.StringVar(value='combinato')
        methods = ['combinato'] + list(STRATEGIES.keys())
        
        for method in methods:
            rb = ttk.Radiobutton(frame, text=method.capitalize(), 
                               variable=self.method_var, value=method)
            rb.pack(anchor=tk.W)
        
        ttk.Button(frame, text="Genera", command=self.generate).pack(pady=20)
        self.result_label = ttk.Label(frame, text="", font=('Arial', 14))
        self.result_label.pack()

    def _build_stats_tab(self, frame):
        """Costruisci il tab statistiche"""
        self.stats_text = tk.Text(frame, wrap=tk.WORD)
        self.stats_text.pack(expand=True, fill=tk.BOTH)
        
        ttk.Button(frame, text="Aggiorna Statistiche", 
                 command=self.update_stats).pack(pady=10)

    def load_data(self):
        """Carica i dati delle estrazioni"""
        try:
            self.estrazioni = load_estrazioni_multifile("./data")
            if not self.estrazioni:
                messagebox.showwarning("Attenzione", "Nessun dato caricato")
        except Exception as e:
            messagebox.showerror("Errore", str(e))

    def generate(self):
        """Genera una nuova sestina"""
        try:
            method = self.method_var.get()
            sestina = genera_sestina(self.estrazioni, method)
            self.result_label.config(text=f"Sestina generata: {sestina}")
        except Exception as e:
            messagebox.showerror("Errore", str(e))

    def update_stats(self):
        """Aggiorna le statistiche"""
        stats = (
            f"Estrazioni caricate: {len(self.estrazioni)}\n"
            f"Ultima estrazione: {self.estrazioni[-1].data if self.estrazioni else 'N/A'}\n"
        )
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(tk.END, stats)
