#!/usr/bin/env python3
import os, sys, json, yaml, requests

"""
Sync the stack config catalog (config/catalog.yaml) to the backend ConfigCatalog via API.

Env vars:
  BACKEND_API_BASE   e.g., https://backend.llmosaic.ai (without /api/v1)
  SYNC_EMAIL         Backend user email to obtain JWT (service account recommended)
  SYNC_PASSWORD      Backend user password
  CATALOG_PATH       Defaults to repos-local/llmosaic-rag/config/catalog.yaml
  STACK_KEY          Defaults to value in YAML or 'llmosaic-rag'

Usage:
  python tools/sync_catalog.py
"""

def main():
    base = os.environ.get('BACKEND_API_BASE', '').rstrip('/')
    email = os.environ.get('SYNC_EMAIL', '')
    password = os.environ.get('SYNC_PASSWORD', '')
    cat_path = os.environ.get('CATALOG_PATH', 'repos-local/llmosaic-rag/config/catalog.yaml')

    if not (base and email and password):
        print('ERROR: BACKEND_API_BASE, SYNC_EMAIL, and SYNC_PASSWORD are required', file=sys.stderr)
        sys.exit(2)

    with open(cat_path, 'r') as fp:
        y = yaml.safe_load(fp) or {}

    stack_key = os.environ.get('STACK_KEY') or (y.get('stack_key') or 'llmosaic-rag')
    version = int(y.get('version') or 1)
    description = y.get('description')
    catalog = y

    # Acquire JWT
    tok_url = f"{base}/api/v1/login/access-token"
    r = requests.post(tok_url, data={'username': email, 'password': password})
    r.raise_for_status()
    token = (r.json() or {}).get('access_token')
    if not token:
        print('ERROR: failed to obtain access token', file=sys.stderr)
        sys.exit(3)

    # Upsert catalog
    body = { 'stack_key': stack_key, 'version': version, 'description': description, 'catalog': catalog }
    api = f"{base}/api/v1/config/catalog"
    r2 = requests.post(api, headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}, data=json.dumps(body))
    if r2.status_code >= 300:
        print('ERROR:', r2.status_code, r2.text, file=sys.stderr)
        sys.exit(4)
    print('OK:', r2.status_code, r2.text[:2000])

if __name__ == '__main__':
    main()

