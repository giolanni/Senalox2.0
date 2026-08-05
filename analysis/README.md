# Senalox Analysis & Laboratory

Questa cartella è completamente separata dalle interfacce **Senalox Legacy** e
**New Senalox**. Gli script leggono soltanto il dataset condiviso tramite
`shared/data_loader.py` e scrivono i risultati sotto `analysis/**/output/`.

Non modificano `estrazioni.csv`, non cambiano gli algoritmi operativi e non
vengono caricati dal launcher.

## Struttura

```text
analysis/
├── common/                         utility condivise
├── experiments/
│   └── parity/                     studio descrittivo della parità
├── laboratory/
│   └── trigger_patterns/           scoperta di regole post-trigger
└── run_all.py                      esecuzione completa iniziale
```

## Avvio

Aprire PowerShell nella cartella principale `C:\mi\Senalox`.

### Tutti gli esperimenti iniziali

```powershell
python -m analysis.run_all
```

### Solo Parità

```powershell
python -m analysis.experiments.parity.run
```

### Trigger singolo, configurazione del libro (13 numeri / 9 estrazioni)

```powershell
python -m analysis.laboratory.trigger_patterns.single_number_window --dataset BOTH --window 9 --pool-size 13 --simulations 50
```

Per una baseline casuale più precisa, aumentare gradualmente le simulazioni:

```powershell
python -m analysis.laboratory.trigger_patterns.single_number_window --dataset BOTH --window 9 --pool-size 13 --simulations 500
```

## Metodo del laboratorio trigger

Per ciascun numero da 1 a 90:

1. il primo 60% cronologico serve alla **scoperta** del gruppo di 13 numeri;
2. il 20% successivo serve alla **validazione**;
3. l’ultimo 20% è il **test fuori campione**;
4. il gruppo resta congelato dopo la scoperta;
5. si misura se, nelle 9 estrazioni successive al trigger, almeno una singola
   estrazione contiene 2, 3, 4, 5 o 6 numeri del gruppo;
6. il risultato viene confrontato con gruppi casuali di 13 numeri.

Un candidato non viene considerato valido solo perché appare buono nel periodo
di scoperta. Il campo più importante è il lift sullo split `TEST`, insieme al
numero di occorrenze disponibili.

## Output

Gli output sono CSV separati da `;`, apribili con LibreOffice Calc.

- `parity_distribution_*.csv`
- `parity_transitions_*.csv`
- `parity_stability_*.csv`
- `single_trigger_w9_p13_*.csv`
- report `.txt` sintetici

## Regola di governance

Le regole seguiranno questi stati:

```text
candidate_rules -> validated_rules -> operational_algorithms
                      |
                      -> rejected_rules
```

In questa prima versione i risultati restano soltanto candidati di laboratorio.
