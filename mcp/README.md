# Die Datenbank als Werkzeugfläche für einen Agenten

Ein MCP-Server über die beiden Schemata `wawi` und `burgermetrics` auf
`supabase.butscher.cloud`. Er ist das Fenster des **Betreibers**: Er
meldet sich mit dem Konto aus der nicht versionierten `.env` an, demselben,
mit dem `lade_csv.py` und `materialisieren.py` arbeiten. Für Studierende
ist er nicht gedacht — die haben die Rolle `studi_daba` aus
[`../db/aufbau/0020_demo_rolle.sql`](../db/aufbau/0020_demo_rolle.sql) und
können sich damit einen eigenen Server bauen; dieser hier ist die Vorlage.

## Wo die Rechte liegen

Nicht hier. Der Server hat keine eigene Rechteprüfung; was das Konto in
der Datenbank darf, darf der Agent. Zwei Riegel gibt es trotzdem, beide
in der Datenbank statt im Programm:

* `abfragen()` läuft **immer** in einer nur lesenden Transaktion. Ein
  `UPDATE` darin weist PostgreSQL ab, nicht der Server.
* `ausfuehren()` ist der einzige Schreibweg: eine Transaktion je Aufruf,
  Commit nur ohne Fehler, und der Aufrufer muss einen Grund nennen. Wer
  den Server nur lesend betreiben will, setzt `BM_MCP_NUR_LESEN=1` in der
  Umgebung des Servers — dann meldet sich `ausfuehren()` gar nicht erst an.

## Einrichten

**1 · Zugangsdaten.** `.env` im Wurzelverzeichnis, wie in `.env.example`:
`PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`. Fehlt sie,
startet der Server nicht und sagt das.

**2 · Umgebung.** Der Server bekommt eine eigene, damit er die
Arbeitsumgebung nicht anfasst, in der noch anderes läuft:

```bash
bash mcp/einrichten.sh
```

Das legt `mcp/.venv` an (gitignored) und nennt am Ende den Python-Pfad,
der in die Konfiguration gehört.

**3 · Prüfen**, bevor irgendein Client ins Spiel kommt:

```bash
mcp/.venv/bin/python mcp/server.py --pruefen
```

Verbindet sich, zählt je eine Tabelle in beiden Schemata, prüft, dass
`abfragen()` Schreiben abweist, zählt die Werkzeuge.

**4 · Eintragen.** Claude Desktop, in
`~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "burgermetrics-db": {
      "command": "<Pfad>/BurgerMetrics_Website/mcp/.venv/bin/python",
      "args": ["<Pfad>/BurgerMetrics_Website/mcp/server.py"]
    }
  }
}
```

Nur lesend: dazu `"env": {"BM_MCP_NUR_LESEN": "1"}` in den Eintrag.
Claude Desktop danach neu starten; `serverstand` sagt, ob der laufende
Prozess noch die Datei auf der Platte ist.

Claude Code nimmt denselben Server:

```bash
claude mcp add burgermetrics-db -- <Pfad>/mcp/.venv/bin/python <Pfad>/mcp/server.py
```

## Die Werkzeuge

| Lesen | |
|---|---|
| `schemata_erklaeren` | was `wawi` und `burgermetrics` sind und wie sie zusammenhängen |
| `tabellen_auflisten` | Tabellen, Sichten, materialisierte Sichten mit Zeilenzahl und Kommentar |
| `tabelle_beschreiben` | Spalten, Typen, Schlüssel, Fremdschlüssel — und wer auf die Tabelle verweist |
| `beziehungen_auflisten` | alle Fremdschlüssel eines Schemas: das Datenmodell als Liste |
| `abfragen` | SQL lesen, höchstens 500 Zeilen, nur lesende Transaktion |
| `serverstand` | Konto, Server, und ob der Prozess veraltet ist |

| Ändern | |
|---|---|
| `ausfuehren` | DDL, DML, Funktionsaufrufe — eine Transaktion, Commit nur ohne Fehler, mit Begründung |

Tabellen immer mit Schemapräfix nennen (`wawi.rechnung`,
`burgermetrics.fact_orders`): Das Betreiberkonto hat keinen Suchpfad auf
die Projektschemata, und `kunde`, `mitarbeiter`, `rechnung` und
`zahlungsart` gibt es auf der Instanz mehrfach.

## Was ein Studierender daraus macht

Denselben Server mit anderem Konto: `PGUSER=studi_daba`,
`PGPASSWORD=thws` in einer eigenen `.env`. Die Rolle ist nur lesend,
`ausfuehren()` liefe dann in den Satz der Datenbank — man kann es auch
gleich mit `BM_MCP_NUR_LESEN=1` abschalten.
