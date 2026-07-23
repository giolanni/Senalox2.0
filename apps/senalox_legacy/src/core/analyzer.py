from collections import Counter
from typing import List, Tuple, Optional
from shared.models.estrazione import Estrazione

def calcola_frequenze(estrazioni: List[Estrazione]) -> List[int]:
    """
    Calcola la frequenza di ogni numero nelle estrazioni.
    
    Args:
        estrazioni (List[Estrazione]): Lista delle estrazioni.
    
    Returns:
        List[int]: Lista di numeri ordinati per frequenza decrescente.
    """
    if not estrazioni:
        raise ValueError("La lista delle estrazioni è vuota.")
    
    frequenze = Counter(num for e in estrazioni for num in e.numeri)
    return [num for num, _ in frequenze.most_common()]

def analisi_ritardi(estrazioni: List[Estrazione]) -> List[Tuple[int, int]]:
    """
    Calcola il ritardo di ogni numero dall'ultima estrazione.
    
    Args:
        estrazioni (List[Estrazione]): Lista delle estrazioni.
    
    Returns:
        List[Tuple[int, int]]: Lista di tuple (numero, ritardo) ordinate per ritardo decrescente.
    """
    if not estrazioni:
        raise ValueError("La lista delle estrazioni è vuota.")
    
    try:
        ultima_data = max(e.data for e in estrazioni)
        ritardi = {num: (ultima_data - max(e.data for e in estrazioni if num in e.numeri)).days 
                   for num in range(1, 91)}
        return sorted(ritardi.items(), key=lambda x: x[1], reverse=True)
    except Exception as e:
        print(f"Errore durante il calcolo dei ritardi: {e}")
        return []

def analisi_somme(estrazioni: List[Estrazione]) -> List[int]:
    """
    Identifica i numeri dalle estrazioni con somma vicina alla media.
    
    Args:
        estrazioni (List[Estrazione]): Lista delle estrazioni.
    
    Returns:
        List[int]: Lista di numeri da estrazioni con somma vicina alla media.
    """
    if not estrazioni:
        raise ValueError("La lista delle estrazioni è vuota.")
    
    try:
        somme = [sum(e.numeri) for e in estrazioni]
        media_somma = sum(somme) / len(somme)
        return [num for e in estrazioni if abs(sum(e.numeri) - media_somma) < 10 for num in e.numeri]
    except Exception as e:
        print(f"Errore durante l'analisi delle somme: {e}")
        return []

def analisi_parita(estrazioni: List[Estrazione]) -> List[int]:
    """
    Analizza la parità dei numeri nelle ultime estrazioni.
    
    Args:
        estrazioni (List[Estrazione]): Lista delle estrazioni.
    
    Returns:
        List[int]: Lista di numeri pari o dispari in base alla tendenza recente.
    """
    if not estrazioni:
        raise ValueError("La lista delle estrazioni è vuota.")
    
    try:
        pari_count = sum(num % 2 == 0 for e in estrazioni for num in e.numeri)
        dispari_count = len(estrazioni) * 6 - pari_count
        return [num for num in range(1, 91) if (num % 2 == 0 if pari_count > dispari_count else num % 2 != 0)]
    except Exception as e:
        print(f"Errore durante l'analisi della parità: {e}")
        return []

def analisi_decine(estrazioni: List[Estrazione]) -> List[int]:
    """
    Identifica le decine meno frequenti nelle estrazioni recenti.
    
    Args:
        estrazioni (List[Estrazione]): Lista delle estrazioni.
    
    Returns:
        List[int]: Lista di numeri dalle decine meno frequenti.
    """
    if not estrazioni:
        raise ValueError("La lista delle estrazioni è vuota.")
    
    try:
        decine = Counter((num-1)//10 for e in estrazioni for num in e.numeri)
        meno_frequenti = [d for d, _ in decine.most_common()[:-3:-1]]
        return [num for num in range(1, 91) if (num-1)//10 in meno_frequenti]
    except Exception as e:
        print(f"Errore durante l'analisi delle decine: {e}")
        return []

def analisi_sequenze(estrazioni: List[Estrazione]) -> List[int]:
    """
    Identifica numeri che formano sequenze nelle estrazioni recenti.
    
    Args:
        estrazioni (List[Estrazione]): Lista delle estrazioni.
    
    Returns:
        List[int]: Lista di numeri che formano sequenze.
    """
    if not estrazioni:
        raise ValueError("La lista delle estrazioni è vuota.")
    
    try:
        return [num for e in estrazioni for num in e.numeri 
                if num+1 in e.numeri or num-1 in e.numeri]
    except Exception as e:
        print(f"Errore durante l'analisi delle sequenze: {e}")
        return []

def controlla_duplicati(estrazioni: List[Estrazione]) -> Tuple[bool, Optional[List[Tuple[int, int]]]]:
    """
    Controlla se ci sono sestine duplicate nelle estrazioni storiche.
    
    Args:
        estrazioni (List[Estrazione]): Lista delle estrazioni storiche.
    
    Returns:
        Tuple[bool, Optional[List[Tuple[int, int]]]]: 
        - True se ci sono duplicati, False altrimenti.
        - Lista di tuple con gli indici delle estrazioni duplicate.
    """
    if not estrazioni:
        raise ValueError("La lista delle estrazioni è vuota.")
    
    try:
        seen = {}
        duplicates = []
        
        for idx, estrazione in enumerate(estrazioni):
            sestina = tuple(sorted(estrazione.numeri))
            
            if sestina in seen:
                duplicates.append((seen[sestina], idx))
            else:
                seen[sestina] = idx
        
        return (len(duplicates) > 0, duplicates) if duplicates else (False, None)
    except Exception as e:
        print(f"Errore durante il controllo dei duplicati: {e}")
        return False, None
