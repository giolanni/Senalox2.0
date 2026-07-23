"""
SENALOX - Caricamento centralizzato delle estrazioni
====================================================

Questo è l'unico modulo del progetto autorizzato a leggere il file
delle estrazioni.

Sia Senalox Legacy sia New Senalox utilizzano il medesimo archivio:

    shared/data/estrazioni.csv

Il modulo conserva due insiemi statistici distinti:

OVERALL
    Tutte le estrazioni disponibili nell'archivio storico.

NEW MODE
    Le sole estrazioni dal 1 luglio 2009 in avanti.

Le funzioni con i vecchi nomi, come ``load_estrazioni_multifile`` e
``load_estrazioni_filtered``, vengono mantenute perché sono ancora
richiamate dalle interfacce esistenti. Non leggono però più cartelle
multiple: utilizzano sempre il file CSV condiviso.
"""

from __future__ import annotations

import csv

from datetime import date, datetime
from pathlib import Path
from typing import List

from shared.models.estrazione import Estrazione
from shared.paths import ESTRAZIONI_FILE


# Data di inizio della nuova modalità del SuperEnalotto.
NEW_MODE_START_DATE = date(2009, 7, 1)


def load_estrazioni_overall() -> List[Estrazione]:
    """
    Carica tutte le estrazioni presenti nell'archivio condiviso.

    Returns
    -------
    List[Estrazione]
        Estratti ordinati cronologicamente dal più vecchio al più recente.
    """

    estrazioni = _parse_csv(ESTRAZIONI_FILE)

    if not estrazioni:
        raise ValueError(
            f"Nessuna estrazione trovata nel file:\n{ESTRAZIONI_FILE}"
        )

    return sorted(
        estrazioni,
        key=lambda estrazione: estrazione.data,
    )


def load_estrazioni_new_mode() -> List[Estrazione]:
    """
    Carica esclusivamente le estrazioni dal 1 luglio 2009.

    Returns
    -------
    List[Estrazione]
        Estrazioni appartenenti alla nuova modalità.
    """

    return filtra_per_data(
        estrazioni=load_estrazioni_overall(),
        anno=2009,
    )


def load_estrazioni_multifile(
    folder_path: str | Path | None = None,
) -> List[Estrazione]:
    """
    Mantiene compatibilità con il vecchio nome della funzione.

    In passato la funzione leggeva più CSV da una cartella. Oggi il parametro
    ``folder_path`` viene ignorato e viene sempre usato l'unico archivio
    condiviso.

    Parameters
    ----------
    folder_path
        Parametro legacy non più utilizzato.
    """

    return load_estrazioni_overall()


def load_estrazioni_filtered(
    data_dir: str | Path | None = None,
    start_year: int | None = None,
) -> List[Estrazione]:
    """
    Carica OVERALL oppure NEW MODE.

    La firma mantiene il parametro ``data_dir`` perché Senalox Legacy chiama
    ancora la funzione in questo modo:

        load_estrazioni_filtered("./data", start_year)

    Il percorso ricevuto viene ignorato.

    Parameters
    ----------
    data_dir
        Parametro legacy non più utilizzato.

    start_year
        Se vale 2009, restituisce NEW MODE.
        Negli altri casi restituisce OVERALL.
    """

    if start_year == 2009:
        return load_estrazioni_new_mode()

    return load_estrazioni_overall()


def filtra_per_data(
    estrazioni: List[Estrazione],
    anno: int | None = None,
) -> List[Estrazione]:
    """
    Filtra una lista di estrazioni in base alla modalità selezionata.

    Questa funzione è utilizzata da New Senalox:

        anno=None
            restituisce tutte le estrazioni;

        anno=2009
            restituisce le estrazioni dal 1 luglio 2009.

    Parameters
    ----------
    estrazioni
        Lista da filtrare.

    anno
        Anno di riferimento. Attualmente la modalità significativa è 2009.
    """

    if anno is None:
        return list(estrazioni)

    if anno == 2009:
        data_minima = NEW_MODE_START_DATE
    else:
        data_minima = date(anno, 1, 1)

    return [
        estrazione
        for estrazione in estrazioni
        if _as_date(estrazione.data) >= data_minima
    ]


def _parse_csv(file_path: Path) -> List[Estrazione]:
    """
    Legge il CSV condiviso e converte ogni riga in un oggetto Estrazione.
    """

    if not file_path.exists():
        raise FileNotFoundError(
            f"File delle estrazioni non trovato:\n{file_path}"
        )

    estrazioni: List[Estrazione] = []

    with file_path.open(
        mode="r",
        encoding="utf-8-sig",
        newline="",
    ) as csv_file:

        reader = csv.DictReader(
            csv_file,
            delimiter=";",
        )

        if reader.fieldnames is None:
            raise ValueError(
                f"Il file CSV non contiene un'intestazione valida:\n{file_path}"
            )

        for numero_riga, row in enumerate(reader, start=2):
            try:
                data_estrazione = datetime.strptime(
                    row["data"].strip(),
                    "%d/%m/%Y",
                ).date()

                numeri = [
                    _safe_int(row[str(indice)])
                    for indice in range(1, 7)
                ]

                jolly = _safe_int(row.get("jolly"))

                superstar = _safe_int(
                    row.get("supers")
                    or row.get("supers.")
                    or row.get("superstar")
                )

                estrazioni.append(
                    Estrazione(
                        data=data_estrazione,
                        numeri=numeri,
                        jolly=jolly,
                        superstar=superstar,
                    )
                )

            except Exception as errore:
                print(
                    f"Errore nel file {file_path.name}, "
                    f"riga {numero_riga}: {errore}"
                )

    return estrazioni


def _as_date(value: date | datetime) -> date:
    """
    Converte un eventuale datetime in date.

    Serve a mantenere compatibilità con oggetti creati in precedenza dalla
    versione legacy.
    """

    if isinstance(value, datetime):
        return value.date()

    return value


def _safe_int(value: object) -> int:
    """
    Converte un valore in intero.

    Restituisce zero quando il campo è assente, vuoto o non numerico.
    """

    if value is None:
        return 0

    try:
        testo = str(value).strip()

        if not testo:
            return 0

        return int(testo)

    except (TypeError, ValueError):
        return 0