"""
Mostra i sistemi Trigger NEW MODE giocabili dalla prossima estrazione.

Logica globale:
- un trigger compare una sola volta tra gli attivi;
- se ricompare mentre e' gia' attivo viene indicato come RIATTIVATO;
- la riattivazione fa ripartire la finestra delle 9 estrazioni;
- vengono mostrate prima attivazione, ultima attivazione e numero totale
  di attivazioni del ciclo corrente.
"""

from shared.data_loader import load_estrazioni_new_mode
from analysis.laboratory.trigger_patterns.operational.trigger_systems import (
    TRIGGER_SYSTEMS,
    WINDOW_SIZE,
)
from analysis.laboratory.trigger_patterns.operational.trigger_state import (
    build_global_timeline,
)


def fmt(nums):
    return " ".join(f"{n:02d}" for n in sorted(nums))


def main():
    estrazioni = sorted(load_estrazioni_new_mode(), key=lambda e: e.data)
    if not estrazioni:
        print("Nessuna estrazione disponibile.")
        return

    _, _, final_states = build_global_timeline(estrazioni)
    last_index = len(estrazioni) - 1
    last_date = estrazioni[-1].data

    # final_states include anche un trigger che ha appena consumato la nona
    # e ultima estrazione utile: serve a check_draws per valutare quella
    # estrazione, ma non e piu giocabile dalla successiva.
    playable_states = {
        trigger: state
        for trigger, state in final_states.items()
        if last_index < state["active_until_idx"]
    }

    print("=" * 86)
    print("SENALOX - TRIGGER ATTIVI GLOBALI (NEW MODE)")
    print(f"Ultima estrazione: {last_date:%d/%m/%Y}")
    print("=" * 86)

    if not playable_states:
        print("Nessun trigger attivo per la prossima estrazione.")
        return

    for trigger in sorted(playable_states):
        state = playable_states[trigger]
        cfg = TRIGGER_SYSTEMS[trigger]

        first_date = estrazioni[state["cycle_start_idx"]].data
        last_activation_date = estrazioni[state["last_activation_idx"]].data
        elapsed = last_index - state["last_activation_idx"]
        remaining = max(0, WINDOW_SIZE - elapsed)

        print()
        if state["reactivations_in_cycle"]:
            status = (
                f"ATTIVO - RIATTIVATO {state['reactivations_in_cycle']} volta/e "
                f"({state['activations_in_cycle']} attivazioni totali)"
            )
        else:
            status = "ATTIVO - 1 attivazione"

        print(f"SISTEMA {trigger:02d} - {status}")
        print(f"Prima attivazione : {first_date:%d/%m/%Y}")
        print(f"Ultima attivazione: {last_activation_date:%d/%m/%Y}")
        print(
            f"Dall'ultima attivazione: {elapsed}/{WINDOW_SIZE} estrazioni trascorse "
            f"| Restano: {remaining}"
        )
        print(f"Numeri stabili: {fmt(cfg['stable'])}")
        print(f"Pool 13 numeri: {fmt(cfg['pool'])}")


if __name__ == "__main__":
    main()
