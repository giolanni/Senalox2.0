import tkinter as tk
import sys
from tkinter import ttk, messagebox, scrolledtext
from tkcalendar import DateEntry
from datetime import datetime

from shared.data_loader import (
    load_estrazioni_multifile,
    load_estrazioni_filtered,
)
from src.core.generator import genera_sestina_pesata, genera_pool_pesato

from src.core.pattern_analyzer import (
    ricorrenze_per_data,
    ricorrenze_numero_ripetuto,
    ricorrenze_post_estraz_numero
)

from src.core.analyzer import (
    calcola_frequenze,
    analisi_ritardi,
    analisi_somme,
    analisi_parita,
    analisi_decine,
    analisi_sequenze
)

class SenaloxGUI:

    def __init__(self, master, start_year=None):
        self.master = master
        self.start_year = start_year
        self.estrazioni = load_estrazioni_filtered("./data", start_year)
        
        master.title("Senalox - Generatore SuperEnalotto")
        ttk.Label(master, text=self.get_data_range_text(), font=('Arial', 10)).pack(pady=5)
        master.geometry("800x600")

        self.notebook = ttk.Notebook(master)
        self.notebook.pack(expand=True, fill="both")

        self.create_tabs()
        self.create_pesata_tab()
        self.create_pattern_analysis_tab()
        self.create_historical_analysis_tab()

    def create_tabs(self):
        """Crea i vari tab per ogni metodo di generazione."""
        self.tabs = {}

        methods = [
            ("Frequenze", self.generate_by_frequenze,
             "Questo metodo analizza la frequenza con cui ogni numero è stato estratto storicamente. "
             "I numeri più frequenti sono considerati più probabili per le estrazioni future."),
            ("Ritardi", self.generate_by_ritardi,
             "Questo metodo considera il tempo trascorso dall'ultima estrazione di ciascun numero. "
             "I numeri con i ritardi più lunghi sono considerati più probabili per le prossime estrazioni."),
            ("Somme", self.generate_by_somme,
             "Questo metodo analizza la somma dei numeri estratti in ogni estrazione. "
             "Genera una sestina con una somma vicina alla media storica delle somme."),
            ("Parità", self.generate_by_parita,
             "Questo metodo esamina la distribuzione di numeri pari e dispari nelle estrazioni passate. "
             "Genera una sestina che riflette la tendenza storica di parità/disparità."),
            ("Decine", self.generate_by_decine,
             "Questo metodo analizza la distribuzione dei numeri per decine (1-10, 11-20, ecc.). "
             "Genera una sestina che riflette la distribuzione storica delle decine."),
            ("Sequenze", self.generate_by_sequenze,
             "Questo metodo cerca sequenze di numeri consecutivi nelle estrazioni passate. "
             "Genera una sestina che include possibili sequenze basate sui pattern storici.")
        ]

        for method_name, method_function, description in methods:
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=method_name)
            self.tabs[method_name] = frame

            # Aggiungi descrizione del metodo
            desc_text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, height=4)
            desc_text.insert(tk.INSERT, description)
            desc_text.config(state=tk.DISABLED)
            desc_text.pack(pady=10, padx=10, fill=tk.X)

            # Aggiungi un pulsante per generare la sestina
            generate_button = ttk.Button(frame, text="Genera Sestina", command=method_function)
            generate_button.pack(pady=10)

            # Widget Text per mostrare il risultato (testo selezionabile e copiabile)
            result_text = tk.Text(frame, height=2, font=("Arial", 14))
            result_text.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
            result_text.config(state=tk.DISABLED)
            frame.result_text = result_text

            # Pulsante per copiare le sestine
            copy_button = ttk.Button(frame, text="Copia Sestina", command=lambda tab=frame: self.copy_sestine(tab))
            copy_button.pack(pady=5)

    def create_pesata_tab(self):
        """Crea il tab per la generazione pesata."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Generazione Pesata")
        self.tabs["Generazione Pesata"] = frame

        # Descrizione del metodo
        desc_text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, height=4)
        desc_text.insert(tk.INSERT, "Questo metodo genera due tipi di sestine basate sulla frequenza storica dei numeri:\n"
                                     "- Sestina Random: Una sestina generata casualmente, dando più peso ai numeri estratti più spesso.\n"
                                     "- Sestina Top: Una sestina composta dai 6 numeri più frequenti, basata sull'analisi storica.")
        desc_text.config(state=tk.DISABLED)
        desc_text.pack(pady=10, padx=10, fill=tk.X)

        # Pulsante per generare le sestine pesate
        generate_button = ttk.Button(frame, text="Genera Sestine Pesate", command=self.generate_by_pesata)
        generate_button.pack(pady=10)

        # Widget Text per mostrare i risultati (testo selezionabile e copiabile)
        self.pesata_result_text = scrolledtext.ScrolledText(frame, height=4, font=("Arial", 14), wrap=tk.WORD)
        self.pesata_result_text.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        self.pesata_result_text.config(state=tk.DISABLED)

        # Pulsante per copiare le sestine
        copy_button = ttk.Button(frame, text="Copia Sestine", command=self.copy_pesata_sestine)
        copy_button.pack(pady=5)
    
    def load_estrazioni(self):
        """Carica le estrazioni dal file CSV."""
        try:
            estrazioni = load_estrazioni_multifile("./data")
            if not estrazioni:
                raise ValueError("Nessuna estrazione caricata")
            return estrazioni
        except Exception as e:
            messagebox.showerror("Errore", f"Errore durante il caricamento delle estrazioni: {e}")
            return None
        
    def generate_sestina(self, method_function, tab_name):
        """Genera una sestina utilizzando il metodo specificato."""
        estrazioni = self.load_estrazioni()
        if not estrazioni:
            return

        try:
            sestina = method_function(estrazioni)
            sestina = sorted(sestina[:6])  # Prendi solo i primi 6 numeri più probabili
            self.display_sestina(sestina, self.tabs[tab_name])
        except Exception as e:
            messagebox.showerror("Errore", f"Errore durante la generazione della sestina: {e}")

    def display_sestina(self, sestina, tab):
        """Mostra la sestina generata nel widget Text."""
        tab.result_text.config(state=tk.NORMAL)
        tab.result_text.delete("1.0", tk.END)
        tab.result_text.insert(tk.END, ", ".join(map(str, sestina)))
        tab.result_text.config(state=tk.DISABLED)

    def copy_sestine(self, tab):
        """Copia le sestine nel clipboard."""
        tab.result_text.config(state=tk.NORMAL)
        text_to_copy = tab.result_text.get("1.0", tk.END)
        tab.result_text.config(state=tk.DISABLED)
        self.master.clipboard_clear()
        self.master.clipboard_append(text_to_copy)
        self.master.update()

    def copy_pesata_sestine(self):
        """Copia le sestine pesate nel clipboard."""
        self.pesata_result_text.config(state=tk.NORMAL)
        text_to_copy = self.pesata_result_text.get("1.0", tk.END)
        self.pesata_result_text.config(state=tk.DISABLED)
        self.master.clipboard_clear()
        self.master.clipboard_append(text_to_copy)
        self.master.update()

    # Funzioni specifiche per ogni metodo di analisi
    def generate_by_frequenze(self):
        self.generate_sestina(calcola_frequenze, "Frequenze")

    def generate_by_ritardi(self):
        def ritardi_method(estrazioni):
            return [num for num, _ in analisi_ritardi(estrazioni)]
        self.generate_sestina(ritardi_method, "Ritardi")

    def generate_by_somme(self):
        self.generate_sestina(analisi_somme, "Somme")

    def generate_by_parita(self):
        self.generate_sestina(analisi_parita, "Parità")

    def generate_by_decine(self):
        self.generate_sestina(analisi_decine, "Decine")

    def generate_by_sequenze(self):
        self.generate_sestina(analisi_sequenze, "Sequenze")

    def generate_by_pesata(self):
        """Genera una sestina pesata e la mostra nel tab corrispondente."""
        estrazioni = self.load_estrazioni()
        if not estrazioni:
            return

        try:
            pool_pesato = genera_pool_pesato(estrazioni)
            sestina_pesata_random = genera_sestina_pesata(estrazioni)
            sestina_pesata_top = sorted(pool_pesato, key=lambda x: x[1], reverse=True)[:6]
            sestina_pesata_top = [num for num, _ in sestina_pesata_top]

            result_text = (
                f"Sestina Pesata Random: {', '.join(map(str, sestina_pesata_random))}\n"
                f"Sestina Pesata Top: {', '.join(map(str, sestina_pesata_top))}"
            )

            self.display_pesata_results(result_text)

        except Exception as e:
            messagebox.showerror("Errore", f"Errore durante la generazione della sestina pesata: {e}")

    def display_pesata_results(self, result_text):
        """Mostra i risultati della generazione pesata nel widget Text."""
        self.pesata_result_text.config(state=tk.NORMAL)
        self.pesata_result_text.delete("1.0", tk.END)
        self.pesata_result_text.insert(tk.END, result_text)
        self.pesata_result_text.config(state=tk.DISABLED)

    def create_pattern_analysis_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Analisi Pattern")
        
        ttk.Label(frame, text="Analisi ricorrenze temporali").pack(pady=10)
        
        # Controlli per l'analisi delle date
        ttk.Label(frame, text="Data di riferimento:").pack()
        self.date_picker = DateEntry(frame)
        self.date_picker.pack(pady=5)
        
        ttk.Button(frame, text="Analizza ricorrenze date", 
                command=self.analizza_ricorrenze_date).pack(pady=5)
        
        # Controlli per l'analisi delle sequenze
        ttk.Label(frame, text="Numero target:").pack()
        self.numero_target = ttk.Entry(frame)
        self.numero_target.pack(pady=5)
        
        ttk.Button(frame, text="Analizza dipendenze numeriche",
                command=self.analizza_dipendenze).pack(pady=5)
                
        # Controlli per l'analisi di numeri ripetuti consecutivamente
        ttk.Label(frame, text="Numero target:").pack()
        self.numero_target_ripetuto = ttk.Entry(frame)
        self.numero_target_ripetuto.pack(pady=5)
        
        ttk.Button(frame, text="Analizza ricorrenze numero ripetuto",
                command=self.analizza_ricorrenze_numero_ripetuto).pack(pady=5)
        
        self.pattern_result = scrolledtext.ScrolledText(frame, height=15, wrap=tk.WORD)
        self.pattern_result.pack(fill=tk.BOTH, expand=True)

    def analizza_ricorrenze_date(self):
        selected_date = self.date_picker.get_date()
        # Converto selected_date in datetime.datetime
        selected_date = datetime.combine(selected_date, datetime.min.time())
        result = ricorrenze_per_data(self.estrazioni, selected_date)
        
        text = f"Numeri ricorrenti attorno al {selected_date.strftime('%d/%m/%Y')}:\n"
        for num, count in list(result.items())[:10]:
            text += f"Numero {num}: {count} apparizioni\n"
        
        self.pattern_result.delete(1.0, tk.END)
        self.pattern_result.insert(tk.END, text)
        
    def analizza_ricorrenze_numero_ripetuto(self):
        try:
            target = int(self.numero_target_ripetuto.get())
            result = ricorrenze_numero_ripetuto(self.estrazioni, target)
            
            text = f"Ricorrenze del numero {target} ripetuto consecutivamente:\n"
            for ripetizioni, count in result.items():
                text += f"{ripetizioni} volte consecutive: {count} occasioni\n"
            
            self.pattern_result.delete(1.0, tk.END)
            self.pattern_result.insert(tk.END, text)
        except ValueError:
            messagebox.showerror("Errore", "Inserisci un numero valido")

    def analizza_dipendenze(self):
        try:
            target = int(self.numero_target.get())
            result = ricorrenze_post_estraz_numero(self.estrazioni, target)
            
            text = f"Numeri più frequenti dopo il {target}:\n"
            for num, perc in list(result.items())[:10]:
                text += f"Numero {num}: {perc:.2f}%\n"
            
            self.pattern_result.delete(1.0, tk.END)
            self.pattern_result.insert(tk.END, text)
        except ValueError:
            messagebox.showerror("Errore", "Inserisci un numero valido")

    def create_historical_analysis_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Analisi Storica")

        ttk.Label(frame, text="Seleziona una data di riferimento:").pack(pady=10)
        self.date_picker = DateEntry(frame, width=12, background='darkblue', foreground='white', borderwidth=2)
        self.date_picker.pack(pady=10)

        generate_button = ttk.Button(frame, text="Genera Sestine Storiche", command=self.generate_historical_sestine)
        generate_button.pack(pady=10)

        self.historical_result = scrolledtext.ScrolledText(frame, wrap=tk.WORD, height=10)
        self.historical_result.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

    def generate_historical_sestine(self):
        selected_date = self.date_picker.get_date()
        
        # Filtra le estrazioni in base all'anno di inizio (start_year)
        if self.start_year:
            filtered_estrazioni = [e for e in self.estrazioni if e.data.year >= self.start_year]
        else:
            filtered_estrazioni = self.estrazioni
            
        # Converto selected_date in datetime.datetime
        selected_date = datetime.combine(selected_date, datetime.min.time())
            
        # Filtra ulteriormente le estrazioni fino alla data selezionata
        historical_estrazioni = [e for e in filtered_estrazioni if e.data <= selected_date]

        if not historical_estrazioni:
            messagebox.showwarning("Attenzione", "Nessuna estrazione trovata prima della data selezionata.")
            return

        results = []
        methods = [
            ("Frequenze", calcola_frequenze),
            ("Ritardi", lambda e: [num for num, _ in analisi_ritardi(e)]),
            ("Somme", analisi_somme),
            ("Parità", analisi_parita),
            ("Decine", analisi_decine),
            ("Sequenze", analisi_sequenze)
        ]

        for method_name, method_function in methods:
            try:
                sestina = sorted(method_function(historical_estrazioni)[:6])
                results.append(f"{method_name}: {', '.join(map(str, sestina))}")
            except Exception as e:
                results.append(f"{method_name}: Errore - {str(e)}")

        try:
            pool_pesato = genera_pool_pesato(historical_estrazioni)
            sestina_pesata_random = genera_sestina_pesata(historical_estrazioni)
            sestina_pesata_top = sorted(pool_pesato, key=lambda x: x[1], reverse=True)[:6]
            sestina_pesata_top = [num for num, _ in sestina_pesata_top]

            results.append(f"\nGenerazione Pesata Random: {', '.join(map(str, sestina_pesata_random))}")
            results.append(f"Generazione Pesata Top: {', '.join(map(str, sestina_pesata_top))}")
            results.append("\nPool Pesato (Numero: Peso):")
            for num, peso in pool_pesato:
                results.append(f"{num}: {peso:.4f}")
        except Exception as e:
            results.append(f"Errore nella generazione pesata: {str(e)}")

        self.historical_result.delete(1.0, tk.END)
        self.historical_result.insert(tk.END, f"Sestine generate al {selected_date.strftime('%d/%m/%Y')}:\n\n")
        self.historical_result.insert(tk.END, "\n".join(results))

    def get_data_range_text(self):
        if self.start_year == 2009:
            return "Dati caricati dal 01/07/2009 in poi"
        return "Dati completi caricati (tutte le estrazioni disponibili)"

if __name__ == "__main__":
    start_year = None
    if len(sys.argv) > 1:
        try:
            start_year = int(sys.argv[1])
            if start_year != 2009:
                print("Anno non supportato. Carico tutte le estrazioni.")
                start_year = None
        except ValueError:
            print("Argomento non valido. Usa formato: python senalox_gui.py [2009]")
            sys.exit(1)

    root = tk.Tk()
    app = SenaloxGUI(root, start_year=start_year)
    root.mainloop()
