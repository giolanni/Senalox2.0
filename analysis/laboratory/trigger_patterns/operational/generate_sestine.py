"""Genera sestine dai migliori trigger ancora giocabili."""
import argparse
import random
from collections import Counter
from datetime import date

from shared.data_loader import load_estrazioni_new_mode
from analysis.laboratory.trigger_patterns.operational.trigger_systems import TRIGGER_SYSTEMS, WINDOW_SIZE
from analysis.laboratory.trigger_patterns.operational.trigger_state import build_global_timeline
from analysis.laboratory.trigger_patterns.operational.trigger_performance import classify

RANK = ("6", "5+1", "5", "4", "3", "2")

def months_before(d, months):
    y = d.year
    m = d.month - months
    while m <= 0:
        m += 12
        y -= 1
    return date(y, m, min(d.day, __import__("calendar").monthrange(y, m)[1]))

def calculate(estrazioni, snapshots, start, end):
    stats = {t: Counter() for t in TRIGGER_SYSTEMS}
    for i, draw in enumerate(estrazioni):
        if not start <= draw.data <= end:
            continue
        for t in snapshots[i]:
            stats[t]["active"] += 1
            result = classify(draw, TRIGGER_SYSTEMS[t]["pool"])
            if result:
                stats[t][result] += 1
    return stats

def sort_key(t, stats):
    c = stats[t]
    return tuple(c[k] for k in RANK) + (-c["active"], -t)

def main():
    parser = argparse.ArgumentParser(description="Genera sestine dai trigger attivi piu performanti")
    parser.add_argument("-n", "--numero", type=int, required=True, help="Numero di sestine")
    parser.add_argument("--periodo", choices=("auto", "anno", "4mesi"), default="auto")
    parser.add_argument("--seed", type=int, help="Seed per rendere ripetibile la selezione casuale")
    args = parser.parse_args()
    if args.numero < 1:
        parser.error("Il numero di sestine deve essere positivo")
    draws = sorted(load_estrazioni_new_mode(), key=lambda d: d.data)
    if not draws:
        print("Nessuna estrazione disponibile.")
        return
    snapshots, _, states = build_global_timeline(draws)
    last = draws[-1].data
    last_idx = len(draws) - 1
    playable = {t: s for t, s in states.items() if last_idx < s["active_until_idx"]}
    if not playable:
        print("Nessun trigger giocabile alla prossima estrazione.")
        return
    period = args.periodo
    if period == "auto":
        period = "4mesi" if last.month <= 4 else "anno"
    start = months_before(last, 4) if period == "4mesi" else date(last.year, 1, 1)
    stats = calculate(draws, snapshots, start, last)
    ranking = sorted(playable, key=lambda t: sort_key(t, stats), reverse=True)
    count = min(args.numero, len(ranking))
    rng = random.Random(args.seed)
    print(f"SENALOX - SESTINE | Dati al {last:%d/%m/%Y} | Ranking {start:%d/%m/%Y} - {last:%d/%m/%Y}")
    print(f"Trigger giocabili: {len(ranking)} | Sestine richieste: {args.numero}")
    if count < args.numero:
        print(f"ATTENZIONE: disponibili solo {count} trigger diversi; genero {count} sestine.")
    print("Classifica trigger giocabili (risultati sulle sole estrazioni attive):")
    print("Pos Trg Estr  2  3  4  5 5+1  6")
    for pos, t in enumerate(ranking, 1):
        c = stats[t]
        print(f"{pos:>3} {t:>3} {c['active']:>4} " + " ".join(f"{c[k]:>3}" for k in ("2","3","4","5","5+1","6")))
    print("\nSESTINE")
    for pos, t in enumerate(ranking[:count], 1):
        stable = set(TRIGGER_SYSTEMS[t]["stable"])
        pool = set(TRIGGER_SYSTEMS[t]["pool"])
        if len(stable) > 6 or not stable <= pool:
            raise ValueError(f"Configurazione pool/stabili non valida per trigger {t}")
        others = rng.sample(sorted(pool - stable), 6 - len(stable))
        numbers = sorted(stable | set(others))
        remaining = playable[t]["active_until_idx"] - last_idx
        print(f"{pos}. Trigger {t:02d} (restano {remaining} estr.) | " +
              " ".join(f"{x:02d}" for x in numbers) +
              " | stabili: " + " ".join(f"{x:02d}" for x in sorted(stable)))

if __name__ == "__main__":
    main()
