import csv
import math
import requests
import sys
from collections import defaultdict
from typing import Dict, List

# Configuration
SERVER_URL = "http://127.0.0.1:8000/request_locates"
INPUT_FILE = "requests.csv"
OUTPUT_FILE = "approved_locates.csv"


def distribute_logic(requests_list: List[dict], approved_amount: int) -> Dict[str, int]:
    """
    Core Allocation Logic:
    Distributes approved amount among clients based on proportionality,
    while prioritizing 100-chunks to maximize utility.
    """
    total_requested = sum(r['amount'] for r in requests_list)

    # Guardrail for Zero Division
    if total_requested == 0:
        return {r['client']: 0 for r in requests_list}

    if approved_amount >= total_requested:
        return {r['client']: r['amount'] for r in requests_list}

    if approved_amount <= 0:
        return {r['client']: 0 for r in requests_list}

    client_data = []
    for r in requests_list:
        ratio = r['amount'] / total_requested
        raw_share = approved_amount * ratio
        client_data.append({
            'client': r['client'],
            'requested': r['amount'],
            'raw_share': raw_share,
            'allocated': 0
        })

    remaining = approved_amount

    # Step 1: Base Allocation (Floor to nearest 100 based on raw share)
    for c in client_data:
        base_100 = math.floor(c['raw_share'] / 100) * 100
        c['allocated'] = base_100
        remaining -= base_100

    # Step 2: Distribute extra 100-chunks if available
    while remaining >= 100:
        candidates = [c for c in client_data if c['allocated'] + 100 <= c['requested']]
        if not candidates:
            break

        # The winner is the client with the highest fractional remainder relative to 100
        winner = max(candidates, key=lambda x: x['raw_share'] % 100)
        winner['allocated'] += 100
        remaining -= 100

    # Step 3: Distribute the final "dust" (remainder < 100)
    # Prioritize clients who are furthest from their 'raw_share'
    if remaining > 0:
        candidates = [c for c in client_data if c['allocated'] < c['requested']]

        # Sort by "Deprivation": (Raw Share - Allocated).
        # Whoever is missing the most from their fair share gets the dust first.
        candidates.sort(key=lambda x: (x['raw_share'] - x['allocated']), reverse=True)

        for c in candidates:
            space_left = c['requested'] - c['allocated']
            to_give = min(remaining, space_left)

            c['allocated'] += to_give
            remaining -= to_give

            if remaining == 0:
                break

    return {c['client']: c['allocated'] for c in client_data}


def read_csv_safe(filepath):
    """Reads CSV safely, handling errors."""
    data = []
    try:
        with open(filepath, mode='r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for i, row in enumerate(reader, 1):
                if not row: continue
                if len(row) < 3: continue
                try:
                    client = row[0].strip()
                    symbol = row[1].strip()
                    amount = int(row[2].strip())
                    data.append((client, symbol, amount))
                except ValueError:
                    print(f"Warning: Invalid format line {i}")
    except FileNotFoundError:
        print(f"Error: File '{filepath}' not found.")
        sys.exit(1)
    return data


def main():
    # 1. Read Requests
    print(f"Reading requests from {INPUT_FILE}...")
    raw_data = read_csv_safe(INPUT_FILE)

    symbol_requests = defaultdict(list)
    aggregated_counts = defaultdict(int)

    for client, symbol, amount in raw_data:
        symbol_requests[symbol].append({'client': client, 'amount': amount})
        aggregated_counts[symbol] += amount

    if not aggregated_counts:
        print("No valid requests.")
        return

    # 2. Call Server
    print(f"Connecting to server at {SERVER_URL}...")
    try:
        response = requests.post(SERVER_URL, json=aggregated_counts)
        response.raise_for_status()
        approved_by_server = response.json()
    except requests.exceptions.ConnectionError:
        print("Error: Server is not running. Please run 'python server.py' in another terminal.")
        return
    except Exception as e:
        print(f"Error calling server: {e}")
        return

    # 3. Distribute & Save
    print("Calculating distribution...")
    try:
        with open(OUTPUT_FILE, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            for symbol, approved_total in approved_by_server.items():
                requests_for_sym = symbol_requests.get(symbol, [])
                allocations = distribute_logic(requests_for_sym, approved_total)

                for client, qty in allocations.items():
                    if qty > 0:
                        writer.writerow([client, symbol, qty])

        print(f"Success! Check '{OUTPUT_FILE}'")
    except IOError as e:
        print(f"File Error: {e}")


if __name__ == "__main__":
    main()