from collections import Counter, defaultdict
from datetime import date, timedelta
from typing import List, Tuple, Dict
import random

from shared.models.estrazione import Estrazione

class Analyzer:
    """Calcola tutte le metriche necessarie per le strategie"""
    def __init__(self, estrazioni: List[Estrazione]):
        self.estrazioni = estrazioni
        self.ultima_data = max(e.data for e in estrazioni) if estrazioni else date.today()
        self._precalcola()

    def _precalcola(self):
        """Precalcola tutte le metriche per le strategie"""
        # Metriche base
        self.frequenze = self._calcola_frequenze()
        self.ritardi = self._calcola_ritardi()
        self.somme = self._calcola_somme()
        self.sequenze = self._calcola_sequenze()
        
        # Metriche avanzate per strategie speciali
        self.parita = self._calcola_parita()
        self.decine = self._calcola_decine()
        self.termici = self._calcola_termici()
        self.combinazioni_valide = self._genera_combinazioni_valide()

    def _calcola_frequenze(self) -> Counter:
        return Counter(n for e in self.estrazioni for n in e.numeri)

    def _calcola_ritardi(self) -> Dict[int, int]:
        return {n: (self.ultima_data - max(e.data for e in self.estrazioni if n in e.numeri)).days 
                for n in range(1, 91)}

    def _calcola_somme(self) -> Dict[int, List[int]]:
        avg_somma = sum(sum(e.numeri) for e in self.estrazioni) / len(self.estrazioni)
        return {
            'media': avg_somma,
            'numeri': [n for e in self.estrazioni for n in e.numeri 
                      if abs(sum(e.numeri) - avg_somma) < 15]
        }

    def _calcola_sequenze(self) -> List[int]:
        return [n for e in self.estrazioni for n in e.numeri 
               if any(abs(n - m) == 1 for m in e.numeri)]

    def _calcola_parita(self) -> Dict[str, float]:
        pari = sum(1 for e in self.estrazioni for n in e.numeri if n % 2 == 0)
        return {'ratio': pari / (len(self.estrazioni) * 6)}

    def _calcola_decine(self) -> Dict[int, int]:
        return Counter((n-1)//10 for e in self.estrazioni for n in e.numeri)

    def _calcola_termici(self) -> Counter:
        ultimi_3_mesi = [e for e in self.estrazioni 
                        if e.data >= self.ultima_data - timedelta(days=90)]
        return Counter(n for e in ultimi_3_mesi for n in e.numeri)

    def _genera_combinazioni_valide(self) -> List[List[int]]:
        """Per la strategia MIP (combinazioni a bassa similarità)"""
        combs = []
        for _ in range(1000):
            comb = sorted(random.sample(range(1, 91), 6))
            if all(len(set(comb) & set(c)) < 3 for c in combs):
                combs.append(comb)
        return combs
