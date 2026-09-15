# BurgerMetrics — technische Dokumentation

BurgerMetrics ist eine Lernumgebung für Business Intelligence und Datenbanken. Sie bildet den Datenfluss einer fiktiven Systemgastronomie-Kette vollständig ab: vom operativen Erfassungssystem über das analytische Datenmodell bis zum Bericht.

Diese Dokumentation richtet sich an zwei Lesergruppen. **Studierende** sollen nachvollziehen können, wie das Projekt konzipiert und umgesetzt wurde — nicht nur, was am Ende herauskam. **Lehrende** finden die Anschlussstellen an die Kurseinheiten und die Kontrollzahlen, gegen die sich Ergebnisse prüfen lassen.

## Lesepfad

Die Kapitel bauen aufeinander auf und folgen der Reihenfolge, in der das Projekt entstanden ist.

| # | Kapitel | Frage, die es beantwortet |
|---|---------|---------------------------|
| 1 | [Fachkonzept und Anforderungen](01-fachkonzept.md) | Welches Szenario wird abgebildet, und welche Fragen soll es beantwortbar machen? |
| 2 | [Datenmodell](02-datenmodell.md) | Wie kommt man vom operativen 3NF-Modell zum analytischen Galaxy-Schema? |
| 3 | [ETL-Strecke und Reproduzierbarkeit](03-etl.md) | Wie entstehen die Dateien, und wie stellt man sicher, dass sie reproduzierbar sind? |
| 4 | [Validierung](04-validierung.md) | Woher weiß man, dass die Zahlen stimmen? |
| 5 | [Anwendungsarchitektur](05-anwendungen.md) | Wie sind POS, Shop und Dashboard aufgebaut, und wie hängen sie zusammen? |
| 6 | [Betrieb und Auslieferung](06-betrieb.md) | Wie ist das Repository organisiert, und wie kommt die Anwendung ins Netz? |
| 7 | [Lehrbezug DABA, BINT und Datenbasierte Fallstudien](07-lehrbezug.md) | An welchen Stellen knüpft welche Kurseinheit an? |
| 8 | [Entscheidungsjournal](08-entscheidungen.md) | Welche Alternativen gab es an den Weggabelungen, und warum fiel die Wahl so aus? |

Wer nur die Daten nutzen möchte, findet die vollständige Feldbeschreibung in [`../dataset/README.md`](../dataset/README.md).

## Kennzahlen des Datenbestands

| Merkmal | Wert |
|---------|------|
| Zeitraum | 15.03.2017 – 31.03.2026 |
| Bestellungen | 754.513 |
| Bestellpositionen | 2.950.082 |
| Rezensionen | 10.000 |
| Kunden | 25.000 |
| Produkte | 57 |
| Filialen | 8 |
| Nettoumsatz | 14.522.378,70 € |
| Durchschnittlicher Bestellwert | 19,25 € |

Diese Werte sind mit `python dataset/verify_readme.py` nachprüfbar. Das Skript rechnet 79 Angaben der Datensatz-Dokumentation gegen die CSV-Dateien nach und endet mit Exit-Code 1, sobald eine Angabe abweicht.

## Aufbau des Repositorys

```
web/       index.html · pos.html · shop.html · dashboard.html · abgleich.html
           js/ · tests/ · lab/
dataset/   15 CSV-Dateien (Git LFS) · generate_obt.py · generate_reviews.py
           load_duckdb.py · verify_readme.py · wawi_mini.sql
           burgermetrics_mini.sql · wawi_zu_analytisch.sql · README.md
           uebungsblatt.md/.pdf · erp_datenmodell.excalidraw
db/        aufbau/ · betrieb/ · tests/ · lade_csv.py · materialisieren.py
           skript_ausfuehren.py
notebooks/ 00–08 · quellen/ · daten_extern/ · export/ · tests/
dash/      Dash-App (wird ausgeführt)
mcp/       MCP-Server (Betreiberzugang)
docs/      diese Dokumentation · sechs Prüfberichte
```

## Prüfberichte

Der Bericht und weitere Teile des Projekts wurden bislang sechsmal geprüft. Alle sechs Berichte sind erhalten, weil ihre Abfolge selbst dokumentiert, wie Validierung in der Praxis abläuft:

- [Validierungsbericht vom 10.04.2026](validierung-dashboard-2026-04-10.md) — 42 geprüfte Werte, erste Durchsicht
- [Validierungsbericht vom 12.04.2026](validierung-dashboard-2026-04-12.md) — 185 geprüfte Werte, systematisch je Registerkarte
- [Validierungsbericht vom 26.08.2026](validierung-dashboard-2026-08-26.md) — Vollprüfung aller 72 Karten und der Management Summary, fünf Korrekturen, Abschluss
- [Notebook-Abnahme vom 15.09.2026](validierung-notebooks-2026-09-15.md) — alle neun Notebooks ausgeführt
- [Nur-Lese-Zugang, Abnahme vom 15.09.2026](validierung-nur-lesezugang-2026-09-15.md) — Rechte der Rolle `studi_daba`
- [Repository-Prüfung vom 15.09.2026](validierung-repo-2026-09-15.md) — Prüfung des Bestands

## Sprachliche Konventionen

Diese Dokumentation folgt dem Sprachleitfaden der Kursmaterialien: beschreibend statt wertend, Fachbegriffe bei Ersteinführung kurz erläutert, jede Behauptung mit Begründung oder Kontrollzahl. Vergleiche nennen das Kriterium, nach dem verglichen wird.

Für die Schemabezeichnungen gilt die Terminologie aus DABA: **Stern-Schema**, Faktentabelle, Dimensionstabelle, Kennzahlen, Attribute, Surrogatschlüssel, Granularität.
