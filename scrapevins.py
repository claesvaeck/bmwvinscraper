from curl_cffi import requests
from bs4 import BeautifulSoup
import re
import time
import random
import argparse

BASE_URL = "https://www.realoem.com/bmw/enUS/select"

def generate_serials(prefix, start, end):
    return [f"{prefix}{str(i).zfill(5)}" for i in range(start, end + 1)]

def extract_data(html):
    soup = BeautifulSoup(html, "html.parser")

    text = soup.get_text()
    type_match = re.search(r"Type Code:\s*([A-Z0-9]+)", text)
    type_code = type_match.group(1) if type_match else "NOT_FOUND"

    prod_month = "NOT_FOUND"
    prod_select = soup.find("select", {"name": "prod"})
    if prod_select:
        selected_option = prod_select.find("option", selected=True)
        if selected_option:
            prod_month = selected_option.text.strip()

    return type_code, prod_month

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

def main(vin_prefix, vin_start, vin_end):
    vin_dict = {}
    serials = generate_serials(vin_prefix, vin_start, vin_end)

    for serial in serials:
        print(f"Checking {serial}")

        try:
            type_code, prod_month = get_data(serial)
            vin_dict[serial] = (type_code, prod_month)
            print(f"{serial} -> {type_code}, {prod_month}")
        except Exception as e:
            vin_dict[serial] = ("ERROR", "ERROR")
            print("Error:", e)

        time.sleep(random.uniform(3.0, 6.0))

    OUTPUT_FILE = f"VINs_{vin_dict[next(iter(vin_dict))][0]}.txt"

    with open(OUTPUT_FILE, "w") as f:
        for serial, (type_code, prod_month) in vin_dict.items():
            f.write(f"{serial} - {type_code} - {prod_month}\n")

    print(f"\n===DONE===\nSaved VINs to {OUTPUT_FILE}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch Type Codes and Production Month from RealOEM for a specified VIN range.")
    parser.add_argument("prefix", type=str, help="VIN prefix, e.g., CC")
    parser.add_argument("start", type=int, help="VIN start range, e.g., 78000")
    parser.add_argument("end", type=int, help="VIN end range, e.g., 78345")

    args = parser.parse_args()
    main(args.prefix, args.start, args.end)