#!/usr/bin/env python3
import os, sys, json, yaml

# Minimal notebook generator (no nbformat dependency)

SETUP_CODE = r"""
import os, json, requests
from pathlib import Path

# Optionally load .env written by initContainer into /home/jovyan/work/.rag/.env
envfile = Path('/home/jovyan/work/.rag/.env')
if envfile.exists():
    for line in envfile.read_text().splitlines():
        if '=' in line and not line.strip().startswith('#'):
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

PROXY_HOST = os.environ.get('PROXY_HOST', '')
PROXY_BASE = os.environ.get('PROXY_BASE') or (f"https://{PROXY_HOST}" if PROXY_HOST else '')
SCHEMA_NAME = os.environ.get('SCHEMA_NAME', 'public')

USER_EMAIL = os.environ.get('USER_EMAIL', '')
STORAGE_ACCESS_KEY_ID = os.environ.get('STORAGE_ACCESS_KEY_ID', '')
STORAGE_SECRET_ACCESS_KEY = os.environ.get('STORAGE_SECRET_ACCESS_KEY', '')

LLMAPI_BASE = os.environ.get('LLMAPI_BASE', 'https://llmapi6.llmosaic.ai')
LLMAPI_MODEL_NAMES = os.environ.get('LLMAPI_MODEL_NAMES', '')
LLMAPI_COMPLETION_MODEL = os.environ.get('LLMAPI_COMPLETION_MODEL', (LLMAPI_MODEL_NAMES.split(',')[0] if LLMAPI_MODEL_NAMES else 'gpt-oss-120b'))
LLMAPI_EMBED_MODEL = os.environ.get('LLMAPI_EMBED_MODEL', 'titan-embed-text-v2')
LLMAPI_VECTOR_DIMENSION = int(os.environ.get('LLMAPI_VECTOR_DIMENSION', '1024'))
LLM_NAME = LLMAPI_COMPLETION_MODEL
EMBED_NAME = LLMAPI_EMBED_MODEL

assert PROXY_BASE, 'Set PROXY_BASE or PROXY_HOST in env/.env'

AUTH_BEARER = f"{STORAGE_ACCESS_KEY_ID}:{STORAGE_SECRET_ACCESS_KEY}:storage" if STORAGE_ACCESS_KEY_ID and STORAGE_SECRET_ACCESS_KEY else ''
PROXY_HEADERS = {'Authorization': f'Bearer {AUTH_BEARER}'} if AUTH_BEARER else {}
LLM_HEADERS = {
    'Authorization': f"Bearer {os.environ.get('LLMAPI_API_KEY', '')}",
    'Content-Type': 'application/json'
}
_embed_key = (os.environ.get('LLMAPI_EMBED_KEY') or os.environ.get('LLMAPI_API_KEY') or '')
EMBED_HEADERS = {
    'Authorization': f"Bearer {_embed_key}",
    'Content-Type': 'application/json'
}
print('Embed token present:', bool(_embed_key))

print('Using PROXY_BASE=', PROXY_BASE)
print('Using SCHEMA_NAME=', SCHEMA_NAME)
"""

def md(text):
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": text.strip().splitlines(True),
    }

def code(text):
    return {
        "cell_type": "code",
        "metadata": {},
        "source": text.strip().splitlines(True),
        "outputs": [],
        "execution_count": None,
    }

