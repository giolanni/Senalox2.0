# Trigger su ruota

Dal pannello operativo scegliere **Trigger su ruota**. La scheda **Trigger attivi e sestine** mostra i metodi con almeno un colpo disponibile alla data comune dei due archivi. Selezionare un metodo, impostare la quantità e premere **Genera sestine**. Per le tredicine ogni combinazione contiene sei numeri del metodo. Per i metodi a due fissi si aggiungono quattro numeri casuali tra gli altri 88. Le combinazioni sono distinte all’interno di ciascuna generazione. Il cambio di metodo conserva l’ultimo gruppo generato durante la sessione.

La scheda **Statistiche storiche** permette di scegliere tutto lo storico, il periodo dal luglio 2009 o un singolo anno. **Aggiorna dati** rilegge gli archivi e ricalcola le tabelle. Il calcolo scarica lo ZIP completo di Lotto Italia e legge le sestine locali con il caricatore condiviso. Aggiornare le sestine dalla pagina Archivio. Per riutilizzare uno ZIP già scaricato:

    python -m analysis.laboratory.trigger_ruote --lotto storico.zip --periodo 2026

Il 90 (o il 10 per Milano 10) in prima posizione sulla ruota Lotto indicata apre una finestra distinta, anche quando due finestre si sovrappongono. I metodi mensili usano il primo estratto e la somma circolare da 1 a 90. Per Milano a due numeri vale il testo che indica l'ultima estrazione del mese. L'ultimo mese dell'archivio Lotto resta in attesa della prima estrazione del mese seguente per confermarne la chiusura.

Il colpo 1 è il primo concorso SuperEnalotto con data successiva all'estrazione Lotto. I risultati riguardano la copertura della sestina principale. Jolly, SuperStar, importi e combinazioni effettivamente giocate sono esclusi. Le soglie adottate sono almeno 3 numeri per le tredicine e almeno 1 per le coppie.

In analysis/output/trigger_ruote si trovano cinque file CSV separati da punto e virgola.

- **statistiche.csv** contiene il riepilogo per anno di attivazione e per periodo. La percentuale usa le sole attivazioni con tutti e nove i colpi osservabili. OK e KO usano la prima occorrenza della soglia. Un ciclo ancora corto può già essere OK.
- **attivazioni.csv** contiene data del segnale, numeri previsti, primo esito e stato per ogni ciclo.
- **colpi.csv** conserva anche i colpi successivi al primo successo, contrassegnati da Dopo_primo_esito.
- **attivi_passivi.csv** conta ogni concorso una volta per singola tredicina fissa. Un concorso è attivo quando cade in almeno una finestra di nove colpi, anche dopo un primo successo. Il periodo segue la data del concorso. I primi nove concorsi dello storico sono esclusi da questo confronto per evitare esposizioni parziali.

New mode inizia il 1° luglio 2009. Milano 10 ha due versioni, con 71 nella fonte stampata e 21 nel foglio personale. Milano 90 e Venezia 90 usano la stessa tredicina. Sommare le righe dei metodi può contare più volte la stessa sestina.

**concorsi_attivi.csv** è il registro giornaliero: una riga per metodo e data, con riferimento al segnale più recente. Una riattivazione rinnova i nove colpi a partire dal concorso successivo. Nuovi_concorsi misura solo quelli aggiunti e segue la data del segnale. Concorsi_attivi_disputati conta ciascuna data effettiva una volta e segue l’anno del concorso. Le statistiche OK per attivazione restano consultabili separatamente.
