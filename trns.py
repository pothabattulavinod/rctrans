import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

BASE_URL = "https://aepos.ap.gov.in/Qcodesearch.jsp?rcno="

def fetch_card_data(card):
    url = BASE_URL + card["CARDNO"]
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table')
        rows = table.find_all('tr') if table else []

        transition_history = []
        for row in rows[1:]:
            cols = [c.text.strip() for c in row.find_all('td')]
            if cols:
                transition_history.append(cols)

        data = {
            "CARDNO": card["CARDNO"],
            "HEAD_OF_THE_FAMILY": card["HEAD_OF_THE_FAMILY"],
            "UNITS": card["UNITS"],
            "TRANSITION_HISTORY": transition_history,
            "LAST_UPDATED": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        return data

    except Exception as e:
        print(f"Error fetching data for CARDNO {card['CARDNO']}: {e}")
        return None

def fetch_all_cards():
    # Load all cards from cards.json
    with open("cards.json") as f:
        cards = json.load(f)

    all_data = []
    for card in cards:
        data = fetch_card_data(card)
        if data:
            all_data.append(data)

    # Save all card data to data.json
    with open("data.json", "w") as f:
        json.dump(all_data, f, indent=4)

    print("All card data updated successfully!")

if __name__ == "__main__":
    fetch_all_cards()
