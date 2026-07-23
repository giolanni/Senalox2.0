import csv
import requests
from datetime import datetime
from pathlib import Path
from collections import namedtuple
import glob
import sqlite3
from typing import List, Optional

# Configurazione
SISAL_URL = "https://www.sisal.it/sisal-service/statistiche-superenalotto/vincite"
CSV_DIR = Path("./dati_estrazioni")
CSV_DIR.mkdir(exist_ok=True)
DB_PATH = Path("superenalotto.db")

Estrazione = namedtuple('Estrazione', ['data', 'numeri', 'jolly', 'superstar'])

def download_dati_storici() -> None:
    """Scarica i dati storici dal sito ufficiale Sisal"""
    try:
        response = requests.get(SISAL_URL, timeout=10)
        response.raise_for_status()
        
        file_path = CSV_DIR / "superenalotto_storico.csv"
        with open(file_path, 'wb') as f:
            f.write(response.content)
        print(f"Dati scaricati correttamente in {file_path}")
        
    except Exception as e:
        print(f"Errore durante il download: {str(e)}")

def parse_date(date_str: str) -> datetime.date:
    """Gestione formati data multipli con validazione"""
    formats = (
        '%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y',
        '%d/%m/%y', '%Y%m%d', '%d.%m.%Y'
    )
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Formato data non riconosciuto: {date_str}")

def validate_numbers(numbers: List[int]) -> None:
    """Valida i numeri dell'estrazione"""
    if len(numbers) != 6:
        raise ValueError("Deve esserci esattamente 6 numeri")
    
    for n in numbers:
        if not 1 <= n <= 90:
            raise ValueError(f"Numero {n} fuori dal range 1-90")

def load_estrazioni_multifile(cartella_path: str, pattern: str = "*.csv") -> List[Estrazione]:
    """Carica estrazioni da tutti i CSV nella cartella specificata"""
    estrazioni = []
    file_paths = glob.glob(str(Path(cartella_path) / pattern))

    for file_path in file_paths:
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f, delimiter=';')
                
                for row in reader:
                    try:
                        # Conversione e validazione dati
                        data = parse_date(row['data'])
                        numeri = sorted([int(row[str(i)]) for i in range(1, 7)])
                        validate_numbers(numeri)
                        
                        jolly = int(row.get('jolly', 0))
                        superstar = int(row.get('supers', 0)) if 'supers' in row else None
                        
                        estrazioni.append(Estrazione(data, numeri, jolly, superstar))
                        
                    except (ValueError, KeyError) as e:
                        print(f"Errore nel file {file_path}, riga {reader.line_num}: {str(e)}")
        
        except Exception as e:
            print(f"Errore apertura file {file_path}: {str(e)}")

    return sorted(estrazioni, key=lambda x: x.data)

def save_to_database(estrazioni: List[Estrazione]) -> None:
    """Salva le estrazioni in un database SQLite"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Crea tabella se non esiste
    c.execute('''CREATE TABLE IF NOT EXISTS estrazioni
                 (data TEXT PRIMARY KEY, numeri TEXT, 
                  jolly INTEGER, superstar INTEGER)''')

    # Inserisci dati
    for e in estrazioni:
        try:
            c.execute('''INSERT INTO estrazioni 
                         VALUES (?, ?, ?, ?)''',
                      (e.data.isoformat(), 
                       ','.join(map(str, e.numeri)),
                       e.jolly, 
                       e.superstar))
        except sqlite3.IntegrityError:
            continue  # Salva duplicati

    conn.commit()
    conn.close()
    print(f"Dati salvati nel database: {DB_PATH}")

if __name__ == "__main__":
    # 1. Download automatico dati
    download_dati_storici()
    
    # 2. Caricamento dati
    estrazioni = load_estrazioni_multifile(CSV_DIR)
    
    if not estrazioni:
        raise SystemExit("Nessuna estrazione trovata!")
    
    print(f"\nCaricate {len(estrazioni)} estrazioni da {len(glob.glob(str(CSV_DIR/'*.csv')))} file")
    
    # 3. Salvataggio in database
    save_to_database(estrazioni)
    
    # Esempio di output
    print("\nUltima estrazione caricata:")
    last = estrazioni[-1]
    print(f"Data: {last.data.strftime('%d/%m/%Y')}")
    print(f"Numeri: {last.numeri}")
    if last.superstar:
        print(f"Superstar: {last.superstar}")
