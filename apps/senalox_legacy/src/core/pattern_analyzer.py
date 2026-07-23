from collections import defaultdict
from datetime import date

def ricorrenze_per_data(estrazioni, target_date):
    """Trova la frequenza dei numeri estratti nello stesso giorno e mese nel corso degli anni."""
    
    number_counts = defaultdict(int)
    
    for estrazione in estrazioni:
        # Estrai il giorno e il mese dall'estrazione
        extraction_day = estrazione.data.day
        extraction_month = estrazione.data.month
        
        # Estrai il giorno e il mese dalla target_date
        target_day = target_date.day
        target_month = target_date.month
        
        # Verifica se il giorno e il mese corrispondono
        if extraction_day == target_day and extraction_month == target_month:
            for numero in estrazione.numeri:
                number_counts[numero] += 1
                
            number_counts[estrazione.jolly] += 1
            number_counts[estrazione.supers] += 1

    return dict(sorted(number_counts.items(), key=lambda item: item[1], reverse=True))

def ricorrenze_numero_ripetuto(estrazioni, numero_target):
    """
    Analizza le ricorrenze di un numero ripetuto consecutivamente nelle estrazioni.
    Restituisce un dizionario con la frequenza delle ripetizioni consecutive.
    """
    ripetizioni = defaultdict(int)
    conteggio_corrente = 0

    for i in range(len(estrazioni)):
        if numero_target in estrazioni[i].numeri or \
           numero_target == estrazioni[i].jolly or \
           numero_target == estrazioni[i].supers:
            conteggio_corrente += 1
        else:
            if conteggio_corrente > 1:
                ripetizioni[conteggio_corrente] += 1
            conteggio_corrente = 0

    # Gestisci il caso in cui l'ultima serie di estrazioni consecutive arriva fino alla fine
    if conteggio_corrente > 1:
        ripetizioni[conteggio_corrente] += 1

    return dict(sorted(ripetizioni.items(), key=lambda item: item[0]))


def ricorrenze_post_estraz_numero(estrazioni, numero_target):
    """Analizza quali numeri seguono più frequentemente un numero dato."""
    
    numero_counts = defaultdict(int)
    
    for i in range(len(estrazioni) - 1):
        estrazione_corrente = estrazioni[i]
        estrazione_successiva = estrazioni[i + 1]
        
        if numero_target in estrazione_corrente.numeri:
            for numero in estrazione_successiva.numeri:
                numero_counts[numero] += 1
    
    # Calcola le percentuali di occorrenza
    totale_occorrenze = sum(numero_counts.values())
    percentuali = {numero: (count / totale_occorrenze) * 100 for numero, count in numero_counts.items()}
    
    return dict(sorted(percentuali.items(), key=lambda item: item[1], reverse=True))
