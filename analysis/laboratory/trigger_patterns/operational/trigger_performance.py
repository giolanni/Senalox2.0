"""
Verifica l'andamento dei sistemi Trigger NEW MODE in un anno.

Per ogni attivazione del trigger considera le 9 estrazioni successive
e conta esclusivamente: 2, 3, 4, 5, 5+1, 6.

5+1 = esattamente 5 dei 6 numeri principali nel pool + Jolly nel pool.
Le finestre possono sovrapporsi: ogni uscita del trigger è una nuova attivazione.
"""
import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path

from shared.data_loader import load_estrazioni_new_mode
from analysis.laboratory.trigger_patterns.operational.trigger_systems import TRIGGER_SYSTEMS, WINDOW_SIZE

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
    totals = defaultdict(Counter)
    activations = Counter()
    observed = Counter()
    incomplete = Counter()
    detail_rows = []

    for idx, activation_draw in enumerate(estrazioni):
        if activation_draw.data.year != args.year:
            continue

        for trigger in sorted(set(activation_draw.numeri) & set(TRIGGER_SYSTEMS)):
            pool = TRIGGER_SYSTEMS[trigger]["pool"]
            following = estrazioni[idx+1:idx+1+WINDOW_SIZE]

            activations[trigger] += 1
            observed[trigger] += len(following)
            if len(following) < WINDOW_SIZE:
                incomplete[trigger] += 1

            local = Counter()

            for step, draw in enumerate(following, start=1):
                category = classify(draw, pool)
                if category:
                    totals[trigger][category] += 1
                    local[category] += 1

                detail_rows.append({
                    "Trigger": f"{trigger:02d}",
                    "ActivationDate": activation_draw.data.strftime("%d/%m/%Y"),
                    "Step": step,
                    "DrawDate": draw.data.strftime("%d/%m/%Y"),
                    "MainHits": len(set(draw.numeri) & pool),
                    "JollyHit": int(draw.jolly in pool),
                    "Category": category or "",
                    "Pool": ",".join(f"{n:02d}" for n in sorted(pool)),
                })

            if args.details:
                status = "COMPLETA" if len(following) == WINDOW_SIZE else f"IN CORSO {len(following)}/{WINDOW_SIZE}"
                result = " | ".join(f"{c}:{local[c]}" for c in CATEGORIES)
                print(f"Trigger {trigger:02d} - {activation_draw.data:%d/%m/%Y} - {status} - {result}")

    print()
    print("=" * 92)
    print(f"SENALOX - RISULTATI TRIGGER NEW MODE - ATTIVAZIONI {args.year}")
    print("=" * 92)
    print(f"{'Trig':>4} {'Attiv.':>6} {'InCorso':>8} {'Estr.':>6} {'2':>5} {'3':>5} {'4':>5} {'5':>5} {'5+1':>5} {'6':>5}")
    print("-" * 92)

    grand = Counter()
    for trigger in sorted(activations):
        c = totals[trigger]
        print(f"{trigger:>4} {activations[trigger]:>6} {incomplete[trigger]:>8} {observed[trigger]:>6} "
              f"{c['2']:>5} {c['3']:>5} {c['4']:>5} {c['5']:>5} {c['5+1']:>5} {c['6']:>5}")
        grand.update(c)

    print("-" * 92)
    print(f"{'TOT':>4} {sum(activations.values()):>6} {sum(incomplete.values()):>8} {sum(observed.values()):>6} "
          f"{grand['2']:>5} {grand['3']:>5} {grand['4']:>5} {grand['5']:>5} {grand['5+1']:>5} {grand['6']:>5}")

    if args.csv:
        outdir = Path(__file__).resolve().parent / "output"
        outdir.mkdir(parents=True, exist_ok=True)
        outfile = outdir / f"trigger_performance_{args.year}.csv"
        with outfile.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=detail_rows[0].keys() if detail_rows else [
                "Trigger","ActivationDate","Step","DrawDate","MainHits","JollyHit","Category","Pool"
            ], delimiter=";")
            writer.writeheader()
            writer.writerows(detail_rows)
        print(f"\nCSV creato: {outfile}")

if __name__ == "__main__":
    main()
