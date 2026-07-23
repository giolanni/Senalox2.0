import csv
from datetime import datetime, date
from pathlib import Path
from typing import List

from shared.models.estrazione import Estrazione

def load_estrazioni_multifile(folder_path: str = None) -> List[Estrazione]:
    """
    Carica estrazioni da tutti i CSV nella cartella specificata.
    Se folder_path non è fornito, utilizza la cartella 'data' relativa alla root del progetto.
    """
    estrazioni = []

    # Calcola il percorso della cartella 'data'
    if folder_path is None:
        folder_path = Path(__file__).resolve().parent.parent.parent / "data"
    else:
        folder_path = Path(folder_path)

    # Verifica se la directory esiste e contiene file
    if not folder_path.exists():
        raise FileNotFoundError(f"La directory '{folder_path}' non esiste.")
    if not any(folder_path.iterdir()):
        raise FileNotFoundError(f"La directory '{folder_path}' è vuota.")
    
    for csv_file in folder_path.glob("*.csv"):
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                try:
                    # Converti la stringa in oggetto date
                    data_str = row['data']
                    data = datetime.strptime(data_str, "%d/%m/%Y").date()
                    numeri = [int(row[str(i)]) for i in range(1, 7)]
                    jolly = int(row.get('jolly', 0))
                    superstar = int(row.get('supers', 0))
                    
                    estrazioni.append(Estrazione(data, numeri, jolly, superstar))
                except (KeyError, ValueError) as e:
                    print(f"Errore nel file {csv_file.name}, riga {reader.line_num}: {str(e)}")
    
  
    # Filtra eventuali oggetti con data non valida
    estrazioni_valide = [e for e in estrazioni if isinstance(e.data, date)]
    return sorted(estrazioni_valide, key=lambda x: x.data)

def filtra_per_data(estrazioni: List[Estrazione], anno: int = None) -> List[Estrazione]:
    """Filtra le estrazioni in base alla data minima"""
    if not anno:
        return estrazioni
    data_2009 = datetime(anno, 7, 1).date()
    # Se data_min è datetime, converti in date
    if isinstance(data_2009, datetime):
        data_2009 = data_2009.date()
    
    return [e for e in estrazioni if e.data >= data_2009]
