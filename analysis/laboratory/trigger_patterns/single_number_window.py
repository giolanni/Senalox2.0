"""
Laboratorio: trigger singolo -> finestra successiva (versione 2)
================================================================

Per ogni numero-trigger da 1 a 90:

1. usa il periodo di SCOPERTA per individuare un gruppo di numeri candidati;
2. congela il gruppo e lo valuta su SCOPERTA, VALIDAZIONE e TEST;
3. confronta il gruppo con gruppi casuali della stessa dimensione;
4. spiega perche' ogni numero e' entrato nel gruppo, mostrando:
   - frequenza generale;
   - frequenza nelle estrazioni successive al trigger;
   - incremento rispetto alla frequenza generale;
   - quota di finestre in cui compare almeno una volta;
5. mostra in quale posizione della finestra (+1, +2, ..., +N) ogni numero
   tende a comparire;
6. misura la stabilita' dei singoli numeri tra SCOPERTA, VALIDAZIONE e TEST.

Lo script e' completamente separato dalle interfacce Senalox e non modifica
alcun algoritmo operativo.
"""
from __future__ import annotations

import argparse
import math
import random
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any

from analysis.common.datasets import load_dataset
from analysis.common.io_utils import write_csv, write_text

OUTPUT_DIR = Path(__file__).resolve().parent / "output"


@dataclass(frozen=True)
class Split:
    name: str
    draws: list


def chronological_splits(
    draws: list,
    discovery_ratio: float = 0.60,
    validation_ratio: float = 0.20,
) -> tuple[Split, Split, Split]:
    """Divide cronologicamente lo storico in scoperta, validazione e test."""
    n = len(draws)
    discovery_end = max(1, int(n * discovery_ratio))
    validation_end = max(
        discovery_end + 1,
        int(n * (discovery_ratio + validation_ratio)),
    )
    return (
        Split("DISCOVERY", draws[:discovery_end]),
        Split("VALIDATION", draws[discovery_end:validation_end]),
        Split("TEST", draws[validation_end:]),
    )


def trigger_windows(draws: list, trigger: int, window_size: int) -> list[list]:
    """Restituisce le finestre complete successive alle uscite del trigger."""
    windows: list[list] = []
    last_valid_index = len(draws) - window_size - 1

    for index, draw in enumerate(draws):
        if index > last_valid_index:
            break
        if trigger in draw.numeri:
            windows.append(draws[index + 1:index + 1 + window_size])

    return windows


def general_number_rates(draws: list) -> dict[int, float]:
    """Frequenza di presenza di ogni numero nelle estrazioni del periodo."""
    if not draws:
        return {number: 0.0 for number in range(1, 91)}

    counts: Counter[int] = Counter()
    for draw in draws:
        counts.update(set(draw.numeri))

    return {
        number: counts[number] / len(draws)
        for number in range(1, 91)
    }


def number_post_trigger_stats(
    draws: list,
    trigger: int,
    numbers: list[int],
    window_size: int,
) -> dict[int, dict[str, float | int]]:
    """
    Calcola le statistiche post-trigger per i numeri indicati.

    PostRate misura la presenza su tutte le singole estrazioni comprese nelle
    finestre. WindowPresenceRate misura invece in quante finestre il numero
    compare almeno una volta.
    """
    windows = trigger_windows(draws, trigger, window_size)
    rates = general_number_rates(draws)
    post_draw_total = len(windows) * window_size

    post_counts: Counter[int] = Counter()
    window_counts: Counter[int] = Counter()

    for window in windows:
        numbers_seen_in_window: set[int] = set()
        for draw in window:
            draw_numbers = set(draw.numeri)
            post_counts.update(draw_numbers)
            numbers_seen_in_window.update(draw_numbers)
        window_counts.update(numbers_seen_in_window)

    result: dict[int, dict[str, float | int]] = {}

    for number in numbers:
        general_rate = rates[number]
        post_rate = post_counts[number] / post_draw_total if post_draw_total else 0.0
        window_rate = window_counts[number] / len(windows) if windows else 0.0
        lift = post_rate - general_rate
        ratio = post_rate / general_rate if general_rate else 0.0

        result[number] = {
            "Occurrences": len(windows),
            "PostDrawTotal": post_draw_total,
            "GeneralAppearances": round(general_rate * len(draws)),
            "GeneralRatePct": round(general_rate * 100, 6),
            "PostAppearances": post_counts[number],
            "PostRatePct": round(post_rate * 100, 6),
            "LiftPctPoints": round(lift * 100, 6),
            "RateRatio": round(ratio, 6),
            "WindowsContainingNumber": window_counts[number],
            "WindowPresenceRatePct": round(window_rate * 100, 6),
        }

    return result


