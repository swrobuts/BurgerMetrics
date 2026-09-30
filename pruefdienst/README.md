# Prüfdienst

Prüft neue Shop-Rezensionen mit Jev und trägt das Ergebnis in `wawi_intern.rezension_pruefung` ein
(Spezifikation `docs/superpowers/specs/2026-09-30-rezensionen-jev-freigabe-design.md`, Abschnitt 6).
Läuft als Container `bm-pruefdienst` auf dem VPS in `/opt/bm-pruefdienst`, im Docker-Netz
`root_default`, als Datenbankrolle `bm_pruefdienst` mit genau drei Funktionen.

## Einrichten und aktualisieren

```bash
python3 pruefdienst/passwort_setzen.py   # nur beim ersten Mal oder zum Tauschen des Passworts
bash pruefdienst/deploy.sh               # kopiert, schreibt .env.jev, baut und startet neu
```

`deploy.sh` braucht `TYPESAFE_API_KEY` in der `.env` im Repo-Stamm. Beide Umgebungsdateien auf
dem VPS (`.env.db`, `.env.jev`) haben Modus 600 und stehen in keinem Repo.

## Betrieb

```bash
ssh vps 'docker logs --tail 50 bm-pruefdienst'                     # Protokoll, ohne Texte
ssh vps 'cd /opt/bm-pruefdienst && docker compose restart'          # Neustart
ssh vps 'cd /opt/bm-pruefdienst && docker compose down'             # anhalten
```

Einstellungen stehen in `docker-compose.yml`: `BM_PRUEF_STAPEL` (20), `BM_PRUEF_INTERVALL`
(30 Sekunden), `BM_JEV_TAGESLIMIT` (300 Anfragen je Tag). Über dem Limit hält der Dienst neue
Rezensionen mit dem Grund „Tageslimit erreicht“ zurück, ohne Jev zu fragen.

Fällt Jev aus, bleibt eine Rezension offen und wird nach fünf Minuten erneut versucht; nach dem
dritten Fehlversuch hält die Datenbank sie mit „Prüfung nicht möglich“ zurück. Im POS erscheinen
offene Rezensionen, die länger als fünf Minuten warten, mit einem Hinweis.

## Tests

```bash
python3 -m pytest pruefdienst/tests/test_dienst.py -q
bash db/tests/security_local.sh -q -k dienst_datenbank   # braucht Docker Desktop
```
