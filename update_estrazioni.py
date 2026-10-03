"""
SENALOX - Aggiornamento automatico archivio estrazioni
======================================================

Scarica le estrazioni SuperEnalotto da Franknet e aggiorna l'archivio
condiviso shared/data/estrazioni.csv aggiungendo solo le date mancanti.

Uso:
    python update_estrazioni.py
"""

from __future__ import annotations

import csv
import re
import sys

from datetime import date, datetime
from io import StringIO

import requests
from bs4 import BeautifulSoup

from shared.paths import ESTRAZIONI_FILE


URL_TEMPLATE = "https://franknet.altervista.org/superena/{anno}.HTM"

MESI = {
    "gen": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "mag": 5,
    "giu": 6,
    "lug": 7,
    "ago": 8,
    "set": 9,
    "ott": 10,
    "nov": 11,
    "dic": 12,
}

# Esempio:
# 02 ott  02 31 55 56 73 84  77  41  158
RIGA_ESTRAZIONE = re.compile(
    r"^\s*(\d{1,2})\s+"
    r"(gen|feb|mar|apr|mag|giu|lug|ago|set|ott|nov|dic)\s+"
    r"(\d{1,2})\s+(\d{1,2})\s+(\d{1,2})\s+"
    r"(\d{1,2})\s+(\d{1,2})\s+(\d{1,2})\s+"
    r"(\d{1,2})\s+(\d{1,2})\s+(\d+)\s*$",
    re.IGNORECASE,
)

HEADER = ["data", "1", "2", "3", "4", "5", "6", "jolly", "supers."]


def scarica_anno(anno: int) -> list[dict[str, object]]:
    """Scarica e interpreta tutte le estrazioni disponibili per un anno."""

    url = URL_TEMPLATE.format(anno=anno)

    response = requests.get(
        url,
        timeout=20,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/120 Safari/537.36"
            )
        },
    )
    response.raise_for_status()

    # La pagina storica non espone sempre una codifica affidabile.
    response.encoding = response.apparent_encoding or "latin-1"

    testo = BeautifulSoup(response.text, "html.parser").get_text("\n")

    estrazioni: list[dict[str, object]] = []

    for riga in testo.splitlines():
        match = RIGA_ESTRAZIONE.match(riga)
        if not match:
            continue

        valori = match.groups()

        giorno = int(valori[0])
        mese = MESI[valori[1].lower()]
        numeri = [int(x) for x in valori[2:8]]
        jolly = int(valori[8])
        superstar = int(valori[9])
        concorso = int(valori[10])

        try:
            data_estrazione = date(anno, mese, giorno)
        except ValueError:
            continue

        if (
            len(set(numeri)) != 6
            or any(numero < 1 or numero > 90 for numero in numeri)
            or not 1 <= jolly <= 90
            or not 1 <= superstar <= 90
        ):
            print(
                f"ATTENZIONE: estrazione non valida ignorata: {' '.join(valori)}",
                file=sys.stderr,
            )
            continue

        estrazioni.append(
            {
                "data": data_estrazione,
                "numeri": numeri,
                "jolly": jolly,
                "superstar": superstar,
                "concorso": concorso,
            }
        )

    return estrazioni


def leggi_archivio() -> tuple[list[dict[str, str]], set[date]]:
    """Legge il CSV Senalox esistente e restituisce righe e date presenti."""

    if not ESTRAZIONI_FILE.exists():
        raise FileNotFoundError(
            f"Archivio estrazioni non trovato: {ESTRAZIONI_FILE}"
        )

    with ESTRAZIONI_FILE.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file_csv:
        reader = csv.DictReader(file_csv, delimiter=";")
        righe = list(reader)

    date_presenti: set[date] = set()

    for numero_riga, riga in enumerate(righe, start=2):
        try:
            data_estrazione = datetime.strptime(
                riga["data"].strip(),
                "%d/%m/%Y",
            ).date()
            date_presenti.add(data_estrazione)
        except (KeyError, AttributeError, ValueError) as errore:
            raise ValueError(
                f"Data non valida in estrazioni.csv alla riga "
                f"{numero_riga}: {errore}"
            ) from errore

    return righe, date_presenti


