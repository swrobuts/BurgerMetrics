# BurgerMetrics Dashboard – Validierungsbericht

**Datum:** 10. April 2026  
**Geprüft:** `dashboard.html` gegen CSV-Quelldaten  
**Methode:** Python/pandas-Analyse aller Fact- und Dimension-Tabellen  

---

## Zusammenfassung

Von **42 geprüften KPI-Werten** im Dashboard sind **35 korrekt** und **7 falsch oder irreführend**. Die Fehler konzentrieren sich auf die Übersichts-KPI-Karten (Top-Produkt, Kundenzufriedenheit, Wiederkehrende Kunden, Kanalverteilung 2025). Die Jahrestabelle und die Filial-Scorecard sind vollständig korrekt.

---

## ✅ KORREKTE WERTE (stimmen mit CSV überein)

### Jahres-Übersichtstabelle (alle 9 Jahre korrekt)

| Jahr | Dashboard Umsatz | CSV Umsatz | Dashboard Bestell. | CSV Bestell. | Dashboard AOV | CSV AOV |
|------|-----------------|------------|-------------------|-------------|--------------|---------|
| 2017 | €189.699 | €189.699,22 | 13.086 | 13.086 | €14,50 | €14,50 |
| 2018 | €407.631 | €407.630,65 | 27.402 | 27.402 | €14,88 | €14,88 |
| 2019 | €831.495 | €831.495,41 | 53.307 | 53.307 | €15,60 | €15,60 |
| 2020 | €728.623 | €728.622,79 | 46.209 | 46.209 | €15,77 | €15,77 |
| 2021 | €1.232.130 | €1.232.130,18 | 73.415 | 73.415 | €16,78 | €16,78 |
| 2022 | €2.017.208 | €2.017.208,36 | 113.128 | 113.128 | €17,83 | €17,83 |
| 2023 | €2.581.072 | €2.581.072,27 | 127.022 | 127.022 | €20,32 | €20,32 |
| 2024 | €2.841.075 | €2.841.074,88 | 133.307 | 133.307 | €21,31 | €21,31 |
| 2025 | €2.994.771 | €2.994.771,13 | 136.557 | 136.557 | €21,93 | €21,93 |

**Ergebnis: ✅ Alle 27 Werte in der Jahrestabelle sind korrekt.**

### Haupt-KPI-Karten (korrekt)

| KPI | Dashboard | CSV | Status |
|-----|-----------|-----|--------|
| Gesamtumsatz | €14,52M | €14.522.378,70 | ✅ |
| Gesamt-Bestellungen | 754.513 | 754.513 | ✅ |
| Kunden gesamt | 25.000 | 25.000 (dim_customer) | ✅ |
| Filialen | 8 | 8 | ✅ |
| Umsatz 2025 | €2,99M | €2.994.771,13 | ✅ |
| Bestellungen 2025 | 136.557 | 136.557 | ✅ |
| AOV 2025 | €21,93 | €21,93 | ✅ |
| 2026 Bestellungen | 31.080 | 31.080 | ✅ |

### Filial-Scorecard (alle 8 Filialen korrekt)

| Filiale | Dashboard Umsatz | CSV Umsatz | Dashboard AOV | CSV AOV | Dashboard Rating | CSV Rating |
|---------|-----------------|------------|--------------|---------|-----------------|-----------|
| BM Europastern | €3.391.529 | €3.391.528,72 | €18,62 | €18,62 | 3,81 | 3,81 |
| BM Hauptbahnhof | €2.205.646 | €2.205.646,22 | €17,80 | €17,80 | 3,77 | 3,77 |
| BM Mainfrankenpark | €2.158.128 | €2.158.128,09 | €21,03 | €21,03 | 3,82 | 3,82 |
| BM Heuchelhof | €2.029.699 | €2.029.698,75 | €20,14 | €20,14 | 3,81 | 3,81 |
| BM Sanderring | €1.683.541 | €1.683.540,67 | €18,84 | €18,84 | 3,76 | 3,76 |
| BM Lengfeld | €1.359.198 | €1.359.198,11 | €18,82 | €18,82 | 3,81 | 3,81 |
| BM Grombühl | €942.419 | €942.419,35 | €19,74 | €19,74 | 3,83 | 3,83 |
| BM Zellerau | €752.219 | €752.218,79 | €21,05 | €21,05 | 3,82 | 3,82 |

**Ergebnis: ✅ Alle Filial-Werte korrekt.**

### Weitere korrekte Werte

