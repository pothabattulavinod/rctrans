import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

URL = "https://aepos.ap.gov.in/Qcodesearch.jsp?rcno=2808446602"

def fetch_data():
    try:
        response = requests.get(URL)
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
            "CARDNO": "2822192607",
            "HEAD_OF_THE_FAMILY": "Singuluri Venkatalakshmi",
            "UNITS": "2",
            "TRANSITION_HISTORY": transition_history,
            "LAST_UPDATED": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        with open("data.json", "w") as f:
            json.dump(data, f, indent=4)

        print("Data updated successfully!")

    except Exception as e:
        print("Error fetching data:", e)

if __name__ == "__main__":
    fetch_data()
