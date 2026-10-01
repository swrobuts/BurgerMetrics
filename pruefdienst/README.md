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
ssh vps 'cd /opt/bm-pruefdienst && docker compose restart'          # Neustart, ohne neue Umgebungsdateien
ssh vps 'cd /opt/bm-pruefdienst && docker compose down'             # anhalten
```

Einstellungen stehen in `docker-compose.yml`: `BM_PRUEF_STAPEL` (20), `BM_PRUEF_INTERVALL`
(30 Sekunden), `BM_JEV_TAGESLIMIT` (300 Anfragen je Tag). Über dem Limit hält der Dienst neue
Rezensionen mit dem Grund „Tageslimit erreicht“ zurück, ohne Jev zu fragen.

Fällt Jev aus, bleibt eine Rezension offen und wird nach fünf Minuten erneut versucht; nach dem
dritten Fehlversuch hält die Datenbank sie mit „Prüfung nicht möglich“ zurück. Im POS erscheinen
offene Rezensionen, die länger als fünf Minuten warten, mit einem Hinweis.

## Passwort und Schlüssel tauschen

`docker compose restart` liest `.env.db`, `.env.jev` und `docker-compose.yml` nicht neu ein. Jede
Änderung daran wirkt erst, wenn `deploy.sh` den Container mit `docker compose up -d` neu erstellt.

- **Passwort:** `python3 pruefdienst/passwort_setzen.py`, gleich danach `bash pruefdienst/deploy.sh`.
  Ein bloßer Neustart meldet den Dienst mit dem alten Passwort an; er scheitert dann in jeder Runde
  (`Datenbank: OperationalError` im Protokoll). Bricht `passwort_setzen.py` ab, nachdem es
  `.env.db` geschrieben hat, das Skript noch einmal laufen lassen.
- **Jev-Schlüssel:** den neuen Schlüssel in die `.env` im Repo-Stamm schreiben,
  `bash pruefdienst/deploy.sh`, im Protokoll prüfen, dass keine Zeile mit `fehler=HTTP 401`
  erscheint, und erst dann den alten Schlüssel bei TypeSafe sperren. Solange der Dienst mit einem
  gesperrten Schlüssel läuft, scheitert jede Prüfung; nach drei Fehlversuchen hält die Datenbank
  die Rezension mit „Prüfung nicht möglich“ für die Moderation zurück.

## Tests

```bash
python3 -m pytest pruefdienst/tests/test_dienst.py -q
bash db/tests/security_local.sh -q -k dienst_datenbank   # braucht Docker Desktop
```
