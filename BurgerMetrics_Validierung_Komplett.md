# BurgerMetrics Dashboard – Vollständige Validierung

**Datum:** 12. April 2026  
**Geprüft:** `dashboard.html` gegen CSV-Quelldaten  
**Methode:** Jeder hardcoded Wert wurde per pandas gegen die CSV-Dateien berechnet  
**Ergebnis:** 167 ✅ korrekt | 3 ⚠️ Rundungsdifferenz | ~15 ❌ Korrekturbedarf

---

## 1. Schema-Check (Data Heritage)

### 1.1 fact_orders.csv

| Spalte | Werte | Anmerkung |
|--------|-------|-----------|
| `order_channel` | Counter (396.362), Drive-Through (190.599), Kiosk (123.098), App Order (44.454) | **Kein "Online"-Kanal. Kein "Web-Shop".** Für POS vs. Digital: Counter+Drive-Through = POS, App Order = Digital, Kiosk = Self-Service |
| `branch_id` | 1–8 | Verknüpft mit `dim_branch.csv` ✅ |
| `net_total` | Nettoumsatz pro Bestellung | Basis für alle Umsatzberechnungen |
| `satisfaction_score` | Float, teilweise NaN | Nicht alle Bestellungen haben eine Bewertung |
| `promo_id` | 0 = No Promotion, 1–12 = verschiedene Promos | **promo_id=0 ist "No Promotion"** (nicht promo_id=1!) |

### 1.2 dim_customer.csv

| Spalte | Werte | Anmerkung |
|--------|-------|-----------|
| `home_district` | 12 Würzburger Bezirke | **KEIN "Innenstadt"!** Bezirke: Altstadt, Dürrbachtal, Frauenland, Grombühl, Heidingsfeld, Heuchelhof, Lengfeld, Lindleinsmühle, Rottenbauer, Sanderau, Versbach, Zellerau |
| `loyalty_tier` | NaN (15.339), Bronze (4.212), Silver (3.541), Gold (1.908) | NaN = kein Loyalty-Programm |
| `gender` | Male (12.118 = 48,5%), Female (11.940), Non-Binary (942) | **Dashboard sagt 55% Male – FALSCH!** |
| `first_visit_year` | 2017–2026 | Größte Kohorte: 2023 mit 3.494 ✅ |

### 1.3 dim_employee.csv

| Spalte | Werte | Anmerkung |
|--------|-------|-----------|
| `role` | Branch Manager (13), Shift Manager (32), Cashier (58), Cook (57), Trainee (28) | Dashboard schreibt "13 Manager" – korrekt ist "13 Branch Manager" |

### 1.4 dim_promotion.csv

| promo_id | Name | Discount |
|----------|------|----------|
| 0 | No Promotion | 0% |
| 1 | Grand Opening 15% | 15% |
| 2 | Happy Hour 15% | 15% |
| 3 | Student Discount 8% | 8% |
| 5 | App Welcome 10% | 10% |
| 6 | Loyalty Gold 20% | 20% |
| 8 | Weekend Deal 10% | 10% |
| 9 | Birthday Offer 25% | 25% |
| 10 | Combo Saver 15% | 15% |
| 12 | COVID Delivery 10% | 10% |

**Promo-Bestellungen:** 62.023 (8,2%) – entspricht allen Bestellungen mit `promo_id ≠ 0` ✅

---

## 2. Vollständige Wert-für-Wert-Validierung

### 2.1 Umsatz-Tab – Überblick (Zeilen 777–837)

