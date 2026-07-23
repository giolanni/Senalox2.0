import tkinter as tk
from tkinter import ttk

class StrategyTab(ttk.Frame):
    """Template per i tab delle singole strategie"""
    def __init__(self, parent, name, generator):
        super().__init__(parent)
        self.name = name
        self.generator = generator
        self.create_widgets()
    
    def create_widgets(self):
        ttk.Label(self, text=f"Strategia: {self.name}", font=('Arial', 12)).pack(pady=10)
        
        ttk.Button(self, text="Genera", command=self.on_generate).pack(pady=10)
        
        self.result = tk.Text(self, height=4, width=40)
        self.result.pack(pady=10)
    
    def on_generate(self):
        sestina = self.generator()
        self.result.delete(1.0, tk.END)
        self.result.insert(tk.END, ", ".join(map(str, sestina)))