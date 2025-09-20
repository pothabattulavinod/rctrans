import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import os

BASE_URL = "https://aepos.ap.gov.in/Qcodesearch.jsp?rcno="
CURRENT_MONTH = datetime.now().month
CURRENT_YEAR = datetime.now().year
TARGET_CARDNO = "2822192607"
TRANSACTIONS_FILE = "transactions.json"

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
                    date_obj = datetime.strptime(cols[0], "%d-%m-%Y")
                    if date_obj.month == CURRENT_MONTH and date_obj.year == CURRENT_YEAR:
                        transition_history.append(cols)
                except:
                    continue

        return {
            "CARDNO": card.get("CARDNO"),
            "HEAD_OF_THE_FAMILY": card.get("HEAD_OF_THE_FAMILY", "Unknown"),
            "UNITS": card.get("UNITS", "Unknown"),
            "TRANSITION_HISTORY": transition_history,
            "LAST_UPDATED": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    except Exception as e:
        print(f"Error fetching CARDNO {card['CARDNO']}: {e}")
        return None


if __name__ == "__main__":
    # Load cards from 10.json
    with open("10.json") as f:
        cards = json.load(f)

    # Load existing transactions as a list
    if os.path.exists(TRANSACTIONS_FILE):
        with open(TRANSACTIONS_FILE) as f:
            transactions = json.load(f)
    else:
        transactions = []

    # Find target card
    target_card = next((c for c in cards if c.get("CARDNO") == TARGET_CARDNO), None)

    if target_card:
        data = fetch_card_data(target_card)
        if data:
            # Check if the card already exists in transactions
            updated = False
            for i, t in enumerate(transactions):
                if t.get("CARDNO") == TARGET_CARDNO:
                    transactions[i] = data  # update existing
                    updated = True
                    break
            if not updated:
                transactions.append(data)  # add new card

            # Save back to transactions.json
            with open(TRANSACTIONS_FILE, "w") as f:
                json.dump(transactions, f, indent=4)

            print(f"Data for CARDNO {TARGET_CARDNO} saved to {TRANSACTIONS_FILE}")
        else:
            print("Failed to fetch card data.")
    else:
        print(f"CARDNO {TARGET_CARDNO} not found in 10.json")
