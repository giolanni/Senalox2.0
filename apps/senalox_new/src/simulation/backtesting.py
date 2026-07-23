from typing import List, Tuple
from tqdm import tqdm
from shared.models.estrazione import Estrazione
from src.core.generator import genera_sestina

def simulazione_storica(estrazioni: List[Estrazione]) -> Tuple[float, List[int]]:
    """Esegue il backtesting completo"""
    risultati = []
    
    for i in tqdm(range(100, len(estrazioni)), desc="Simulazione storica"):
        train = estrazioni[:i]
        test = estrazioni[i]
        
        sestina = genera_sestina(train)
        match = len(set(sestina) & set(test.numeri))
        risultati.append(match)
    
    distribuzione = [risultati.count(i) for i in range(7)]
    return sum(risultati)/len(risultati), distribuzione