def step_code(step):
    act = (step.get('action') or '').lower()
    p = step.get('params') or {}
    endpoint = step.get('endpoint') or ''
    title = step.get('title') or step.get('id')

    if act == 'http_get':
        hdr = "PROXY_HEADERS" if ('health' in endpoint or '/artifacts' in endpoint) else "dict(**PROXY_HEADERS, **{'Accept-Profile': SCHEMA_NAME})"
        return ("""
url = PROXY_BASE + "{endpoint}"
r = requests.get(url, headers={hdr})
print(r.status_code)
print(r.text[:2000])
"""
        ).format(endpoint=endpoint, hdr=hdr)

    if act == 'restore_backup':
        # Upload an SQL backup file to the proxy restore-backup endpoint and poll for completion
        path = p.get('path', '/home/jovyan/work/examples/film_db_backup.sql')
        return ("""
path = "{path}"
url = PROXY_BASE + "/restore-backup?schemaName=" + SCHEMA_NAME
with open(path, 'rb') as fh:
    files = {{'backup_file': ('film_db_backup.sql', fh, 'application/sql')}}
    r = requests.post(url, headers=PROXY_HEADERS, files=files)
print(r.status_code)
print(r.text[:2000])
try:
    jr = r.json()
except Exception:
    jr = {{}}
# If job was accepted (async), poll for artifact log readiness
if isinstance(jr, dict) and jr.get('status') == 'accepted' and jr.get('artifact_url'):
    import time
    artifact_url = PROXY_BASE + str(jr['artifact_url'])
    print('Polling for restore completion:', artifact_url)
    t0=time.time(); timeout=180; interval=3
    while True:
        rr = requests.get(artifact_url, headers=PROXY_HEADERS)
        if rr.status_code == 200:
            print('Restore log available (HTTP 200).')
            print(rr.text[-1000:])
            break
        if time.time()-t0 > timeout:
            print('Timed out waiting for restore completion log.')
            break
        time.sleep(interval)
"""
        ).format(path=path)

    if act == 'drop_table':
        table = p.get('table_name', 'items5')
        return ("""
url = PROXY_BASE + "/drop-table?schemaName=" + SCHEMA_NAME
body = {{"table_name": "{table}", "if_exists": True}}
r = requests.post(url, headers=dict(**PROXY_HEADERS, **{{'Content-Type':'application/json'}}), json=body)
print(r.status_code, r.text)
"""
        ).format(table=table)

    if act == 'create_table':
        table = p.get('table_name', 'items5')
        cols = json.dumps(p.get('columns', []))
        return ("""
url = PROXY_BASE + "/create-table?schemaName=" + SCHEMA_NAME
body = {{"table_name": "{table}", "not_exists": True, "columns": {cols}}}
r = requests.post(url, headers=dict(**PROXY_HEADERS, **{{'Content-Type':'application/json'}}), json=body)
print(r.status_code, r.text)
"""
        ).format(table=table, cols=cols)

    if act == 'create_vector_index':
        table = p.get('table_name', 'items5')
        vec_col = p.get('vector_column', 'embedding')
        idx_type = p.get('index_type', 'hnsw')
        dist_op = p.get('distance_operator', 'vector_cosine_ops')
        return ("""
url = PROXY_BASE + "/create-vector-index?schemaName=" + SCHEMA_NAME
body = {{"table_name": "{table}", "vector_column": "{vec_col}", "index_type": "{idx_type}", "distance_operator": "{dist_op}"}}
r = requests.post(url, headers=dict(**PROXY_HEADERS, **{{'Content-Type':'application/json'}}), json=body)
print(r.status_code, r.text)
"""
        ).format(table=table, vec_col=vec_col, idx_type=idx_type, dist_op=dist_op)

    if act == 'embed_and_insert':
        table = p.get('table_name', 'items5')
        texts = p.get('texts', ["Hello world"])  # demo texts
        return ("""
texts = {texts}
for t in texts:
    er = requests.post(LLMAPI_BASE + "/" + EMBED_NAME + "/v1/embeddings", headers=EMBED_HEADERS, json={{"model": EMBED_NAME, "input": [t]}})
    if er.status_code != 200:
        print('embed error', er.status_code, er.text[:500])
        continue
    try:
        ej = er.json()
    except Exception as e:
        print('embed parse error', str(e), er.text[:500])
        continue
    vec = (ej.get('data') or [{{}}])[0].get('embedding')
    ir = requests.post(PROXY_BASE + "/{table}", headers=dict(**PROXY_HEADERS, **{{'Content-Type':'application/json', 'Content-Profile': SCHEMA_NAME}}), json={{"text": t, "embedding": vec}})
    print('insert', ir.status_code)
"""
        ).format(texts=json.dumps(p.get('texts', [])), table=table)

    if act == 'embed_and_insert_films':
        table = p.get('table_name', 'film_embeddings')
        return ("""
assert 'FILM_DOCS' in globals(), "Run 'Prepare Film Texts' step first"
for i, t in enumerate(FILM_DOCS):
    fid = (FILM_IDS[i] if 'FILM_IDS' in globals() and i < len(FILM_IDS) else i+1)
    er = requests.post(LLMAPI_BASE + "/" + EMBED_NAME + "/v1/embeddings", headers=EMBED_HEADERS, json={{"model": EMBED_NAME, "input": [t]}})
    if er.status_code != 200:
        print('embed error', er.status_code, er.text[:500])
        continue
    try:
        ej = er.json()
    except Exception as e:
        print('embed parse error', str(e), er.text[:500])
        continue
    vec = (ej.get('data') or [{{}}])[0].get('embedding')
    ir = requests.post(PROXY_BASE + "/{table}", headers=dict(**PROXY_HEADERS, **{{'Content-Type':'application/json', 'Content-Profile': SCHEMA_NAME}}), json={{"film_id": fid, "document_text": t, "embedding": vec}})
    print('insert', fid, ir.status_code)
"""
        ).format(table=table)

    if act == 'vector_query':
        table = p.get('table_name', 'items5')
        qtext = p.get('query_text', '')
        lim = int(p.get('limit', 1))
        return ("""
er = requests.post(LLMAPI_BASE + "/" + EMBED_NAME + "/v1/embeddings", headers=EMBED_HEADERS, json={{"model": EMBED_NAME, "input": ["{qtext}"]}})
if er.status_code != 200:
    print('embed error', er.status_code, er.text[:500])
try:
    ej = er.json(); vec = (ej.get('data') or [{{}}])[0].get('embedding')
except Exception as e:
    print('embed parse error', str(e), er.text[:500]); vec = None
if not vec:
    print('no embedding vector produced; check tokens and model name'); vec = []
encoded = requests.utils.quote(json.dumps(vec))
qr = requests.get(PROXY_BASE + "/{table}?query_vector=" + encoded + "&vector_column=embedding&distance_operator=<=>&limit={lim}", headers=dict(**PROXY_HEADERS, **{{'Accept-Profile': SCHEMA_NAME}}))
print(qr.status_code)
print(qr.text)
try:
    LAST_RESULTS = qr.json()
except Exception:
    LAST_RESULTS = []
"""
        ).format(table=table, qtext=qtext.replace('"', '\"'), lim=lim)

    if act == 'chat_with_context':
        # Convert Jinja-style placeholders to Python format placeholders for safe substitution
        raw_tmpl = (p.get('template') or '')
        fmt_tmpl = raw_tmpl.replace('{{', '{').replace('}}', '}')
        question = p.get('question', '')
        return ("""
ctx = ''
try:
    if isinstance(LAST_RESULTS, list) and LAST_RESULTS:
        first = LAST_RESULTS[0]
        ctx = first.get('data', {{}}).get('text') or first.get('document_text') or ''
except Exception:
    pass
template = {tmpl}
prompt = template.format(context=ctx, question={q})
cr = requests.post(LLMAPI_BASE + "/" + LLM_NAME + "/v1/chat/completions", headers=LLM_HEADERS, json={{"model": LLM_NAME, "messages": [{{"role": "user", "content": prompt}}], "max_tokens": 256, "temperature": 0.7}})
print(cr.status_code)
print(cr.text)
"""
        ).format(tmpl=json.dumps(fmt_tmpl), q=json.dumps(question))

    if act == 'http_get' and 'film_list' in endpoint:
        # handled by http_get + add capture
        pass

    return f"# TODO implement action: {act}"

