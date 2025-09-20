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

def fetch_monthly_transactions(cardno, month=TARGET_MONTH, year=TARGET_YEAR):
    """Fetch current month transaction details as structured JSON."""
    url = BASE_URL + cardno
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
            print(f"No transaction table found for CARDNO {cardno}")
            return []

        # Skip header rows
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
        print(f"HTTP error fetching CARDNO {cardno}: {e}")
        return []

def update_current_month_transactions(cardno, monthly_data):
    """Update only the current month transactions in transactions.json."""
    if os.path.exists(TRANSACTIONS_FILE):
        with open(TRANSACTIONS_FILE, "r") as f:
            transactions = json.load(f)
    else:
        transactions = []

    existing_card = next((t for t in transactions if t.get("CARDNO") == cardno), None)
    if existing_card:
        existing_card["MONTHLY_TRANSACTIONS"] = monthly_data
        existing_card["LAST_UPDATED"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    else:
        transactions.append({
            "CARDNO": cardno,
            "MONTHLY_TRANSACTIONS": monthly_data,
            "LAST_UPDATED": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

    with open(TRANSACTIONS_FILE, "w") as f:
        json.dump(transactions, f, indent=4)

    print(f"Updated current month transactions for CARDNO {cardno} in {TRANSACTIONS_FILE}")


if __name__ == "__main__":
    monthly_data = fetch_monthly_transactions(TARGET_CARDNO, month=TARGET_MONTH, year=TARGET_YEAR)
    if monthly_data:
        update_current_month_transactions(TARGET_CARDNO, monthly_data)
    else:
        print("No transactions found for the current month.")
