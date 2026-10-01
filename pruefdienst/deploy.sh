#!/usr/bin/env bash
# deploy.sh — bringt den Prüfdienst auf den VPS und startet ihn neu.
# Kopiert Paket und Dienst nach vps:/opt/bm-pruefdienst, schreibt den
# Jev-Schlüssel aus der lokalen .env nach .env.jev (Modus 600, über stdin,
# ohne Ausgabe) und baut den Container neu. .env.db legt passwort_setzen.py an.
set -euo pipefail
cd "$(dirname "$0")/.."
ziel=/opt/bm-pruefdienst

ssh vps "test -f $ziel/.env.db" || { echo ".env.db fehlt: erst python3 pruefdienst/passwort_setzen.py" >&2; exit 1; }

vorhanden=$(python3 -c 'import sys; sys.path.insert(0, "."); from bm_jev import jev, umgebung; umgebung.env_laden(); print(jev.api_schluessel() is not None)')
[ "$vorhanden" = "True" ] || { echo "TYPESAFE_API_KEY fehlt in der .env" >&2; exit 1; }

# Nur was der Container braucht: keine Tests, keine Daten.
tar -czf - bm_jev/__init__.py bm_jev/fragen.py bm_jev/muster.py bm_jev/regeln.py bm_jev/jev.py \
    bm_jev/datenbank.py pruefdienst/dienst.py pruefdienst/Dockerfile pruefdienst/requirements.txt \
    pruefdienst/docker-compose.yml \
  | ssh vps "mkdir -p $ziel && tar -xzf - -C $ziel && cp $ziel/pruefdienst/docker-compose.yml $ziel/docker-compose.yml"

# Der Schlüssel geht über stdin, nie über die Befehlszeile oder ins Terminal.
python3 -c 'import sys; sys.path.insert(0, "."); from bm_jev import jev, umgebung; umgebung.env_laden(); print("TYPESAFE_API_KEY=" + jev.api_schluessel())' \
  | ssh vps "umask 077 && cat > $ziel/.env.jev && chmod 600 $ziel/.env.jev"

ssh vps "cd $ziel && docker compose up -d --build && docker compose ps --format '{{.Name}} {{.State}}'"
