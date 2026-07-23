import tkinter as tk
from tkinter import ttk
from tkcalendar import DateEntry
from datetime import datetime

class OptimizationTab(ttk.Frame):
    def __init__(self, master, optimizer, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.optimizer = optimizer
        self._create_widgets()

    def _create_widgets(self):
        # Configurazione griglia
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Controlli input
        ttk.Label(self, text="Data di Riferimento:").grid(row=0, column=0, pady=5)
        self.date_picker = DateEntry(self)
        self.date_picker.grid(row=0, column=1, pady=5)

        # Pesi iniziali
        self.weights_frame = ttk.LabelFrame(self, text="Pesi Iniziali")
        self.weights_frame.grid(row=1, column=0, columnspan=2, pady=10, sticky="ew")
        
        self.weight_entries = {}
        default_weights = self.optimizer.default_weights
        for idx, (name, value) in enumerate(default_weights.items()):
            ttk.Label(self.weights_frame, text=f"{name.capitalize()}:").grid(row=idx, column=0)
            entry = ttk.Entry(self.weights_frame, width=8)
            entry.insert(0, str(value))
            entry.grid(row=idx, column=1)
            self.weight_entries[name] = entry

        # Risultati
        self.result_text = tk.Text(self, wrap=tk.WORD)
        self.result_text.grid(row=2, column=0, columnspan=2, sticky="nsew")

        # Pulsante ottimizzazione
        ttk.Button(self, 
                 text="Avvia Ottimizzazione", 
                 command=self._run_optimization).grid(row=3, column=0, pady=10)

    def _run_optimization(self):
        try:
            target_date = datetime.combine(
                self.date_picker.get_date(),
                datetime.min.time()
            )
            
            initial_weights = {
                name: float(entry.get())
                for name, entry in self.weight_entries.items()
            }

            best_weights = self.optimizer.find_optimal_weights(target_date)
            
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, "Pesi ottimali:\n")
            for name, value in best_weights.items():
                self.result_text.insert(tk.END, f"{name}: {value:.4f}\n")
                
        except Exception as e:
            messagebox.showerror("Errore", str(e))
