#!/bin/sh
set -e

DATA_DIR="${MAVIS_DATA_DIR:-/data}"
mkdir -p "$DATA_DIR"

# Copia os JSON-semente para o volume persistente apenas se ainda não existirem.
# Depois disso, o app LOCAL mantém os dados atualizados via POST /api/publish.
if [ -d /seed ]; then
  for f in /seed/*.json; do
    [ -e "$f" ] || continue
    base="$(basename "$f")"
    if [ ! -f "$DATA_DIR/$base" ]; then
      cp "$f" "$DATA_DIR/$base"
    fi
  done
fi

exec uvicorn server:app --host 0.0.0.0 --port 8001
