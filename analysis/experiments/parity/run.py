"""
Esperimento Parità
==================

Produce, separatamente per OVERALL e NEW_MODE:
- distribuzione del numero di pari per estrazione;
- matrice di transizione tra configurazioni consecutive;
- distribuzione per blocchi temporali;
- report sintetico.

Non modifica alcun algoritmo operativo e non interagisce con le GUI.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path

from analysis.common.datasets import load_dataset
from analysis.common.io_utils import write_csv, write_text

OUTPUT_DIR = Path(__file__).resolve().parent / "output"


def even_count(numbers: list[int]) -> int:
    return sum(1 for number in numbers if number % 2 == 0)


def analyze_dataset(dataset_name: str) -> None:
    draws = load_dataset(dataset_name)  # ordinamento cronologico garantito dal loader
    counts = [even_count(draw.numeri) for draw in draws]
    total = len(counts)

    distribution = Counter(counts)
    distribution_rows = []
    for even in range(7):
        occurrences = distribution.get(even, 0)
        distribution_rows.append({
            "Dataset": dataset_name,
            "EvenCount": even,
            "OddCount": 6 - even,
            "Occurrences": occurrences,
            "Percentage": round(occurrences / total * 100, 4) if total else 0,
        })

    transition_counts: dict[int, Counter[int]] = defaultdict(Counter)
    for previous, following in zip(counts, counts[1:]):
        transition_counts[previous][following] += 1

    transition_rows = []
    for previous in range(7):
        row_total = sum(transition_counts[previous].values())
        for following in range(7):
            occurrences = transition_counts[previous].get(following, 0)
            transition_rows.append({
                "Dataset": dataset_name,
                "PreviousEvenCount": previous,
                "NextEvenCount": following,
                "Occurrences": occurrences,
                "ConditionalPercentage": round(occurrences / row_total * 100, 4) if row_total else 0,
            })

    # Blocchi temporali di 500 estrazioni per verificare la stabilità.
    block_rows = []
    block_size = 500
    for start in range(0, total, block_size):
        block = draws[start:start + block_size]
        block_counts = Counter(even_count(draw.numeri) for draw in block)
        for even in range(7):
            occurrences = block_counts.get(even, 0)
            block_rows.append({
                "Dataset": dataset_name,
                "BlockStartIndex": start + 1,
                "BlockEndIndex": start + len(block),
                "StartDate": block[0].data.isoformat(),
                "EndDate": block[-1].data.isoformat(),
                "EvenCount": even,
                "Occurrences": occurrences,
                "Percentage": round(occurrences / len(block) * 100, 4),
            })

    slug = dataset_name.lower()
    write_csv(
        OUTPUT_DIR / f"parity_distribution_{slug}.csv",
        ["Dataset", "EvenCount", "OddCount", "Occurrences", "Percentage"],
        distribution_rows,
    )
    write_csv(
        OUTPUT_DIR / f"parity_transitions_{slug}.csv",
        ["Dataset", "PreviousEvenCount", "NextEvenCount", "Occurrences", "ConditionalPercentage"],
        transition_rows,
    )
    write_csv(
        OUTPUT_DIR / f"parity_stability_{slug}.csv",
        ["Dataset", "BlockStartIndex", "BlockEndIndex", "StartDate", "EndDate", "EvenCount", "Occurrences", "Percentage"],
        block_rows,
    )

    most_common_even, most_common_occurrences = distribution.most_common(1)[0]
    report = (
        f"ESPERIMENTO PARITÀ — {dataset_name}\n"
        f"Estrazioni analizzate: {total}\n"
        f"Periodo: {draws[0].data.isoformat()} / {draws[-1].data.isoformat()}\n"
        f"Configurazione più frequente: {most_common_even} pari + {6 - most_common_even} dispari "
        f"({most_common_occurrences / total * 100:.2f}%)\n\n"
        "Nota metodologica: la frequenza descrittiva non dimostra capacità predittiva. "
        "Le transizioni e la stabilità temporale servono a decidere se costruire un backtest dedicato.\n"
    )
    write_text(OUTPUT_DIR / f"parity_report_{slug}.txt", report)


def main() -> None:
    for dataset in ("OVERALL", "NEW_MODE"):
        analyze_dataset(dataset)
    print(f"Esperimento Parità completato. Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
