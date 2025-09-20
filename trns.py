import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

BASE_URL = "https://aepos.ap.gov.in/Qcodesearch.jsp?rcno="
CURRENT_MONTH = datetime.now().month
CURRENT_YEAR = datetime.now().year

def fetch_card_data(card):
    url = BASE_URL + card["CARDNO"]
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table')
        rows = table.find_all('tr') if table else []

        transition_history = []
        for row in rows[1:]:
            cols = [c.text.strip() for c in row.find_all('td')]
            if cols:
                try:
                    date_obj = datetime.strptime(cols[0], "%d-%m-%Y")  # adjust format if needed
                    if date_obj.month == CURRENT_MONTH and date_obj.year == CURRENT_YEAR:
                        transition_history.append(cols)
                except:
                    continue

        return {
            "CARDNO": card["CARDNO"],
            "HEAD_OF_THE_FAMILY": card["HEAD_OF_THE_FAMILY"],
            "UNITS": card["UNITS"],
            "TRANSITION_HISTORY": transition_history,
            "LAST_UPDATED": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    except Exception as e:
        print(f"Error fetching CARDNO {card['CARDNO']}: {e}")
        return None

def fetch_all_cards(cards):
    all_data = []
    with ThreadPoolExecutor(max_workers=20) as executor:  # parallel 20 threads
        results = executor.map(fetch_card_data, cards)
        for result in results:
            if result:
                all_data.append(result)

    # Save latest data to transactions.json
    with open("transactions.json", "w") as f:
        json.dump(all_data, f, indent=4)

    print("All card data saved to transactions.json!")

if __name__ == "__main__":
    with open("cards.json") as f:
        cards = json.load(f)
    fetch_all_cards(cards)
