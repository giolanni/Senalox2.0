from typing import List, Tuple
from tqdm import tqdm
from shared.models.estrazione import Estrazione
from src.core.generator import genera_sestina_pesata

def simulazione_storica(estrazioni: List[Estrazione]) -> Tuple[float, List[int]]:
    """
    Simula l'algoritmo testandolo su estrazioni storiche.
    
    Args:
        estrazioni (List[Estrazione]): Elenco delle estrazioni storiche.
        num_simulazioni (int): Numero di simulazioni da eseguire.

    Returns:
        Tuple[float, List[int]]: Media dei numeri indovinati e distribuzione dei risultati.
    """
    indice_iter = 0
    if len(estrazioni) < 100:
        raise ValueError("Servono almeno 100 estrazioni per la simulazione.")
    
    try:
        risultati = []
        estrazioni = estrazioni[-200:]  # Usa solo le ultime 1000 estrazioni per efficienza

        num_simulazioni: int = len(estrazioni)
        
        for i in range(num_simulazioni):
            indice_iter = i
            if i>=num_simulazioni-1:
                raise ValueError(f"l'indice raggiunto è errato : {i}")
            if i % 100 == 0:
                print(f"Simulazione: {i}/{num_simulazioni}")
            
            train_data = estrazioni[:100 + i]
            test_data = estrazioni[100 + i]
            
            sestina_generata = genera_sestina_pesata(train_data)
            numeri_indovinati = len(set(sestina_generata) & set(test_data.numeri))
            risultati.append(numeri_indovinati)
        
        media = sum(risultati) / len(risultati)
        distribuzione = [risultati.count(i) for i in range(7)]
        
        return media, distribuzione
    
    except ValueError as e:
        print(f"Errore durante la simulazione storica: {e}")
        return media, distribuzione
    
    except Exception as e:
        print(f"Errore durante la simulazione storica: {e.__traceback__}")
        print(f"indice all'errore: {indice_iter}")
        return 0.0, []


def simulazione_storica_completa(estrazioni: List[Estrazione]) -> Tuple[float, List[int]]:
    """
    Esegue il backtesting completo su tutte le estrazioni disponibili
    
    Args:
        estrazioni (List[Estrazione]): Lista completa delle estrazioni storiche ordinate per data
    
    Returns:
        Tuple[float, List[int]]: Media dei numeri indovinati e distribuzione completa dei risultati
    """
    if len(estrazioni) < 100:
        raise ValueError("Servono almeno 100 estrazioni per una simulazione significativa")
    
    risultati = []
    min_train_size = 100  # Dimensione minima del training set
    
    for test_idx in range(min_train_size, len(estrazioni)):
        # Usa TUTTE le estrazioni precedenti come training
        train_data = estrazioni[:test_idx]
        test_data = estrazioni[test_idx]
        
        try:
            sestina_generata = genera_sestina_pesata(train_data)
            numeri_indovinati = len(set(sestina_generata) & set(test_data.numeri))
            risultati.append(numeri_indovinati)
        except Exception as e:
            print(f"\nErrore all'estrazione {test_idx}: {str(e)}")
            continue
        
        # Stampa aggiornamenti periodici
        if test_idx % 100 == 0:
            media_corrente = sum(risultati) / len(risultati)
            print(f"Progresso: {test_idx}/{len(estrazioni)}, Media: {media_corrente:.2f}, Data: {test_data.data.strftime('%d/%m/%Y')}")

    # Calcola le statistiche finali
    media = sum(risultati) / len(risultati) if risultati else 0
    distribuzione = [risultati.count(i) for i in range(7)]
    
    return media, distribuzione