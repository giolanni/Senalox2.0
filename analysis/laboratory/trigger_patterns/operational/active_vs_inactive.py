"""
Confronta il rendimento dei 15 pool Trigger NEW MODE quando il relativo
trigger e' ATTIVO e quando NON e' ATTIVO.

ATTIVO = estrazione presente nello snapshot globale ufficiale, cioe' una
delle 9 estrazioni successive all'attivazione/riattivazione.
NON_ATTIVO = tutte le altre estrazioni NEW MODE.

Il confronto usa tassi percentuali, non soli conteggi, perche' i due gruppi
hanno numerosita' molto diverse.
"""

import csv
from pathlib import Path

from shared.data_loader import load_estrazioni_new_mode
from analysis.laboratory.trigger_patterns.operational.trigger_systems import TRIGGER_SYSTEMS
from analysis.laboratory.trigger_patterns.operational.trigger_performance import classify
from analysis.laboratory.trigger_patterns.operational.trigger_state import build_global_timeline

CATEGORIES = ("2", "3", "4", "5", "5+1", "6")


def empty_stats():
    return {"Estrazioni": 0, **{c: 0 for c in CATEGORIES}}


def pct(num, den):
    return (100.0 * num / den) if den else 0.0


def plus_count(stats, level):
    if level == 3:
        cats = ("3", "4", "5", "5+1", "6")
    elif level == 4:
        cats = ("4", "5", "5+1", "6")
    elif level == 5:
        cats = ("5", "5+1", "6")
    else:
        raise ValueError(level)
    return sum(stats[c] for c in cats)


def main():
    estrazioni = sorted(load_estrazioni_new_mode(), key=lambda e: e.data)
    if not estrazioni:
        print("Nessuna estrazione disponibile.")
        return

    snapshots, _, _ = build_global_timeline(estrazioni)
    stats = {
        trigger: {"ATTIVO": empty_stats(), "NON_ATTIVO": empty_stats()}
        for trigger in TRIGGER_SYSTEMS
    }

    for idx, draw in enumerate(estrazioni):
        active_now = snapshots[idx]
        for trigger, cfg in TRIGGER_SYSTEMS.items():
            stato = "ATTIVO" if trigger in active_now else "NON_ATTIVO"
            s = stats[trigger][stato]
            s["Estrazioni"] += 1
            category = classify(draw, cfg["pool"])
            if category:
                s[category] += 1

    summary = []
    detail_rows = []

    for trigger in sorted(TRIGGER_SYSTEMS):
        row_by_state = {}
        for stato in ("ATTIVO", "NON_ATTIVO"):
            s = stats[trigger][stato]
            n = s["Estrazioni"]
            row = {
                "Trigger": f"{trigger:02d}",
                "Stato": stato,
                "Estrazioni": n,
                **{c: s[c] for c in CATEGORIES},
                "Pct3Plus": pct(plus_count(s, 3), n),
                "Pct4Plus": pct(plus_count(s, 4), n),
                "Pct5Plus": pct(plus_count(s, 5), n),
            }
            row_by_state[stato] = row
            detail_rows.append(row)

        a = row_by_state["ATTIVO"]
        n = row_by_state["NON_ATTIVO"]
        ratio4 = (a["Pct4Plus"] / n["Pct4Plus"]) if n["Pct4Plus"] else float("inf")
        summary.append({
            "Trigger": f"{trigger:02d}",
            "AttivoN": a["Estrazioni"],
            "NonAttivoN": n["Estrazioni"],
            "AttivoPct3Plus": a["Pct3Plus"],
            "NonAttivoPct3Plus": n["Pct3Plus"],
            "AttivoPct4Plus": a["Pct4Plus"],
            "NonAttivoPct4Plus": n["Pct4Plus"],
            "Delta4PlusPP": a["Pct4Plus"] - n["Pct4Plus"],
            "Rapporto4Plus": ratio4,
            "AttivoPct5Plus": a["Pct5Plus"],
            "NonAttivoPct5Plus": n["Pct5Plus"],
        })

    summary.sort(
        key=lambda r: (r["Rapporto4Plus"], r["Delta4PlusPP"], r["AttivoPct4Plus"]),
        reverse=True,
    )

    print("=" * 116)
    print("SENALOX - CONFRONTO POOL TRIGGER: ATTIVO vs NON ATTIVO (NEW MODE)")
    print("=" * 116)
    print(
        f"{'#':>2} {'TRG':>3} {'N ATT':>6} {'4+ ATT':>8} {'N OFF':>6} "
        f"{'4+ OFF':>8} {'DELTA':>8} {'RAPPORTO':>9} {'3+ A/O':>15} {'5+ A/O':>15}"
    )
    print("-" * 116)

    for pos, r in enumerate(summary, 1):
        ratio = "INF" if r["Rapporto4Plus"] == float("inf") else f"{r['Rapporto4Plus']:.2f}x"
        print(
            f"{pos:>2} {r['Trigger']:>3} {r['AttivoN']:>6} {r['AttivoPct4Plus']:>7.2f}% "
            f"{r['NonAttivoN']:>6} {r['NonAttivoPct4Plus']:>7.2f}% "
            f"{r['Delta4PlusPP']:>+7.2f} {ratio:>9} "
            f"{r['AttivoPct3Plus']:>6.2f}/{r['NonAttivoPct3Plus']:<6.2f} "
            f"{r['AttivoPct5Plus']:>6.2f}/{r['NonAttivoPct5Plus']:<6.2f}"
        )

    outdir = Path(__file__).resolve().parent / "output"
    outdir.mkdir(parents=True, exist_ok=True)

    detail_file = outdir / "trigger_active_vs_inactive.csv"
    detail_headers = [
        "Trigger", "Stato", "Estrazioni", "2", "3", "4", "5", "5+1", "6",
        "Pct3Plus", "Pct4Plus", "Pct5Plus",
    ]
    with detail_file.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=detail_headers, delimiter=";")
        w.writeheader()
        for row in detail_rows:
            out = dict(row)
            for k in ("Pct3Plus", "Pct4Plus", "Pct5Plus"):
                out[k] = f"{out[k]:.4f}"
            w.writerow(out)

    ranking_file = outdir / "trigger_active_vs_inactive_ranking.csv"
    ranking_headers = [
        "Posizione", "Trigger", "AttivoN", "NonAttivoN",
        "AttivoPct3Plus", "NonAttivoPct3Plus",
        "AttivoPct4Plus", "NonAttivoPct4Plus", "Delta4PlusPP", "Rapporto4Plus",
        "AttivoPct5Plus", "NonAttivoPct5Plus",
    ]
    with ranking_file.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=ranking_headers, delimiter=";")
        w.writeheader()
        for pos, row in enumerate(summary, 1):
            out = {"Posizione": pos, **row}
            for k in (
                "AttivoPct3Plus", "NonAttivoPct3Plus",
                "AttivoPct4Plus", "NonAttivoPct4Plus", "Delta4PlusPP",
                "AttivoPct5Plus", "NonAttivoPct5Plus",
            ):
                out[k] = f"{out[k]:.4f}"
            out["Rapporto4Plus"] = (
                "INF" if out["Rapporto4Plus"] == float("inf")
                else f"{out['Rapporto4Plus']:.4f}"
            )
            w.writerow(out)

    print()
    print(f"Dettaglio CSV : {detail_file}")
    print(f"Ranking CSV   : {ranking_file}")


if __name__ == "__main__":
    main()
