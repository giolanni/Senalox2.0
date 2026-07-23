"""
Caricamento delle estrazioni per Senalox 1.0.

Il modulo legge un solo archivio condiviso:

    shared/data/estrazioni.csv

Mantiene due insiemi statistici distinti:

1. OVERALL: tutte le estrazioni presenti nell'archivio;
2. NEW MODE: soltanto le estrazioni dal 1 luglio 2009 in avanti.

Le vecchie funzioni ``load_estrazioni_multifile`` e
``load_estrazioni_filtered`` restano disponibili per non rompere il codice
esistente, ma ora delegano alle due modalità esplicite.
"""
from __future__ import annotations

import csv
import os
from datetime import datetime
from pathlib import Path
from typing import List

from shared.models.estrazione import Estrazione


# Data iniziale della nuova modalità del SuperEnalotto.
NEW_MODE_START_DATE = datetime(2009, 7, 1)


def get_estrazioni_file() -> Path:
    """
    Restituisce il percorso dell'archivio condiviso delle estrazioni.

    Quando l'applicazione viene avviata dal launcher, il percorso arriva dalla
    variabile d'ambiente ``SENALOX_DATA_DIR``. In caso di avvio diretto viene
    ricavato dalla struttura standard del progetto.
    """
    configured_data_dir = os.environ.get("SENALOX_DATA_DIR")

    if configured_data_dir:
        data_dir = Path(configured_data_dir)
    else:
        project_root = Path(__file__).resolve().parents[4]
        data_dir = project_root / "shared" / "data"

    return data_dir / "estrazioni.csv"


def load_estrazioni_overall() -> List[Estrazione]:
    """
    Carica tutte le estrazioni disponibili nell'archivio storico.

    Questo insieme comprende sia la vecchia modalità sia la nuova modalità.
    """
    estrazioni = _parse_csv(get_estrazioni_file())

    if not estrazioni:
        raise ValueError("Nessuna estrazione OVERALL caricata.")

    return sorted(estrazioni, key=lambda estrazione: estrazione.data)


def load_estrazioni_new_mode() -> List[Estrazione]:
    """
    Carica soltanto le estrazioni dal 1 luglio 2009 in avanti.
    """
    estrazioni = [
        estrazione
        for estrazione in load_estrazioni_overall()
        if estrazione.data >= NEW_MODE_START_DATE
    ]

    if not estrazioni:
        raise ValueError("Nessuna estrazione disponibile per la NEW MODE.")

    return estrazioni


def load_estrazioni_multifile(folder_path: str = None) -> List[Estrazione]:
    """
    Funzione mantenuta per compatibilità con il codice storico.

    Il parametro non viene più utilizzato perché esiste un solo CSV condiviso.
    Restituisce l'insieme OVERALL.
    """
    return load_estrazioni_overall()


def load_estrazioni_filtered(
    data_dir: str = None,
    start_year: int = None,
) -> List[Estrazione]:
    """
    Funzione mantenuta per compatibilità con il codice storico.

    - ``start_year == 2009``: restituisce NEW MODE;
    - in tutti gli altri casi: restituisce OVERALL.
    """
    if start_year == 2009:
        return load_estrazioni_new_mode()

    return load_estrazioni_overall()


def _parse_csv(file_path: Path) -> List[Estrazione]:
    """Converte le righe del CSV condiviso in oggetti ``Estrazione``."""
    if not file_path.exists():
        raise FileNotFoundError(
            f"Archivio delle estrazioni non trovato: {file_path}"
        )

    estrazioni: List[Estrazione] = []

    with file_path.open("r", encoding="utf-8-sig", newline="") as file_csv:
        reader = csv.DictReader(file_csv, delimiter=";")

        for row_number, row in enumerate(reader, start=2):
            try:
                data = datetime.strptime(row["data"], "%d/%m/%Y")
                numeri = [safe_int_convert(row[str(i)]) for i in range(1, 7)]
                jolly = safe_int_convert(row.get("jolly", "0"))
                supers = safe_int_convert(
                    row.get("supers.", row.get("supers", "0"))
                )

                estrazioni.append(Estrazione(data, numeri, jolly, supers))

            except (KeyError, TypeError, ValueError) as error:
                print(
                    f"Errore nel parsing della riga {row_number}: {error}. "
                    f"Contenuto: {row}"
                )

    return estrazioni


def safe_int_convert(value: str) -> int:
    """Converte una stringa in intero; per valori vuoti restituisce zero."""
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        print(f"Valore non numerico '{value}'")
        return 0
