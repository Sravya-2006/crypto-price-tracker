import os
import time
from datetime import datetime
import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from webdriver_manager.chrome import ChromeDriverManager


URL = "https://coinmarketcap.com/"
CSV_FILE = "crypto_prices_v2.csv"


def start_browser(headless=True):
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")

    options.add_argument("--window-size=1920,1080")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


def clean_number(text):
    return (
        text.replace("$", "")
            .replace(",", "")
            .replace("%", "")
            .replace("\n", "")
            .strip()
    )


def fetch_crypto_data(driver):
    driver.get(URL)
    wait = WebDriverWait(driver, 25)

    wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "tbody tr")))
    rows = driver.find_elements(By.CSS_SELECTOR, "tbody tr")[:10]

    data = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for row in rows:
        cols = row.find_elements(By.TAG_NAME, "td")
        if len(cols) < 7:
            continue

        try:
            coin = {
                "Time": timestamp,
                "Rank": cols[0].text,
                "Name": cols[1].text.split("\n")[0],
                "Price": cols[2].text,
                "1h": cols[3].text,
                "24h": cols[4].text,
                "7d": cols[5].text,
                "Market Cap": cols[6].text
            }
            data.append(coin)
        except:
            continue

    return data


def show_data(data):
    df = pd.DataFrame(data)
    print("\n========= LIVE CRYPTO DATA =========")
    print(df.to_string(index=False))
    return df


def save_to_csv(df):
    if os.path.exists(CSV_FILE):
        df.to_csv(CSV_FILE, mode="a", header=False, index=False)
    else:
        df.to_csv(CSV_FILE, index=False)

    print(f"\nSaved to {CSV_FILE}")


def find_gainers_and_losers(df):
    df["24h_num"] = df["24h"].apply(lambda x: float(clean_number(x)) if "%" in x else 0)

    gainers = df.sort_values("24h_num", ascending=False).head(3)
    losers = df.sort_values("24h_num").head(3)

    print("\n========= TOP 3 GAINERS (24H) =========")
    print(gainers[["Name", "24h"]].to_string(index=False))

    print("\n========= TOP 3 LOSERS (24H) =========")
    print(losers[["Name", "24h"]].to_string(index=False))


def filter_data(df):
    choice = input("\nApply filter? (y/n): ").lower()
    if choice != "y":
        return df

    try:
        min_price = input("Minimum Price ($): ")
        min_change = input("Minimum 24h change (%) : ")

        if min_price:
            df["Price_num"] = df["Price"].apply(lambda x: float(clean_number(x)))
            df = df[df["Price_num"] >= float(min_price)]

        if min_change:
            df["24h_num"] = df["24h"].apply(lambda x: float(clean_number(x)))
            df = df[df["24h_num"] >= float(min_change)]

    except:
        print("Filter error. Showing full data.")
        return df

    return df


def main():
    print("=== Crypto Price Tracker V2 ===")

    headless = input("Headless mode (y/n): ").lower() == "y"

    driver = start_browser(headless)

    print("\nFetching data...")
    data = fetch_crypto_data(driver)
    driver.quit()

    if not data:
        print("No data fetched. Site layout may have changed.")
        return

    df = show_data(data)

    df = filter_data(df)

    if df.empty:
        print("\nNo data matched your filter.")
    else:
        print("\n========= FILTERED DATA =========")
        print(df.to_string(index=False))
        save_to_csv(df)
        find_gainers_and_losers(df)

    print("\nDONE ✅")


if __name__ == "__main__":
    main()