"""
Tab grafico condiviso dalle strategie di New Senalox.

Ogni tab mostra:
- il nome della strategia;
- una spiegazione dell'algoritmo;
- il dataset attualmente utilizzato;
- il numero di estrazioni analizzate;
- il pulsante di generazione e il risultato.
"""

import tkinter as tk
from tkinter import ttk


class StrategyTab(ttk.Frame):
    """Interfaccia di una singola strategia di generazione."""

    def __init__(
        self,
        parent,
        name,
        generator,
        description,
        dataset_label,
        extraction_count,
    ):
        super().__init__(parent, padding=20)

        self.name = name
        self.generator = generator
        self.description = description
        self.dataset_label = dataset_label
        self.extraction_count = extraction_count

        self.create_widgets()

    def create_widgets(self):
        """Costruisce tutti i controlli del tab."""

        ttk.Label(
            self,
            text=f"Strategia: {self.name}",
            font=("Arial", 14, "bold"),
        ).pack(anchor="w", pady=(0, 12))

        description_box = tk.Text(
            self,
            height=10,
            wrap=tk.WORD,
            font=("Arial", 10),
        )
        description_box.insert("1.0", self.description)
        description_box.config(state=tk.DISABLED)
        description_box.pack(fill=tk.X, pady=(0, 12))

        ttk.Label(
            self,
            text=(
                f"Dataset utilizzato: {self.dataset_label} | "
                f"Estrazioni analizzate: {self.extraction_count}"
            ),
            font=("Arial", 10, "bold"),
        ).pack(anchor="w", pady=(0, 15))

        ttk.Button(
            self,
            text="Genera",
            command=self.on_generate,
        ).pack(pady=10)

        self.result = tk.Text(
            self,
            height=4,
            width=40,
            font=("Arial", 13),
        )
        self.result.pack(pady=10)

    def on_generate(self):
        """Esegue la strategia e mostra la sestina ottenuta."""

        sestina = self.generator()
        self.result.delete("1.0", tk.END)
        self.result.insert(tk.END, ", ".join(map(str, sestina)))
