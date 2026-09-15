# Praxistest: Colab, Dash und externe Aktualisierung

Datum: 15. September 2026. Ergänzung zur
[vollständigen Windows-Abnahme](validierung-notebooks-2026-09-15.md).

## Google Colab

Notebook 00 wurde über seinen GitHub-Link in der angemeldeten Colab-Oberfläche
geöffnet und mit „Alle ausführen“ vollständig gestartet. Alle 13 Codezellen
liefen erfolgreich: Paketinstallation, PostgreSQL-Zugang als `studi_daba`,
Schemata und materialisierte Sichten, Kennzahlen, Git-LFS-CSV, DuckDB,
CSV-/Parquet-Export und die erwartete Ablehnung der Schreibprobe mit SQLSTATE
`42501`.

Die weiteren Notebooks wurden aus demselben Colab-Notebook heraus mit
`nbclient` in jeweils einem frischen Python-Kernel der Google-Laufzeit
ausgeführt. Grundlage war GitHub-Commit `d7b116f`; Notebook 05 erhielt dabei
die unten beschriebene VPI-Korrektur. Es wurden keine Google-Drive-Dateien
eingebunden. Die Laufzeit verwendete Python 3.13.15 unter Linux.

**Alle neun Notebooks bestanden auch in Colab: 105 von 105 Codezellen,
keine Fehlerausgaben.** Notebook 05 bestand zusätzlich einen vollständigen
Lauf mit `AKTUALISIEREN=True` und zunächst leerem Datenverzeichnis. Damit
ist auch der Bezug des kuratierten VPI aus GitHub bei aktivierter
Aktualisierung geprüft.

| Notebook | Codezellen | Laufzeit | Ergebnis |
|---|---:|---:|---|
| 00 Zugang und Daten | 13 | interaktiv ausgeführt | bestanden |
| 01 Analytisches Datenmodell | 10 | 26,5 s | bestanden |
| 02 RFM und Kundensegmente | 11 | 21,6 s | bestanden |
| 03 Warenkorbanalyse | 10 | 18,2 s | bestanden |
| 04 Nachfrageprognose | 13 | 14,9 s | bestanden |
| 05 Wetter und Ereignisse | 13 | 15,2 s | bestanden |
| 06 Zufriedenheit erklären | 9 | 24,0 s | bestanden |
| 07 Ausreißer Tagesumsatz | 11 | 11,8 s | bestanden |
| 08 Sentiment Rezensionen | 15 | 133,1 s | bestanden |
| 05 zusätzlich mit Aktualisierung | 13 | 17,2 s | bestanden |

Der BERT-Vergleich lief auf allen 500 Texten: 94,2 % Treffer für BERT,
100,0 % für TF-IDF mit logistischer Regression. Verwendet wurden pandas
2.2.3, NumPy 2.1.3, scikit-learn 1.6.1, mlxtend 0.23.4, statsmodels
0.15.0, Dash 4.4.1, Transformers 5.16.1, PyTorch 2.11.0+cpu und
nbclient 0.10.4.

## Dash im Browser

Die eigenständige Anwendung `dash/app.py` lief lokal gegen die echte Datenbank
mit dem öffentlichen Nur-Lese-Demo-Konto. Geprüft wurden die gerenderten
Kennzahlkacheln und die Diagramme für Monatsumsatz, Kanalanteile und
Produktbewertungen. Die Werte für 2025 waren 2,99 Mio. Euro Umsatz,
136.557 Bestellungen, 21,93 Euro durchschnittlicher Bestellwert und
3,82 von 5 Zufriedenheit.

Der Filialfilter wurde von „Alle Filialen“ auf „BM Europastern“, danach auf
„BM Zellerau“ und zurück auf die Gesamtsicht umgestellt. Die Umsatzkurve
aktualisierte sich erfolgreich. Die Browserkonsole meldete keine Fehler.

Die kleinere Dash-App aus Notebook 00 wurde zusätzlich in Colab mit
`app.run(jupyter_mode="inline", port=8050)` gestartet. Die Inline-Ausgabe
erschien. Der interaktive Wechsel auf „BM Europastern“ wurde über die von
Colab bereitgestellte App-Adresse im selben Browser geprüft; die Kurve
aktualisierte sich. Die automatisierte Bedienung im verschachtelten Iframe
selbst war durch eine Koordinatenbeschränkung des Browserwerkzeugs nicht
möglich. Das ist eine Grenze dieses Testwerkzeugs, kein festgestellter
Anwendungsfehler.

Die Dokumentation unterscheidet jetzt ausdrücklich zwischen der kleinen
Notebook-App mit Monatsumsatz und der eigenständigen App mit vier Karten.

## Externe Daten und behobener Fehler

`AKTUALISIEREN=True` führte bisher trotz vorhandener `vpi_jahr.csv` zu
`FileNotFoundError`. Der Schalter übersprang sowohl die lokale Datei als auch
die GitHub-Fassung; für diese kuratierte Quelle existiert kein automatischer
Abruf.

`hole_oder_lies` aktualisiert jetzt ausschließlich Quellen mit Abruffunktion.
Der VPI bleibt unabhängig vom Schalter lokal oder über GitHub lesbar.
Vier Regressionstests decken die lokale und die entfernte kuratierte Datei
sowie API-Quellen mit aktiviertem und deaktiviertem Schalter ab.

Echte API-Abrufe in einem getrennten Testverzeichnis lieferten:

| Quelle | Zeilen |
|---|---:|
| Open-Meteo, Tageswetter | 3.304 |
| OpenHolidays, Schulferien Bayern | 70 |
| OpenLigaDB, Kickers-Heimspiele | 110 |
| Kuratierter VPI, weiterhin gelesen | 10 |

Die versionierten CSV-Dateien wurden dabei nicht überschrieben. Die
eingecheckten Notebook-Ausgaben verwenden weiterhin den dokumentierten
Datenstand mit `AKTUALISIEREN=False`. Für aktualisierte Daten müssen die
statischen Deutungstexte anhand der neuen Ergebnisse erneut eingeordnet
werden.

Notebook 05 lief nach der Korrektur unter Windows erneut vollständig:
13 von 13 Codezellen, keine Fehlerausgaben, etwa 14 Sekunden. Die vier neuen
Regressionstests und die fünf vorhandenen Dash-Tests bestanden zusammen:

```text
python -m pytest notebooks/tests/test_externe_daten.py dash/test_app.py -q
9 passed
```
