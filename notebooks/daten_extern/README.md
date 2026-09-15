# Externe Daten (einmal geholt, versioniert)

| Datei | Quelle | Stand | Lizenz |
|---|---|---|---|
| `wetter_open_meteo.csv` | Open-Meteo Historical Weather API, Würzburg 49,79 N / 9,95 O, täglich `temperature_2m_max/min`, `precipitation_sum` | 13.09.2026 | Daten CC BY 4.0, API für nicht-kommerzielle Nutzung kostenfrei |
| `schulferien_bayern.csv` | OpenHolidays API (`openholidaysapi.org/SchoolHolidays`, DE-BY) | 13.09.2026 | frei (Open Data der Länder) |
| `kickers_heimspiele.csv` | OpenLigaDB (`api.openligadb.de`), Würzburger Kickers: 2. Bundesliga 2016/17 und 2020/21, 3. Liga 2017/18 bis 2019/20 und 2021/22; Regionalliga Bayern 2022/23 bis 2025/26 dort nicht abgedeckt | 13.09.2026 | frei |
| `vpi_jahr.csv` | Destatis, Verbraucherpreisindex Deutschland, 2020 = 100 (Herkunft je Zeile in der Spalte `quelle`) | 10.09.2026 | Datenlizenz Deutschland 2.0 |

Notebook 05 liest zuerst diese Dateien; fehlen sie — etwa in Colab, wo der Ordner
`daten_extern/` nicht existiert —, liest es dieselben Dateien aus GitHub (Branch `main`). Erst
wenn auch das scheitert oder `AKTUALISIEREN = True` gesetzt ist, ruft es die Anbieter erneut.
Der kuratierte VPI hat keinen automatischen Abruf und wird unabhängig von diesem Schalter
aus der lokalen Datei oder aus GitHub gelesen.
Feiertage kommen aus dem Python-Paket `holidays` (MIT) und brauchen keine Datei.