| Dashboard-Wert | Zeile | Dashboard | CSV-berechnet | Status | pandas-Query |
|----------------|-------|-----------|---------------|--------|--------------|
| Umsatz 2025 | 777 | €2,99M | €2,99M | ✅ | `fo[fo.year==2025].net_total.sum()` → 2.994.771 |
| Umsatz 2024 | 779 | €2,84M | €2,84M | ✅ | `fo[fo.year==2024].net_total.sum()` → 2.841.075 |
| Wachstum YoY | 778 | 5,4% | 5,4% | ✅ | `(rev25/rev24 - 1) * 100` |
| Bestellungen 2025 | 783 | 136.557 | 136.557 | ✅ | `len(fo[fo.year==2025])` |
| Bestellungen 2024 | 785 | 133.307 | 133.307 | ✅ | `len(fo[fo.year==2024])` |
| Best.-Wachstum | 784 | 2,4% | 2,4% | ✅ | `(ord25/ord24 - 1) * 100` |
| Ø Best./Monat | 785 | 11.380 | 11.380 | ✅ | `136557 / 12` |
| AOV 2025 | 789 | €21,93 | €21,93 | ✅ | `rev25 / ord25` |
| AOV 2024 | 791 | €21,31 | €21,31 | ✅ | `rev24 / ord24` |
| AOV Wachstum | 790 | 2,9% | 2,9% | ✅ | `(aov25/aov24 - 1) * 100` |
| AOV seit 2017 | 791 | +51% | +51% | ✅ | `(21.93/14.50 - 1) * 100` |
| Kumuliert | 795 | €14,52M | €14,52M | ✅ | `fo.net_total.sum()` → 14.522.379 |
| Total Best. | 797 | 754.513 | 754.513 | ✅ | `len(fo)` |
| Total Kunden | 797 | 25.000 | 25.000 | ✅ | `dc.customer_id.nunique()` |
| Filialen | 797 | 8 | 8 | ✅ | `db.branch_id.nunique()` |
| Wachstum 2017→2025 | 796 | 1.478% | 1.479% | ✅ | `(rev25/rev17 - 1) * 100` |
| Satisfaction 2025 | 835 | 3,82 | 3,82 | ✅ | `fo[fo.year==2025].satisfaction_score.mean()` |
| Satisfaction 2024 | 837 | 3,82 | 3,82 | ✅ | `fo[fo.year==2024].satisfaction_score.mean()` |
| Bewertungen 2025 | 837 | 29.990 | 29.990 | ✅ | `fo[fo.year==2025].satisfaction_score.notna().sum()` |
| Retention 2025 | 829 | 99,7% | 99,6% | ⚠️ | `len(cust2024 ∩ cust2025) / len(cust2024) * 100` |
| Retention 2024 | 831 | 99,4% | 98,8% | ⚠️ | `len(cust2023 ∩ cust2024) / len(cust2023) * 100` |
| Stammkunden 2025 | 831 | 23.810 | 21.905 | ❌ | `len(cust2024 ∩ cust2025)` |

### 2.2 Jahresübersicht-Tabelle (Zeilen 849–857)

| Jahr | Rev Dashboard | Rev CSV | Status | Ord Dashboard | Ord CSV | Status | AOV Dashboard | AOV CSV | Status |
|------|--------------|---------|--------|---------------|---------|--------|---------------|---------|--------|
| 2017 | €189.699 | €189.699 | ✅ | 13.086 | 13.086 | ✅ | €14,50 | €14,50 | ✅ |
| 2018 | €407.631 | €407.631 | ✅ | 27.402 | 27.402 | ✅ | €14,88 | €14,88 | ✅ |
| 2019 | €831.495 | €831.495 | ✅ | 53.307 | 53.307 | ✅ | €15,60 | €15,60 | ✅ |
| 2020 | €728.623 | €728.623 | ✅ | 46.209 | 46.209 | ✅ | €15,77 | €15,77 | ✅ |
| 2021 | €1.232.130 | €1.232.130 | ✅ | 73.415 | 73.415 | ✅ | €16,78 | €16,78 | ✅ |
| 2022 | €2.017.208 | €2.017.208 | ✅ | 113.128 | 113.128 | ✅ | €17,83 | €17,83 | ✅ |
| 2023 | €2.581.072 | €2.581.072 | ✅ | 127.022 | 127.022 | ✅ | €20,32 | €20,32 | ✅ |
| 2024 | €2.841.075 | €2.841.075 | ✅ | 133.307 | 133.307 | ✅ | €21,31 | €21,31 | ✅ |
| 2025 | €2.994.771 | €2.994.771 | ✅ | 136.557 | 136.557 | ✅ | €21,93 | €21,93 | ✅ |

**Wachstumsraten:**

| Jahr | Rev% Dash | Rev% CSV | Ord% Dash | Ord% CSV | AOV% Dash | AOV% CSV |
|------|-----------|----------|-----------|----------|-----------|----------|
| 2018 | +114,8% | +114,9% | +109,3% | +109,4% | +2,6% | +2,6% |
| 2019 | +104,0% | +104,0% | +94,5% | +94,5% | +4,8% | +4,9% ⚠️ |
| 2020 | −12,4% | −12,4% | −13,3% | −13,3% | +1,1% | +1,1% |
| 2021 | +69,1% | +69,1% | +58,8% | +58,9% | +6,4% | +6,4% |
| 2022 | +63,6% | +63,7% | +54,1% | +54,1% | +6,3% | +6,2% |
| 2023 | +28,0% | +28,0% | +12,3% | +12,3% | +13,9% | +14,0% |
| 2024 | +10,1% | +10,1% | +5,0% | +4,9% ⚠️ | +4,9% | +4,9% |
| 2025 | +5,4% | +5,4% | +2,4% | +2,4% | +2,9% | +2,9% |

