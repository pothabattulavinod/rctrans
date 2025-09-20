import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import os

BASE_URL = "https://aepos.ap.gov.in/Qcodesearch.jsp?rcno="
TARGET_CARDNO = "2822192607"
TRANSACTIONS_FILE = "transactions.json"
CURRENT_MONTH = datetime.now().month
CURRENT_YEAR = datetime.now().year

def fetch_card_data(card):
    url = BASE_URL + card["CARDNO"]
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find('table')
        if not table:
            print(f"No table found for CARDNO {card['CARDNO']}")
            return None

        rows = table.find_all('tr')
        new_transitions = []

        for row in rows[1:]:  # skip header
            cols = [c.text.strip() for c in row.find_all('td')]
            if cols and len(cols) >= 1:
                try:
                    date_obj = datetime.strptime(cols[0], "%d-%m-%Y")
                    # Only include transitions from the current month & year
                    if date_obj.month == CURRENT_MONTH and date_obj.year == CURRENT_YEAR:
                        new_transitions.append(cols)
                except ValueError:
                    # If date parsing fails, include anyway
                    new_transitions.append(cols)

        return {
            "CARDNO": card.get("CARDNO"),
            "HEAD_OF_THE_FAMILY": card.get("HEAD_OF_THE_FAMILY", "Unknown"),
            "UNITS": card.get("UNITS", "Unknown"),
            "TRANSITION_HISTORY": new_transitions,
            "LAST_UPDATED": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    except requests.RequestException as e:
        print(f"HTTP error fetching CARDNO {card['CARDNO']}: {e}")
        return None

def update_transactions(data):
    # Load existing transactions
    if os.path.exists(TRANSACTIONS_FILE):
        with open(TRANSACTIONS_FILE, "r") as f:
            transactions = json.load(f)
    else:
        transactions = []

    # Check if the card already exists
    existing_card = next((t for t in transactions if t.get("CARDNO") == data["CARDNO"]), None)
    if existing_card:
        # Append only new transitions
        existing_transitions = existing_card.get("TRANSITION_HISTORY", [])
        for t in data["TRANSITION_HISTORY"]:
            if t not in existing_transitions:
                existing_transitions.append(t)
        existing_card["TRANSITION_HISTORY"] = existing_transitions
        existing_card["LAST_UPDATED"] = data["LAST_UPDATED"]
    else:
        # Add new card
        transactions.append(data)

    # Save updated transactions
    with open(TRANSACTIONS_FILE, "w") as f:
        json.dump(transactions, f, indent=4)

    print(f"Data for CARDNO {data['CARDNO']} saved/updated in {TRANSACTIONS_FILE}")


if __name__ == "__main__":
    # Load cards from 10.json
    if not os.path.exists("10.json"):
        print("10.json file not found!")
        exit(1)

    with open("10.json", "r") as f:
        cards = json.load(f)

    # Find target card
    target_card = next((c for c in cards if c.get("CARDNO") == TARGET_CARDNO), None)
    if not target_card:
        print(f"CARDNO {TARGET_CARDNO} not found in 10.json")
        exit(1)

    # Fetch card data
    data = fetch_card_data(target_card)
    if data:
        update_transactions(data)
    else:
        print("Failed to fetch card data.")
