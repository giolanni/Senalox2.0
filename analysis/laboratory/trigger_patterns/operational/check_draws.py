"""
Controlla le ultime X estrazioni e mostra quali sistemi Trigger NEW MODE
attivi in ciascuna estrazione hanno prodotto un risultato.

LOGICA GLOBALE:
- un trigger compare una sola volta per estrazione;
- se si riattiva durante la finestra precedente, la finestra riparte da 9
  ma non nasce una seconda istanza;
- vengono mostrate le attivazioni totali del ciclo e le riattivazioni;
- senza -x analizza solo l'ultima estrazione;
- con -x N analizza le ultime N estrazioni;
- con -csv / --csv esporta i risultati trovati.
"""

import argparse
import csv
from pathlib import Path

from shared.data_loader import load_estrazioni_new_mode
from analysis.laboratory.trigger_patterns.operational.trigger_systems import (
    TRIGGER_SYSTEMS,
    WINDOW_SIZE,
)
from analysis.laboratory.trigger_patterns.operational.trigger_performance import classify
from analysis.laboratory.trigger_patterns.operational.trigger_state import (
    build_global_timeline,
)


def fmt_nums(nums):
    return " ".join(f"{n:02d}" for n in nums)


def main():
    parser = argparse.ArgumentParser(
        description="Controlla i risultati dei trigger nelle ultime X estrazioni."
    )
    parser.add_argument("-x", type=int, default=1, metavar="N")
    parser.add_argument(
        "-csv", "--csv", action="store_true", dest="export_csv"
    )
    args = parser.parse_args()

    if args.x < 1:
        parser.error("-x deve essere almeno 1")

    estrazioni = sorted(load_estrazioni_new_mode(), key=lambda e: e.data)
    if not estrazioni:
        print("Nessuna estrazione disponibile.")
        return

    snapshots, _, _ = build_global_timeline(estrazioni)

    n = min(args.x, len(estrazioni))
    first_target_idx = len(estrazioni) - n
    csv_rows = []

    print("=" * 104)
    print(f"SENALOX - CONTROLLO RISULTATI TRIGGER GLOBALI - ULTIME {n} ESTRAZIONI")
    print("=" * 104)

    for target_idx in range(first_target_idx, len(estrazioni)):
        draw = estrazioni[target_idx]
        active_states = snapshots[target_idx]
        result_rows = []

        for trigger, state in sorted(active_states.items()):
            cfg = TRIGGER_SYSTEMS[trigger]
            pool = cfg["pool"]
            hits = len(set(draw.numeri) & pool)
            jolly_hit = draw.jolly in pool
            category = classify(draw, pool)

            row = {
                "DataEstrazione": draw.data.strftime("%d/%m/%Y"),
                "NumeriEstratti": fmt_nums(draw.numeri),
                "Jolly": f"{draw.jolly:02d}",
                "Trigger": f"{trigger:02d}",
                "PrimaAttivazione": estrazioni[state["cycle_start_idx"]].data.strftime("%d/%m/%Y"),
                "UltimaAttivazione": estrazioni[state["last_activation_idx"]].data.strftime("%d/%m/%Y"),
                "AttivazioniCiclo": state["activations_in_cycle"],
                "RiattivazioniCiclo": state["reactivations_in_cycle"],
                "EstrazioneSu9": target_idx - state["last_activation_idx"],
                "NumeriIndovinati": hits,
                "JollyPresente": "SI" if jolly_hit else "NO",
                "Risultato": category or "",
                "NumeriSistema": ",".join(f"{x:02d}" for x in sorted(pool)),
            }

            if category:
                result_rows.append(row)
                csv_rows.append(row)

        print()
        print("-" * 104)
        print(
            f"ESTRAZIONE {draw.data:%d/%m/%Y} - "
            f"{fmt_nums(draw.numeri)} | Jolly {draw.jolly:02d}"
        )
        print(f"Trigger globali attivi: {len(active_states)}")
        print("-" * 104)

        if not result_rows:
            print("Nessun trigger attivo ha prodotto un risultato >= 2.")
            continue

        rank = {"2": 2, "3": 3, "4": 4, "5": 5, "5+1": 6, "6": 7}
        result_rows.sort(
            key=lambda r: (-rank.get(r["Risultato"], 0), int(r["Trigger"]))
        )

        for row in result_rows:
            reatt = ""
            if row["RiattivazioniCiclo"]:
                reatt = (
                    f", {row['AttivazioniCiclo']} attivazioni "
                    f"({row['RiattivazioniCiclo']} riatt.)"
                )
            extra = " + Jolly" if row["Risultato"] == "5+1" else ""
            print(
                f"Trigger {row['Trigger']} "
                f"(ultima att. {row['UltimaAttivazione']}, "
                f"step {row['EstrazioneSu9']}/{WINDOW_SIZE}{reatt}) "
                f"-> {row['Risultato']}{extra}"
            )

    print()
    print("=" * 104)
    print(f"Totale risultati trovati nelle {n} estrazioni analizzate: {len(csv_rows)}")
    print("=" * 104)

    if args.export_csv:
        outdir = Path(__file__).resolve().parent / "output"
        outdir.mkdir(parents=True, exist_ok=True)
        outfile = outdir / f"check_draws_last_{n}.csv"

        headers = [
            "DataEstrazione",
            "NumeriEstratti",
            "Jolly",
            "Trigger",
            "PrimaAttivazione",
            "UltimaAttivazione",
            "AttivazioniCiclo",
            "RiattivazioniCiclo",
            "EstrazioneSu9",
            "NumeriIndovinati",
            "JollyPresente",
            "Risultato",
            "NumeriSistema",
        ]

        # RIGA 2 FISSA DI SPIEGAZIONE.
        descriptions = [
            "Data dell'estrazione analizzata",
            "I 6 numeri principali estratti",
            "Numero Jolly dell'estrazione",
            "Trigger globale attivo",
            "Data della prima attivazione del ciclo globale corrente",
            "Data dell'ultima attivazione o riattivazione del trigger",
            "Numero totale di attivazioni nel ciclo globale corrente",
            "Numero di riattivazioni avvenute mentre il trigger era gia attivo",
            "Posizione dell'estrazione rispetto all'ultima attivazione (da 1 a 9)",
            "Quanti dei 6 estratti sono presenti nei 13 numeri del sistema",
            "SI se il Jolly e presente nei 13 numeri del sistema, altrimenti NO",
            "Risultato ottenuto: 2, 3, 4, 5, 5+1 oppure 6",
            "I 13 numeri associati al sistema trigger",
        ]

        with outfile.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(headers)
            writer.writerow(descriptions)
            for row in csv_rows:
                writer.writerow([row[h] for h in headers])

        print(f"\nCSV creato: {outfile}")


if __name__ == "__main__":
    main()
