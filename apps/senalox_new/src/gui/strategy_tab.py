import tkinter as tk
from tkinter import ttk

class StrategyTab(ttk.Frame):
    def __init__(self, parent, strategy_name, generate_callback):
        super().__init__(parent)
        self.strategy_name = strategy_name
        self.generate_callback = generate_callback
        self.create_widgets()
        
    def create_widgets(self):
        ttk.Label(self, text=f"Strategia: {self.strategy_name}", font=('Arial', 12)).pack(pady=10)
        
        ttk.Button(self, text="Genera Sestina", 
                 command=self.on_generate).pack(pady=10)
        
        self.result_text = tk.Text(self, height=4, width=40)
        self.result_text.pack(pady=10)
    
    def on_generate(self):
        result = self.generate_callback()
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, ", ".join(map(str, result)))