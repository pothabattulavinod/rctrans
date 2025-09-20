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
        kyc_data = []
        if table:
            rows = table.find_all('tr')
            for row in rows[1:]:  # skip header
                cols = [c.get_text(strip=True) for c in row.find_all('td')]
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
    """Fetch current month transaction details as structured JSON."""
    url = BASE_URL + card["CARDNO"]
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Identify the transaction table by header names
        tables = soup.find_all('table')
        transaction_table = None
        for table in tables:
            headers = [th.get_text(strip=True) for th in table.find_all('th')]
            if 'Sl.No' in headers and 'Avail. Date' in headers:
                transaction_table = table
                break

        if not transaction_table:
            print(f"No transaction table found for CARDNO {card['CARDNO']}")
            return []

        # Skip the first 3 header rows (merged headers)
        rows = transaction_table.find_all('tr')[3:]
        transactions = []

        for row in rows:
            cols = [td.get_text(strip=True) for td in row.find_all('td')]
            if len(cols) >= 9:
                try:
                    avail_date = datetime.strptime(cols[5], "%d-%m-%Y")
                    if avail_date.month == month and avail_date.year == year:
                        transaction = {
                            "SlNo": int(cols[0]),
                            "Member": cols[1],
                            "AvailedFPS": cols[2],
                            "AllottedMonth": cols[3],
                            "AllottedYear": int(cols[4]),
                            "AvailDate": avail_date.strftime("%Y-%m-%d"),
                            "AvailType": cols[6],
                            "SugarKG": float(cols[7].replace(",", "")),
                            "RiceKG": float(cols[8].replace(",", ""))
                        }
                        transactions.append(transaction)
                except ValueError:
                    continue

        return transactions

    except requests.RequestException as e:
        print(f"HTTP error fetching CARDNO {card['CARDNO']}: {e}")
        return []

def update_transactions(data, monthly_data):
    """Update transactions.json with card KYC and monthly transaction info."""
    if os.path.exists(TRANSACTIONS_FILE):
        with open(TRANSACTIONS_FILE, "r") as f:
            transactions = json.load(f)
    else:
        transactions = []

    existing_card = next((t for t in transactions if t.get("CARDNO") == data["CARDNO"]), None)
    if existing_card:
        existing_card["KYC_INFO"] = data.get("KYC_INFO", existing_card.get("KYC_INFO", []))
        existing_card["MONTHLY_TRANSACTIONS"] = monthly_data
        existing_card["LAST_UPDATED"] = data["LAST_UPDATED"]
    else:
        data["MONTHLY_TRANSACTIONS"] = monthly_data
        transactions.append(data)

    with open(TRANSACTIONS_FILE, "w") as f:
        json.dump(transactions, f, indent=4)

    print(f"Data for CARDNO {data['CARDNO']} saved/updated in {TRANSACTIONS_FILE}")

if __name__ == "__main__":
    if not os.path.exists("10.json"):
        print("10.json file not found!")
        exit(1)

    with open("10.json", "r") as f:
        cards = json.load(f)

    target_card = next((c for c in cards if c.get("CARDNO") == TARGET_CARDNO), None)
    if not target_card:
        print(f"CARDNO {TARGET_CARDNO} not found in 10.json")
        exit(1)

    kyc_data = fetch_card_data(target_card)
    monthly_data = fetch_monthly_transactions(target_card, month=TARGET_MONTH, year=TARGET_YEAR)

    if kyc_data:
        update_transactions(kyc_data, monthly_data)
    else:
        print("Failed to fetch card data.")
