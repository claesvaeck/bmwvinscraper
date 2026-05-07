from curl_cffi import requests
from bs4 import BeautifulSoup
from datetime import timedelta
import re
import time
import random
import argparse

BASE_URL = "https://www.realoem.com/bmw/enUS/select"

def generate_serials(prefix, start, end, step):
    return [f"{prefix}{str(i).zfill(5)}" for i in range(start, end + 1, step)]

def extract_data(html):
    soup = BeautifulSoup(html, "html.parser")

    text = soup.get_text()
    type_match = re.search(r"Type Code:\s*([A-Z0-9]+)", text)
    type_code = type_match.group(1) if type_match else "NOT_FOUND"
    
    series = "NOT_FOUND"
    series_select = soup.find("select", {"name": "series"})
    if series_select:
        selected_series = series_select.find("option", selected=True)
        if selected_series:
            series = selected_series.text.strip()

    prod_month = "NOT_FOUND"
    prod_select = soup.find("select", {"name": "prod"})
    if prod_select:
        selected_month = prod_select.find("option", selected=True)
        if selected_month:
            prod_month = selected_month.text.strip()

    return type_code, series.split("(")[0].strip(), prod_month

def get_data(serial):
    params = {"vin": serial}

    r = requests.get(
        BASE_URL,
        params=params,
        impersonate="chrome124",
        timeout=30
    )

    if r.status_code != 200:
        return f"HTTP_{r.status_code}", f"HTTP_{r.status_code}"

    return extract_data(r.text)

def main(vin_prefix, vin_start, vin_end, step, target_list):
    vin_dict = {}
    serials = generate_serials(vin_prefix, vin_start, vin_end, step)

    print(f"--- Scraping started. Estimated time: {str(timedelta(seconds=(vin_end-vin_start)/step*4.5)).split('.')[0]}")

    for serial in serials:
        #print(f"Checking {serial}")

        try:
            type_code, series, prod_month = get_data(serial)
            vin_dict[serial] = (type_code, series, prod_month)
            print(f"{serial} -> {type_code}, {series:12}, {prod_month}")
        except Exception as e:
            vin_dict[serial] = ("ERROR", "ERROR")
            print("Error:", e)

        time.sleep(random.uniform(3.0, 6.0))

    OUTPUT_FILE = f"{vin_prefix}{vin_start} - {vin_prefix}{vin_end}.txt"

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for serial, (type_code, series, prod_month) in vin_dict.items():
            f.write(f"{serial} - {type_code} - {series:12} - {prod_month}\n")

    print(f"\n===DONE===\nSaved VINs to {OUTPUT_FILE}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch Type Codes and Production Month from RealOEM for a specified VIN range.")
    parser.add_argument("prefix", type=str, help="VIN7 prefix, e.g., CC")
    parser.add_argument("start", type=int, help="VIN7 start range, e.g., 78000")
    parser.add_argument("end", type=int, help="VIN7 end range, e.g., 78345")
    parser.add_argument("--step", type=int, default=1, help="Step size (default 1, for precision recording, increase for exploratory use)")
    parser.add_argument("--targets", nargs="+", help="Model types to listen for (e.g. F06 F12 F13)")

    args = parser.parse_args()
    target_list = args.targets if args.targets else []
    main(args.prefix, args.start, args.end, args.step, target_list)