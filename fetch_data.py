import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import os

BASE_URL = "https://aepos.ap.gov.in/Qcodesearch.jsp?rcno="
TARGET_CARDNO = "2822192607"
TRANSACTIONS_FILE = "transactions.json"

# Specify month and year for transactions
TARGET_MONTH = 9   # September
TARGET_YEAR = 2025

def fetch_card_data(card):
    """Fetch member/KYC info for the card."""
    url = BASE_URL + card["CARDNO"]
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Assume first table is member/KYC info
        table = soup.find('table')
        if not table:
            print(f"No member/KYC table found for CARDNO {card['CARDNO']}")
            kyc_data = []
        else:
            rows = table.find_all('tr')
            kyc_data = []
            for row in rows[1:]:  # skip header
                cols = [c.text.strip() for c in row.find_all('td')]
                if cols:
                    kyc_data.append(cols)

        return {
            "CARDNO": card.get("CARDNO"),
            "HEAD_OF_THE_FAMILY": card.get("HEAD_OF_THE_FAMILY", "Unknown"),
            "UNITS": card.get("UNITS", "Unknown"),
            "KYC_INFO": kyc_data,
            "LAST_UPDATED": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    except requests.RequestException as e:
        print(f"HTTP error fetching CARDNO {card['CARDNO']}: {e}")
        return None

def fetch_monthly_transactions(card, month=TARGET_MONTH, year=TARGET_YEAR):
    """Fetch monthly transaction details for the card."""
    url = BASE_URL + card["CARDNO"]
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find table containing transaction headers
        tables = soup.find_all('table')
        transaction_table = None
        for table in tables:
            headers = [th.text.strip() for th in table.find_all('th')]
            if 'Sl.No' in headers and 'Avail. Date' in headers:
                transaction_table = table
                break

        if not transaction_table:
            print(f"No transaction table found for CARDNO {card['CARDNO']}")
            return []

        rows = transaction_table.find_all('tr')
        transactions = []

        for row in rows[1:]:  # skip header
            cols = [c.text.strip() for c in row.find_all('td')]
            if cols:
                try:
                    avail_date = datetime.strptime(cols[5], "%d-%m-%Y")  # 6th column = Avail. Date
                    if avail_date.month == month and avail_date.year == year:
                        transactions.append(cols)
                except (ValueError, IndexError):
                    continue  # Skip rows with invalid/missing date

        return transactions

    except requests.RequestException as e:
        print(f"HTTP error fetching CARDNO {card['CARDNO']}: {e}")
        return []

def update_transactions(data, monthly_data):
    """Update transactions.json with card KYC and monthly transaction info."""
    # Load existing transactions
    if os.path.exists(TRANSACTIONS_FILE):
        with open(TRANSACTIONS_FILE, "r") as f:
            transactions = json.load(f)
    else:
        transactions = []

    # Check if card already exists
    existing_card = next((t for t in transactions if t.get("CARDNO") == data["CARDNO"]), None)
    if existing_card:
        # Update KYC info
        existing_card["KYC_INFO"] = data.get("KYC_INFO", existing_card.get("KYC_INFO", []))
        # Update monthly transactions, append only new rows
        existing_monthly = existing_card.get("MONTHLY_TRANSACTIONS", [])
        for t in monthly_data:
            if t not in existing_monthly:
                existing_monthly.append(t)
        existing_card["MONTHLY_TRANSACTIONS"] = existing_monthly
        existing_card["LAST_UPDATED"] = data["LAST_UPDATED"]
    else:
        # New card entry
        data["MONTHLY_TRANSACTIONS"] = monthly_data
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

    # Fetch KYC and monthly transaction data
    kyc_data = fetch_card_data(target_card)
    monthly_data = fetch_monthly_transactions(target_card, month=TARGET_MONTH, year=TARGET_YEAR)

    if kyc_data:
        update_transactions(kyc_data, monthly_data)
    else:
        print("Failed to fetch card data.")
