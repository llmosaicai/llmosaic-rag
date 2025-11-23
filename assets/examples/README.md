# RAG Examples (Python, Bash, JavaScript)

This directory contains runnable examples for the Film DB RAG stack from the dev-host.

Environment variables (set in your dev-host shell):

- PROXY_HOST: FQDN for your tenant PostgREST-Proxy (from your profile). Example: `postgrest.<tenant-host>`
- SCHEMA_NAME: Target schema (e.g., `filmdata1`).

Optional (for in-cluster access): if `PROXY_HOST` is not set, examples will attempt to connect to the in-cluster Service `http://postgrest:3000` with `Accept-Profile: $SCHEMA_NAME`.

## Python

Create a venv and install deps:

```
cd assets/examples/python
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
SCHEMA_NAME=filmdata1 PROXY_HOST=postgrest-proxy.your-tenant.example.com python film_db_rag.py
```

## Bash

```
cd assets/examples/bash
SCHEMA_NAME=filmdata1 PROXY_HOST=postgrest-proxy.your-tenant.example.com bash film_db_rag.sh
```

## JavaScript (Node.js)

Node.js (v20) is preinstalled on dev-host via NVM. From the dev-host:

```
cd assets/examples/js
node film_db_rag.mjs
# or with envs
SCHEMA_NAME=filmdata1 PROXY_HOST=postgrest-proxy.your-tenant.example.com node film_db_rag.mjs
```

