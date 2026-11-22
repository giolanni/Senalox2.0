"""Statistiche e sestine dei trigger storici su ruota."""
from math import comb
from queue import Empty, Queue
from random import SystemRandom
from threading import Thread
from analysis.laboratory.trigger_ruote import REGOLE
import tkinter as tk
from tkinter import messagebox, ttk

from analysis.laboratory.trigger_ruote import aggiorna_report, carica_lotto
from shared.data_loader import load_estrazioni_overall
from shared.paths import PROJECT_ROOT


def numeri(pool):
    return '   '.join(f'{n:02}' for n in pool)


def carica_quadro():
    lotto = carica_lotto(None)
    estrazioni = load_estrazioni_overall()
    eventi, stats, giornaliero = aggiorna_report(lotto, estrazioni, PROJECT_ROOT/'analysis/output/trigger_ruote')
    recenti = {r['Metodo']: r for r in eventi}
    attivi = {nome: r for nome, r in recenti.items() if r['Sempre_attivo'] or r['Osservati'] < 9}
    fine = min(max(lotto), estrazioni[-1].data)
    ultime = [e for e in estrazioni if e.data <= fine][-30:]
    risultati = {e.data: (e.numeri, []) for e in reversed(ultime)}
    pools = {(e['Metodo'], e['Attivazione']): e['Pool'] for e in eventi}
    for r in giornaliero:
        if r['Data'] in risultati:
            pool = pools[r['Metodo'], r['Attivazione']]
            risultati[r['Data']][1].append((r['Metodo'], r['Punti'], r['Numeri'] or '—', pool))
    return max(lotto), estrazioni[-1].data, stats, attivi, risultati


class Sestine:
    """Campiona combinazioni distinte. Decodifica solo la pagina visualizzata."""
    def __init__(self, pool, quantita):
        self.fissi = tuple(pool) if len(pool) == 2 else ()
        self.scelte = sorted(set(range(1, 91)) - set(pool)) if self.fissi else sorted(pool)
        self.posti = 6 - len(self.fissi)
        massimo = comb(len(self.scelte), self.posti)
        if not 1 <= quantita <= massimo:
            raise ValueError(f'Inserisci una quantità tra 1 e {massimo:,}.'.replace(',', '.'))
        self.indici = SystemRandom().sample(range(massimo), quantita)

    def riga(self, i):
        rank = self.indici[i]
        posti = self.posti
        valori = list(self.fissi)
        for pos, n in enumerate(self.scelte):
            quanti = comb(len(self.scelte)-pos-1, posti-1)
            if rank < quanti:
                valori.append(n)
                posti -= 1
                if posti == 0:
                    break
            else:
                rank -= quanti
        return sorted(valori)


def tabella(parent, colonne, altezza):
    box = ttk.Frame(parent)
    box.pack(fill='both', expand=True, pady=(8, 0))
    tree = ttk.Treeview(box, columns=[k for k, _ in colonne], show='headings',
                        selectmode='browse', height=altezza, style='Ruote.Treeview')
    for k, w in colonne:
        tree.heading(k, text=k)
        tree.column(k, width=w, minwidth=40, anchor='w' if k=='Metodo' else 'center')
    for orient, command, side in [('vertical',tree.yview,'right'), ('horizontal',tree.xview,'bottom')]:
        bar = ttk.Scrollbar(box, orient=orient, command=command)
        tree.configure(**{('y' if orient=='vertical' else 'x')+'scrollcommand':bar.set})
        bar.pack(side=side, fill='y' if orient=='vertical' else 'x')
    tree.pack(fill='both', expand=True)
    tree.tag_configure('chiaro', background='#f1f6fa')
    return tree


