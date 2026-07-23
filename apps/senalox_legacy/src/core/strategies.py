from typing import List, Callable
from datetime import datetime
from collections import Counter
from shared.models.estrazione import Estrazione

STRATEGIES_MAP = {}

def register_strategy(name: str) -> Callable:
    """Decorator per registrare nuove strategie"""
    def decorator(func: Callable) -> Callable:
        STRATEGIES_MAP[name] = func
        return func
    return decorator

@register_strategy('frequenza')
def strategia_frequenza(estrazioni: List[Estrazione], top_n: int = 30) -> List[int]:
    """Numeri più frequenti storicamente"""
    counter = Counter(num for e in estrazioni for num in e.numeri)
    return [num for num, _ in counter.most_common(top_n)]

@register_strategy('ritardo')
def strategia_ritardo(estrazioni: List[Estrazione], soglia: int = 50) -> List[int]:
    """Numeri con maggior ritardo dall'ultima estrazione"""
    ultima_data = max(e.data for e in estrazioni)
    ritardi = {}
    
    for num in range(1, 91):
        ultima_estrazione = next(
            (e for e in reversed(estrazioni) if num in e.numeri),
            None
        )
        ritardi[num] = (ultima_data - ultima_estrazione.data).days if ultima_estrazione else 0
    
    return [num for num, _ in sorted(ritardi.items(), key=lambda x: x[1], reverse=True)[:soglia]]

@register_strategy('stagionale')
def strategia_stagionale(estrazioni: List[Estrazione], stagione: str = None) -> List[int]:
    """Numeri per stagione specifica o corrente"""
    stagioni = {
        'inverno': [12, 1, 2],
        'primavera': [3, 4, 5],
        'estate': [6, 7, 8],
        'autunno': [9, 10, 11]
    }
    
    target_stagione = stagione or _get_current_season()
    mesi_target = stagioni[target_stagione]
    
    return list({
        num for e in estrazioni
        if e.data.month in mesi_target
        for num in e.numeri
    })

@register_strategy('data')
def strategia_data(estrazioni: List[Estrazione], giorni_diff: int = 7) -> List[int]:
    """Numeri usciti in date simili (±giorni_diff)"""
    oggi = datetime.now().date()
    return [
        num for e in estrazioni
        if abs((e.data - oggi).days) <= giorni_diff
        for num in e.numeri
    ]

def _get_current_season() -> str:
    today = datetime.now().month
    return next(
        (season for season, months in [
            ('inverno', [12, 1, 2]),
            ('primavera', [3, 4, 5]),
            ('estate', [6, 7, 8]),
            ('autunno', [9, 10, 11])
        ] if today in months),
        'inverno'
    )
