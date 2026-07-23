import random
from typing import List, Tuple, Dict
from tqdm import tqdm
from shared.models.estrazione import Estrazione
from src.core.generator import genera_sestina_pesata

def simulazione_storica_completa(
    estrazioni: List[Estrazione],
    strategy_config: Dict[str, float],
    num_simulazioni: int = 10000
) -> Dict[str, float]:
    """Simulazione avanzata con progress bar e parametri configurabili"""
    risultati = {
        'media': 0.0,
        'distribuzione': {i: 0 for i in range(7)},
        'miglior_sistema': {'count': 0, 'sistema': None}
    }
    
    for _ in tqdm(range(num_simulazioni), desc="Simulazioni"):
        # Selezione casuale di un'estrazione storica
        target = random.choice(estrazioni)
        
        # Generazione sestina
        generated = genera_sestina_pesata(
            [e for e in estrazioni if e != target],
            strategy_config
        )
        
        # Calcolo match
        matches = len(set(generated) & set(target.numeri))
        
        # Aggiornamento statistiche
        risultati['distribuzione'][matches] += 1
        if matches > risultati['miglior_sistema']['count']:
            risultati['miglior_sistema'] = {
                'count': matches,
                'sistema': generated,
                'target': target.numeri
            }
    
    risultati['media'] = sum(
        k * v for k, v in risultati['distribuzione'].items()
    ) / num_simulazioni
    
    return risultati
