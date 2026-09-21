# Power-BI-Projekt zur Fallstudie

`BurgerMetrics/` ist das Power-BI-Projekt (PBIP) zu Lab 04 der Lernumgebung
(`web/lab/lab-04-powerbi.html`): das Modell aus sieben Tabellen des Schemas
`burgermetrics`, die Measures aus `web/lab/vorlagen/powerbi-measures.dax` und
`powerbi-dashboard.dax`, die Seite „Bericht“ und die Seite „Dashboard“.
Gebaut und geprüft am 21.09.2026 mit Power BI Desktop 2.157.1354.0 (August 2026).

## Öffnen

1. Power BI Desktop (Windows) starten, `BurgerMetrics/BurgerMetrics.pbip` öffnen.
2. Das Projekt enthält keine Daten: Power BI fragt beim ersten Aktualisieren nach
   der Anmeldung an `supabase.butscher.cloud:5433` — Authentifizierungsart
   Standard, Benutzername `studi_daba`, Kennwort `thws` (Lab 01). Der Import der
   sieben Tabellen dauert rund zwei Minuten.
3. Das Kennwort wird von Power BI auf dem Rechner gespeichert, nicht im Projekt.

## Was wo liegt

```
BurgerMetrics.pbip                          Einstiegsdatei
BurgerMetrics.SemanticModel/definition/     Modell als TMDL: tables/*.tmdl (Spalten, Measures,
                                            Power-Query-Quelle je Tabelle), relationships.tmdl
BurgerMetrics.Report/definition/pages/      Seiten als PBIR-JSON: bc79…/ ist „Bericht“,
                                            dashboard/ die Seite „Dashboard“, je Visual eine Datei
```

`.pbi/cache.abf` (die importierten Daten, rund 70 MB) und `localSettings.json`
sind über `.gitignore` ausgeschlossen. Wer das Projekt in Power BI speichert,
schreibt dieselben Textdateien zurück — Änderungen sind im Git-Diff lesbar.
