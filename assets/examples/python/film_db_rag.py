#!/usr/bin/env python3
import os
import sys
import json
from urllib.parse import urljoin

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

SCHEMA = os.getenv("SCHEMA_NAME", "filmdata1")
PROXY_HOST = (os.getenv("PROXY_HOST") or "").strip()

def base_url():
    if PROXY_HOST:
        scheme = "https" if "://" not in PROXY_HOST else PROXY_HOST.split("://")[0]
        host = PROXY_HOST.split("://")[-1]
        return f"{scheme}://{host}"
    # in-cluster fallback
    return "http://postgrest:3000"

def get(url: str):
    import requests
    h = {"Accept-Profile": SCHEMA}
    r = requests.get(url, headers=h, timeout=20)
    r.raise_for_status()
    return r.json()

def list_films(limit=5):
    url = base_url() + f"/film?select=film_id,title,description&order=title.asc&limit={limit}"
    return get(url)

def main():
    print(f"Using schema={SCHEMA}")
    print(f"Proxy base={base_url()}")
    try:
        rows = list_films(5)
        print(json.dumps(rows, indent=2)[:2000])
        print("\nOK: fetched films")
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(2)

if __name__ == "__main__":
    main()