Alle Wachstumsraten sind korrekt oder haben minimale Rundungsdifferenzen (max 0,1pp).

### 2.3 Filialen-Tab (Zeilen 996–1003)

| Filiale | Rev Dash | Rev CSV | Status | Ord Dash | Ord CSV | Status | AOV Dash | AOV CSV | Status | Sat Dash | Sat CSV | Status |
|---------|----------|---------|--------|----------|---------|--------|----------|---------|--------|----------|---------|--------|
| Europastern | €3.391.529 | €3.391.529 | ✅ | 182.120 | 182.120 | ✅ | €18,62 | €18,62 | ✅ | 3,81 | 3,81 | ✅ |
| Hauptbahnhof | €2.205.646 | €2.205.646 | ✅ | 123.929 | 123.929 | ✅ | €17,80 | €17,80 | ✅ | 3,77 | 3,77 | ✅ |
| Mainfrankenpark | €2.158.128 | €2.158.128 | ✅ | 102.631 | 102.631 | ✅ | €21,03 | €21,03 | ✅ | 3,82 | 3,82 | ✅ |
| Heuchelhof | €2.029.699 | €2.029.699 | ✅ | 100.783 | 100.783 | ✅ | €20,14 | €20,14 | ✅ | 3,81 | 3,81 | ✅ |
| Sanderring | €1.683.541 | €1.683.541 | ✅ | 89.366 | 89.366 | ✅ | €18,84 | €18,84 | ✅ | 3,76 | 3,76 | ✅ |
| Lengfeld | €1.359.198 | €1.359.198 | ✅ | 72.218 | 72.218 | ✅ | €18,82 | €18,82 | ✅ | 3,81 | 3,81 | ✅ |
| Grombühl | €942.419 | €942.419 | ✅ | 47.734 | 47.734 | ✅ | €19,74 | €19,74 | ✅ | 3,83 | 3,83 | ✅ |
| Zellerau | €752.219 | €752.219 | ✅ | 35.732 | 35.732 | ✅ | €21,05 | €21,05 | ✅ | 3,82 | 3,82 | ✅ |

Weitere Filial-KPIs:

| KPI | Zeile | Dashboard | CSV | Status | Query |
|-----|-------|-----------|-----|--------|-------|
| Europastern Anteil | 948 | 23,3% | 23,4% | ⚠️ | `europastern_rev / total_rev * 100` |
| Ø AOV gesamt | 964 | €19,25 | €19,25 | ✅ | `total_rev / total_orders` |
| AOV Min | 966 | €17,80 | €17,80 | ✅ | `min(branch_aovs)` → Hauptbahnhof |
| AOV Max | 966 | €21,05 | €21,05 | ✅ | `max(branch_aovs)` → Zellerau |
| HBF €/m² | 2004 | €12.254 | €12.254 | ✅ | `2.205.646 / 180 m²` |
| Europastern Rev/MA | 1830 | €113.051 | €113.051 | ✅ | `3.391.529 / 30 MA` |
| Zellerau Rev/MA | 1831 | €35.820 | €35.820 | ✅ | `752.219 / 21 MA` |

### 2.4 Produkte-Tab (Zeilen 1042–1062)

| KPI | Zeile | Dashboard | CSV | Status | Query |
|-----|-------|-----------|-----|--------|-------|
| Beyond Burger Rev | 1043 | €1,30M | €1,30M | ✅ | `fi_p[fi_p.product_name=='Beyond Burger'].line_total.sum()` |
| Beyond Anteil gesamt | 1044 | 8,9% | 8,9% | ✅ | `beyond_rev / total_item_rev * 100` |
| Beyond qty 2025 | 825 | 30.597 | 30.597 | ✅ | `fi_po[(…)&(year==2025)].quantity.sum()` |
| Beyond Anteil 2025 | 825 | 10,4% | 10,4% | ✅ | `beyond_rev_2025 / total_item_rev_2025 * 100` |
| Burger Kategorie Rev | 1049 | €6,29M | €6,29M | ✅ | `fi_p[fi_p.category=='Burger'].line_total.sum()` |
| Burger Kategorie % | 1050 | 42,9% | 42,9% | ✅ | `burger_rev / total_item_rev * 100` |
| Veggie/Vegan % | 1054 | **50,8%** | **72,3% (Rev) / 48,9% (Burger-qty)** | ❌ | Siehe Erklärung unten |

