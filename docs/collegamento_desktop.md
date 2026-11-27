# Collegamento desktop SenaLox

Su ogni PC Windows, dopo aver scaricato il repository, fai doppio clic su
`Crea_collegamento.bat` nella cartella principale.

Il collegamento `SenaLox.lnk` viene creato sul desktop dell'utente corrente,
compreso il desktop reindirizzato a OneDrive. Avvia `avvia_senalox.bat` e usa
`assets/icons/SenaLox.ico`. L'icona deve restare nel repository.

Puoi ripetere l'operazione: aggiorna lo stesso collegamento senza aggiungere
copie. Se sposti o rinomini la cartella del repository, eseguila nuovamente.
I vecchi collegamenti con nomi diversi restano invariati.

Il collegamento e' locale al PC: non va aggiunto a Git. Icona e script invece
sono versionati. Python e le dipendenze del progetto devono essere installati.
Lo script non richiede privilegi amministrativi. Il wrapper usa la policy
Bypass soltanto per il processo PowerShell avviato, senza modificare le
impostazioni permanenti. Eventuali policy aziendali restano applicabili.
