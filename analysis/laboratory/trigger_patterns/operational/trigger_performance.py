"""
Verifica l'andamento dei sistemi Trigger NEW MODE in un anno.

LOGICA GLOBALE:
- un trigger e' un solo sistema globale;
- se ricompare durante le sue 9 estrazioni attive, viene RIATTIVATO:
  non nasce una seconda istanza e la finestra riparte da 9;
- ogni estrazione viene conteggiata al massimo una volta per trigger;
- EstrAttive = numero di estrazioni reali/uniche in cui il trigger e' stato attivo;
- Attiv. = uscite del trigger nell'anno;
- Riattiv. = quante di quelle uscite sono avvenute mentre era gia' attivo.

L'estrazione della prima attivazione non e' una performance del sistema.
Se il trigger ricompare mentre e' gia' attivo, quella estrazione e' invece
gia' una performance della finestra precedente e viene conteggiata una sola volta;
subito dopo la finestra viene riavviata.

5+1 = esattamente 5 dei 6 numeri principali nel pool + Jolly nel pool.
"""

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path

from shared.data_loader import load_estrazioni_new_mode
from analysis.laboratory.trigger_patterns.operational.trigger_systems import (
    TRIGGER_SYSTEMS,
    WINDOW_SIZE,
)
from analysis.laboratory.trigger_patterns.operational.trigger_state import (
    build_global_timeline,
)

CATEGORIES = ("2", "3", "4", "5", "5+1", "6")


