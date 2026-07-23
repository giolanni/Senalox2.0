import os

def salva_codice_sorgente(directory: str, output_file: str):
    """
    Legge tutti i file .py in una directory (e sottodirectory) e salva il contenuto in un file di testo,
    saltando le cartelle `venv`, `__pycache__` e `salva_codice`.

    Args:
        directory (str): Percorso della directory principale.
        output_file (str): Percorso del file di output dove salvare il codice sorgente.
    """
    try:
        with open(output_file, 'w', encoding='utf-8') as output:
            for root, dirs, files in os.walk(directory):
                # Salta le cartelle specifiche
                if "venv" in root or "__pycache__" in root or "salva_codice" in root:
                    continue
                
                for file in files:
                    if file.endswith('.py'):
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                codice = f.read()
                                # Scrive il nome del file e il contenuto nel file di output
                                output.write(f"\n# ---- File: {file_path} ----\n")
                                output.write(codice)
                                output.write("\n\n")
                        except Exception as e:
                            print(f"Errore nella lettura del file {file_path}: {e}")
        print(f"Codice sorgente salvato con successo in '{output_file}'.")
    except Exception as e:
        print(f"Errore nella scrittura del file di output: {e}")

# Esempio di utilizzo
if __name__ == "__main__":
    # Percorso della directory principale e del file di output
    directory_principale = r"C:\Users\GioAsus\senalox"  # Modifica con la tua directory principale
    file_output = r"C:\Users\GioAsus\repos\senalox\perplexity.txt"
    
    salva_codice_sorgente(directory_principale, file_output)