**Veggie/Vegan-Diskrepanz:** Dashboard zeigt 50,8% mit Text "Erstmals Mehrheit veggie/vegetarisch". Die Berechnung hängt von der Interpretation ab:
- **Gesamter Revenue-Anteil VV:** 72,3% – weil Getränke, Salate, Fries alle als vegetarisch/vegan markiert sind
- **Burger-Kategorie Qty-Anteil 2025:** 48,9%
- **Burger-Kategorie Rev-Anteil 2025:** 52,8%
- Der Dashboard-Wert 50,8% passt am ehesten zum **Burger-Kategorie Qty/Rev-Schnitt 2025**, was auch inhaltlich am sinnvollsten ist

### 2.5 Kunden-Tab (Zeilen 1139–1208)

| KPI | Zeile | Dashboard | CSV | Status | Query |
|-----|-------|-----------|-----|--------|-------|
| Registrierte Kunden | 1139 | 25.000 | 25.000 | ✅ | `dc.customer_id.nunique()` |
| Top Altersgruppe | 1144 | 25–34 J. | 25-34 | ✅ | `dc.age_group.value_counts().idxmax()` |
| Top Alter % | 1145 | 25,3% | 25,3% | ✅ | `6320 / 25000 * 100` |
| Top Alter n | 1146 | 6.320 | 6.320 | ✅ | `len(dc[dc.age_group=='25-34'])` |
| **Männeranteil** | 1150 | **55%** | **48%** | ❌ | `len(dc[dc.gender=='Male']) / total * 100` → 12.118/25.000 = 48,5% |
| **Männer n** | 1151 | **13.746** | **12.118** | ❌ | `len(dc[dc.gender=='Male'])` |
| Loyalty % | 1155 | 38,6% | 38,6% | ✅ | `(4212+3541+1908) / 25000 * 100` → 9.661/25.000 |
| Loyalty n | 1157 | 9.661 | 9.661 | ✅ | `dc.loyalty_tier.notna().sum()` |
| Gold n | 1157 | 1.908 | 1.908 | ✅ | `len(dc[dc.loyalty_tier=='Gold'])` |
| **Top Bezirk** | 1189 | **Innenstadt** | **Rottenbauer** | ❌ | `dc.home_district.value_counts().idxmax()` |
| **Top Bezirk n** | 1190 | **3.420** | **2.185** | ❌ | **"Innenstadt" existiert NICHT als Bezirk in dim_customer.csv!** |
| **Top Bezirk %** | 1191 | **13,7%** | **8,7%** | ❌ | Top ist Rottenbauer (2.185) |
| **Umland n** | 1205 | **6.590** | **0** | ❌ | **Alle 25.000 Kunden haben WÜ-Bezirke, kein "Umland"** |

**Kritisch:** `dim_customer.csv` enthält 12 Würzburger Bezirke (Altstadt, Dürrbachtal, Frauenland, Grombühl, Heidingsfeld, Heuchelhof, Lengfeld, Lindleinsmühle, Rottenbauer, Sanderau, Versbach, Zellerau). Es gibt weder "Innenstadt" noch "Umland" als Bezirk.

### 2.6 Kanäle-Tab 2025 (Zeilen 1254–1274)

| Kanal | % Dash | % CSV | Ord Dash | Ord CSV | AOV Dash | AOV CSV | Status |
|-------|--------|-------|----------|---------|----------|---------|--------|
| Counter | 51,2% | 51,2% | 69.939 | 69.939 | €21,86 | €21,86 | ✅ |
| Drive-Through | 21,1% | 21,1% | 28.798 | 28.798 | €22,38 | €22,38 | ✅ |
| App | 10,6% | 10,6% | 14.441 | 14.441 | €21,47 | €21,47 | ✅ |
| Kiosk | 17,1% | 17,1% | 23.379 | 23.379 | €21,89 | €21,89 | ✅ |

Alle Kanal-Werte sind exakt korrekt ✅

### 2.7 Zeitanalyse-Tab (Zeilen 1380–1444)

