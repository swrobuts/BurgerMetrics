# Validierungsbericht — Vollprüfung und Abschluss, 26.08.2026

**Gegenstand:** alle 72 KPI-Karten der zwölf Registerkarten und alle 30 Kacheln der
Management Summary, jede unabhängig aus den Roh-CSV nachgerechnet (DuckDB 1.5.5).
**Ergebnis:** Nach fünf Korrekturen (Commit `3479f3c`) ist kein offener Befund mehr bekannt.

Dieser Bericht **schließt den Befund Nr. 7 des Berichts vom 12.04.2026** — mit einer
anderen Korrektur als dort empfohlen, siehe unten.

---

## Die fünf Korrekturen vom 26.08.2026 (alle Management Summary)

| # | vorher | nachher | Begründung |
|---|--------|---------|------------|
| 1 | „+22,1 % p.a. CAGR 2017–2025" | „+23,8 % p.a., CAGR 2019–2025 (ab dem ersten Jahr mit vier Filialen)" | 22,1 % ist mit keiner Basis reproduzierbar; geprüft wurden Netto- und Bruttoumsatz, Bestellungen, Umsatz je Filiale, alle Jahrespaare und ein log-linearer Trend über 109 Monatswerte. |
| 2 | „Filialexpansion (3 → 8 Standorte)" | „1 → 8 Standorte bis 2023" | 2017 war genau eine Filiale in Betrieb (Europastern); die achte eröffnete im März 2023. |
| 3 | „Q4 Peak … konsistent über alle Jahre" | „Q3 Peak … stärkstes Quartal in sieben von acht vollen Jahren" | Nur 2019 war Q4 das stärkste Quartal, 2018 und 2020–2025 durchgehend Q3. |
| 4 | „42 % aller Bestellungen enthalten genau 4 Positionen" | „Häufigster Wert: 3 verschiedene Artikel (20,7 %)" | Genau 4 verschiedene Artikel haben 18,0 % der Bestellungen, genau 4 Stück 17,0 %. Keine Lesart ergibt 42 %. |
| 5 | Lift-Kachel „2,38 · 2,10 · 2,03" | „3,29 · 2,73 · 2,28" | Die Kachel widersprach dem eigenen Data-Mining-Reiter. Auf Produktgruppen gerechnet ergäben sich 1,48 / 1,59 / 2,28 — auch das stützt die alten Werte nicht. |

### Warum nicht +41,2 %, wie am 12.04. empfohlen

Der Bericht vom 12.04.2026 empfahl, die CAGR-Kachel auf **+41,2 %** (Basis 2017→2025) zu
korrigieren. Diese Empfehlung ist **überholt**: 2017 ist ein Rumpfjahr (Start 15.03., eine
Filiale). Eine Wachstumsrate von dieser Basis aus misst überwiegend die Filialexpansion und
den Rumpfjahreseffekt, nicht das Geschäft. Gewählt wurde stattdessen **2019→2025 (+23,8 %)**
— das erste Jahr mit vier Filialen als Basis, auf der Kachel ausgewiesen.

---

## Bestätigte Werte, deren Definition nicht offensichtlich ist

Diese Werte sahen zunächst falsch aus und sind korrekt — die Definition gehört dazu:

| Wert | Definition, mit der er sich reproduziert |
|------|------------------------------------------|
| Kumuliert „↑ 1.478 %" | Jahresumsatz 2025 gegen Jahresumsatz 2017 (1.479 % exakt) |
| „Unter 35 Jahre: 55 % / 13.746" | einschließlich der Gruppe <18 (2.034 + 5.392 + 6.320) |
| Veggie-Anteil „50,8 %, von 8,9 %" | Mengenanteil vegetarisch/vegan **nur innerhalb der Kategorie Burger**, 2026 gegen 2017 |
| Simulation „Marge 70,4 % / DB 5,94" | Kosten je Jahr **linear interpoliert** zwischen `cost_price_2017` und `cost_price` |
| „r = −0,48" (Wartezeit ↔ Zufriedenheit) | Korrelation auf **Filialmittelwerten** (r = −0,475); je Bestellung −0,061 |
| „Ab 10+ Min. → Ø 3,69" | Bestellungen mit Dauer **> 10** Minuten |
| „5,9 % App" (Personal) | kumulierter Kanalanteil 2017–2026 (44.454/754.513), nicht der 2025er-Anteil (10,6 %) |
| Kohorte „2023: 3.494" | nach `dim_customer.first_visit_year`, nicht nach erster Bestellung in `fact_orders` |
| „Ø Retention 99,4 %" | Folgejahr-Retention je Kohorte, gewichtet über alle Kunden, volle Jahre (99,39 %) |
| „Extremwert-Bin −15…−10 °C: €8.899" | genau **ein** Tag im Bestand — die Kachel nennt das selbst einen Sondereffekt |

## Nicht unabhängig prüfbar (kein Befund, aber gekennzeichnet)

- **RFM-Segmentgrößen und -kennzahlen:** in sich konsistent (Summe exakt 24.992 = Kunden
  mit Bestellung), aber ohne die Segmentierungsregeln nicht unabhängig herleitbar.
- **Mietquoten (2,4 % / 6,4 %)** und **Promo-ROI (11,5× / 3,0×):** Miet- und
  Aktionskostendaten sind nicht Teil des veröffentlichten Bestands.

## Grenzfälle, bewusst nicht geändert

- „Wärmste Tage +43 % vs. Ø": nachgerechnet +41,3 % (6.210/4.395). Größenordnung stimmt.
- „Kälteste Tage: 25 Tage / Ø 3.854 / 196": je nach Schwellen-Lesart 25–28 Tage,
  Ø 3.917–4.048. Vermutlich eine leicht andere Tageszuordnung der Temperatur.
- „Counter ↓ von 61,6 %": Basis ist der Höchststand 2018; die Drive-Through-Kachel daneben
  nutzt 2017 als Basis. Inkonsistente Basiswahl, aber beide Zahlen sind korrekt.
- „Kohorten-Retention 98–100 %": die 2017er-Kohorte liegt bei 97,7 %.

**Methodik:** wie in den Vorberichten — jede Zahl unabhängig aus `dataset/*.csv` berechnet,
Definitionen vor dem Vergleich festgehalten, Reproduktionswege in diesem Bericht genannt.