def learn_pool(
    draws: list,
    trigger: int,
    window_size: int,
    pool_size: int,
) -> tuple[list[int], int, list[dict[str, Any]]]:
    """
    Impara il gruppo candidato sul solo periodo di scoperta.

    L'ordinamento usa prima l'incremento rispetto alla frequenza generale,
    poi la frequenza post-trigger e infine il numero di presenze osservate.
    """
    windows = trigger_windows(draws, trigger, window_size)
    if not windows:
        return [], 0, []

    all_numbers = [number for number in range(1, 91) if number != trigger]
    stats = number_post_trigger_stats(
        draws=draws,
        trigger=trigger,
        numbers=all_numbers,
        window_size=window_size,
    )

    ranked = sorted(
        all_numbers,
        key=lambda number: (
            float(stats[number]["LiftPctPoints"]),
            float(stats[number]["PostRatePct"]),
            int(stats[number]["PostAppearances"]),
            -number,
        ),
        reverse=True,
    )

    selected = ranked[:pool_size]
    pool = sorted(selected)

    ranking_rows: list[dict[str, Any]] = []
    for rank, number in enumerate(selected, start=1):
        ranking_rows.append({
            "Rank": rank,
            "Number": number,
            **stats[number],
        })

    return pool, len(windows), ranking_rows


def evaluate_pool(
    draws: list,
    trigger: int,
    pool: list[int],
    window_size: int,
) -> dict[str, float | int]:
    """Valuta il massimo numero di elementi del pool centrati in ogni finestra."""
    windows = trigger_windows(draws, trigger, window_size)
    pool_set = set(pool)
    best_hits: list[int] = []

    for window in windows:
        best = max(
            (len(pool_set.intersection(draw.numeri)) for draw in window),
            default=0,
        )
        best_hits.append(best)

    result: dict[str, float | int] = {
        "Occurrences": len(windows),
        "AverageBestHit": round(mean(best_hits), 6) if best_hits else 0,
    }

    for threshold in range(2, 7):
        successes = sum(1 for hit in best_hits if hit >= threshold)
        result[f"WindowsAtLeast{threshold}"] = successes
        result[f"RateAtLeast{threshold}"] = (
            round(successes / len(best_hits) * 100, 6)
            if best_hits
            else 0
        )

    return result


def random_baseline(
    draws: list,
    trigger: int,
    window_size: int,
    pool_size: int,
    simulations: int,
    seed: int,
) -> dict[str, float]:
    """Calcola la baseline media di gruppi casuali della stessa dimensione."""
    rng = random.Random(seed + trigger)
    candidates = [number for number in range(1, 91) if number != trigger]
    metrics = {f"RateAtLeast{threshold}": [] for threshold in range(2, 7)}
    metrics["AverageBestHit"] = []

    for _ in range(simulations):
        pool = rng.sample(candidates, pool_size)
        result = evaluate_pool(draws, trigger, pool, window_size)
        for key in metrics:
            metrics[key].append(float(result[key]))

    return {
        f"Random{key}": round(mean(values), 6) if values else 0
        for key, values in metrics.items()
    }


