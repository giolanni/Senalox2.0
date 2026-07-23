import csv
import os
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import pytz

# Configurazioni
BASE_URL = "https://www.sisal.it/estrazioni/superenalotto"
DATA_DIR = "./data"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}

def get_current_year_filename():
    """Restituisce il nome del file CSV per l'anno corrente"""
    current_year = datetime.now().year
    return os.path.join(DATA_DIR, f"{current_year}.csv")

def get_last_date_from_csv(filename):
    """Legge l'ultima data disponibile dal file CSV esistente"""
    try:
        with open(filename, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            dates = [datetime.strptime(row['data'], '%d/%m/%Y') for row in reader]
            return max(dates) if dates else None
    except FileNotFoundError:
        return None

def fetch_new_draws(last_date):
    """Scarica tutte le estrazioni successive alla data specificata dal sito Sisal"""
    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        draws = []
        
        # Estrae i dati dalla tabella delle estrazioni
        table = soup.find('table')
        for row in table.find_all('tr')[1:]:  # Salta l'intestazione
            cells = row.find_all('td')
            
            draw_date_str = cells[0].text.strip().split('del')[-1].strip()
            draw_date = datetime.strptime(draw_date_str, '%d %B %Y').date()
            
            if last_date and draw_date <= last_date.date():
                continue
                
            numbers = [int(cells[1].text.strip().split()[i]) for i in range(6)]
            jolly = int(cells[2].text.split()[-1])
            superstar = int(cells[3].text.split()[-1])
            
            draws.append({
                'data': draw_date.strftime('%d/%m/%Y'),
                'conc.': cells[0].text.split()[1].strip('#'),
                '1': numbers[0],
                '2': numbers[1],
                '3': numbers[2],
                '4': numbers[3],
                '5': numbers[4],
                '6': numbers[5],
                'jolly': jolly,
                'supers': superstar
            })
            
        return draws
    
    except Exception as e:
        print(f"Errore durante lo scraping: {str(e)}")
        return []

def update_csv(filename, new_draws):
    """Aggiorna il file CSV con le nuove estrazioni"""
    file_exists = os.path.exists(filename)
    
    with open(filename, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, delimiter=';', fieldnames=[
            'data', 'conc.', '1', '2', '3', '4', '5', '6', 'jolly', 'supers'
        ])
        
        if not file_exists:
            writer.writeheader()
            
        for draw in new_draws:
            writer.writerow(draw)

def main():
    # Crea la cartella data se non esiste
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Trova il file CSV corretto
    csv_file = get_current_year_filename()
    
    # Recupera l'ultima data registrata
    last_date = get_last_date_from_csv(csv_file)
    print(f"Ultima estrazione registrata: {last_date.strftime('%d/%m/%Y') if last_date else 'Nessuna'}")

    # Scarica le nuove estrazioni
    new_draws = fetch_new_draws(last_date)
    
    if new_draws:
        print(f"Trovate {len(new_draws)} nuove estrazioni da aggiungere")
        update_csv(csv_file, new_draws)
        print("Aggiornamento completato con successo!")
    else:
        print("Nessuna nuova estrazione trovata")

if __name__ == "__main__":
    main()