def main():
    if len(sys.argv) < 3:
        print("Usage: gen_nb.py <spec.yaml> <out.ipynb>")
        sys.exit(2)
    spec_path, out_path = sys.argv[1], sys.argv[2]
    with open(spec_path, 'r') as fp:
        spec = yaml.safe_load(fp) or {}

    cells = []
    title = os.path.splitext(os.path.basename(out_path))[0].replace('_', ' ').title()
    cells.append(md(f"# {title}\n\nGenerated from spec: {os.path.basename(spec_path)}"))
    cells.append(code(SETUP_CODE))

    for s in spec.get('steps', []):
        heading = f"## {s.get('title') or s.get('id')}\n\n{(s.get('purpose') or '')}"
        cells.append(md(heading))
        # special capture for film_list
        if (s.get('action') == 'http_get') and isinstance(s.get('endpoint'), str) and 'film_list' in s['endpoint']:
            c = """
url = PROXY_BASE + "{endpoint}"
r = requests.get(url, headers=dict(**PROXY_HEADERS, **{{'Accept-Profile': SCHEMA_NAME}}))
print(r.status_code)
try:
    j = r.json()
    FILM_DOCS = [row.get('description', '') for row in (j or [])]
    FILM_IDS = [row.get('id') for row in (j or [])]
    print('prepared', len(FILM_DOCS), 'film docs')
except Exception as e:
    print('failed to parse film list:', e)
"""
            cells.append(code(c.format(endpoint=s['endpoint'])))
        else:
            cells.append(code(step_code(s)))

    nb = {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.11"}
        },
        "nbformat": 4,
        "nbformat_minor": 5
    }
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w') as fp:
        json.dump(nb, fp, indent=1)
    print('wrote', out_path)

if __name__ == '__main__':
    main()
