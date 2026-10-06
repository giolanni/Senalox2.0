"""
Classifica annuale delle prestazioni dei Trigger NEW MODE.

Per ogni anno e trigger:
- conta le estrazioni in cui il trigger era realmente attivo;
- conta i risultati 2, 3, 4, 5, 5+1, 6;
- confronta le estrazioni attive con il totale reale di estrazioni presenti
  nel dataset per quell'anno;
- ordina con gerarchia: 6 > 5+1 > 5 > 4 > 3 > 2.

A parita' di risultati, viene favorito il trigger con meno estrazioni attive
(e quindi migliore resa a parita' di esiti).
"""

import csv
from collections import Counter, defaultdict
from pathlib import Path

from shared.data_loader import load_estrazioni_new_mode
from analysis.laboratory.trigger_patterns.operational.trigger_systems import TRIGGER_SYSTEMS
from analysis.laboratory.trigger_patterns.operational.trigger_performance import classify
from analysis.laboratory.trigger_patterns.operational.trigger_state import build_global_timeline

CATEGORIES = ("2", "3", "4", "5", "5+1", "6")
RANK_CATEGORIES = ("6", "5+1", "5", "4", "3", "2")


def pct(num, den):
    return (100.0 * num / den) if den else 0.0


def rank_key(row):
    # Prima la qualita'/quantita' dei risultati secondo la gerarchia ufficiale.
    # Solo a perfetta parita' di risultati, meno esposizione e' migliore.
    return tuple(row[c] for c in RANK_CATEGORIES) + (-row["EstrazioniAttive"],)


def max_result(row):
    for c in RANK_CATEGORIES:
        if row[c]:
            return c
    return "-"


def main():
    estrazioni = sorted(load_estrazioni_new_mode(), key=lambda e: e.data)
    if not estrazioni:
        print("Nessuna estrazione disponibile.")
        return

    snapshots, _, _ = build_global_timeline(estrazioni)

    total_by_year = Counter(draw.data.year for draw in estrazioni)
    stats = defaultdict(lambda: defaultdict(Counter))

    for idx, draw in enumerate(estrazioni):
        year = draw.data.year
        for trigger in snapshots[idx]:
            stats[year][trigger]["EstrazioniAttive"] += 1
            category = classify(draw, TRIGGER_SYSTEMS[trigger]["pool"])
            if category:
                stats[year][trigger][category] += 1

    years = sorted(total_by_year)
    all_rows = []

    for year in years:
        total_year = total_by_year[year]
        year_rows = []

        # Mostriamo tutti i 15 sistemi, anche se in un anno un trigger
        # non ha avuto alcuna estrazione attiva.
        for trigger in sorted(TRIGGER_SYSTEMS):
            c = stats[year][trigger]
            active = c["EstrazioniAttive"]
            row = {
                "Anno": year,
                "Trigger": trigger,
                "EstrazioniAttive": active,
                "EstrazioniTotaliAnno": total_year,
                "PctAnnoAttivo": pct(active, total_year),
                **{cat: c[cat] for cat in CATEGORIES},
            }
            row["Massimo"] = max_result(row)
            year_rows.append(row)

        year_rows.sort(key=rank_key, reverse=True)
        for pos, row in enumerate(year_rows, 1):
            row["Posizione"] = pos
            all_rows.append(row)

        print()
        print("=" * 112)
        print(f"SENALOX - CLASSIFICA TRIGGER NEW MODE - {year} | Estrazioni anno: {total_year}")
        print("=" * 112)
        print(
            f"{'#':>2} {'TRG':>3} {'ATT/TOT':>11} {'%ATT':>7} "
            f"{'2':>4} {'3':>4} {'4':>4} {'5':>4} {'5+1':>5} {'6':>4} {'MAX':>5}"
        )
        print("-" * 112)

        for row in year_rows:
            print(
                f"{row['Posizione']:>2} {row['Trigger']:>3} "
                f"{row['EstrazioniAttive']:>4}/{row['EstrazioniTotaliAnno']:<6} "
                f"{row['PctAnnoAttivo']:>6.2f}% "
                f"{row['2']:>4} {row['3']:>4} {row['4']:>4} {row['5']:>4} "
                f"{row['5+1']:>5} {row['6']:>4} {row['Massimo']:>5}"
            )

    outdir = Path(__file__).resolve().parent / "output"
    outdir.mkdir(parents=True, exist_ok=True)
    outfile = outdir / "trigger_performance_by_year.csv"

    headers = [
        "Anno", "Posizione", "Trigger",
        "EstrazioniAttive", "EstrazioniTotaliAnno", "PctAnnoAttivo",
        "2", "3", "4", "5", "5+1", "6", "Massimo",
    ]

    with outfile.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=headers, delimiter=";")
        writer.writeheader()
        for row in all_rows:
            out = dict(row)
            out["Trigger"] = f"{out['Trigger']:02d}"
            out["PctAnnoAttivo"] = f"{out['PctAnnoAttivo']:.4f}"
            writer.writerow(out)

    print()
    print("=" * 112)
    print(f"CSV storico creato: {outfile}")
    print("Ranking: 6 > 5+1 > 5 > 4 > 3 > 2; a parita', minori estrazioni attive.")
    print("=" * 112)


if __name__ == "__main__":
    main()