class WheelPage(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style='App.TFrame')
        self.stats, self.attivi = [], {}
        self.lotto = self.se = None
        self.coda = Queue()
        self.lotti = {}
        self.ticket = None
        self.pagina = 0
        self.periodo = tk.StringVar()
        self.quantita = tk.StringVar(value='3')
        style = ttk.Style(self)
        style.configure('Ruote.Treeview', rowheight=28, font=('Segoe UI',10))
        style.configure('Ruote.Treeview.Heading', font=('Segoe UI',9,'bold'))
        top = ttk.Frame(self, style='App.TFrame')
        top.pack(fill='x', pady=(0, 10))
        self.aggiorna = ttk.Button(top,text='Aggiorna dati',command=self.refresh)
        self.aggiorna.pack(side='right')
        self.info = ttk.Label(top, style='Muted.TLabel',wraplength=460)
        self.info.pack(side='left')
        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill='both',expand=True)
        gioco = ttk.Frame(self.tabs,padding=12)
        storico = ttk.Frame(self.tabs,padding=12)
        attivi = ttk.Frame(self.tabs,padding=12)
        self.tabs.add(attivi,text='  Prossimo concorso  ')
        self.tabs.add(gioco,text='  Genera sestine  ')
        self.tabs.add(storico,text='  Risultati per metodo  ')
        recenti = ttk.Frame(self.tabs, padding=12)
        self.tabs.add(recenti, text='  Ultime estrazioni  ')
        barra_date = ttk.Frame(recenti)
        barra_date.pack(fill='x')
        ttk.Label(barra_date, text='Estrazione SuperEnalotto').pack(side='left')
        self.data_recente = ttk.Combobox(barra_date, width=13, state='readonly')
        self.data_recente.pack(side='left', padx=8)
        self.data_recente.bind('<<ComboboxSelected>>', self.mostra_estrazione)
        self.sei_estratti = ttk.Label(recenti, font=('Segoe UI', 12, 'bold'))
        self.sei_estratti.pack(anchor='w', pady=(10, 2))
        self.esiti_recenti = tabella(recenti, [('Metodo', 135), ('Punti', 50),
                                     ('Numeri centrati', 100), ('Tredicina in gioco', 270)], 10)
        self.esiti_recenti.tag_configure('centro', background='#d9f1e3')
        ttk.Label(attivi,text='Metodi ancora in gioco',font=('Segoe UI',14,'bold')).pack(anchor='w')
        self.elenco = tabella(attivi,[('Metodo',160),('Validità',115),('Data Lotto',95),('Già giocati',90),('Restano',80)],8)
        self.elenco.bind('<<TreeviewSelect>>',self.scegli_attivo)
        self.elenco.bind('<Double-1>',lambda _: self.apri_generatore())
        self.prova = ttk.Label(attivi,wraplength=560)
        self.prova.pack(anchor='w',pady=6)
        self.apri = ttk.Button(attivi,text='Genera sestine per questo metodo',command=self.apri_generatore)
        self.apri.pack(anchor='w')
        self.apri.state(['disabled'])
        ttk.Label(gioco,text='Sestine per il metodo',font=('Segoe UI',14,'bold')).pack(anchor='w',pady=(0,7))
        self.selettore = ttk.Combobox(gioco,state='readonly',width=34)
        self.selettore.pack(anchor='w')
        self.selettore.bind('<<ComboboxSelected>>',self.seleziona)
        self.dettaglio = ttk.Label(gioco)
        self.dettaglio.pack(anchor='w',pady=(10,4))
        self.pool_label = tk.Label(gioco,anchor='w',bg='#173952',fg='white',
                                   font=('Segoe UI',13,'bold'),padx=12,pady=8)
        self.pool_label.pack(fill='x')
        self.modalita = ttk.Label(gioco,wraplength=540)
        self.modalita.pack(anchor='w',pady=5)
        barra = ttk.Frame(gioco)
        barra.pack(fill='x')
        ttk.Label(barra,text='Numero di sestine').pack(side='left')
        ttk.Entry(barra,textvariable=self.quantita,width=7).pack(side='left',padx=7)
        self.genera = ttk.Button(barra,text='Genera sestine',command=self.genera_sestine)
        self.genera.pack(side='left')
        self.sestine = tabella(gioco,[('Sestina',64)]+[(f'{i}°',55) for i in range(1,7)],5)
        foot = ttk.Frame(gioco)
        foot.pack(fill='x',pady=(5,0))
        self.contatore = ttk.Label(foot)
        self.contatore.pack(side='left')
        self.avanti = ttk.Button(foot,text='Successive ›',command=lambda:self.mostra_pagina(1))
        self.avanti.pack(side='right')
        self.indietro = ttk.Button(foot,text='‹ Precedenti',command=lambda:self.mostra_pagina(-1))
        self.indietro.pack(side='right')
        filtri = ttk.Frame(storico)
        filtri.pack(fill='x')
        ttk.Label(filtri,text='Periodo').pack(side='left')
        self.periodi = ttk.Combobox(filtri,state='readonly',textvariable=self.periodo,width=21)
        self.periodi.pack(side='left',padx=8)
        self.periodi.bind('<<ComboboxSelected>>',self.mostra_stats)
        ttk.Label(storico,text='Quanti numeri del metodo sono usciti nella stessa sestina?',
                  font=('Segoe UI',12,'bold')).pack(anchor='w',pady=(10,0))
        self.storico = tabella(storico,[('Metodo',145),('Concorsi',75),
                                *[(f'{k} punto' if k==1 else f'{k} punti',62) for k in range(1,7)]],8)
        self.storico.bind('<<TreeviewSelect>>',self.dettaglio_storico)
        self.sintesi = ttk.Label(storico,wraplength=550,justify='left')
        self.sintesi.pack(anchor='w',pady=(6,0))
        self.seleziona()
        self.refresh()

    def refresh(self):
        self.aggiorna.state(['disabled'])
        self.info.configure(text='Aggiornamento degli archivi in corso…')
        def worker():
            try:
                self.coda.put(carica_quadro())
            except Exception as exc:
                self.coda.put(exc)
        Thread(target=worker,daemon=True).start()
        self.after(80,self.ricevi)

    def ricevi(self):
        try:
            dati = self.coda.get_nowait()
        except Empty:
            self.after(80,self.ricevi)
            return
        self.aggiorna.state(['!disabled'])
        if isinstance(dati,Exception):
            self.info.configure(text='Aggiornamento fallito.' + (f' Ultimi dati al {min(self.lotto,self.se):%d/%m/%Y}.' if self.lotto else ''))
            messagebox.showerror('Aggiornamento trigger',str(dati),parent=self)
            return
        self.lotto,self.se,self.stats,self.attivi,self.risultati = dati
        self.date_recenti = list(self.risultati)
        self.data_recente.configure(values=[d.strftime('%d/%m/%Y') for d in self.date_recenti])
        if self.date_recenti:
            self.data_recente.current(0)
        self.mostra_estrazione()
        aggiornamento = f'Lotto {self.lotto:%d/%m/%Y}   ·   SuperEnalotto {self.se:%d/%m/%Y}'
        if self.lotto != self.se:
            aggiornamento += f'   ·   Situazione al {min(self.lotto,self.se):%d/%m/%Y}'
        self.info.configure(text=aggiornamento)
        nomi_attivi = sorted({self.nome_segnale(n) for n in self.attivi})
        self.tabs.tab(0,text=f'  Prossimo concorso ({len(nomi_attivi)} attivi)  ')
        precedente = self.elenco.selection()
        self.elenco.delete(*self.elenco.get_children())
        for i, nome in enumerate(nomi_attivi):
            r = self.attivi[self.variante(nome)]
            self.elenco.insert('', 'end', iid=nome, values=(nome, 'Sempre attivo' if r['Sempre_attivo'] else '9 concorsi', r['Attivazione'].strftime('%d/%m/%Y'),
                              '—' if r['Sempre_attivo'] else r['Osservati'], '—' if r['Sempre_attivo'] else 9-r['Osservati']), tags=('chiaro',) if i%2==0 else ())
        if nomi_attivi:
            self.elenco.selection_set(precedente[0] if precedente and precedente[0] in nomi_attivi else nomi_attivi[0])
        self.scegli_attivo()
        nomi = sorted(self.attivi)
        self.selettore.configure(values=nomi)
        if self.selettore.get() not in nomi:
            self.selettore.set(nomi[0] if nomi else '')
        anni = sorted({r['Periodo'] for r in self.stats if r['Periodo'].isdigit()},reverse=True)
        if not self.periodo.get():
            self.periodo.set(str(min(self.lotto,self.se).year))
        self.periodi.configure(values=['Dal luglio 2009','Tutto lo storico',*anni])
        self.seleziona()
        self.mostra_stats()

    def mostra_estrazione(self, event=None):
        self.esiti_recenti.delete(*self.esiti_recenti.get_children())
        i = self.data_recente.current()
        if i < 0:
            self.sei_estratti.configure(text='Nessuna estrazione disponibile.')
            return
        sestina, righe = self.risultati[self.date_recenti[i]]
        self.sei_estratti.configure(text='Sestina estratta   ' + numeri(sestina))
        for riga in sorted(righe, key=lambda r: (-r[1], r[0])):
            self.esiti_recenti.insert('', 'end', values=riga, tags=('centro',) if riga[1] >= 3 else ())

    @staticmethod
    def nome_segnale(nome):
        return 'Milano 10' if nome.startswith('Milano 10 ') else nome

    def variante(self, nome):
        if nome == 'Milano 10':
            return 'Milano 10 Excel'
        return nome

    def scegli_attivo(self, event=None):
        scelta = self.elenco.selection()
        if not scelta:
            self.prova.configure(text='Nessun metodo attivo alla data degli archivi.')
            self.apri.state(['disabled'])
            return
        r = self.attivi[self.variante(scelta[0])]
        if r['Sempre_attivo']:
            self.prova.configure(text=f"{scelta[0]} · Sempre attivo. Tredicina calcolata sul primo estratto "
                                     f"{r['Primo_estratto_Lotto']} del {r['Attivazione']:%d/%m/%Y}.")
            self.apri.state(['!disabled'])
            return
        pos = r['Posizione_spia']
        motivo = f"Spia in posizione {pos}." if pos else f"Primo estratto {r['Primo_estratto_Lotto']}."
        self.prova.configure(text=f"{scelta[0]} · Cinque estratti Lotto: {r['Estratti_Lotto']}. {motivo} "
                                 f"Il prossimo è il colpo {r['Osservati']+1} di 9.")
        self.apri.state(['!disabled'])

    def apri_generatore(self):
        scelta = self.elenco.selection()
        if scelta:
            self.selettore.set(self.variante(scelta[0]))
            self.seleziona()
            self.tabs.select(1)

    def seleziona(self, event=None):
        self.ticket = self.lotti.get(self.chiave())
        self.pagina = 0
        self.mostra_pagina(0)
        r = self.attivi.get(self.selettore.get())
        if not r:
            self.dettaglio.configure(text='Nessun trigger attivo per il prossimo concorso.' if self.lotto else 'Caricamento trigger…')
            self.pool_label.configure(text='—')
            self.modalita.configure(text='')
            self.genera.state(['disabled'])
            return
        self.genera.state(['!disabled'])
        self.dettaglio.configure(text=f"Sempre attivo · Tredicina aggiornata il {r['Attivazione']:%d/%m/%Y}" if r['Sempre_attivo'] else f"Attivazione {r['Attivazione']:%d/%m/%Y}     ·     Prossimo colpo {r['Osservati']+1} di 9")
        self.pool_label.configure(text=numeri(map(int,r['Pool'].split())))
        self.modalita.configure(text='I due numeri restano fissi. Gli altri quattro sono estratti dagli altri 88 numeri.' if r['Soglia']==1
                               else 'Ogni sestina contiene sei numeri estratti dai tredici del metodo.')

    def chiave(self):
        nome = self.selettore.get()
        r = self.attivi.get(nome)
        return (nome, r['Attivazione'], r['Pool']) if r else None

    def genera_sestine(self):
        r = self.attivi.get(self.selettore.get())
        if not r:
            return
        try:
            n = int(self.quantita.get())
        except ValueError:
            messagebox.showerror('Quantità','Inserisci un numero intero.',parent=self)
            return
        try:
            self.ticket = Sestine(list(map(int,r['Pool'].split())), n)
        except ValueError as exc:
            messagebox.showerror('Quantità',str(exc),parent=self)
            return
        self.lotti[self.chiave()] = self.ticket
        self.pagina = 0
        self.mostra_pagina(0)

    def mostra_pagina(self, delta):
        self.sestine.delete(*self.sestine.get_children())
        self.pagina += delta
        totale = len(self.ticket.indici) if self.ticket else 0
        start = self.pagina*50
        stop = min(start+50,totale)
        for i in range(start,stop):
            self.sestine.insert('','end',values=(i+1,*[f'{n:02}' for n in self.ticket.riga(i)]),
                                tags=('chiaro',) if i%2==0 else ())
        self.contatore.configure(text=f'Sestine {start+1}–{stop} di {totale}' if totale else '')
        self.indietro.state(['!disabled' if start else 'disabled'])
        self.avanti.state(['!disabled' if stop<totale else 'disabled'])

    def mostra_stats(self,event=None):
        periodo = {'Tutto lo storico':'Overall','Dal luglio 2009':'New mode'}.get(self.periodo.get(),self.periodo.get())
        self.storico.delete(*self.storico.get_children())
        self.righe = {r['Metodo']:r for r in self.stats if r['Periodo']==periodo}
        for i,(nome, _, _, pool) in enumerate(REGOLE):
            r = self.righe.get(nome, {})
            valori = [r.get(f'Punti_{k}',0) if k<=len(pool) else '—' for k in range(1,7)]
            self.storico.insert('','end',iid=nome,values=(nome,r.get('Concorsi_attivi_disputati',0),*valori),
                                tags=('chiaro',) if i%2==0 else ())
        self.sintesi.configure(text='Ogni data conta una volta. Seleziona un metodo per leggere la regola e confrontare i risultati.')

    def dettaglio_storico(self, event=None):
        scelta = self.storico.selection()
        if not scelta:
            return
        nome = scelta[0]
        _, ruota, condizione, valori = next(regola for regola in REGOLE if regola[0]==nome)
        r = self.righe.get(nome, {})
        if isinstance(condizione,int):
            regola = f'{nome}: {condizione} primo estratto su {ruota}.'
        else:
            regola = (f'{nome}: {condizione} estrazione del mese su {ruota}. Al primo estratto si sommano '
                      + ', '.join(map(str,valori))+' (oltre 90 si sottrae 90).')
        soglia = 1 if len(valori)==2 else 3
        n = r.get('Concorsi_attivi_disputati',0)
        centri = sum(r.get(f'Punti_{k}',0) for k in range(soglia,7))
        def rapporto(ok, totale):
            if not totale:
                return 'nessun concorso'
            return f'{ok} su {totale} ({100*ok/totale:.1f}%)'.replace('.',',')
        ambito = 'nei concorsi del periodo' if condizione == 'prima' else 'durante i nove colpi'
        righe = [regola,f'Almeno {soglia} in una sestina {ambito}: {rapporto(centri,n)}.']
        if isinstance(condizione,int):
            righe.append('Stessi 13 numeri fuori dai nove colpi: '+rapporto(r.get('Tre_o_piu_passivo',0),r.get('Base_passivo',0))+'.')
        completi = r.get('Finestre_complete',0)
        if completi:
            righe.append(f"Segnali del periodo con almeno un centro entro nove colpi: {r['OK_complete']} su {completi} completi.")
        self.sintesi.configure(text='\n'.join(righe))
