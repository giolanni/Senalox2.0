"""
Descrizioni centralizzate degli algoritmi di Senalox.

Il modulo contiene le informazioni mostrate nelle interfacce Legacy e New.
Le descrizioni spiegano l'obiettivo dell'algoritmo, il criterio analizzato e
il modo in cui viene costruita la sestina.

Nota importante:
le descrizioni documentano il comportamento previsto. Gli algoritmi Parità e
Decine saranno verificati e corretti nel passaggio successivo, perché nella
versione Legacy mostrano attualmente un comportamento anomalo.
"""

from __future__ import annotations


ALGORITHM_INFO: dict[str, dict[str, str]] = {
    "Frequenze": {
        "objective": "Individuare i numeri comparsi più spesso nel dataset selezionato.",
        "analysis": (
            "Conta quante volte ciascun numero da 1 a 90 è presente nelle "
            "estrazioni analizzate."
        ),
        "generation": (
            "La sestina privilegia i numeri con la frequenza storica più alta."
        ),
    },
    "Ritardi": {
        "objective": "Individuare i numeri assenti da più estrazioni.",
        "analysis": (
            "Calcola, per ogni numero, quante estrazioni sono trascorse dalla "
            "sua ultima comparsa."
        ),
        "generation": (
            "La sestina privilegia i numeri con il ritardo corrente maggiore."
        ),
    },
    "Somme": {
        "objective": "Generare una sestina con una somma coerente con lo storico.",
        "analysis": (
            "Calcola la somma dei sei numeri di ogni estrazione e ne studia il "
            "valore medio o l'intervallo più rappresentativo."
        ),
        "generation": (
            "La sestina viene costruita cercando una somma vicina al valore "
            "statistico individuato."
        ),
    },
    "Parità": {
        "objective": "Riprodurre la distribuzione storica tra numeri pari e dispari.",
        "analysis": (
            "Conta, nelle estrazioni analizzate, quante sestine presentano le "
            "diverse combinazioni di numeri pari e dispari."
        ),
        "generation": (
            "La sestina dovrebbe rispettare la composizione pari/dispari più "
            "rappresentativa nel dataset selezionato."
        ),
    },
    "Decine": {
        "objective": "Distribuire la sestina tra le fasce numeriche da 1 a 90.",
        "analysis": (
            "Suddivide i numeri nelle fasce 1-10, 11-20, 21-30, fino a 81-90, "
            "e ne analizza la presenza storica."
        ),
        "generation": (
            "La sestina dovrebbe distribuire i numeri tra più fasce, seguendo "
            "la distribuzione osservata nello storico."
        ),
    },
    "Sequenze": {
        "objective": "Individuare la ricorrenza di numeri consecutivi.",
        "analysis": (
            "Cerca nelle estrazioni storiche coppie o gruppi di numeri "
            "consecutivi e misura quanto spesso compaiono."
        ),
        "generation": (
            "La sestina viene costruita includendo i numeri associati ai pattern "
            "di sequenza più ricorrenti."
        ),
    },
    "Generazione Pesata": {
        "objective": "Generare sestine usando pesi derivati dalla frequenza storica.",
        "analysis": (
            "Assegna a ogni numero un peso proporzionale alla frequenza con cui "
            "è comparso nel dataset selezionato."
        ),
        "generation": (
            "Produce una sestina casuale pesata e una sestina Top composta dai "
            "sei numeri con il peso più elevato."
        ),
    },
    "Bilanciata": {
        "objective": "Produrre una sestina con caratteristiche strutturali equilibrate.",
        "analysis": (
            "Combina vincoli come parità, distribuzione per decine e somma "
            "complessiva della sestina."
        ),
        "generation": (
            "La sestina viene scelta tra combinazioni che rispettano i criteri "
            "di equilibrio previsti dalla strategia."
        ),
    },
    "Termici": {
        "objective": "Privilegiare i numeri più presenti nel periodo recente.",
        "analysis": (
            "Analizza una finestra temporale recente e misura la frequenza dei "
            "numeri al suo interno."
        ),
        "generation": (
            "La sestina privilegia i numeri considerati più caldi nel periodo "
            "recente."
        ),
    },
    "Casuale": {
        "objective": "Generare una sestina senza applicare criteri statistici.",
        "analysis": "Non utilizza frequenze, ritardi o altri indicatori storici.",
        "generation": (
            "Estrae casualmente sei numeri distinti compresi tra 1 e 90."
        ),
    },
    "Pesata": {
        "objective": "Combinare più strategie in una singola generazione.",
        "analysis": (
            "Raccoglie le proposte delle strategie disponibili e applica i pesi "
            "configurati per ciascuna di esse."
        ),
        "generation": (
            "La sestina finale viene estratta dal pool combinato, dando maggiore "
            "influenza alle strategie con peso più alto."
        ),
    },
}


def get_algorithm_description(name: str) -> str:
    """Restituisce una descrizione completa pronta per essere mostrata in GUI."""

    info = ALGORITHM_INFO.get(name)

    if info is None:
        return (
            "Descrizione non ancora disponibile per questo algoritmo. "
            "La relativa logica sarà documentata durante il refactoring."
        )

    return (
        f"OBIETTIVO\n{info['objective']}\n\n"
        f"COME LAVORA\n{info['analysis']}\n\n"
        f"COME GENERA LA SESTINA\n{info['generation']}"
    )
