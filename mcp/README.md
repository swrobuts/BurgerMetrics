# Die Datenbank als Werkzeugfläche für einen Agenten

Ein MCP-Server über die beiden Schemata `wawi` und `burgermetrics` auf
`supabase.butscher.cloud`. Er ist das Fenster des **Betreibers**: Er
nutzt zum Schreiben das Betreiberkonto aus der nicht versionierten `.env`.
Für Lesezugriffe meldet er sich separat als `studi_daba` an. Dieselbe
Lesefunktion steht mit `BM_MCP_NUR_LESEN=1` auch ohne Betreiberzugang bereit.

## Wo die Rechte liegen

Die Schreibsperre liegt in den Datenbankrechten der Leserolle:

* `abfragen()` und Metadatenabfragen verwenden **immer** eine direkte Anmeldung
  als `studi_daba`. Der Server prüft `session_user` und `current_user` und lehnt
  andere Identitäten ab. Ein Pooler-Suffix im Anmeldenamen ist möglich.
  Die ACLs dieser Rolle sperren Schreiben auch nach `COMMIT; BEGIN READ WRITE`
  oder `RESET ROLE`. Die zusätzliche `READ ONLY`-Voreinstellung allein wäre
  keine Sicherheitsgrenze.
* `ausfuehren()` ist der einzige Schreibweg: eine Transaktion je Aufruf,
  Commit nur ohne Fehler, und der Aufrufer muss einen Grund nennen. Wer
  den Server nur lesend betreiben will, setzt `BM_MCP_NUR_LESEN=1` in der
  Umgebung des Servers — dann meldet sich `ausfuehren()` gar nicht erst an.

## Einrichten

**1 · Zugangsdaten.** `.env` im Wurzelverzeichnis, wie in `.env.example`:
`PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`. Im Nur-Lesen-Modus
sind `PGUSER` und `PGPASSWORD` nicht erforderlich.

Lesezugang: `BM_MCP_READ_USER=studi_daba`, `BM_MCP_READ_PASSWORD=thws`
(öffentliche Demo-Standardwerte). Vor Benutzung müssen **beide** Skripte
[`0020_demo_rolle.sql`](../db/aufbau/0020_demo_rolle.sql) und
[`studi_daba_lesend.sql`](../db/betrieb/studi_daba_lesend.sql) angewandt sein;
das zweite entfernt auch indirekte Schreibwege über `PUBLIC` und Funktionen.
Ein anderer Rollenname oder das Betreiberkonto ist kein Ersatz.

Alle Verbindungen erzwingen `sslmode=verify-full`: Das Serverzertifikat muss
zu `PGHOST` passen und vertrauenswürdig sein. Mit `PGSSLROOTCERT` die CA-Datei
angeben; ohne Angabe gilt die libpq-Standarddatei `~/.postgresql/root.crt`.
Die CA über einen vertrauenswürdigen Weg beziehen. Auch ein gesetztes
`PGSSLMODE=disable` schaltet diese Prüfung nicht ab. Ein Endpunkt ohne
geeignetes TLS-Zertifikat muss zuerst auf Betreiberseite eingerichtet werden.

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
| `abfragen` | SQL lesen, höchstens 500 Zeilen, eingeschränkte Datenbankrolle |
| `serverstand` | Konto, Server, und ob der Prozess veraltet ist |

| Ändern | |
|---|---|
| `ausfuehren` | DDL, DML, Funktionsaufrufe — eine Transaktion, Commit nur ohne Fehler, mit Begründung |

Tabellen immer mit Schemapräfix nennen (`wawi.rechnung`,
`burgermetrics.fact_orders`): Das Betreiberkonto hat keinen Suchpfad auf
die Projektschemata, und `kunde`, `mitarbeiter`, `rechnung` und
`zahlungsart` gibt es auf der Instanz mehrfach.

## Was ein Studierender daraus macht

Denselben Server mit `BM_MCP_NUR_LESEN=1`, dem Lesezugang und einer gültigen
CA-Konfiguration starten. Betreiberzugangsdaten sind dafür nicht nötig.
