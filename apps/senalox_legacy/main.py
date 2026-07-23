import argparse
from shared.data_loader import ... load_estrazioni_multifile
from src.core.generator import genera_sestina_pesata
from src.core.simulation import simulazione_storica_completa
from src.core.ml_model import DataPreprocessor, LotteryPredictor
from src.core.clustering import NumberClusterAnalyzer
import pandas as pd  # Importa pandas qui

def main():
    parser = argparse.ArgumentParser(
        description="SuperEnalotto Analyzer - Strumento avanzato per analisi e generazione sestine",
        epilog="Esempi:\n"
               "  python main.py data/ --genera\n"
               "  python main.py data/ --predici\n"
               "  python main.py data/ --cluster --num_cluster 5"
    )

    # Argomenti principali
    parser.add_argument('data_path', help="Percorso alla cartella con i dati CSV")

    # Modalità operative
    parser.add_argument('--genera', action='store_true', help="Genera una nuova sestina")
    parser.add_argument('--simula', type=int, help="Esegui simulazioni storiche")
    parser.add_argument('--predici', action='store_true', help="Genera previsioni usando ML")
    parser.add_argument('--cluster', action='store_true', help="Esegui analisi dei cluster")

    # Parametri aggiuntivi
    parser.add_argument('--strategies', nargs='+',
                      choices=['frequenza', 'ritardo', 'stagionale', 'data'],
                      help="Strategie da utilizzare per la generazione")
    parser.add_argument('--weights', nargs='+', type=float,
                      help="Pesi per le strategie (ordine corrispondente ai criteri)")
    parser.add_argument('--num_cluster', type=int, default=5,
                      help="Numero di cluster da identificare (default: 5)")
    parser.add_argument('--window_size', type=int, default=2000,
                      help="Dimensione finestra storica per previsioni (default: 2000)")

    args = parser.parse_args()

    try:
        print(f"Caricamento dati da {args.data_path}...")
        estrazioni = load_estrazioni_multifile(args.data_path)
        print(f"Caricate {len(estrazioni)} estrazioni")

        strategy_config = {}
        if args.strategies and args.weights:
            strategy_config = dict(zip(args.strategies, args.weights))

        # Generazione sestina classica
        if args.genera:
            sestina = genera_sestina_pesata(estrazioni, strategy_config)
            print(f"\n[SISTEMA CLASSICO] Sestina generata: {sestina}")

        # Simulazione storica
        if args.simula:
            print(f"\nAvvio simulazione con {args.simula} iterazioni...")
            risultati = simulazione_storica_completa(estrazioni, strategy_config, args.simula)
            print("\n[RISULTATI SIMULAZIONE]")
            print(f"Media numeri indovinati: {risultati['media']:.2f}")
            print("Distribuzione risultati:")
            for k, v in risultati['distribuzione'].items():
                print(f"- {k} numeri: {v} volte")

        # Previsione con Machine Learning
        if args.predici:
            if len(estrazioni) < args.window_size:
                raise ValueError(f"Servono almeno {args.window_size} estrazioni per le previsioni")

            print("\nPreparazione dati per Machine Learning...")
            preprocessor = DataPreprocessor(estrazioni[-args.window_size:])
            X, y = preprocessor.create_features()

            print("Addestramento modello...")
            predictor = LotteryPredictor()
            predictor.train(X, y)

            # Predici usando l'ultima estrazione come input
            latest_data = X.iloc[[-1]]  # Prendi l'ultima riga come input
            predicted_numbers = predictor.predict_next(latest_data)

            print(f"\n[PREVISIONE ML] Prossima sestina: {sorted(predicted_numbers)}")


        # Analisi dei cluster
        if args.cluster:
            print("\nAnalisi dei cluster in corso...")
            cluster_analyzer = NumberClusterAnalyzer(n_clusters=args.num_cluster)
            clusters = cluster_analyzer.analyze(estrazioni[-args.window_size:])

            print("\n[RISULTATI CLUSTER]")
            for cluster, numbers in clusters.items():
                print(f"Cluster {cluster + 1}: {sorted(numbers)}")

    except Exception as e:
        print(f"\nERRORE: {str(e)}")

if __name__ == "__main__":
    main()