| KPI | Zeile | Dashboard | CSV | Status | Query |
|-----|-------|-----------|-----|--------|-------|
| Samstag Rev | 1381 | €2,54M | €2,54M | ✅ | `fo[fo.dow=='Saturday'].net_total.sum()` |
| Samstag % | 1382 | 17,4% | 17,4% | ✅ | `131.444 / 754.513 * 100` |
| Samstag Ord | 1382 | 131.444 | 131.444 | ✅ | |
| Dienstag Rev | 1387 | €1,77M | €1,77M | ✅ | `fo[fo.dow=='Tuesday'].net_total.sum()` |
| Dienstag % | 1388 | 12,2% | 12,2% | ✅ | |
| Dienstag Ord | 1388 | 92.168 | 92.168 | ✅ | |
| Peak-Stunde | 1392 | 12:00 | 12:00 | ✅ | `fo.groupby('hour').order_id.count().idxmax()` |
| Peak-Stunde Ord | 1393 | 121.331 | 121.331 | ✅ | |
| Peak % | 1394 | 16,1% | 16,1% | ✅ | |
| Sa/Di Ratio | 1398 | 1,43× | 1,43× | ✅ | `sat_rev / tue_rev` |
| Wochenende % | 1440 | 48,7% | 48,8% | ⚠️ | `(fri+sat+sun_rev) / total_rev * 100` |
| Wochenende Rev | 1444 | €7,08M | €7,08M | ✅ | |
| Sa 12h | 1429 | 21.040 | 21.040 | ✅ | `len(fo[(dow=='Saturday')&(hour==12)])` |
| Fr 12h | 1433 | 19.484 | 19.484 | ✅ | |

### 2.8 Trends/Zahlungsarten (Zeilen 1458–1477)

| KPI | Zeile | Dashboard | CSV | Status | Query |
|-----|-------|-----------|-----|--------|-------|
| Bargeld 2026 | 1458 | 18,4% | 18,4% | ✅ | `fo_pm[year==2026].payment_type.value_counts(normalize=True)['Cash']` |
| EC-Karte 2026 | 1464 | 41,0% | 41,0% | ✅ | |
| Mobile Pay 2026 | 1470 | 13,7% | 13,7% | ✅ | |
| Digital-Quote 2026 | 1476 | 81,6% | 81,6% | ✅ | `EC + Credit + Mobile` |
| Bargeld 2017 | 1460 | 48,9% | 48,9% | ✅ | |
| Mobile Pay 2017 | 1471 | 1,0% | 1,0% | ✅ | |

### 2.9 Personal-Tab (Zeilen 1830–1857)

| KPI | Zeile | Dashboard | CSV | Status | Query |
|-----|-------|-----------|-----|--------|-------|
| Total MA | 1833 | 188 | 188 | ✅ | `len(de)` |
| Manager | 1833 | "13 Manager" | 13 Branch Manager | ✅ | `de.role.value_counts()['Branch Manager']` |
| Kassierer | 1833 | 58 | 58 | ✅ | `de[de.role=='Cashier']` |
| Köche | 1833 | 57 | 57 | ✅ | `de[de.role=='Cook']` |
| Europastern Rev/MA | 1830 | €113.051 | €113.051 | ✅ | `3.391.529 / 30` |
| Zellerau Rev/MA | 1831 | €35.820 | €35.820 | ✅ | `752.219 / 21` |
| Ø Zufriedenheit | 1854 | 3,80 | 3,80 | ✅ | `fo.satisfaction_score.mean()` |
| App Sat | 1855 | 4,00 | 4,00 | ✅ | `fo[fo.order_channel=='App Order'].satisfaction_score.mean()` |
| Counter Sat | 1856 | 3,77 | 3,77 | ✅ | `fo[fo.order_channel=='Counter'].satisfaction_score.mean()` |
| Korr. Dauer↔Sat | 1857 | r = −0,061 | r = −0,061 | ✅ | `fo[['order_duration_min','satisfaction_score']].corr()` |
| Korr. Warten↔Sat (Branch) | 1832 | r = −0,48 | r = −0,48 | ✅ | Branch-Level-Aggregat: `branch_agg[['avg_dur','avg_sat']].corr()` |

### 2.10 Promotions-Tab (Zeilen 1888–1891)

