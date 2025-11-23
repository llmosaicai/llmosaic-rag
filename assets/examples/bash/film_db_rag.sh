#!/usr/bin/env bash
set -euo pipefail

: "${SCHEMA_NAME:=filmdata1}"

base() {
  if [[ -n "${PROXY_HOST:-}" ]]; then
    case "$PROXY_HOST" in
      http://*|https://*) echo "$PROXY_HOST" ;;
      *) echo "https://$PROXY_HOST" ;;
    esac
  else
    echo "http://postgrest:3000"
  fi
}

H=("-H" "Accept-Profile: ${SCHEMA_NAME}")
URL="$(base)/film?select=film_id,title,description&order=title.asc&limit=5"
echo "GET $URL"
curl -sS "${H[@]}" "$URL" | sed -n '1,200p'
echo
echo "OK"

