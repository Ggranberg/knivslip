#!/usr/bin/env python3
"""Synka lokal data till Railway-servern (körs EN gång)."""

import json
import os
import sys
from urllib.request import Request, urlopen

# === ÄNDRA DENNA TILL DIN RAILWAY-URL ===
RAILWAY_URL = os.environ.get('RAILWAY_URL', '').strip('/')

if not RAILWAY_URL:
    print("Ange din Railway-URL:")
    print("  Exempel: https://knivslip-production-abc.up.railway.app")
    RAILWAY_URL = input("URL: ").strip().strip('/')

if not RAILWAY_URL.startswith('http'):
    RAILWAY_URL = 'https://' + RAILWAY_URL

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')

FILES_TO_SYNC = [
    'customers.json',
    'orders.json',
    'knives.json',
    'invoices.json',
    'transactions.json',
    'schedule.json',
    'timelog.json',
    'users.json',
]

def sync_file(filename):
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        print(f"  ⏭  {filename} — finns inte lokalt, hoppar over")
        return False

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    url = f"{RAILWAY_URL}/api/save/{filename}"
    body = json.dumps(data).encode('utf-8')

    req = Request(url, data=body, method='POST')
    req.add_header('Content-Type', 'application/json')

    try:
        resp = urlopen(req)
        result = json.loads(resp.read())
        if result.get('ok'):
            # Count items
            items = 0
            for key, val in data.items():
                if isinstance(val, list):
                    items = len(val)
                    break
            print(f"  ✅ {filename} — {items} poster synkade")
            return True
        else:
            print(f"  ❌ {filename} — servern svarade: {result}")
            return False
    except Exception as e:
        print(f"  ❌ {filename} — fel: {e}")
        return False

def main():
    print(f"\n  KNIVSLIP DATA-SYNC")
    print(f"  ══════════════════")
    print(f"  Fran: {DATA_DIR}")
    print(f"  Till: {RAILWAY_URL}")
    print()

    # Verify connection
    try:
        resp = urlopen(f"{RAILWAY_URL}/data/pricing.json")
        print("  ✅ Railway-servern svarar!\n")
    except Exception as e:
        print(f"  ❌ Kan inte na Railway-servern: {e}")
        print(f"     Kolla att URL:en stammer och att servern kor.")
        sys.exit(1)

    success = 0
    failed = 0
    for f in FILES_TO_SYNC:
        if sync_file(f):
            success += 1
        else:
            failed += 1

    print(f"\n  Klart! {success} filer synkade, {failed} misslyckades.\n")

if __name__ == '__main__':
    main()
