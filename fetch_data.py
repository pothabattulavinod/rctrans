import os
import json
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

BASE_URL = "https://aepos.ap.gov.in/Qcodesearch.jsp?rcno="
TARGET_CARDNO = os.getenv("CARDNO", "2822192607")
TRANSACTIONS_FILE = "transactions.json"
TARGET_MONTH = 9   # September
TARGET_YEAR = 2025

def setup_driver(headless=True):
    """Set up Selenium Chrome WebDriver."""
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=chrome_options)

def fetch_monthly_transactions(cardno, month=TARGET_MONTH, year=TARGET_YEAR):
    """Fetch transactions for a given month/year from the AP POS website."""
    driver = setup_driver()
    try:
        driver.get(BASE_URL + cardno)
        time.sleep(3)  # Wait for page to load

        table = driver.find_element(By.XPATH, "//table[contains(., 'Sl.No') and contains(., 'Avail. Date')]")
        rows = table.find_elements(By.TAG_NAME, "tr")[3:]  # Skip header rows

        transactions = []
        for row in rows:
            cols = [td.text.strip() for td in row.find_elements(By.TAG_NAME, "td")]
            if len(cols) >= 9:
                try:
                    avail_date = datetime.strptime(cols[5], "%d-%m-%Y")
                    if avail_date.month == month and avail_date.year == year:
                        transactions.append({
                            "SlNo": int(cols[0]),
                            "Member": cols[1],
                            "AvailedFPS": cols[2],
                            "AllottedMonth": cols[3],
                            "AllottedYear": int(cols[4]),
                            "AvailDate": avail_date.strftime("%Y-%m-%d"),
                            "AvailType": cols[6],
                            "SugarKG": float(cols[7].replace(",", "")),
                            "RiceKG": float(cols[8].replace(",", ""))
                        })
                except ValueError:
                    continue

        return transactions
    finally:
        driver.quit()

def update_current_month_transactions(cardno, monthly_data):
    """Update transactions.json with current month data."""
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
    monthly_data = fetch_monthly_transactions(TARGET_CARDNO)
    if monthly_data:
        for tx in monthly_data:
            print(tx)
        update_current_month_transactions(TARGET_CARDNO, monthly_data)
    else:
        print(f"No transactions found for {TARGET_MONTH}/{TARGET_YEAR} for CARDNO {TARGET_CARDNO}")
