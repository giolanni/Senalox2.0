import numpy as np
from typing import List, Dict
from collections import defaultdict

class GeneticOptimizer:
    def __init__(self, strategies: List[Dict], population_size=100, generations=50):
        self.strategies = strategies
        self.population_size = population_size
        self.generations = generations
        self.fitness_history = []
        
    class Chromosome:
        def __init__(self, weights):
            self.weights = np.array(weights)
            self.weights /= np.sum(weights)  # Normalizzazione
            self.fitness = 0.0
            
    def initialize_population(self):
        """Crea popolazione iniziale con pesi casuali"""
        return [self.Chromosome(np.random.rand(len(self.strategies))) 
                for _ in range(self.population_size)]
                
    def calculate_fitness(self, chromosome, historical_data):
        """Valuta la performance storica dei pesi"""
        total_score = 0
        for strategy, weight in zip(self.strategies, chromosome.weights):
            strategy_score = self._evaluate_strategy(strategy, historical_data)
            total_score += weight * strategy_score
        return total_score
        
    def _evaluate_strategy(self, strategy, data):
        """Calcola il punteggio per una singola strategia"""
        # Implementazione base (da completare con logiche specifiche)
        if strategy['type'] == 'frequency':
            return self._frequency_score(data)
        elif strategy['type'] == 'delay':
            return self._delay_score(data)
        return 0.0
        
    def evolve_population(self, population):
        """Esegue un ciclo di evoluzione genetica"""
        # Selezione, crossover e mutazione
        new_population = []
        elites = sorted(population, key=lambda x: -x.fitness)[:2]
        new_population.extend(elites)
        
        while len(new_population) < self.population_size:
            parent1, parent2 = np.random.choice(population[:50], 2, replace=False)
            child = self._crossover(parent1, parent2)
            child = self._mutate(child)
            new_population.append(child)
            
        return new_population
        
    def _crossover(self, parent1, parent2):
        """Single-point crossover"""
        idx = np.random.randint(1, len(parent1.weights)-1)
        new_weights = np.concatenate([parent1.weights[:idx], parent2.weights[idx:]])
        return self.Chromosome(new_weights)
        
    def _mutate(self, chromosome, mutation_rate=0.1):
        """Applica mutazioni casuali"""
        mask = np.random.rand(len(chromosome.weights)) < mutation_rate
        chromosome.weights[mask] = np.random.rand(np.sum(mask))
        chromosome.weights /= np.sum(chromosome.weights)
        return chromosome
