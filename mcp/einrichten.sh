#!/usr/bin/env bash
# =====================================================================
# Die virtuelle Umgebung des MCP-Servers anlegen
#
# Eigen und nicht global: 'mcp' zieht pydantic nach, und eine angehobene
# pydantic-Version hat in der allgemeinen Umgebung schon einmal andere
# Programme zerlegt. Ein Lehrprojekt darf die Arbeitsumgebung nicht
# anfassen, in der noch anderes laeuft.
#
# Aufruf: bash mcp/einrichten.sh
# =====================================================================
set -euo pipefail
HIER="$(cd "$(dirname "$0")" && pwd)"

python3 -m venv "$HIER/.venv"
"$HIER/.venv/bin/pip" install --quiet --upgrade pip
"$HIER/.venv/bin/pip" install --quiet -r "$HIER/requirements.txt"

echo "Umgebung steht: $HIER/.venv"
"$HIER/.venv/bin/pip" list 2>/dev/null | grep -iE '^(mcp|psycopg2-binary) ' | sed 's/^/  /'
echo
echo "Selbsttest:  $HIER/.venv/bin/python $HIER/server.py --pruefen"
echo
echo "In claude_desktop_config.json gehoert genau dieser Python:"
echo "  \"command\": \"$HIER/.venv/bin/python\","
echo "  \"args\": [\"$HIER/server.py\"]"