def position_profile(
    draws: list,
    trigger: int,
    pool: list[int],
    window_size: int,
) -> list[dict[str, Any]]:
    """Mostra la frequenza di ciascun numero a ogni offset della finestra."""
    windows = trigger_windows(draws, trigger, window_size)
    general_rates = general_number_rates(draws)
    rows: list[dict[str, Any]] = []

    for number in pool:
        for offset in range(window_size):
            appearances = sum(
                1
                for window in windows
                if number in window[offset].numeri
            )
            rate = appearances / len(windows) if windows else 0.0
            baseline = general_rates[number]

            rows.append({
                "Trigger": trigger,
                "CandidateNumber": number,
                "Offset": offset + 1,
                "Occurrences": len(windows),
                "Appearances": appearances,
                "RatePct": round(rate * 100, 6),
                "GeneralRatePct": round(baseline * 100, 6),
                "LiftPctPoints": round((rate - baseline) * 100, 6),
            })

    return rows


def hypergeometric_single_draw_probability(pool_size: int, at_least: int) -> float:
    """Probabilita' teorica di almeno N numeri del pool in una sestina."""
    denominator = math.comb(90, 6)
    probability = 0.0

    for hits in range(at_least, min(pool_size, 6) + 1):
        probability += (
            math.comb(pool_size, hits)
            * math.comb(90 - pool_size, 6 - hits)
            / denominator
        )

    return probability


