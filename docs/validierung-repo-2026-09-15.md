# Repository-Prüfung vom 15. September 2026

Ausgangspunkt: `main` bei `228d9f873cc4229c528f8b859078cbded3bca478`.
Geprüft wurden die Webanwendungen samt PostgREST-Adapter, die Dataset-Tests,
der DuckDB-Import, die Dash-App, die Materialisierung und die gespeicherten
Notebook-Ausgaben.

## Behobene Fehler

| Bereich | Fehler und Auswirkung | Korrektur |
|---|---|---|
| Datentypen im Webadapter | Numerischer Text wurde ungefragt in Zahlen verwandelt: `007` wurde zu `7`, `01067` zu `1067`; eine RPC-Antwort `null` löste einen TypeError aus. | Die JSON-Datentypen der API bleiben erhalten. |
| Wetterdaten | Der Adapter wertete nur die erste Antwort aus. Bei einem Serverlimit unterhalb der Zahl der Betriebstage wurden Diagramm und Mittelwerte aus einem Ausschnitt berechnet. | Nachladen anhand von Offset und exaktem Content-Range bis zum vollständigen Ergebnis; erst dann cachen. |
| Rezensionen | JavaScript zählte Emojis doppelt. Drei Emojis bestanden die Mindestlänge, 500 Emojis wurden abgewiesen. Zusätzlich begrenzte das HTML-Feld die rohe UTF-16-Länge vor der Normalisierung. | Zählen nach Unicode-Codepunkten; das Formular benutzt denselben normalisierten Zähler und dieselbe Prüfung. |
| DuckDB-Import | Eine bestehende Datenbank wurde vor dem Laden gelöscht, einschließlich eigener Übungstabellen. Abweichende Zeilenzahlen endeten trotzdem mit Erfolg. | Nur die Datensatztabellen werden ersetzt, in einer gemeinsamen Transaktion. Ein Lese- oder Mengenfehler führt zu Rollback und Fehlerstatus. |
| Materialisierung | Autocommit bestätigte jeden einzelnen DROP, CREATE und REFRESH. Ein späterer Fehler konnte bereits gelöschte Sichten oder gemischte Datenstände hinterlassen. | Eine Transaktion für den gesamten Lauf, Rollback auch bei Abbruch und verlässliches Schließen der Verbindung. |

Die neuen Regressionstests reproduzierten die jeweiligen Fehler vor der
Korrektur. Die Live-Instanz lieferte bereits vor der Korrektur alle 3.304
Wettertage; der Nachladetest bildet ausdrücklich ein kleineres Serverlimit ab.

## Prüfung

- 32 Dataset-Tests bestanden: einschließlich Mini-ETL, Rezensionsgenerator,
  Glättung sowie Import und Erhalt eigener Tabellen mit echten temporären
  DuckDB-Datenbanken.
- 5 Dash-Integrationstests gegen das lesende Demo-Konto bestanden.
- 4 Transaktionstests der Materialisierung bestanden: Neuaufbau und Refresh,
  jeweils mit Erfolg und simuliertem Fehler beim zweiten Objekt. Diese Tests
  verwenden eine simulierte Verbindung, keinen produktiven Schema-Umbau.
- 19 Webtests bestanden: lokale Regressionstests und bestehende API-Tests.
- Vollständiger Import aller 14 Tabellen in eine neue lokale Prüfdatei
  erfolgreich, darunter 754.513 Bestellungen und 2.950.082 Bestellpositionen.
- Alle fünf HTML-Seiten ohne JavaScript-Syntaxfehler; 33 Python-Dateien
  syntaktisch gültig.
- Alle neun gespeicherten Notebooks mit ausgeführten Codezellen,
  Pflichtabschnitten und ohne gespeicherte Fehlerausgabe; keine Neuausführung.
- Live-Abfrage aller 34 Dashboard-Sichten erfolgreich.
- Browserprüfung: Wetteransicht zeigt 3.304 Betriebstage; 500 Emojis ergeben
  `500 / 500`, drei Emojis werden vor dem Absenden abgewiesen. Keine
  Konsolenfehler in den geprüften Shop- und Dashboard-Ansichten.

## Technische Grundlagen

Die Paginierung folgt [PostgREST: Pagination and Count](https://docs.postgrest.org/en/stable/references/api/pagination_count.html).
Die Zeichenzählung richtet sich nach [PostgreSQL: char_length](https://www.postgresql.org/docs/current/functions-string.html).
