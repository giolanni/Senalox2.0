import random
from typing import List, Dict
from shared.models.estrazione import Estrazione
from .strategies import STRATEGIES_MAP

def genera_sestina_pesata(
    estrazioni: List[Estrazione],
    strategy_config: Dict[str, float] = None,
    params: Dict[str, dict] = None
) -> List[int]:
    """
    Versione migliorata che supporta diverse strategie
    
    Args:
        strategy_config: Dizionario {nome_strategia: peso}
        params: Parametri specifici per strategia
    """
    strategy_config = strategy_config or {
        'frequenza': 0.3,
        'ritardo': 0.2,
        'stagionale': 0.2,
        'data': 0.3
    }
    
    params = params or {}
    pool = []
    
    for strategy_name, weight in strategy_config.items():
        strategy = STRATEGIES_MAP.get(strategy_name)
        if strategy and weight > 0:
            try:
                candidates = strategy(estrazioni, **params.get(strategy_name, {}))
                pool += candidates * int(weight * 10)
            except Exception as e:
                print(f"Errore nella strategia {strategy_name}: {str(e)}")
    
    return _select_unique_numbers(pool)

def _select_unique_numbers(pool: List[int]) -> List[int]:
    """Seleziona 6 numeri unici dal pool"""
    unique = list(set(pool))
    return sorted(random.sample(unique, 6)) if len(unique) >= 6 else []


def genera_pool_pesato(estrazioni):
    frequenze = {}
    for estrazione in estrazioni:
        for numero in estrazione.numeri:
            frequenze[numero] = frequenze.get(numero, 0) + 1
    
    totale_estrazioni = len(estrazioni)
    pool_pesato = [(num, freq / totale_estrazioni) for num, freq in frequenze.items()]
    return sorted(pool_pesato, key=lambda x: x[1], reverse=True)

def genera_sestina_pesata(estrazioni):
    pool = genera_pool_pesato(estrazioni)
    numeri, pesi = zip(*pool)
    return sorted(random.choices(numeri, weights=pesi, k=6))