def run(
    dataset_name: str,
    window_size: int,
    pool_size: int,
    simulations: int,
    seed: int,
) -> None:
    draws = load_dataset(dataset_name)
    discovery, validation, test = chronological_splits(draws)

    result_rows: list[dict[str, Any]] = []
    member_rows: list[dict[str, Any]] = []
    position_rows: list[dict[str, Any]] = []
    stability_rows: list[dict[str, Any]] = []

    for trigger in range(1, 91):
        pool, discovery_occurrences, discovery_ranking = learn_pool(
            discovery.draws,
            trigger,
            window_size,
            pool_size,
        )

        if len(pool) != pool_size:
            continue

        pool_text = ",".join(f"{number:02d}" for number in pool)
        rank_by_number = {
            int(row["Number"]): int(row["Rank"])
            for row in discovery_ranking
        }

        split_member_stats: dict[str, dict[int, dict[str, float | int]]] = {}

        for split in (discovery, validation, test):
            evaluation = evaluate_pool(
                split.draws,
                trigger,
                pool,
                window_size,
            )
            baseline = random_baseline(
                split.draws,
                trigger,
                window_size,
                pool_size,
                simulations,
                seed,
            )

            row: dict[str, Any] = {
                "Dataset": dataset_name,
                "Trigger": trigger,
                "WindowSize": window_size,
                "PoolSize": pool_size,
                "CandidatePool": pool_text,
                "Split": split.name,
                "SplitStartDate": split.draws[0].data.isoformat() if split.draws else "",
                "SplitEndDate": split.draws[-1].data.isoformat() if split.draws else "",
                "DiscoveryOccurrences": discovery_occurrences,
                **evaluation,
                **baseline,
            }

            for threshold in range(2, 7):
                row[f"LiftAtLeast{threshold}PctPoints"] = round(
                    float(row[f"RateAtLeast{threshold}"])
                    - float(row[f"RandomRateAtLeast{threshold}"]),
                    6,
                )

            result_rows.append(row)

            member_stats = number_post_trigger_stats(
                draws=split.draws,
                trigger=trigger,
                numbers=pool,
                window_size=window_size,
            )
            split_member_stats[split.name] = member_stats

            for number in pool:
                member_rows.append({
                    "Dataset": dataset_name,
                    "Trigger": trigger,
                    "CandidatePool": pool_text,
                    "CandidateNumber": number,
                    "DiscoveryRank": rank_by_number[number],
                    "Split": split.name,
                    **member_stats[number],
                })

            for profile_row in position_profile(
                draws=split.draws,
                trigger=trigger,
                pool=pool,
                window_size=window_size,
            ):
                position_rows.append({
                    "Dataset": dataset_name,
                    "CandidatePool": pool_text,
                    "DiscoveryRank": rank_by_number[int(profile_row["CandidateNumber"])],
                    "Split": split.name,
                    **profile_row,
                })

        positive_validation = 0
        positive_test = 0
        positive_both = 0
        stable_numbers: list[int] = []

        for number in pool:
            validation_lift = float(
                split_member_stats["VALIDATION"][number]["LiftPctPoints"]
            )
            test_lift = float(
                split_member_stats["TEST"][number]["LiftPctPoints"]
            )

            if validation_lift > 0:
                positive_validation += 1
            if test_lift > 0:
                positive_test += 1
            if validation_lift > 0 and test_lift > 0:
                positive_both += 1
                stable_numbers.append(number)

        stability_rows.append({
            "Dataset": dataset_name,
            "Trigger": trigger,
            "WindowSize": window_size,
            "PoolSize": pool_size,
            "CandidatePool": pool_text,
            "DiscoveryOccurrences": discovery_occurrences,
            "PositiveLiftMembersValidation": positive_validation,
            "PositiveLiftMembersTest": positive_test,
            "PositiveLiftMembersBoth": positive_both,
            "StableMembers": ",".join(f"{number:02d}" for number in stable_numbers),
            "StableMemberRatePct": round(positive_both / pool_size * 100, 6),
        })

    slug = dataset_name.lower()

    result_fieldnames = [
        "Dataset", "Trigger", "WindowSize", "PoolSize", "CandidatePool", "Split",
        "SplitStartDate", "SplitEndDate", "DiscoveryOccurrences", "Occurrences",
        "AverageBestHit", "WindowsAtLeast2", "RateAtLeast2", "WindowsAtLeast3",
        "RateAtLeast3", "WindowsAtLeast4", "RateAtLeast4", "WindowsAtLeast5",
        "RateAtLeast5", "WindowsAtLeast6", "RateAtLeast6", "RandomAverageBestHit",
        "RandomRateAtLeast2", "RandomRateAtLeast3", "RandomRateAtLeast4",
        "RandomRateAtLeast5", "RandomRateAtLeast6", "LiftAtLeast2PctPoints",
        "LiftAtLeast3PctPoints", "LiftAtLeast4PctPoints", "LiftAtLeast5PctPoints",
        "LiftAtLeast6PctPoints",
    ]
    result_file = OUTPUT_DIR / f"single_trigger_w{window_size}_p{pool_size}_{slug}.csv"
    write_csv(result_file, result_fieldnames, result_rows)

    member_fieldnames = [
        "Dataset", "Trigger", "CandidatePool", "CandidateNumber", "DiscoveryRank",
        "Split", "Occurrences", "PostDrawTotal", "GeneralAppearances",
        "GeneralRatePct", "PostAppearances", "PostRatePct", "LiftPctPoints",
        "RateRatio", "WindowsContainingNumber", "WindowPresenceRatePct",
    ]
    member_file = OUTPUT_DIR / f"single_trigger_members_w{window_size}_p{pool_size}_{slug}.csv"
    write_csv(member_file, member_fieldnames, member_rows)

    position_fieldnames = [
        "Dataset", "Trigger", "CandidatePool", "CandidateNumber", "DiscoveryRank",
        "Split", "Offset", "Occurrences", "Appearances", "RatePct",
        "GeneralRatePct", "LiftPctPoints",
    ]
    position_file = OUTPUT_DIR / f"single_trigger_positions_w{window_size}_p{pool_size}_{slug}.csv"
    write_csv(position_file, position_fieldnames, position_rows)

    stability_fieldnames = [
        "Dataset", "Trigger", "WindowSize", "PoolSize", "CandidatePool",
        "DiscoveryOccurrences", "PositiveLiftMembersValidation",
        "PositiveLiftMembersTest", "PositiveLiftMembersBoth", "StableMembers",
        "StableMemberRatePct",
    ]
    stability_file = OUTPUT_DIR / f"single_trigger_stability_w{window_size}_p{pool_size}_{slug}.csv"
    write_csv(stability_file, stability_fieldnames, stability_rows)

    test_rows = [
        row
        for row in result_rows
        if row["Split"] == "TEST" and int(row["Occurrences"]) >= 10
    ]
    top = sorted(
        test_rows,
        key=lambda row: (
            float(row["LiftAtLeast4PctPoints"]),
            int(row["Occurrences"]),
        ),
        reverse=True,
    )[:15]

    stability_by_trigger = {
        int(row["Trigger"]): row
        for row in stability_rows
    }

    theoretical_single = hypergeometric_single_draw_probability(pool_size, 4) * 100
    theoretical_window_independent = (
        1 - (1 - theoretical_single / 100) ** window_size
    ) * 100

    report_lines = [
        f"LABORATORIO TRIGGER SINGOLO — {dataset_name}",
        f"Estrazioni: {len(draws)}",
        f"Finestra successiva: {window_size}",
        f"Dimensione gruppo: {pool_size}",
        f"Simulazioni casuali per trigger/split: {simulations}",
        "",
        f"Baseline teorica indicativa P(>=4 in una singola estrazione): {theoretical_single:.4f}%",
        f"Baseline teorica indicativa in {window_size} estrazioni (ipotesi indipendenza): {theoretical_window_independent:.4f}%",
        "",
        "Migliori candidati sul TEST (ordinati per lift >=4 rispetto ai pool casuali):",
    ]

    for row in top:
        trigger = int(row["Trigger"])
        stability = stability_by_trigger[trigger]
        report_lines.append(
            f"Trigger {trigger:02d} | pool {row['CandidatePool']} | "
            f"occorrenze {row['Occurrences']} | >=4 {float(row['RateAtLeast4']):.2f}% | "
            f"baseline {float(row['RandomRateAtLeast4']):.2f}% | "
            f"lift {float(row['LiftAtLeast4PctPoints']):+.2f} pp | "
            f"membri stabili {stability['PositiveLiftMembersBoth']}/{pool_size}: "
            f"{stability['StableMembers'] or '-'}"
        )

    report_lines.extend([
        "",
        "FILE AGGIUNTIVI:",
        f"- {member_file.name}: spiega perche' ogni numero e' stato selezionato e come si comporta nei tre split.",
        f"- {position_file.name}: mostra la posizione +1, +2, ..., +{window_size} in cui ogni numero compare.",
        f"- {stability_file.name}: riassume quanti membri del pool mantengono lift positivo in validazione e test.",
        "",
        "AVVERTENZA: un risultato positivo sul TEST e' soltanto un candidato. Deve essere stabile",
        "su piu' finestre, periodi e dataset prima di essere promosso a regola validata.",
    ])

    report_file = OUTPUT_DIR / f"single_trigger_report_{slug}.txt"
    write_text(report_file, "\n".join(report_lines) + "\n")

    print(f"Laboratorio trigger completato: {result_file}")
    print(f"Dettaglio numeri: {member_file}")
    print(f"Profilo posizioni: {position_file}")
    print(f"Stabilita': {stability_file}")
    print(f"Report: {report_file}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ricerca e spiega gruppi post-trigger su Senalox."
    )
    parser.add_argument(
        "--dataset",
        choices=["OVERALL", "NEW_MODE", "BOTH"],
        default="BOTH",
    )
    parser.add_argument("--window", type=int, default=9)
    parser.add_argument("--pool-size", type=int, default=13)
    parser.add_argument("--simulations", type=int, default=50)
    parser.add_argument("--seed", type=int, default=20260805)
    args = parser.parse_args()

    if args.window < 1:
        raise ValueError("--window deve essere almeno 1")
    if not 1 <= args.pool_size <= 89:
        raise ValueError("--pool-size deve essere compreso tra 1 e 89")
    if args.simulations < 1:
        raise ValueError("--simulations deve essere almeno 1")

    datasets = (
        ("OVERALL", "NEW_MODE")
        if args.dataset == "BOTH"
        else (args.dataset,)
    )

    for dataset in datasets:
        run(
            dataset_name=dataset,
            window_size=args.window,
            pool_size=args.pool_size,
            simulations=args.simulations,
            seed=args.seed,
        )


if __name__ == "__main__":
    main()
