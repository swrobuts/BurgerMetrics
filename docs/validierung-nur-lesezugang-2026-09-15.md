# Nur-Lese-Zugang: Abnahme am 15. September 2026

Ergebnis: **fixed**. Die Korrektur wurde auf der PostgreSQL-17-Instanz
eingespielt und mit einer frischen Anmeldung als `studi_daba` geprüft.
Das öffentliche Demo-Kennwort bleibt `thws`.

## Ursache und Korrektur

Über `PUBLIC` erhielt die Rolle außerhalb der Lehrdaten zusätzliche
Schreibrechte. `default_transaction_read_only` ließ sich abschalten;
zurückgerollte Proben bestätigten Tabellenänderungen, Large-Object-Erstellung
und temporäre Tabellen. Projektgrants allein schlossen diese Wege nicht.

`db/betrieb/studi_daba_lesend.sql` ersetzt betroffene bestehende PUBLIC-Grants
durch ausdrückliche Rechte für die anderen bestehenden Rollen und entzieht
der Studierendenrolle die effektiven Schreibrechte. Erfasst sind Tabellen,
Spaltengrants, Sequenzen, privilegierte Funktionen, Large-Object-/WAL-Funktionen,
Schemaerstellung, temporäre Tabellen und Zugänge zu anderen Datenbanken.
Neu angelegte Funktionen bekommen kein automatisches PUBLIC-Ausführungsrecht.
Vorhandene ausdrückliche Default-Grants bleiben erhalten.

Die Änderung braucht Superuser-Rechte und eine Transaktion. Die bisherigen
Berechtigungen wurden vor dem Einspielen lokal gesichert. Die Migration
entfernte 90 effektive Rechte und bestätigte 2.517 weiterhin gültige Rechte
anderer Rollen. Es wurden keine Nutzdaten verändert und keine laufenden
Studierendensitzungen getrennt, weil zum Zeitpunkt der Umstellung keine bestanden.

Die additive Rechtevergabe und die Wirkung globaler Default-Privileges sind
in der [PostgreSQL-Rechtedokumentation](https://www.postgresql.org/docs/17/ddl-priv.html)
und bei [ALTER DEFAULT PRIVILEGES](https://www.postgresql.org/docs/17/sql-alterdefaultprivileges.html)
beschrieben.

## Prüfungen

| Prüfung | Ergebnis |
|---|---|
| SQL-Migration in zurückgerollter Transaktion, einschließlich zweiter Ausführung | bestanden |
| `python -m pytest db/tests/test_studi_daba_lesend.py -q`, Superuser-DSN separat über `BM_READONLY_TEST_DSN` | 13 bestanden |
| `python -m pytest db/tests/test_materialisieren.py -q` | 4 bestanden |
| Unabhängige Prüfung der Änderung | Wechselwirkung bei neu angelegten Betreiberfunktionen gefunden, reproduziert, korrigiert und durch Regressionstest abgedeckt |
| Frische Anmeldung mit dem Demo-Zugang | erfolgreich, Suchpfad `wawi, burgermetrics` |
| Lesen aller Tabellen, Sichten und materialisierten Sichten des Projekts | 78 von 78 erfolgreich |
| CSV-Export | 1.000 Datenzeilen erfolgreich |
| Acht Schreibproben mit ausdrücklich schreibbarer Transaktion | jeweils SQLSTATE `42501`, fehlende Berechtigung |
| Tabellen-/Spaltenschreibrechte, Sequenzänderungen, Schema-CREATE, Datenbank-CREATE/TEMP, fremde Datenbankzugänge, privilegierte/net-Funktionen und LO-/WAL-Schreibfunktionen | jeweils 0 verbleibende Rechte |
| Verbindung zur zusätzlichen Systemdatenbank | durch Datenbankrechte abgewiesen |
| SQLAlchemy/pandas und dynamische Notebook-Abfragen | erfolgreich |
| Shop-Rollen `anon` und `authenticated` | Speisekarte lesbar, Bestell- und Rezensions-RPC weiterhin ausführbar |

Die Regressionstests prüfen zusätzlich einen vorbereiteten Funktionsaufruf,
Spaltengrants und einen Sequenzaufruf über die Objekt-ID. Sie verändern nur
synthetische Testobjekte innerhalb einer anschließend zurückgerollten Transaktion.
Der ursprüngliche Tabellen-Schreibweg und die Large-Object-Erstellung wurden
nach dem Commit erneut versucht und beide mit `42501` abgewiesen.

## Umfang und Betrieb

Geändert wurden das Betriebsskript, dessen Integrationstests, Hinweise in
`db/aufbau/0020_demo_rolle.sql`, `db/README.md` und dieser Bericht.
Die Anmeldung bleibt für Leseabfragen und Exporte nutzbar. BI-Werkzeuge dürfen
keine temporären Tabellen auf dem Server erwarten; gegebenenfalls Extrakte
oder CSV verwenden. Die lokalen PGlite-/DuckDB-Labs bleiben unabhängig davon.

Die Zusage betrifft Daten und die geprüften Schreibwege. PostgreSQL erlaubt
weiterhin eigene Sitzungseinstellungen und Kennwortänderungen. Nach neuen
Datenbanken, Erweiterungsupdates oder neuen PUBLIC-Grants erneut prüfen.
Ein vollständiger Durchlauf aller Notebooks und BI-Oberflächen war nicht Teil
dieser Rechtekorrektur; geprüft wurden deren Datenzugriffe und Treiberweg.
