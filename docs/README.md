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
| 7 | [Lehrbezug DABA und BINT](07-lehrbezug.md) | An welchen Stellen knüpft welche Kurseinheit an? |
| 8 | [Entscheidungsjournal](08-entscheidungen.md) | Welche Alternativen gab es an den Weggabelungen, und warum fiel die Wahl so aus? |

Wer nur die Daten nutzen möchte, findet die vollständige Feldbeschreibung in [`../dataset/README.md`](../dataset/README.md).

## Kennzahlen des Datenbestands

| Merkmal | Wert |
|---------|------|
| Zeitraum | 15.03.2017 – 31.03.2026 |
| Bestellungen | 754.513 |
| Bestellpositionen | 2.950.082 |
| Kunden | 25.000 |
| Produkte | 57 |
| Filialen | 8 |
| Nettoumsatz | 14.522.378,70 € |
| Durchschnittlicher Bestellwert | 19,25 € |

Diese Werte sind mit `python dataset/verify_readme.py` nachprüfbar. Das Skript rechnet 79 Angaben der Datensatz-Dokumentation gegen die CSV-Dateien nach und endet mit Exit-Code 1, sobald eine Angabe abweicht.

## Aufbau des Repositorys

```
web/       index.html · pos.html · shop.html · dashboard.html
dataset/   13 CSV-Dateien (Git LFS) · generate_obt.py · verify_readme.py
           README.md · uebungsblatt.md · uebungsblatt.pdf
           erp_datenmodell.excalidraw
docs/      diese Dokumentation
```

## Prüfberichte

Die Dashboard-Kennzahlen wurden zweimal vollständig gegen die Quelldaten geprüft. Beide Berichte sind erhalten, weil ihre Abfolge selbst dokumentiert, wie Validierung in der Praxis abläuft:

- [Validierungsbericht vom 10.04.2026](validierung-dashboard-2026-04-10.md) — 42 geprüfte Werte, erste Durchsicht
- [Validierungsbericht vom 12.04.2026](validierung-dashboard-2026-04-12.md) — 185 geprüfte Werte, systematisch je Registerkarte

## Sprachliche Konventionen

Diese Dokumentation folgt dem Sprachleitfaden der Kursmaterialien: beschreibend statt wertend, Fachbegriffe bei Ersteinführung kurz erläutert, jede Behauptung mit Begründung oder Kontrollzahl. Vergleiche nennen das Kriterium, nach dem verglichen wird.

Für die Schemabezeichnungen gilt die Terminologie aus DABA: **Stern-Schema**, Faktentabelle, Dimensionstabelle, Kennzahlen, Attribute, Surrogatschlüssel, Granularität.