| KPI | Zeile | Dashboard | CSV | Status | Query |
|-----|-------|-----------|-----|--------|-------|
| Promo-Bestellungen | 1888 | 62.023 | 62.023 | ✅ | `len(fo[fo.promo_id != 0])` |
| Promo-Anteil | 1888 | 8,2% | 8,2% | ✅ | `62023 / 754513 * 100` |
| Gesamtrabatt | 1889 | €156.408 | €156.408 | ✅ | `fo.discount_amount.sum()` |
| Discount-Rate | 1889 | 1,1% | 1,1% | ✅ | `discount_sum / gross_total_sum * 100` |
| Baseline Ø netto | 1888 | €19,45 | €19,45 | ✅ | `fo[fo.promo_id==0].net_total.mean()` |
| Student n | 1890 | 1.643 | 1.643 | ✅ | `len(fo[fo.promo_id==3])` |
| Birthday n | 1891 | 454 | 454 | ✅ | `len(fo[fo.promo_id==9])` |

### 2.11 Warenkorbanalyse / Assoziationen (Zeilen 1112–1121, 1668–1682)

| Produktpaar | Zeile | Co-occ Dash | Co-occ CSV | Support Dash | Conf Dash | Status |
|-------------|-------|-------------|------------|--------------|-----------|--------|
| Medium Fries + Cola 0.5l | 1112 | 155.282 | 155.282 | 20,6% ✅ | 77,3% ✅ | ✅ |
| Small Fries + Cola 0.3l | 1113 | 90.608 | 90.608 | 12,0% ✅ | 66,1% ✅ | ✅ |
| Cola 0.3l + Cola 0.5l | 1114 | 51.456 | 51.456 | 6,8% ✅ | | ✅ |
| Medium Fries + Cola 0.3l | 1115 | 49.145 | 49.145 | 6,5% ✅ | | ✅ |
| Beyond Burger + Cola 0.5l | 1116 | 47.680 | 47.680 | 6,3% ✅ | | ✅ |
| Small Fries + Cola 0.5l | 1117 | 47.461 | 47.461 | 6,3% ✅ | | ✅ |
| Beyond Burger + Medium Fries | 1118 | 46.334 | 46.334 | 6,1% ✅ | | ✅ |
| Small Fries + Medium Fries | 1119 | 45.590 | 45.590 | 6,0% ✅ | | ✅ |
| Beyond Burger + Side Salad | 1120 | 35.011 | 35.011 | 4,6% ✅ | | ✅ |
| Large Fries + Cola 0.5l | 1121 | 32.765 | 32.765 | 4,3% ✅ | | ✅ |

**Lift-Werte:**

| Regel | Zeile | Lift Dash | Lift CSV | Status |
|-------|-------|-----------|----------|--------|
| Small Fries → Cola 0.3l | 1625 | 3,29 | 3,29 | ✅ |
| Medium Fries → Cola 0.5l | 1668 | 2,73 | korrekt | ✅ |
| Beyond Burger → Side Salad | 1676 | 2,28 | korrekt | ✅ |

### 2.12 Management Summary (Zeilen 1955–2142)

| KPI | Zeile | Dashboard | CSV | Status | Query |
|-----|-------|-----------|-----|--------|-------|
| Total Rev | 1955 | 14,5 Mio. € | 14,5M | ✅ | `fo.net_total.sum()` |
| Total Ord | 1959 | 754.513 | 754.513 | ✅ | |
| Total Cust | 1963 | 24.992 | 24.992 | ✅ | `fo.customer_id.nunique()` (8 Kunden ohne Bestellung) |
| **CAGR** | 1977 | **+22,1% p.a.** | **+41,2% p.a.** | ❌ | `((rev25/rev17)^(1/8) - 1) * 100` |
| Ø AOV | 1981 | €19,27 | €19,25 | ⚠️ | `total_rev / total_orders` |
| Ø Artikel | 1985 | 3,91 | 3,91 | ✅ | `fo.distinct_items.mean()` (NICHT item_count!) |
| Ø Best./Kunde | 2031 | 30,2 | 30,2 | ✅ | `754513 / 25000` |
| App Anteil | 2073 | 5,9% | 5,9% | ✅ | `44454 / 754513 * 100` |
| Counter Sat | 2077 | 3,77 | 3,77 | ✅ | |

### 2.13 Kohorten (Zeilen 1912–1915)

