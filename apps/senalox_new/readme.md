# Senalox 2.0

Programma per l'analisi e la generazione di sestine per il SuperEnalotto

## Installazione

1. Clona il repository
2. Installa le dipendenze: pip install -r requirements.txt
3. Posiziona i file CSV delle estrazioni nella cartella `data`

## Utilizzo

Esegui il programma con: python exec_gui.py o python exec_gui.py 2009 (per considerare solo le estrazioni con nuova formula dal 1 luglio 2009)

- Scegli il metodo di generazione dal menu a schede
- Genera sestine utilizzando diverse strategie
- Visualizza le statistiche storiche

## Struttura dei dati

I file CSV devono avere il formato:
data;1;2;3;4;5;6;jolly;superstar

## Licenza
MIT License
