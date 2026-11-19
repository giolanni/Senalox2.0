# Trigger su ruota

Dal pannello operativo scegliere **Trigger su ruota**. Il calcolo scarica lo ZIP completo di Lotto Italia e legge le sestine locali con il caricatore condiviso. Aggiornare le sestine dalla pagina Archivio. Per riutilizzare uno ZIP già scaricato:

    python -m analysis.laboratory.trigger_ruote --lotto storico.zip --periodo 2026

Ogni uscita della spia in una delle cinque posizioni apre una finestra distinta, anche quando due finestre si sovrappongono. I metodi mensili usano il primo estratto e la somma circolare da 1 a 90. Per Milano a due numeri vale il testo che indica l'ultima estrazione del mese. L'ultimo mese dell'archivio Lotto resta in attesa della prima estrazione del mese seguente per confermarne la chiusura.

Il colpo 1 è il primo concorso SuperEnalotto con data successiva all'estrazione Lotto. I risultati riguardano la copertura della sestina principale. Jolly, SuperStar, importi e combinazioni effettivamente giocate sono esclusi. Le soglie adottate sono almeno 3 numeri per le tredicine e almeno 1 per le coppie.

In analysis/output/trigger_ruote si trovano quattro file CSV separati da punto e virgola.

- **statistiche.csv** contiene il riepilogo per anno di attivazione e per periodo. La percentuale usa le sole attivazioni con tutti e nove i colpi osservabili. OK e KO usano la prima occorrenza della soglia. Un ciclo ancora corto può già essere OK.
- **attivazioni.csv** contiene data del segnale, numeri previsti, primo esito e stato per ogni ciclo.
- **colpi.csv** conserva anche i colpi successivi al primo successo, contrassegnati da Dopo_primo_esito.
- **attivi_passivi.csv** conta ogni concorso una volta per singola tredicina fissa. Un concorso è attivo quando cade in almeno una finestra di nove colpi, anche dopo un primo successo. Il periodo segue la data del concorso. I primi nove concorsi dello storico sono esclusi da questo confronto per evitare esposizioni parziali.

New mode inizia il 1° luglio 2009. Milano 10 ha due versioni, con 71 nella fonte stampata e 21 nel foglio personale. Milano 90 e Venezia 90 usano la stessa tredicina. Sommare le righe dei metodi può contare più volte la stessa sestina.
