from datetime import datetime
import random
from shared.data_loader import load_estrazioni_filtered

class StrategyOptimizer:
    def __init__(self, data_path, start_year=None):
        self.estrazioni = load_estrazioni_filtered(data_path, start_year)
        self.default_weights = {
            'frequenza': 0.3,
            'ritardo': 0.2,
            'stagionale': 0.2,
            'data': 0.3
        }

    def find_optimal_weights(self, target_date, iterations=500):
        train_data = [e for e in self.estrazioni if e.data < target_date]
        target = next((e for e in self.estrazioni if e.data >= target_date), None)
        
        if not target or len(train_data) < 100:
            return None

        best_weights = self.default_weights.copy()
        best_score = float('inf')

        for _ in range(iterations):
            current_weights = {
                k: v + random.uniform(-0.1, 0.1) 
                for k, v in best_weights.items()
            }
            total = sum(current_weights.values())
            norm_weights = {k: v/total for k, v in current_weights.items()}
            
            generated = genera_sestina_pesata(train_data, norm_weights)
            score = sum(1 for n in generated if n not in target.numeri)
            
            if score < best_score:
                best_score = score
                best_weights = norm_weights

        return best_weights
