"""
Mostra quali sistemi Trigger NEW MODE sono attivi sull'ultima estrazione disponibile.

Regola:
- il sistema si attiva quando il trigger compare tra i 6 numeri estratti;
- resta attivo per le 9 estrazioni successive;
- se lo stesso trigger ricompare, nasce una nuova attivazione indipendente.
"""
from shared.data_loader import load_estrazioni_new_mode
from analysis.laboratory.trigger_patterns.operational.trigger_systems import TRIGGER_SYSTEMS, WINDOW_SIZE

def fmt(nums):
    return " ".join(f"{n:02d}" for n in sorted(nums))

def main():
    estrazioni = sorted(load_estrazioni_new_mode(), key=lambda e: e.data)
    last_index = len(estrazioni) - 1
    last_date = estrazioni[-1].data
    active = []

    for idx, estrazione in enumerate(estrazioni):
        for trigger in sorted(set(estrazione.numeri) & set(TRIGGER_SYSTEMS)):
            elapsed = last_index - idx
            if 0 <= elapsed < WINDOW_SIZE:
                cfg = TRIGGER_SYSTEMS[trigger]
                active.append((estrazione.data, trigger, elapsed, WINDOW_SIZE - elapsed, cfg))

    print("=" * 78)
    print("SENALOX - TRIGGER ATTIVI (NEW MODE)")
    print(f"Ultima estrazione: {last_date:%d/%m/%Y}")
    print("=" * 78)

    if not active:
        print("Nessun trigger attivo.")
        return

    for date, trigger, elapsed, remaining, cfg in sorted(active, reverse=True):
        print()
        print(f"SISTEMA {trigger:02d} - attivato il {date:%d/%m/%Y}")
        print(f"Trascorse: {elapsed} estrazioni | Restano: {remaining}")
        print(f"Numeri stabili: {fmt(cfg['stable'])}")
        print(f"Pool 13 numeri: {fmt(cfg['pool'])}")

if __name__ == "__main__":
    main()
