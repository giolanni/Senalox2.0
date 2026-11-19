"""Backtest delle regole storiche Lotto -> SuperEnalotto."""
import argparse
import csv
from bisect import bisect_right
from collections import Counter, defaultdict
from datetime import date
from io import BytesIO
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile

from shared.data_loader import load_estrazioni_overall, NEW_MODE_START_DATE
from shared.paths import PROJECT_ROOT

URL = 'https://www.brightstarlottery.it/STORICO_ESTRAZIONI_LOTTO/storico.zip'
# Nome, ruota, numero spia o posizione del concorso nel mese, pool/fissi.
MILANO_90 = (43,40,75,72,73,20,81,6,3,26,7,12,54)
REGOLE = [
    ('Roma 90','RM',90,(33,73,85,81,88,71,89,61,77,43,13,3,6)),
    ('Palermo 90','PA',90,(33,42,16,25,5,73,71,3,61,72,1,88,2)),
    ('Napoli 90','NA',90,(1,88,72,63,23,45,83,14,81,87,46,4,24)),
    ('Milano 90','MI',90,MILANO_90),
    ('Firenze 90','FI',90,(55,90,20,70,3,25,71,1,76,88,37,72,46)),
    ('Bari 90','BA',90,(23,13,88,34,36,61,89,1,18,77,7,81,48)),
    ('Venezia 90','VE',90,MILANO_90),
    ('Milano 10 libro','MI',10,(33,85,47,3,73,40,23,81,28,68,61,87,71)),
    ('Milano 10 Excel','MI',10,(33,85,47,3,73,40,23,81,28,68,61,87,21)),
    ('Roma prima','RM','prima',(74,83,17,38,7,70,23,27,42,55,52,75,16)),
    ('Palermo prima','PA','prima',(27,35,24,4,49,20,42,43,6,65,30,50,23)),
    ('Napoli prima','NA','prima',(41,85,26,35,50,39,44,55,13,19,52,78,38)),
    ('Bari prima','BA','prima',(10,70)),
    ('Firenze ultima','FI','ultima',(27,74)),
    ('Milano ultima','MI','ultima',(18,24)),
]


def carica_lotto(path):
    dati = path.read_bytes() if path else urlopen(URL, timeout=60).read()
    ruote = defaultdict(dict)
    with ZipFile(BytesIO(dati)) as archivio:
        for line in archivio.read('storico.txt').decode('ascii').splitlines():
            if not line.strip():
                continue
            giorno, ruota, *estratti = line.split()
            giorno = date.fromisoformat(giorno.replace('/', '-'))
            if giorno.year < 1997:
                continue
            valori = tuple(map(int, estratti))
            if len(set(valori)) != 5 or len(valori) != 5 or min(valori)<1 or max(valori)>90:
                raise ValueError(f'Estrazione Lotto non valida: {giorno} {ruota}')
            if ruota in ruote[giorno]:
                raise ValueError(f'Doppione Lotto: {giorno} {ruota}')
            ruote[giorno][ruota] = valori
    return ruote


def scrivi(path, righe):
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(righe[0]), delimiter=';')
        writer.writeheader()
        writer.writerows(righe)


def analizza(ruote, estrazioni):
    calendario = sorted(ruote)
    fine = min(calendario[-1], estrazioni[-1].data)
    sestine = {e.data:set(e.numeri) for e in estrazioni if e.data <= fine}
    giorni = sorted(sestine)
    if len(giorni) != sum(e.data <= fine for e in estrazioni):
        raise ValueError('Date duplicate nel SuperEnalotto')
    eventi, colpi, confronti = [], [], []
    for nome, ruota, condizione, valori in REGOLE:
        attivi = set()
        fine_precedente = 0
        for i, giorno in enumerate(calendario):
            if not giorni[0] <= giorno <= fine:
                continue
            numeri = ruote[giorno][ruota]
            if condizione == 'prima':
                scatta = i > 0 and calendario[i-1].month != giorno.month
            elif condizione == 'ultima':
                scatta = i+1 < len(calendario) and calendario[i+1].month != giorno.month
            else:
                scatta = numeri[0] == condizione
            if not scatta:
                continue
            pool = set(valori) if isinstance(condizione,int) else {(numeri[0]+x-1)%90+1 for x in valori}
            soglia = 1 if len(pool)==2 else 3
            inizio = bisect_right(giorni, giorno)
            sovrapposti = max(0, fine_precedente - inizio)
            fine_precedente = inizio + 9
            finestra = giorni[inizio:inizio+9]
            attivi.update(finestra)
            primo, punti, data_esito = 0, 0, ''
            for n, d in enumerate(finestra, 1):
                comuni = sorted(pool & sestine[d])
                colpi.append(dict(Metodo=nome, Attivazione=giorno, Colpo=n, Data=d,
                                  Punti=len(comuni), Numeri=' '.join(map(str,comuni)),
                                  Dopo_primo_esito=int(bool(primo))))
                if not primo and len(comuni)>=soglia:
                    primo, punti, data_esito = n, len(comuni), d
            stato = 'OK' if primo else 'KO' if len(finestra)==9 else 'APERTO'
            eventi.append(dict(Metodo=nome, Attivazione=giorno, Primo_estratto_Lotto=numeri[0], Pool=' '.join(map(str,sorted(pool))),
                               Soglia=soglia, Nuovi_concorsi=9-sovrapposti, Sovrapposti=sovrapposti, Osservati=len(finestra), Stato=stato, Primo_colpo=primo or '',
                               Punti_primo=punti or '', Data_esito=data_esito))
        if isinstance(condizione,int):
            # Nove concorsi interi come esposizione. Un concorso conta una sola volta per metodo.
            gruppi = defaultdict(Counter)
            for d in giorni[9:]:
                stato = 'attivo' if d in attivi else 'passivo'
                punti = len(set(valori) & sestine[d])
                for periodo in (str(d.year), 'Overall', 'New mode' if d >= NEW_MODE_START_DATE else 'Pre 2009-07'):
                    gruppi[periodo, stato][punti] += 1
            for (anno, stato), conti in sorted(gruppi.items()):
                confronti.append(dict(Metodo=nome, Periodo=anno, Stato=stato, Concorsi=sum(conti.values()),
                                      **{f'Punti_{k}':conti[k] for k in range(7)}))
    return eventi, colpi, confronti


