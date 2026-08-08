#!/usr/bin/env bash
# Pin and download the Tranco top-10k corpus. Records the list ID and full
# configuration so the corpus is exactly reproducible.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p data

meta="$(curl -sS --max-time 30 https://tranco-list.eu/api/lists/date/latest)"
list_id="$(printf '%s' "$meta" | python3 -c 'import json,sys; print(json.load(sys.stdin)["list_id"])')"

curl -sS --max-time 120 "https://tranco-list.eu/download/${list_id}/10000" -o data/corpus-top10k.csv
printf '%s\n' "$meta" > data/tranco-list-meta.json

lines="$(wc -l < data/corpus-top10k.csv)"
echo "Pinned Tranco list ${list_id}: ${lines} domains in data/corpus-top10k.csv"
