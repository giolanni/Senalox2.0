"""
Gestione globale dello stato dei trigger Senalox.

Regola ufficiale:
- un trigger apre un solo ciclo globale;
- resta attivo per le 9 estrazioni successive;
- se ricompare mentre e' gia' attivo, NON nasce un secondo trigger:
  viene registrata una riattivazione e la finestra riparte da 9;
- una stessa estrazione viene quindi valutata al massimo una volta
  per ciascun trigger.
"""

from analysis.laboratory.trigger_patterns.operational.trigger_systems import (
    TRIGGER_SYSTEMS,
    WINDOW_SIZE,
)


def triggers_in_draw(draw):
    return sorted(set(draw.numeri) & set(TRIGGER_SYSTEMS))


def build_global_timeline(estrazioni):
    """
    Restituisce:
      snapshots[i] = trigger attivi PRIMA di elaborare l'estrazione i.
                     Serve per valutare quella estrazione senza duplicazioni.
      events[i]    = attivazioni/riattivazioni avvenute nell'estrazione i.
      final_states = stato globale DOPO l'ultima estrazione.

    Lo stato di un trigger contiene gli indici del ciclo e il numero di
    attivazioni/riattivazioni del ciclo corrente.
    """
    states = {}
    snapshots = []
    events = []

    for idx, draw in enumerate(estrazioni):
        # Scadono i trigger la cui nona estrazione successiva e' gia' passata.
        for trigger in list(states):
            if idx > states[trigger]["active_until_idx"]:
                del states[trigger]

        # Stato valido per valutare l'estrazione corrente.
        active_before = {
            trigger: dict(state)
            for trigger, state in states.items()
            if idx <= state["active_until_idx"]
        }
        snapshots.append(active_before)

        draw_events = []
        for trigger in triggers_in_draw(draw):
            if trigger in states and idx <= states[trigger]["active_until_idx"]:
                state = states[trigger]
                state["last_activation_idx"] = idx
                state["active_until_idx"] = idx + WINDOW_SIZE
                state["activations_in_cycle"] += 1
                state["reactivations_in_cycle"] += 1
                event_type = "RIATTIVAZIONE"
            else:
                state = {
                    "cycle_start_idx": idx,
                    "last_activation_idx": idx,
                    "active_until_idx": idx + WINDOW_SIZE,
                    "activations_in_cycle": 1,
                    "reactivations_in_cycle": 0,
                }
                states[trigger] = state
                event_type = "ATTIVAZIONE"

            draw_events.append(
                {
                    "trigger": trigger,
                    "type": event_type,
                    **dict(state),
                }
            )

        events.append(draw_events)

    return snapshots, events, {t: dict(s) for t, s in states.items()}