def classify(draw, pool):
    hits = len(set(draw.numeri) & pool)
    jolly_hit = draw.jolly in pool
    if hits == 6:
        return "6"
    if hits == 5 and jolly_hit:
        return "5+1"
    if hits == 5:
        return "5"
    if hits in (2, 3, 4):
        return str(hits)
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=2026)
    parser.add_argument("--details", action="store_true")
    parser.add_argument("--csv", action="store_true")
    args = parser.parse_args()

    estrazioni = sorted(load_estrazioni_new_mode(), key=lambda e: e.data)
    if not estrazioni:
        print("Nessuna estrazione disponibile.")
        return

    snapshots, events, final_states = build_global_timeline(estrazioni)

    totals = defaultdict(Counter)
    activations = Counter()
    reactivations = Counter()
    active_draws = Counter()
    detail_rows = []

    # Attivazioni e riattivazioni avvenute nell'anno richiesto.
    for idx, draw_events in enumerate(events):
        if estrazioni[idx].data.year != args.year:
            continue
        for event in draw_events:
            trigger = event["trigger"]
            activations[trigger] += 1
            if event["type"] == "RIATTIVAZIONE":
                reactivations[trigger] += 1

            if args.details:
                suffix = ""
                if event["type"] == "RIATTIVAZIONE":
                    suffix = (
                        f" - attivazione #{event['activations_in_cycle']} del ciclo; "
                        f"finestra ripartita da 9"
                    )
                print(
                    f"Trigger {trigger:02d} - {estrazioni[idx].data:%d/%m/%Y} "
                    f"- {event['type']}{suffix}"
                )

    # Performance: ogni trigger compare al massimo una volta per estrazione.
    for idx, draw in enumerate(estrazioni):
        if draw.data.year != args.year:
            continue

        for trigger, state in sorted(snapshots[idx].items()):
            pool = TRIGGER_SYSTEMS[trigger]["pool"]
            category = classify(draw, pool)
            hits = len(set(draw.numeri) & pool)
            jolly_hit = draw.jolly in pool

            active_draws[trigger] += 1
            if category:
                totals[trigger][category] += 1

            detail_rows.append({
                "Trigger": f"{trigger:02d}",
                "CycleStartDate": estrazioni[state["cycle_start_idx"]].data.strftime("%d/%m/%Y"),
                "LastActivationDate": estrazioni[state["last_activation_idx"]].data.strftime("%d/%m/%Y"),
                "ActivationsInCycle": state["activations_in_cycle"],
                "ReactivationsInCycle": state["reactivations_in_cycle"],
                "StepFromLastActivation": idx - state["last_activation_idx"],
                "DrawDate": draw.data.strftime("%d/%m/%Y"),
                "MainHits": hits,
                "JollyHit": int(jolly_hit),
                "Category": category or "",
                "Pool": ",".join(f"{n:02d}" for n in sorted(pool)),
            })

    trigger_ids = sorted(
        set(activations) | set(reactivations) | set(active_draws) | set(totals)
    )

    print()
    print("=" * 108)
    print(f"SENALOX - RISULTATI TRIGGER GLOBALI NEW MODE - ANNO {args.year}")
    print("=" * 108)
    print(
        f"{'Trig':>4} {'Attiv.':>6} {'Riattiv.':>8} {'EstrAttive':>10} "
        f"{'2':>5} {'3':>5} {'4':>5} {'5':>5} {'5+1':>5} {'6':>5}"
    )
    print("-" * 108)

    grand = Counter()
    for trigger in trigger_ids:
        c = totals[trigger]
        print(
            f"{trigger:>4} {activations[trigger]:>6} {reactivations[trigger]:>8} "
            f"{active_draws[trigger]:>10} "
            f"{c['2']:>5} {c['3']:>5} {c['4']:>5} {c['5']:>5} "
            f"{c['5+1']:>5} {c['6']:>5}"
        )
        grand.update(c)

    print("-" * 108)
    print(
        f"{'TOT':>4} {sum(activations.values()):>6} {sum(reactivations.values()):>8} "
        f"{sum(active_draws.values()):>10} "
        f"{grand['2']:>5} {grand['3']:>5} {grand['4']:>5} {grand['5']:>5} "
        f"{grand['5+1']:>5} {grand['6']:>5}"
    )

    # Stato dei trigger ancora attivi alla fine dei dati disponibili.
    active_now = []
    last_index = len(estrazioni) - 1
    for trigger, state in sorted(final_states.items()):
        active_now.append(
            f"{trigger:02d}({last_index - state['last_activation_idx']}/{WINDOW_SIZE}, "
            f"attiv.{state['activations_in_cycle']})"
        )
    if active_now:
        print("\nAttivi sull'ultima estrazione: " + ", ".join(active_now))

    if args.csv:
        outdir = Path(__file__).resolve().parent / "output"
        outdir.mkdir(parents=True, exist_ok=True)
        outfile = outdir / f"trigger_performance_{args.year}.csv"

        headers = [
            "Trigger",
            "Attivazioni",
            "Riattivazioni",
            "EstrazioniAttive",
            "Risultati2",
            "Risultati3",
            "Risultati4",
            "Risultati5",
            "Risultati5+1",
            "Risultati6",
        ]

        descriptions = [
            "Numero del trigger",
            "Quante volte il trigger e uscito nell'anno",
            "Quante volte e ricomparso mentre era gia attivo",
            "Numero di estrazioni uniche in cui il trigger e stato effettivamente attivo",
            "Quante estrazioni attive hanno prodotto 2 numeri nel sistema",
            "Quante estrazioni attive hanno prodotto 3 numeri nel sistema",
            "Quante estrazioni attive hanno prodotto 4 numeri nel sistema",
            "Quante estrazioni attive hanno prodotto 5 numeri nel sistema",
            "Quante estrazioni attive hanno prodotto 5 numeri + Jolly nel sistema",
            "Quante estrazioni attive hanno prodotto 6 numeri nel sistema",
        ]

        with outfile.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(headers)
            writer.writerow(descriptions)

            for trigger in trigger_ids:
                c = totals[trigger]
                writer.writerow([
                    f"{trigger:02d}",
                    activations[trigger],
                    reactivations[trigger],
                    active_draws[trigger],
                    c["2"],
                    c["3"],
                    c["4"],
                    c["5"],
                    c["5+1"],
                    c["6"],
                ])

            writer.writerow([
                "TOT",
                sum(activations.values()),
                sum(reactivations.values()),
                sum(active_draws.values()),
                grand["2"],
                grand["3"],
                grand["4"],
                grand["5"],
                grand["5+1"],
                grand["6"],
            ])

        print(f"\nCSV riepilogativo creato: {outfile}")


if __name__ == "__main__":
    main()
