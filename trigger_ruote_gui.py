"""Statistiche e sestine dei trigger storici su ruota."""
from math import comb
from queue import Empty, Queue
from random import SystemRandom
from threading import Thread
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
    eventi, stats = aggiorna_report(lotto, estrazioni, PROJECT_ROOT/'analysis/output/trigger_ruote')
    recenti = {r['Metodo']: r for r in eventi}
    attivi = {nome: r for nome, r in recenti.items() if r['Osservati'] < 9}
    return max(lotto), estrazioni[-1].data, stats, attivi


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
        self.periodo = tk.StringVar(value='Dal luglio 2009')
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
        self.tabs.add(gioco,text='  Trigger attivi e sestine  ')
        self.tabs.add(storico,text='  Statistiche storiche  ')
        ttk.Label(gioco,text='Trigger per il prossimo concorso',font=('Segoe UI',14,'bold')).pack(anchor='w',pady=(0,7))
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
        self.storico = tabella(storico,[('Metodo',140),('Soglia',54),('OK',52),('KO',52),
                                ('Complete',78),('Successo %',84),('Nuovi',62),('Disputati',76)],10)
        ttk.Label(storico,text='OK e KO sulle finestre complete di 9 colpi. Concorsi attivi contati una volta per data.',
                  wraplength=550).pack(anchor='w',pady=6)
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
        self.lotto,self.se,self.stats,self.attivi = dati
        self.info.configure(text=f'Lotto {self.lotto:%d/%m/%Y}   ·   SuperEnalotto {self.se:%d/%m/%Y}')
        self.tabs.tab(0,text=f'  Trigger attivi ({len(self.attivi)}) e sestine  ')
        nomi = sorted(self.attivi)
        self.selettore.configure(values=nomi)
        if self.selettore.get() not in nomi:
            self.selettore.set(nomi[0] if nomi else '')
        anni = sorted({r['Periodo'] for r in self.stats if r['Periodo'].isdigit()},reverse=True)
        self.periodi.configure(values=['Dal luglio 2009','Tutto lo storico',*anni])
        self.seleziona()
        self.mostra_stats()

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
        self.dettaglio.configure(text=f"Attivazione {r['Attivazione']:%d/%m/%Y}     ·     Prossimo colpo {r['Osservati']+1} di 9")
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
        righe = sorted((r for r in self.stats if r['Periodo']==periodo),
                       key=lambda r:float(r['Percentuale'] or -1), reverse=True)
        for i,r in enumerate(righe):
            totale,ok = r['Finestre_complete'],r['OK_complete']
            soglia = 1 if r['Metodo'] in ('Bari prima','Milano ultima','Firenze ultima') else 3
            percentuale = f"{100*ok/totale:.2f}".replace('.',',') if totale else '—'
            self.storico.insert('','end',values=(r['Metodo'],soglia,ok,totale-ok,totale,percentuale,r['Nuovi_concorsi'],r['Concorsi_attivi_disputati']),
                                tags=('chiaro',) if i%2==0 else ())
