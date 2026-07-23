import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.multioutput import MultiOutputClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

class LotteryPredictor:
    def __init__(self):
        # Usa un classificatore base come RandomForest per multi-label classification
        base_model = RandomForestClassifier(random_state=42)
        self.model = MultiOutputClassifier(base_model)

    def train(self, X, y):
        # Dividi i dati in training e test
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Addestra il modello
        self.model.fit(X_train, y_train)
        
        # Valuta il modello
        y_pred = self.model.predict(X_test)
        accuracy = np.mean([accuracy_score(y_test[:, i], y_pred[:, i]) for i in range(y.shape[1])])
        print(f"Accuracy media su tutti i numeri: {accuracy:.2f}")

    def predict_next(self, data):
        # Prevedi i numeri per la prossima estrazione
        predictions = self.model.predict(data)
        
        # Trova gli indici dei numeri previsti come "1" (estratti)
        predicted_numbers = np.where(predictions[0] == 1)[0] + 1  # +1 per riportare all'intervallo 1-90
        
        # Restituisci al massimo 6 numeri predetti
        return predicted_numbers[:6]

class DataPreprocessor:
    def __init__(self, estrazioni):
        self.estrazioni = estrazioni

    def create_features(self):
        features = []
        targets = []
        
        for estrazione in self.estrazioni:
            # Crea una feature binaria per ogni numero (da 1 a 90)
            row = [1 if i+1 in estrazione.numeri else 0 for i in range(90)]
            features.append(row)
            
            # Il target è la sestina estratta (binaria)
            target_row = [1 if i+1 in estrazione.numeri else 0 for i in range(90)]
            targets.append(target_row)

        # Restituisci le feature e il target come DataFrame e array numpy
        X = pd.DataFrame(features)
        y = np.array(targets)  # Matrice binaria con forma (n_estrazioni, 90)
        
        return X, y
