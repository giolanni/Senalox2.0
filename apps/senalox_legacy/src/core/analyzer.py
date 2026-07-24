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
    Genera una sestina coerente con la distribuzione storica pari/dispari.

    Il metodo non sceglie semplicemente tutti i pari o tutti i dispari.
    Prima determina quante volte, nelle estrazioni analizzate, sono usciti
    0, 1, 2, 3, 4, 5 o 6 numeri pari. Seleziona quindi la composizione più
    frequente e sceglie i numeri più ricorrenti all'interno dei due gruppi.

    Esempio: se la composizione storica più frequente è 3 pari e 3 dispari,
    la funzione restituisce i tre pari e i tre dispari più frequenti nel
    dataset attualmente selezionato.
    """
    if not estrazioni:
        raise ValueError("La lista delle estrazioni è vuota.")

    try:
        # Conta, per ogni estrazione, quanti numeri pari contiene.
        distribuzione_pari = Counter(
            sum(numero % 2 == 0 for numero in estrazione.numeri)
            for estrazione in estrazioni
        )

        # In caso di parità tra più composizioni, preferisce quella più
        # equilibrata rispetto a 3 pari e 3 dispari.
        numero_pari_target = max(
            distribuzione_pari,
            key=lambda numero_pari: (
                distribuzione_pari[numero_pari],
                -abs(numero_pari - 3),
            ),
        )

        numero_dispari_target = 6 - numero_pari_target

        # Calcola la frequenza storica di ciascun numero.
        frequenze = Counter(
            numero
            for estrazione in estrazioni
            for numero in estrazione.numeri
        )

        pari_ordinati = sorted(
            range(2, 91, 2),
            key=lambda numero: (-frequenze[numero], numero),
        )

        dispari_ordinati = sorted(
            range(1, 91, 2),
            key=lambda numero: (-frequenze[numero], numero),
        )

        sestina = (
            pari_ordinati[:numero_pari_target]
            + dispari_ordinati[:numero_dispari_target]
        )

        return sorted(sestina)

    except Exception as e:
        print(f"Errore durante l'analisi della parità: {e}")
        return []


def analisi_decine(estrazioni: List[Estrazione]) -> List[int]:
    """
    Genera una sestina coerente con la distribuzione storica per decine.

    I numeri vengono divisi nelle nove fasce 1-10, 11-20, ..., 81-90.
    Per ciascuna estrazione viene costruito il relativo profilo, ad esempio:

        (1, 1, 0, 1, 1, 0, 1, 0, 1)

    che indica un numero nella prima decina, uno nella seconda, nessuno nella
    terza e così via. La funzione individua il profilo più frequente nello
    storico selezionato e, per ogni fascia prevista dal profilo, sceglie i
    numeri più ricorrenti di quella fascia.
    """
    if not estrazioni:
        raise ValueError("La lista delle estrazioni è vuota.")

    try:
        profili_decine = Counter()

        for estrazione in estrazioni:
            profilo = [0] * 9

            for numero in estrazione.numeri:
                indice_decina = (numero - 1) // 10
                profilo[indice_decina] += 1

            profili_decine[tuple(profilo)] += 1

        # Se più profili hanno la stessa frequenza, preferisce quello che
        # distribuisce la sestina sul maggior numero di decine differenti.
        profilo_target = max(
            profili_decine,
            key=lambda profilo: (
                profili_decine[profilo],
                sum(1 for quantita in profilo if quantita > 0),
            ),
        )

        frequenze = Counter(
            numero
            for estrazione in estrazioni
            for numero in estrazione.numeri
        )

        sestina = []

        for indice_decina, quantita_da_prendere in enumerate(profilo_target):
            if quantita_da_prendere == 0:
                continue

            inizio = indice_decina * 10 + 1
            fine = inizio + 10

            numeri_decina = sorted(
                range(inizio, fine),
                key=lambda numero: (-frequenze[numero], numero),
            )

            sestina.extend(numeri_decina[:quantita_da_prendere])

        return sorted(sestina)

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
