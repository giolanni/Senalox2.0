from collections import defaultdict
from typing import List
import random

from shared.models.estrazione import Estrazione
from src.core.strategies import *

class GeneratorePesato:
    """Genera sestine combinando tutte le strategie con pesi"""
    def __init__(self, analyzer: Analyzer):
        self.analyzer = analyzer
        self.strategie = {
            'Frequenze': (FrequenzaStrategy(analyzer), 0.30),
            'Ritardi': (RitardiStrategy(analyzer), 0.25),
            'Bilanciata': (BilanciataStrategy(analyzer), 0.20),
            'Termici': (TermiciStrategy(analyzer), 0.15),
            'Casuale': (self._casuale, 0.10)
        }
    
    def _casuale(self) -> List[int]:
        return sorted(random.sample(range(1, 91), 6))
    
    def genera_sestina_pesata(self) -> List[int]:
        pool = []
        for name, (strategy, weight) in self.strategie.items():
            nums = strategy.generate() if name != 'Casuale' else self._casuale()
            pool.extend(nums * int(weight * 100))
        
        while True:
            try:
                return sorted(random.sample(pool, 6))
            except ValueError:
                pool.extend(range(1, 91))  # Fallback se pool troppo piccolo
    
class Generatore:
    def __init__(self, analyzer: Analyzer):
        self.analyzer = analyzer
        self.strategies = {
            "Bilanciata": BalancedCombinationStrategy(analyzer),
            "Wheeling": NumberWheelingStrategy(analyzer),
            "Frequenze": FrequencyBasedStrategy(analyzer),
            "Ritardi": DelayBasedStrategy(analyzer),
            "Low/High": LowHighStrategy(analyzer),
            "Ottimizzata": OptimizedWheelingStrategy(analyzer)
        }

    def genera_sestina(self, strategy_name: str) -> List[int]:
        if strategy_name not in self.strategies:
            raise ValueError(f"Strategia {strategy_name} non valida")
        return self.strategies[strategy_name].generate()
