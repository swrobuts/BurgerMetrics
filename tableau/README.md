# Tableau-Arbeitsmappe zur Fallstudie

`BurgerMetrics.twb` ist die Arbeitsmappe zu Lab 05 der Lernumgebung
(`web/lab/lab-05-tableau.html`, Abschnitt „Das Kennzahlen-Dashboard“): die Datenquelle
aus `fact_orders`, `dim_branch` und `fact_reviews` des Schemas `burgermetrics`, der
Parameter `Jahr`, die 28 Calculated Fields aus `web/lab/vorlagen/tableau-dashboard-felder.txt`,
zehn Blätter und das Dashboard „Dashboard 1“ (1600 × 1100). Gebaut und geprüft am
22.09.2026 mit Tableau Desktop 2026.2 auf macOS in deutscher Oberfläche.

## Öffnen

1. Tableau Desktop starten, `BurgerMetrics.twb` öffnen.
2. Die Arbeitsmappe enthält keine Daten und kein Kennwort. Sie verweist auf einen Extrakt
   (`.hyper`) im Tableau-Repository des Rechners, auf dem sie gebaut wurde; der liegt nicht
   im Repository. Tableau meldet deshalb beim Öffnen den fehlenden Extrakt und bietet an,
   ihn neu zu erzeugen; dafür verlangt es die Anmeldung an `supabase.butscher.cloud`,
   Port `5433`, Datenbank `postgres`, mit `studi_daba` / `thws` (Lab 01). Der Extrakt
   von `fact_orders` hat rund 755.000 Zeilen und entsteht in unter einer Minute.
3. Danach steht das Dashboard mit dem Parameter `Jahr` auf 2025: Umsatz 2.994.771 €,
   136.557 Bestellungen, Bestellwert 21,93 €, Ø Sterne 3,750, +5,4 % zum Vorjahr.

## Was drin ist

```
Datenquelle   fact_orders — dim_branch (Branch Id = Branch Id)
              fact_orders — fact_reviews (Order Id = Order Id), Extrakt
Parameter     Jahr: Ganzzahl, 2025, Bereich 2018 bis 2026
Felder        Umsatz, Bestellungen, Bestellwert, Ø Sterne; je Kennzahl Jahr und VJ über
              IF YEAR([Date]) = [Jahr]; Δ in Prozent und Sternen; Δ Umsatz Richtung;
              Umsatz Tsd Jahr/VJ; Umsatz Tsd letzter Monat (roter Punkt); Spalte und
              Zeile (Raster der Small Multiples); Top Filiale; Titel Dashboard;
              vier Δ-Texte für die Karten
Blätter       Filialen Umsatz, Filialen Kennzahlen, Umsatz je Monat, Abweichung je Monat,
              Filialen je Monat, Karte Umsatz, Karte Bestellungen, Karte Bestellwert,
              Karte Sterne, Titel
Dashboard 1   vertikaler Container als Rahmen: Titel, Kartenreihe, mittlere Reihe aus
              Balken, Tabelle, Linie und Abweichung, Small Multiples 4 × 2; zwölf Pixel
              Füllung je Kachel; Parameter unverankert oben rechts
```

Die Datei ist XML; wer sie in Tableau speichert, schreibt sie als Text zurück, und
Änderungen sind im Git-Diff lesbar. Die Sperrdatei `.~BurgerMetrics__*.twbr`, die Tableau
neben einer geöffneten Arbeitsmappe anlegt, ist über `.gitignore` ausgeschlossen.