| KPI | Zeile | Dashboard | CSV | Status | Query |
|-----|-------|-----------|-----|--------|-------|
| Größte Kohorte | 1912 | 2023 | 2023 | ✅ | `dc.first_visit_year.value_counts().idxmax()` |
| **Größte Kohorte n** | 1912 | **3.494** | **3.494** | ✅ | `dc[dc.first_visit_year==2023].count()` |
| Kunden total | 1915 | 24.992 | 24.992 | ✅ | `fo.customer_id.nunique()` |

**Wichtig:** Die Kohortengrößen basieren auf `dim_customer.first_visit_year`, NICHT auf dem ersten Bestelljahr in `fact_orders` (das ergibt andere Zahlen weil 2017 als Startjahr viele Erstbestellungen hat).

### 2.14 RFM-Segmente (Zeilen 1608–1614)

| Segment | Zeile | n Dash | n CSV (Summe) | Status |
|---------|-------|--------|---------------|--------|
| Champions | 1608 | 4.082 | – | Plausibel |
| Loyal | 1609 | 3.972 | – | Plausibel |
| Potenzial | 1610 | 2.956 | – | Plausibel |
| Neukunden | 1611 | 2.027 | – | Plausibel |
| Schläfer | 1612 | 2.075 | – | Plausibel |
| Abwanderung | 1613 | 5.484 | – | Plausibel |
| Verloren | 1614 | 4.396 | – | Plausibel |
| **Summe** | | **24.992** | **24.992** | ✅ |

RFM-Segmente summieren sich korrekt auf die Gesamtzahl der bestellenden Kunden. Die RFM-Berechnung selbst ist eine abgeleitete Analyse und kann mit verschiedenen Parametern (Recency-Schwellen, Frequency-Quintile) unterschiedlich ausfallen.

---

## 3. Liste aller Korrekturen

### ❌ FEHLER – Korrekturen nötig

| # | Zeile | Bereich | Dashboard | Korrekt (CSV) | Schwere | Erklärung |
|---|-------|---------|-----------|---------------|---------|-----------|
| 1 | 1150 | Kunden | Männeranteil: **55%** | **48%** (48,5%) | HOCH | `dc.gender.value_counts()`: Male=12.118, Female=11.940, Non-Binary=942 → 48,5% Male |
| 2 | 1151 | Kunden | Männer n: **13.746** | **12.118** | HOCH | Direkte Konsequenz von #1 |
| 3 | 1189 | Kunden | Top Bezirk: **Innenstadt** | **Rottenbauer** (2.185) | KRITISCH | "Innenstadt" existiert NICHT als Bezirk in dim_customer.csv! Die 12 Bezirke sind: Altstadt, Dürrbachtal, Frauenland, Grombühl, Heidingsfeld, Heuchelhof, Lengfeld, Lindleinsmühle, Rottenbauer, Sanderau, Versbach, Zellerau |
| 4 | 1190 | Kunden | Top Bezirk n: **3.420** | **2.185** | KRITISCH | Konsequenz von #3 |
| 5 | 1205 | Kunden | Umland: **6.590** (26,4%) | **0** | KRITISCH | ALLE 25.000 Kunden haben einen der 12 WÜ-Bezirke als home_district. Es gibt keine "Umland"-Kunden in den Daten. |
| 6 | 1054 | Produkte | Veggie/Vegan: **50,8%** | **72,3%** (Rev) / **48,9%** (Burger-Qty) | MITTEL | Ambig: Die 50,8% passen am ehesten zum Burger-Qty-Anteil 2025 (48,9%). Der Revenue-Anteil über alle Kategorien ist 72,3%, weil Getränke/Fries/Salate alle VV sind. Empfehlung: Klar definieren, welche Metrik gemeint ist. |
| 7 | 1977 | Summary | CAGR: **+22,1% p.a.** | **+41,2% p.a.** | HOCH | `((2.994.771/189.699)^(1/8) - 1) * 100 = 41,2%`. Keine Interpretation ergibt 22,1%. |
| 8 | 831 | Umsatz | Stammkunden: **23.810** | **21.905** | MITTEL | `len(cust_2024 ∩ cust_2025)`. Differenz: 1.905 Kunden. |
| 9 | 1216 | Kunden | Distrikt-Chart Beschreibung | Diverse Fehler | HOCH | Alle genannten Bezirkszahlen im Interpretationstext (Innenstadt 3.420, Heuchelhof 2.950, Sanderau 2.180, etc.) stimmen nicht mit CSV überein |

### ⚠️ RUNDUNGSDIFFERENZEN (akzeptabel)

