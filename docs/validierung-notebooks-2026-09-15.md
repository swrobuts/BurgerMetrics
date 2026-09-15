# Vollständige Notebook-Abnahme am 15. September 2026

**Alle neun Notebooks bestanden: 105 von 105 Codezellen ausgeführt, keine
Fehlerausgaben oder fehlenden Pflichtabschnitte.** Die frischen Ausgaben sind
in den Notebooks gespeichert. Getestet wurde gegen die echte Datenbank mit
der bereits auf ausschließlich lesende Datenzugriffe eingeschränkten Rolle
`studi_daba`.

## Umfang und Ergebnisse

Jedes Notebook lief mit einem frischen Jupyter-Kernel unter Windows und
Python 3.12.14. Ausführung mit `nbclient` 0.11.0, maximal 1.800 Sekunden je
Zelle, anschließend Kontrolle mit `notebooks/quellen/pruefe_ausgaben.py`.
Die Notebooks 00 und 03 wurden nach ihren gezielten Korrekturen erneut
vollständig ausgeführt. Die folgende Tabelle enthält den jeweils letzten Lauf.

| Notebook | Codezellen | Laufzeit | Ergebnis |
|---|---:|---:|---|
| 00 Zugang und Daten | 13 | 10 s | bestanden |
| 01 Analytisches Datenmodell | 10 | 27 s | bestanden |
| 02 RFM und Kundensegmente | 11 | 33 s | bestanden |
| 03 Warenkorbanalyse | 10 | 11 s | bestanden |
| 04 Nachfrageprognose | 13 | 15 s | bestanden |
| 05 Wetter und Ereignisse | 13 | 12 s | bestanden |
| 06 Zufriedenheit erklären | 9 | 16 s | bestanden |
| 07 Ausreißer Tagesumsatz | 11 | 10 s | bestanden |
| 08 Sentiment Rezensionen | 15 | 104 s | bestanden |

Die Laufzeiten enthalten die Notebook-Ausführung; die erstmalige Installation
der Pakete ist nicht enthalten. Es wurden zehn PNG-Diagramme erzeugt.
Die Grafiken aus Prognose, Wettervergleich und Sentiment wurden zusätzlich
visuell geprüft. Der BERT-Vergleich lief tatsächlich auf allen 500 vorgesehenen
Texten: 94,2 % Treffer für BERT, 100,0 % für TF-IDF/logistische Regression.

## Behobene Fehler

1. **Installation unter Windows:** Die einfachen Shell-Anführungszeichen um
   `mlxtend>=0.23.2` führten zu `Invalid requirement`. `%pip` ließ die Zelle
   trotzdem als ausgeführt erscheinen. Das gemeinsame Bauskript verwendet
   jetzt eine Argumentliste und `subprocess.check_call`; Installationsfehler
   werden damit zu echten Notebook-Fehlern. Alle neun Installationszellen
   wurden erfolgreich ausgeführt.
2. **Produktpaare mit gleichem Support:** Notebook 03 entfernte Duplikate
   anhand der Häufigkeit. Dadurch verschwand eines von zwei unterschiedlichen,
   gleich häufigen Produktpaaren. Die Auswahl verwendet jetzt die beiden
   Produktnamen unabhängig von ihrer Reihenfolge. Ein Regressionstest mit
   zwei gleich häufigen Paaren prüft außerdem die unveränderten Konfidenzen
   beider Regelrichtungen.
3. **Aussagekraft der Rechteprobe:** Notebook 00 fordert für seine Negativprobe
   ausdrücklich eine schreibbare Transaktion an und akzeptiert ausschließlich
   SQLSTATE `42501` als Nachweis fehlender Schreibrechte. `WHERE false` verhindert
   jede Zeilenänderung, selbst bei fehlerhafter Rechtevergabe. Verbindungsfehler,
   SQL-Fehler und unerwartet erlaubtes Schreiben lassen die Abnahme scheitern.

Zusätzlicher Test:
`python -m pytest notebooks/tests/test_warenkorb.py -q` — **1 bestanden**.

## Laufzeitumgebung und Grenzen

Verwendet wurden pandas 3.0.5, NumPy 2.5.3, scikit-learn 1.9.1,
mlxtend 0.25.0, statsmodels 0.15.0, Matplotlib 3.11.2,
Transformers 5.17.0 und PyTorch 2.14.0.

Die Standardparameter blieben erhalten: externe Wetter-/Ereignisdaten aus
den mitgelieferten CSV-Dateien (`AKTUALISIEREN=False`),
`DASH_STARTEN=False`. Die Dash-App wurde zusätzlich über ihren Flask-Testclient
geprüft: Startseite und Layout antworten erfolgreich; die Filter für alle
Filialen und Filiale 1 liefern jeweils 109 Monatswerte. Ein sichtbarer
interaktiver Dash-Server und die Google-Colab-Oberfläche wurden nicht geöffnet.

Die Abnahme belegt die Ausführbarkeit der Analysen und ihrer Diagramme mit
diesem Datenstand. Sie ersetzt keine Prüfung an echten, nicht synthetisch
erzeugten Geschäftsdaten. Insbesondere ist die sehr hohe Sentiment-Trefferquote
weiterhin durch die im Notebook erläuterten Generatorbausteine geprägt.