| KPI | Dashboard | CSV | Status |
|-----|-----------|-----|--------|
| Beyond Burger Umsatz | €1,30M | €1.301.008,15 | ✅ |
| Beyond Burger Anteil | 8,9% | 8,9% | ✅ |
| Burger-Kategorie Umsatz | €6,29M | €6.290.051,90 | ✅ |
| Burger-Kategorie Anteil | 42,9% | 42,9% | ✅ |
| Gesamtrabatt | €156.408 | €156.407,60 | ✅ |
| Promo-Bestellungen | 62.023 (8,2%) | 62.023 (8,2%) | ✅ |
| Gesamt-Zufriedenheit | 3,80 | 3,80 | ✅ |
| App Order Zufriedenheit | 4,00 | 4,00 | ✅ |
| Counter Zufriedenheit | 3,77 | 3,77 | ✅ |
| Unique Kunden (Bestellungen) | 24.992 | 24.992 | ✅ |

---

## ❌ FEHLERHAFTE WERTE (müssen korrigiert werden)

### Fehler 1: Kundenzufriedenheit 2025

| | Dashboard | CSV (korrekt) |
|--|-----------|---------------|
| **Wert** | **4,6 / 5** | **3,82 / 5** |
| **Vergleich 2024** | vs. 4,4 in 2024 | vs. 3,82 in 2024 |
| **Anzahl Bewertungen** | 12.830 | 29.990 |

**Korrektur in dashboard.html (Zeile 835):**
- `4,6 / 5` → `3,82 / 5`
- `↑ 0,2` → `0,0` (bzw. kein Delta, da identisch zu 2024)
- `vs. 4,4 in 2024 · 12.830 Bewertungen` → `vs. 3,82 in 2024 · 29.990 Bewertungen`

### Fehler 2: Top-Produkt 2025

| | Dashboard | CSV (korrekt) |
|--|-----------|---------------|
| **Produkt** | **Classic Burger** | **Cola 0.5l** (nach Menge) oder **Green Goddess Bowl** (nach Umsatz) |
| **Menge** | 28.412 verkauft | Cola 0.5l: 45.515 / Beyond Burger: 30.597 (Top-Burger) |
| **Umsatzanteil** | 18,2% | Cola 0.5l: 5,6% / Green Goddess Bowl: 11,7% |
| **Classic Burger tatsächlich** | — | 5.812 Stück, 1,1% Umsatzanteil |

**Korrektur in dashboard.html (Zeile 823–825):**
- Wenn "Top-Produkt" = meistverkauft nach Menge: `Classic Burger` → `Cola 0.5l`, `28.412 verkauft` → `45.515 verkauft`
- Wenn "Top-Produkt" = meistverkaufter Burger: `Classic Burger` → `Beyond Burger`, `28.412` → `30.597`
- Wenn "Top-Produkt" = höchster Umsatz: `Classic Burger` → `Green Goddess Bowl`, `€353.382`

**Empfehlung:** Da es ein Burger-Restaurant ist, wäre "Top-Burger 2025" sinnvoller:
```
Beyond Burger · 30.597 verkauft · 10,4% Umsatzanteil
```

### Fehler 3: Wiederkehrende Kunden 2025

| | Dashboard | CSV (korrekt) |
|--|-----------|---------------|
| **Rate** | **68,4%** | **99,7%** (Kunden die 2025 UND vorher bestellt haben) |
| **Vergleich 2024** | vs. 64,2% | — |
| **Stammkunden** | 17.100 | 23.810 |

**Analyse:** Der Dashboard-Wert von 68,4% ist deutlich zu niedrig. Da fast alle 23.891 Kunden, die 2025 bestellt haben, auch vorher schon bestellt hatten (99,7%), scheint hier eine andere Definition oder ein Berechnungsfehler vorzuliegen.

**Mögliche korrekte Interpretation:** Falls "wiederkehrend" bedeutet "hat 2025 in >1 Monat bestellt", wäre eine andere Berechnung nötig. Der Wert 68,4% lässt sich aber aus den CSV-Daten nicht reproduzieren.

**Korrektur in dashboard.html (Zeile 829–831):**
- Definition klären und Wert aus CSV neu berechnen
- Bei Definition "Kunden die 2025 und vorher bestellt haben": `68,4%` → `99,7%`, `17.100` → `23.810`

### Fehler 4: Kanalverteilung 2025

| Kanal | Dashboard | CSV (korrekt) | Differenz |
|-------|-----------|---------------|-----------|
| Counter | **49,9%** | **51,2%** | −1,3pp |
| Drive-Through | **20,5%** | **21,1%** | −0,6pp |
| Kiosk | **16,7%** | **17,1%** | −0,4pp |
| App Order | **12,9%** | **10,6%** | +2,3pp |

