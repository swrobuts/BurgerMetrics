# Abschlussprüfung von Repository und Labs · 15.09.2026

Ausgangspunkt: GitHub `main` und lokales `bm-analyse` auf
`de26778e74bd126a2edb097f539bcb56a9323d1e` (einschließlich aller acht Labs).

## Gefundene und behobene Fehler

1. **Lab-Prüfung unter Windows:** Der dynamische Import von PGlite erhielt einen
   Windows-Dateipfad statt einer Modul-URL. `verify.mjs` scheiterte deshalb sechsmal
   mit `Received protocol 'c:'`. Der Import verwendet jetzt eine relative Datei-URL.
2. **Zurücksetzen der Browser-Datenbank:** Ein gültiger Schema-Name mit einem
   Anführungszeichen führte zu einem Syntaxfehler beim Reset. Beispiel:
   `CREATE SCHEMA "Probe""Schema"`. Bezeichner werden korrekt maskiert;
   nach einem Startfehler bleibt der Wiederholungsversuch erreichbar.
3. **Überlappende SQL-Aufträge:** Eine zweite Übungsprüfung konnte zwischen dem
   Tabellenaufbau und der Kontrollabfrage einer ersten Prüfung deren Tabelle
   löschen (`relation "t1" does not exist`). Eine gemeinsame Warteschlange führt
   vollständige Prüfungen, freie Abfragen und Resets nacheinander aus.
4. **Abweichende Ergebnisprüfung:** Der lokale Abnahmelauf verband Spalten ohne
   Trennzeichen: `['ab', 'c']` und `['a', 'bc']` galten als gleich. Browser und
   Abnahmelauf verwenden jetzt denselben Vergleich mit erhaltenen Spaltengrenzen.
   Auch NULL, JSON-Inhalte und unterschiedliche Uhrzeiten bleiben unterscheidbar.
   Die Musterlösung wird bei einer Prüfung nur einmal ausgeführt.
5. **Lokale TLS-Konfiguration:** In der nicht versionierten `.env` stand
   `PGSSLROOTCERT=/etc/ssl/cert.pem`, ein auf diesem Windows-Rechner ungültiger
   Pfad. Er wurde lokal auf `system` geändert. Zertifikatskette und Hostname werden
   weiterhin mit `verify-full` geprüft. Der anschließende Live-MCP-Selbsttest bestand.

## Automatische Prüfungen

| Prüfung | Ergebnis |
|---|---|
| Dataset-, Notebook-, Dash- und Materialisierungs-Tests | 46 bestanden |
| DB-/MCP-Sicherheitsprüfung mit PostgreSQL 17.5, einschließlich Materialisierung | 35 bestanden |
| Darin separat gestartete ACL-Regressionsprüfung | 13 bestanden |
| Website-Tests unter Node | 19 bestanden |
| Neue Lab-Regressionstests unter Node/PGlite | 4 bestanden |
| Struktur, Inhalte und Lösungen aller acht Labs | 782 Zusicherungen, 0 Fehler |
| Eingebettetes JavaScript aller 14 HTML-Seiten | 0 Syntaxfehler |

Die vier Materialisierungsfälle sind in beiden Python-Läufen enthalten. Die
DB-Sicherheitstests liefen auf einer neu angelegten, ausschließlich lokal
erreichbaren Testinstanz mit eigenem Testzertifikat und synthetischen Stammdaten.
Geprüft wurden unter anderem Zertifikatsprüfung, direkte Leserollen-Anmeldung,
Transaktionsumgehungen, Bestellquoten bei wechselnden bzw. fehlenden Sitzungen,
acht gleichzeitige Bestellversuche am letzten freien Platz und idempotente Migration.

## Browserprüfung der Labs

Alle acht Lab-Seiten gestartet; die Übungen wurden vollständig aufgebaut.
Alle sieben Übungsformen wurden bedient:

- SQL: falscher Starttext abgewiesen; alle vier Aufgaben in Lab 03 gelöst,
  einschließlich `CREATE TABLE`, `CREATE VIEW` und Fan Trap.
- Quiz: richtige Antworten bewertet; Lab 03 erreicht 5/5 und behält den Stand
  nach einem Neuladen.
- Zuordnung und Checkliste: Bedienung und Fortschrittsanzeige in Lab 04 geprüft.
  Dies prüft die Lab-Oberfläche, nicht eine Installation von Power BI Desktop.
- Shelf: Umsatz je Filiale richtig; SUM der Bestell-ID abgewiesen, COUNT akzeptiert.
- Reihenfolge: falsche Folge in Lab 02 abgewiesen; korrekte Folge akzeptiert.
- JSON: Syntaxfehler und unterschiedlich lange Wetterlisten abgewiesen;
  Formatierung und vollständige Lösung in Lab 08 akzeptiert.
- Der zuvor fehlschlagende Reset nach einem Schema-Namen mit Anführungszeichen
  stellt den Miniaturbestand wieder her. Keine Konsolenfehler bei den geprüften
  normalen Abläufen.

Die vollständigen früheren Windows- und Colab-Läufe der neun umfangreichen
Notebooks sind in [Notebook-Prüfung](validierung-notebooks-2026-09-15.md) und
[Colab-/Dash-Prüfung](validierung-colab-dash-2026-09-15.md) dokumentiert.
In dieser Runde wurden ihre Regressionstests erneut ausgeführt.

## Erneute Live-Prüfung des Demo-Kontos

Anmeldung als `studi_daba`, Datenbank `postgres`, Suchpfad `wawi, burgermetrics`:

- **78 Objekte lesbar**, CSV-Export mit 1.000 Datensätzen erfolgreich.
- **754.513 Bestellungen**, Gesamtumsatz 14.522.378,70 €.
- Keine effektiven Schreibrechte auf Tabellen, Spalten, Sequenzen oder Schemata;
  keine CREATE-/TEMP-Rechte, keine Rollenmitgliedschaften, keine zusätzlichen
  Schreibwege über SECURITY-DEFINER-, net-, Large-Object- oder WAL-Funktionen.
- **Acht Schreibversuche in READ WRITE abgewiesen**, jeweils SQLSTATE `42501`;
  Prüftransaktionen zurückgerollt. Zugriff auf die andere Datenbank abgewiesen.
- TLS mit System-Vertrauensspeicher und vollständiger Zertifikatsprüfung erfolgreich.
- MCP-Selbsttest: beide Schemata lesbar, Schreiben über `abfragen()` abgewiesen,
  sieben Werkzeuge angemeldet. Der explizite Betreiber-Schreibweg bleibt getrennt.

## Abgleich

Die Änderungen gehören in GitHub `main` und den lokalen Repository-Unterordner
`BurgerMetrics_Website` unter `Datenbasierte Fallstudien/BurgerMetrics`.
Die `.env` bleibt lokal; veröffentlicht werden ausschließlich Quelltext,
Regressionstests und Dokumentation. Die bereits veröffentlichten Labs bleiben erhalten.