def periodi(d):
    return ('Overall', 'New mode' if d >= NEW_MODE_START_DATE else 'Pre 2009-07', str(d.year))


def registro_giornaliero(colpi):
    # I segnali arrivano in ordine cronologico per metodo.
    registro = {}
    for r in colpi:
        registro[r['Metodo'], r['Data']] = r
    return sorted(registro.values(), key=lambda r: (r['Data'], r['Metodo']))


def riepilogo(eventi, giornaliero):
    osservati = Counter()
    for r in giornaliero:
        for periodo in periodi(r['Data']):
            osservati[periodo, r['Metodo']] += 1
    gruppi = defaultdict(list)
    for r in eventi:
        d = r['Attivazione']
        for periodo in periodi(d):
            gruppi[periodo,r['Metodo']].append(r)
    rows = []
    for periodo, nome in sorted(gruppi.keys() | osservati.keys()):
        gruppo = gruppi[periodo,nome]
        stati = Counter(r['Stato'] for r in gruppo)
        # Frequenza calcolata su coorti con nove esiti osservabili anche per chi ha già fatto centro.
        maturi = [r for r in gruppo if r['Osservati']==9]
        ok = sum(r['Stato']=='OK' for r in maturi)
        rows.append(dict(Periodo=periodo, Metodo=nome, Attivazioni=len(gruppo), Nuovi_concorsi=sum(r['Nuovi_concorsi'] for r in gruppo),
                         Concorsi_attivi_disputati=osservati[periodo,nome], OK=stati['OK'],
                         KO=stati['KO'], Aperti=stati['APERTO'], Finestre_complete=len(maturi),
                         OK_complete=ok, Percentuale=round(100*ok/len(maturi),2) if maturi else ''))
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lotto',type=Path,help='ZIP ufficiale locale (default: download aggiornato)')
    parser.add_argument('--output',type=Path,default=PROJECT_ROOT/'analysis/output/trigger_ruote')
    parser.add_argument('--periodo',default='New mode',help='Overall, New mode o anno')
    args = parser.parse_args()
    lotto = carica_lotto(args.lotto)
    estrazioni = load_estrazioni_overall()
    eventi,colpi,confronti = analizza(lotto,estrazioni)
    giornaliero = registro_giornaliero(colpi)
    stats = riepilogo(eventi, giornaliero)
    args.output.mkdir(parents=True,exist_ok=True)
    for nome,righe in [('statistiche',stats),('attivazioni',eventi),('colpi',colpi),('concorsi_attivi',giornaliero),('attivi_passivi',confronti)]:
        scrivi(args.output/(nome+'.csv'),righe)
    print(f'Ultimo Lotto {max(lotto)} | Ultimo SuperEnalotto {estrazioni[-1].data} | {args.periodo}')
    print('Metodo               OK su complete    %            Nuovi  Disputati  Soglia')
    for r in sorted(stats,key=lambda r:float(r['Percentuale'] or 0),reverse=True):
        if r['Periodo']==args.periodo:
            print(f"{r['Metodo']:20} {r['OK_complete']:3}/{r['Finestre_complete']:<4} {str(r['Percentuale']):>7}     {r['Nuovi_concorsi']:8}  {r['Concorsi_attivi_disputati']:9}    {1 if r['Metodo'] in ('Bari prima','Firenze ultima','Milano ultima') else 3}")
    print(f'Dettagli: {args.output}')


if __name__ == '__main__':
    main()