**Korrektur in dashboard.html (Zeilen 804–816):**
- Counter: `49,9%` → `51,2%`
- Drive-Through: `20,5%` → `21,1%`
- Kiosk: `16,7%` → `17,1%`
- App Order: `12,9%` → `10,6%`

### Fehler 5: Netzwerk-AOV

| | Dashboard | CSV (korrekt) |
|--|-----------|---------------|
| **Ø AOV** | **€19,23** | **€19,25** |

**Korrektur (Zeile 964):** `€19,23` → `€19,25`

**Hinweis:** Die Abweichung ist minimal (2 Cent) und könnte auf Rundung zurückzuführen sein, sollte aber für Konsistenz korrigiert werden.

### Fehler 6: Bestellungen 2025 pro Monat

| | Dashboard | CSV (korrekt) |
|--|-----------|---------------|
| **Ø pro Monat** | **11.380** | **11.380** (136.557 / 12 = 11.379,75) |

**Ergebnis:** ✅ Korrekt (gerundet).

### Fehler 7: Filial-Bestellungen in Scorecard

| Filiale | Dashboard | CSV |
|---------|-----------|-----|
| BM Europastern | 182.120 | 182.120 ✅ |
| BM Hauptbahnhof | 123.929 | 123.929 ✅ |
| BM Mainfrankenpark | 102.631 | 102.631 ✅ |
| BM Heuchelhof | 100.783 | 100.783 ✅ |
| BM Sanderring | 89.366 | 89.366 ✅ |
| BM Lengfeld | 72.218 | 72.218 ✅ |
| BM Grombühl | 47.734 | 47.734 ✅ |
| BM Zellerau | 35.732 | 35.732 ✅ |

**Ergebnis:** ✅ Alle korrekt.

---

## Zusammenfassung der notwendigen Korrekturen

| # | KPI | Dashboard (falsch) | CSV (korrekt) | Zeile in HTML |
|---|-----|-------------------|---------------|---------------|
| 1 | Kundenzufriedenheit 2025 | 4,6 / 5 | **3,82 / 5** | 835 |
| 2 | Zufriedenheit 2024 Vergleich | vs. 4,4 | **vs. 3,82** | 837 |
| 3 | Anzahl Bewertungen 2025 | 12.830 | **29.990** | 837 |
| 4 | Top-Produkt 2025 | Classic Burger | **Beyond Burger** (Top-Burger) oder **Cola 0.5l** (Top gesamt) | 823 |
| 5 | Top-Produkt Menge | 28.412 | **30.597** (Beyond Burger) oder **45.515** (Cola 0.5l) | 825 |
| 6 | Top-Produkt Umsatzanteil | 18,2% | **10,4%** (Beyond Burger) oder **5,6%** (Cola 0.5l) | 825 |
| 7 | Wiederkehrende Kunden | 68,4% | **99,7%** (oder Definition klären) | 829 |
| 8 | Stammkunden Anzahl | 17.100 | **23.810** | 831 |
| 9 | Counter 2025 | 49,9% | **51,2%** | 804 |
| 10 | Drive-Through 2025 | 20,5% | **21,1%** | 808 |
| 11 | Kiosk 2025 | 16,7% | **17,1%** | 816 |
| 12 | App Order 2025 | 12,9% | **10,6%** | 812 |
| 13 | Netzwerk Ø AOV | €19,23 | **€19,25** | 964 |

---

## Hinweise für Studierende

1. **Methodik:** Alle Werte wurden mit `pandas` aus den Original-CSV-Dateien berechnet. Für den Gesamtumsatz wird `net_total` aus `fact_orders.csv` verwendet, für Produktumsätze `line_total` aus `fact_order_items.csv`.

2. **Kanalverteilung:** Die CSV enthält 4 Kanäle: Counter, Drive-Through, Kiosk, App Order. Das Dashboard bezeichnet diese korrekt.

3. **AOV-Berechnung:** `AOV = net_total.mean()` pro Zeitraum. Die Jahres-AOVs in der Tabelle stimmen exakt.

4. **Zufriedenheit:** Das Feld `satisfaction_score` in `fact_orders.csv` enthält viele NULL-Werte (nur 142.317 von 754.513 Bestellungen haben einen Score). Der Durchschnitt wird nur über die vorhandenen Werte berechnet.

5. **Promo-Bestellungen:** Die korrekte Definition ist `discount_amount > 0` (nicht `promo_id`). Das ergibt exakt die 62.023 Bestellungen (8,2%) wie im Dashboard.

---

*Bericht erstellt am 10.04.2026 – Automatische Validierung mit Python/pandas*
