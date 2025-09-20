import os
import json
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, WebDriverException

# Configuration
BASE_URL = "https://aepos.ap.gov.in/Qcodesearch.jsp?rcno="
INPUT_FILE = "10.json"           # file containing card numbers
TRANSACTIONS_FILE = "transactions.json"
TARGET_MONTH = 9                 # September
TARGET_YEAR = 2025

def setup_driver(headless=True):
    """Set up Selenium Chrome WebDriver with GitHub Actions compatible binary."""
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.binary_location = "/usr/bin/chromium-browser"
    return webdriver.Chrome(options=chrome_options)

def fetch_monthly_transactions(cardno, month=TARGET_MONTH, year=TARGET_YEAR):
    """Fetch transactions for a given card and month/year from AP POS."""
    try:
        driver = setup_driver()
        driver.get(BASE_URL + cardno)
        time.sleep(3)  # Wait for page/table to load

        try:
            table = driver.find_element(By.XPATH, "//table[contains(., 'Sl.No') and contains(., 'Avail. Date')]")
        except NoSuchElementException:
            return []  # No table, no transactions

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

    except WebDriverException as e:
        print(f"WebDriver error for CARDNO {cardno}: {e}")
        return []

    finally:
        try:
            driver.quit()
        except:
            pass

def update_transactions_json(cardno, monthly_data):
    """Update transactions.json only if monthly_data is not empty."""
    if not monthly_data:
        return  # Skip cards with no transactions

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

    print(f"Updated transactions for CARDNO {cardno}")

def load_card_numbers(file_path=INPUT_FILE):
    """Load all card numbers from the input JSON file."""
    if not os.path.exists(file_path):
        print(f"{file_path} not found.")
        return []

    with open(file_path, "r") as f:
        data = json.load(f)

    return [entry.get("CARDNO") for entry in data if "CARDNO" in entry]

def main():
    card_numbers = load_card_numbers()
    if not card_numbers:
        print("No card numbers found in input file.")
        return

    print(f"Processing {len(card_numbers)} cards...")

    for cardno in card_numbers:
        try:
            monthly_data = fetch_monthly_transactions(cardno)
            if monthly_data:  # Only update if there are transactions
                update_transactions_json(cardno, monthly_data)
            else:
                print(f"No transactions for CARDNO {cardno}, skipping.")
        except Exception as e:
            print(f"Error processing CARDNO {cardno}: {e}")

if __name__ == "__main__":
    main()