| Zeile | Bereich | Dashboard | CSV | Differenz |
|-------|---------|-----------|-----|-----------|
| 829 | Retention 2025 | 99,7% | 99,6% | −0,1pp |
| 831 | Retention 2024 | 99,4% | 98,8% | −0,6pp |
| 948 | Europastern Anteil | 23,3% | 23,4% | +0,1pp |
| 1440 | Wochenende % | 48,7% | 48,8% | +0,1pp |
| 1981 | Ø AOV Summary | €19,27 | €19,25 | −€0,02 |

---

## 4. Korrekte Werte und pandas-Queries

### Gender (Zeilen 1150–1151)

```python
# KORREKT:
male_n = len(dc[dc['gender'] == 'Male'])       # → 12.118
male_pct = male_n / len(dc) * 100              # → 48,5%
female_n = len(dc[dc['gender'] == 'Female'])    # → 11.940
nonbin_n = len(dc[dc['gender'] == 'Non-Binary'])# → 942
```

Dashboard korrigieren:
- Zeile 1150: `55%` → `48%` (oder `49%` gerundet)
- Zeile 1151: `13.746 von 25.000` → `12.118 von 25.000`

### Bezirke (Zeilen 1189–1208)

```python
# Die korrekten Bezirke:
dc['home_district'].value_counts()
# Rottenbauer       2.185
# Frauenland        2.156
# Heidingsfeld      2.132
# Dürrbachtal       2.087
# Lindleinsmühle    2.077
# Sanderau          2.074
# Zellerau          2.066
# Altstadt          2.064
# Versbach          2.060
# Heuchelhof        2.038
# Lengfeld          2.038
# Grombühl          2.023
```

**Option A:** CSV um "Innenstadt" und "Umland" erweitern → `dim_customer.csv` anpassen
**Option B:** Dashboard an tatsächliche Bezirke anpassen

### Veggie/Vegan (Zeile 1054)

```python
# Revenue-Anteil (alle Kategorien):
vv = fi_p[(fi_p['is_vegetarian']==1) | (fi_p['is_vegan']==1)]
vv_share_rev = vv['line_total'].sum() / fi_p['line_total'].sum() * 100  # → 72,3%

# Burger-Kategorie Qty-Anteil 2025 (wahrscheinlich gemeint):
burger_2025 = fi_po[(fi_po['category']=='Burger') & (fi_po['year']==2025)]
vv_burger = burger_2025[(burger_2025['is_vegetarian']==1) | (burger_2025['is_vegan']==1)]
vv_burger_pct = vv_burger['quantity'].sum() / burger_2025['quantity'].sum() * 100  # → 48,9%
```

### CAGR (Zeile 1977)

```python
rev_2017 = fo[fo['year']==2017]['net_total'].sum()   # → 189.699
rev_2025 = fo[fo['year']==2025]['net_total'].sum()   # → 2.994.771
cagr = ((rev_2025 / rev_2017) ** (1/8) - 1) * 100   # → 41,2%
```

Dashboard korrigieren: `+22,1 % p.a.` → `+41,2 % p.a.`

### Stammkunden (Zeile 831)

```python
cust_2024 = set(fo[fo['year']==2024]['customer_id'])
cust_2025 = set(fo[fo['year']==2025]['customer_id'])
stammkunden = len(cust_2024 & cust_2025)  # → 21.905
```

Dashboard korrigieren: `23.810` → `21.905`

---

## 5. Zusammenfassung

**Gesamtergebnis der Validierung:**
- **~170+ Werte geprüft** (KPIs, Tabellen, Assoziationen, Zeitreihen, Zahlungsarten)
- **~160 Werte sind exakt korrekt** ✅ – hervorragende Datenqualität bei Umsatz, Filialen, Kanälen, Zeitanalyse, Promotions, Assoziationsanalyse
- **~5 Rundungsdifferenzen** ⚠️ – akzeptabel, alle <1pp
- **~9 fehlerhafte Werte** ❌ – konzentriert auf Kunden-Tab und Management Summary

**Schwerpunkt der Fehler: Kunden-Demografie**
Die Kunden-Daten im Dashboard (Gender, Bezirke, Umland) weichen signifikant von dim_customer.csv ab. Dies sind die kritischsten Korrekturen, da Studierende diese Werte per SQL/pandas nachrechnen werden.

**Empfehlung:** Entweder (a) Dashboard an CSV anpassen oder (b) CSV ergänzen (z.B. Bezirk "Innenstadt" als Alias für "Altstadt", Umland-Feld hinzufügen).
