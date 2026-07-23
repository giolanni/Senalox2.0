from __future__ import annotations
from typing import List
import random
import itertools
from collections import Counter, defaultdict
from datetime import timedelta


from src.core.analyzer import Analyzer

class BaseStrategy:
    def __init__(self, analyzer: Analyzer):
        self.analyzer = analyzer
    
    def generate(self) -> List[int]:
        raise NotImplementedError

class BalancedCombinationStrategy(BaseStrategy):
    """Strategia 1: Combinazioni bilanciate (alto/basso, pari/dispari)"""
    def generate(self) -> List[int]:
        # Filtra numeri con buon bilanciamento
        balanced_pool = []
        for n in range(1, 91):
            is_even = n % 2 == 0
            is_low = n <= 45
            if (is_even and is_low) or (not is_even and not is_low):
                balanced_pool.append(n)
        return sorted(random.sample(balanced_pool, 6))

class NumberWheelingStrategy(BaseStrategy):
    """Strategia 3: Number Wheeling con core dinamico"""
    def __init__(self, analyzer: Analyzer, core_size=8):
        super().__init__(analyzer)
        self.core_size = core_size
    
    def generate(self) -> List[int]:
        # Seleziona core numbers dalle frequenze
        core = [n for n, _ in self.analyzer.frequenze.most_common(self.core_size)]
        # Genera tutte le combinazioni 6/8
        combinations = list(itertools.combinations(core, 6))
        return sorted(random.choice(combinations))

class FrequencyBasedStrategy(BaseStrategy):
    """Strategia 2: Numeri più frequenti (ricerca 1)"""
    def generate(self) -> List[int]:
        freq_nums = [n for n, _ in self.analyzer.frequenze.most_common(15)]
        return sorted(random.sample(freq_nums, 6))

class DelayBasedStrategy(BaseStrategy):
    """Strategia ricerca 2: Numeri con maggior ritardo"""
    def generate(self) -> List[int]:
        delayed = [n for n, _ in sorted(self.analyzer.ritardi.items(), 
                                      key=lambda x: -x[1])[:15]]
        return sorted(random.sample(delayed, 6))

class LowHighStrategy(BaseStrategy):
    """Strategia ricerca 1: Bilanciamento low/high"""
    def generate(self) -> List[int]:
        low = [n for n in range(1, 46)]
        high = [n for n in range(46, 91)]
        selection = random.sample(low, 3) + random.sample(high, 3)
        return sorted(selection)

class OptimizedWheelingStrategy(BaseStrategy):
    """Strategia ricerca 4: Wheeling ottimizzato (MIP)"""
    def generate(self) -> List[int]:
        # Implementazione semplificata del paper SSRN
        core = list(set(
            self.analyzer.frequenze.most_common(5) +
            sorted(self.analyzer.ritardi.items(), key=lambda x: -x[1])[:5]
        ))
        combs = list(itertools.combinations([n for n, _ in core], 6))
        return sorted(random.choice(combs))

class BaseStrategy:
    """Classe base per tutte le strategie"""
    def __init__(self, analyzer: Analyzer):
        self.analyzer = analyzer
    
    def generate(self) -> List[int]:
        raise NotImplementedError

class FrequenzaStrategy(BaseStrategy):
    """Strategia 1: Numeri più frequenti"""
    def generate(self) -> List[int]:
        return sorted(random.sample([
            n for n, _ in self.analyzer.frequenze.most_common(15)
        ], 6))

class RitardiStrategy(BaseStrategy):
    """Strategia 2: Numeri con maggior ritardo"""
    def generate(self) -> List[int]:
        return sorted(random.sample([
            n for n, _ in sorted(self.analyzer.ritardi.items(), key=lambda x: -x[1])[:15]
        ], 6))

class BilanciataStrategy(BaseStrategy):
    """Strategia 3: Combinazione bilanciata (pari/dispari, bassi/alti)"""
    def generate(self) -> List[int]:
        def is_balanced(nums):
            pari = sum(1 for n in nums if n % 2 == 0)
            bassi = sum(1 for n in nums if n <= 45)
            return 2 <= pari <= 4 and 2 <= bassi <= 4
        
        candidates = []
        for _ in range(1000):
            candidate = sorted(random.sample(range(1, 91), 6))
            if is_balanced(candidate):
                candidates.append(candidate)
        return random.choice(candidates) if candidates else []

class TermiciStrategy(BaseStrategy):
    """Strategia 4: Numeri termici (più estratti negli ultimi 3 mesi)"""
    def generate(self) -> List[int]:
        recenti = [e for e in self.analyzer.estrazioni if e.data >= self.analyzer.ultima_data - timedelta(days=90)]
        freq = defaultdict(int)
        for e in recenti:
            for n in e.numeri:
                freq[n] += 1
        return sorted(random.sample([
            n for n, _ in sorted(freq.items(), key=lambda x: -x[1])[:20]
        ], 6))

class MIPOptimizedStrategy(BaseStrategy):
    """Strategia basata sul paper SSRN (combinazioni a minima similarità)"""
    def generate(self, num_tickets=15) -> List[List[int]]:
        # Implementazione semplificata dell'algoritmo MIP
        candidates = []
        all_nums = list(range(1, 91))
        
        for _ in range(num_tickets):
            while True:
                comb = sorted(random.sample(all_nums, 6))
                if self._is_valid_combination(comb, candidates):
                    candidates.append(comb)
                    break
        return candidates

def _is_valid_combination(self, new_comb, existing_combs):
    # Massimo 2 numeri in comune con qualsiasi combinazione esistente
    for comb in existing_combs:
        common = len(set(new_comb) & set(comb))
        if common > 2:
            return False
    return True