def nuova_riga(estrazione: dict[str, object]) -> dict[str, str]:
    """Converte un'estrazione nel formato del CSV condiviso."""

    data_estrazione = estrazione["data"]
    numeri = estrazione["numeri"]

    assert isinstance(data_estrazione, date)
    assert isinstance(numeri, list)

    return {
        "data": data_estrazione.strftime("%d/%m/%Y"),
        "1": str(numeri[0]),
        "2": str(numeri[1]),
        "3": str(numeri[2]),
        "4": str(numeri[3]),
        "5": str(numeri[4]),
        "6": str(numeri[5]),
        "jolly": str(estrazione["jolly"]),
        "supers.": str(estrazione["superstar"]),
    }


def aggiorna_archivio() -> int:
    """Aggiunge al CSV soltanto le estrazioni non ancora presenti."""

    righe, date_presenti = leggi_archivio()

    if not date_presenti:
        raise ValueError("estrazioni.csv non contiene alcuna estrazione.")

    ultima_data = max(date_presenti)
    anno_corrente = date.today().year

    if ultima_data.year > anno_corrente:
        raise ValueError(
            "L'ultima estrazione nel CSV appartiene a un anno futuro."
        )

    trovate: list[dict[str, object]] = []

    for anno in range(ultima_data.year, anno_corrente + 1):
        estrazioni_web = scarica_anno(anno)

        if not estrazioni_web:
            print(f"ATTENZIONE: nessuna estrazione trovata per il {anno}.")
            continue

        for estrazione in estrazioni_web:
            data_estrazione = estrazione["data"]
            assert isinstance(data_estrazione, date)

            if data_estrazione not in date_presenti:
                trovate.append(estrazione)
                date_presenti.add(data_estrazione)

    trovate.sort(key=lambda item: item["data"])

    print("SENALOX - AGGIORNAMENTO ESTRAZIONI")
    print("=" * 50)
    print(f"Ultima estrazione presente : {ultima_data:%d/%m/%Y}")
    print(f"Nuove estrazioni trovate   : {len(trovate)}")

    if not trovate:
        print("\nArchivio gia' aggiornato. Nessuna modifica effettuata.")
        return 0

    for estrazione in trovate:
        data_estrazione = estrazione["data"]
        numeri = estrazione["numeri"]

        assert isinstance(data_estrazione, date)
        assert isinstance(numeri, list)

        numeri_testo = " ".join(f"{numero:02d}" for numero in numeri)

        print(
            f"+ {data_estrazione:%d/%m/%Y}  {numeri_testo} "
            f"| Jolly {int(estrazione['jolly']):02d} "
            f"| SuperStar {int(estrazione['superstar']):02d}"
        )

        righe.append(nuova_riga(estrazione))

    # Ordina l'intero archivio cronologicamente: in questo modo viene
    # recuperata correttamente anche un'eventuale estrazione mancante
    # all'interno dello storico, non soltanto in coda.
    righe.sort(
        key=lambda riga: datetime.strptime(
            riga["data"].strip(),
            "%d/%m/%Y",
        )
    )

    buffer = StringIO(newline="")
    writer = csv.DictWriter(
        buffer,
        fieldnames=HEADER,
        delimiter=";",
        lineterminator="\n",
        extrasaction="ignore",
    )
    writer.writeheader()
    writer.writerows(righe)

    # Scrittura atomica: il file originale viene sostituito soltanto dopo
    # che tutto il nuovo contenuto e' stato costruito correttamente.
    file_temporaneo = ESTRAZIONI_FILE.with_suffix(".csv.tmp")
    file_temporaneo.write_text(
        buffer.getvalue(),
        encoding="utf-8-sig",
        newline="",
    )
    file_temporaneo.replace(ESTRAZIONI_FILE)

    print(f"\nArchivio aggiornato: {ESTRAZIONI_FILE}")
    return len(trovate)


def main() -> None:
    try:
        aggiorna_archivio()
    except requests.RequestException as errore:
        print(
            f"ERRORE: impossibile scaricare le estrazioni: {errore}",
            file=sys.stderr,
        )
        raise SystemExit(1) from errore
    except (OSError, ValueError) as errore:
        print(f"ERRORE: {errore}", file=sys.stderr)
        raise SystemExit(1) from errore


if __name__ == "__main__":
    main()
