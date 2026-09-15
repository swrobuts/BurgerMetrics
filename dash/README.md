# Dash-App zur Fallstudie BurgerMetrics

Eine Datei, vier Karten: Kennzahlkacheln (Umsatz, Bestellungen, Ø Bestellwert, Zufriedenheit
2025), Umsatz je Monat mit Filialfilter, Kanalanteile je Jahr, Ø Sterne je Produkt. Jede Karte
liest eine Sicht der Semantikschicht — dieselben Zahlen wie das Dashboard.

```bash
python3 -m pip install -r dash/requirements.txt
python3 dash/app.py            # http://127.0.0.1:8050
```

Die Verbindung kommt aus `DATABASE_URL`; ohne die Variable nutzt die App das Demo-Konto
`studi_daba` (nur lesend). In Colab startet die letzte Codezelle von
`notebooks/00_zugang_und_daten.ipynb` mit `app.run(jupyter_mode="inline")` die Karte
„Umsatz je Monat“ mit Filialauswahl; die vollständige App mit vier Karten läuft lokal.

Test gegen die Datenbank: `python3 -m pytest dash/test_app.py -q` (fünf Tests).
