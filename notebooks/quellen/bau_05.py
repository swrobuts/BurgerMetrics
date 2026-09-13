#!/usr/bin/env python3
"""bau_05.py — schreibt notebooks/05_wetter_und_ereignisse.ipynb."""
from gemeinsam import code, kopf, md, schreiben

ZELLEN = kopf("05", "Wetter und Ereignisse", "05_wetter_und_ereignisse.ipynb") + [
md("""
## Fragestellung

Wie stark hängt der Tagesumsatz von Wetter, Wochentag, Feiertagen und Ereignissen ab — und
was ändert sich, wenn wir statt des eingebauten Wetters gemessene Daten von außen nehmen?

## Daten

Tagesumsatz aller Filialen aus `fact_orders`, Kalender aus `dim_date`, Wetter aus
`dim_weather`. Dazu fünf externe Quellen: Open-Meteo (gemessenes Wetter), Feiertage Bayern
(Paket `holidays`), Schulferien Bayern (OpenHolidays API), Heimspiele der Würzburger Kickers
(OpenLigaDB) und der Verbraucherpreisindex (Destatis, kuratierte CSV). Jede API-Antwort wird
einmal geholt und unter `daten_extern/` versioniert.

## Vorgehen

Erst eine Regression des Tagesumsatzes auf die eingebauten Merkmale, dann die externen
Quellen holen, über das Datum verknüpfen und die Fragen stellen, die nur sie beantworten:
Stimmt `dim_weather` mit dem gemessenen Wetter überein? Zählen Ferien und Heimspiele? Wie
sieht der Umsatz real statt nominal aus?
"""),
code("""
tage = lade_sql(\"\"\"
    SELECT o.date AS tag, sum(o.net_total) AS umsatz, count(*) AS bestellungen,
           d.year AS jahr, d.day_name AS wochentag, d.is_holiday AS feiertag, d.holiday_name AS feiertagsname,
           d.special_event AS ereignis, w.temperature_celsius AS temperatur, w.precipitation_mm AS niederschlag,
           w.condition AS wetterlage
    FROM fact_orders o
    JOIN dim_date d ON d.date = o.date
    LEFT JOIN dim_weather w ON w.date = o.date
    GROUP BY o.date, d.year, d.day_name, d.is_holiday, d.holiday_name, d.special_event,
             w.temperature_celsius, w.precipitation_mm, w.condition
    ORDER BY o.date\"\"\")
tage["tag"] = pd.to_datetime(tage["tag"])
tage["feiertag"] = tage["feiertag"].astype(int)
tage["ereignis"] = tage["ereignis"].fillna("keines")
print(f"{zahl(len(tage))} Tage, {tage['tag'].min().date()} bis {tage['tag'].max().date()}.")
tage.head()
"""),
md("""
### Regression auf die eingebauten Merkmale

Eine lineare Regression mit `statsmodels` — die Jahre als Kategorie fangen das Wachstum ab,
damit Wetter und Kalender nicht den Trend erklären müssen.
"""),
code("""
import statsmodels.formula.api as smf

modell = smf.ols("umsatz ~ temperatur + niederschlag + C(wochentag) + feiertag + C(ereignis) + C(jahr)", data=tage).fit()
koeffizienten = pd.DataFrame({"koeffizient": modell.params, "p_wert": modell.pvalues}).round(3)
print(f"R² = {zahl(modell.rsquared, 3)} auf {zahl(int(modell.nobs))} Tagen.")
koeffizienten.loc[[z for z in koeffizienten.index if not z.startswith("C(jahr)")]]
"""),
md("""
Wochentage und Ereignisse tragen: Kiliani ist in der Regression die Basiskategorie und
erscheint deshalb nicht als eigene Zeile; ein Tag ohne Ereignis (keines) liegt 1.158,64 €
darunter. Niederschlag trägt praktisch nicht bei (p = 0,516); Temperatur ist mit 41,64 € je
Grad statistisch signifikant (p < 0,001) und damit kein kleiner Koeffizient.

### Externe Quellen holen (oder aus der Datei lesen)
"""),
code("""
import requests
from pathlib import Path

DATEN = Path("daten_extern")
AKTUALISIEREN = False   # True: Anbieter erneut abrufen und die CSV-Dateien überschreiben

def hole_oder_lies(name, holen):
    # Liest daten_extern/<name>.csv, wenn vorhanden; sonst ruft die Quelle und speichert die Antwort
    pfad = DATEN / f"{name}.csv"
    if pfad.exists() and not AKTUALISIEREN:
        return pd.read_csv(pfad)
    daten = holen()
    DATEN.mkdir(exist_ok=True)
    daten.to_csv(pfad, index=False)
    print(f"{name}: {zahl(len(daten))} Zeilen von der Quelle geholt und gespeichert.")
    return daten

def hole_wetter():
    # Open-Meteo Archive: Tageswerte für Würzburg über den ganzen Zeitraum, ohne Schlüssel
    antwort = requests.get("https://archive-api.open-meteo.com/v1/archive", timeout=60, params={
        "latitude": 49.79, "longitude": 9.95, "start_date": "2017-03-15", "end_date": "2026-03-31",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum", "timezone": "Europe/Berlin"})
    antwort.raise_for_status()
    d = antwort.json()["daily"]
    return pd.DataFrame({"tag": d["time"], "tmax": d["temperature_2m_max"],
                         "tmin": d["temperature_2m_min"], "niederschlag_mm": d["precipitation_sum"]})

def hole_schulferien():
    # OpenHolidays API erlaubt höchstens 1095 Tage je Anfrage, deshalb in Blöcken
    zeilen = []
    for von, bis in [("2017-01-01", "2019-12-31"), ("2020-01-01", "2022-12-31"),
                     ("2023-01-01", "2025-12-31"), ("2026-01-01", "2026-12-31")]:
        antwort = requests.get("https://openholidaysapi.org/SchoolHolidays", timeout=60, params={
            "countryIsoCode": "DE", "subdivisionCode": "DE-BY", "validFrom": von, "validTo": bis, "languageIsoCode": "DE"})
        antwort.raise_for_status()
        for ferien in antwort.json():
            zeilen.append({"von": ferien["startDate"], "bis": ferien["endDate"], "name": ferien["name"][0]["text"]})
    return pd.DataFrame(zeilen).drop_duplicates()

def hole_kickers():
    # OpenLigaDB: Heimspiele der Würzburger Kickers in den Saisons, die die Datenbank abdeckt
    saisons = [("bl2", 2016), ("bl3", 2017), ("bl3", 2018), ("bl3", 2019), ("bl2", 2020), ("bl3", 2021)]
    zeilen = []
    for liga, saison in saisons:
        antwort = requests.get(f"https://api.openligadb.de/getmatchdata/{liga}/{saison}", timeout=60)
        antwort.raise_for_status()
        for spiel in antwort.json():
            if "rzburg" in spiel["team1"]["teamName"]:
                zeilen.append({"tag": spiel["matchDateTime"][:10], "liga": liga, "saison": saison,
                               "gegner": spiel["team2"]["teamName"]})
    return pd.DataFrame(zeilen)

wetter = hole_oder_lies("wetter_open_meteo", hole_wetter)
schulferien = hole_oder_lies("schulferien_bayern", hole_schulferien)
kickers = hole_oder_lies("kickers_heimspiele", hole_kickers)
vpi = pd.read_csv(DATEN / "vpi_jahr.csv")   # kuratiert, siehe daten_extern/README.md
pd.DataFrame({"quelle": ["Open-Meteo", "Schulferien", "Kickers-Heimspiele", "VPI"],
              "zeilen": [len(wetter), len(schulferien), len(kickers), len(vpi)]})
"""),
md("""
Feiertage kommen aus dem Paket `holidays`; ein Vergleich mit `dim_date.is_holiday` zeigt,
wo die Fallstudie und das Paket verschieden zählen.
"""),
code("""
import holidays

bayern = holidays.country_holidays("DE", subdiv="BY", years=range(2017, 2027))
tage["feiertag_paket"] = tage["tag"].dt.date.map(lambda t: int(t in bayern))
unterschied = tage[tage["feiertag"] != tage["feiertag_paket"]][["tag", "feiertagsname", "feiertag", "feiertag_paket"]]
print(f"{zahl(len(unterschied))} Tage zählen dim_date und das Paket verschieden:")
unterschied.groupby("feiertagsname", dropna=False).size().rename("tage").reset_index()
"""),
md("""
Mariä Himmelfahrt ist in Bayern nur in überwiegend katholischen Gemeinden Feiertag — in
Würzburg ja, im Paket standardmäßig nein. `dim_date` folgt Würzburg.

### Verknüpfen über das Datum
"""),
code("""
wetter["tag"] = pd.to_datetime(wetter["tag"])
ferientage = set()
for zeile in schulferien.itertuples():
    ferientage.update(pd.date_range(zeile.von, zeile.bis))
kickers["tag"] = pd.to_datetime(kickers["tag"])

daten = tage.merge(wetter, on="tag", how="left")
daten["ferien"] = daten["tag"].isin(ferientage).astype(int)
daten["heimspiel"] = daten["tag"].isin(set(kickers["tag"])).astype(int)
daten = daten.merge(vpi[["jahr", "vpi_2020_100"]], on="jahr", how="left")
daten[["tag", "umsatz", "temperatur", "tmax", "niederschlag", "niederschlag_mm", "ferien", "heimspiel", "vpi_2020_100"]].head()
"""),
md("### Stimmt das eingebaute Wetter mit dem gemessenen überein?"),
code("""
import matplotlib.pyplot as plt

r_temp = daten["temperatur"].corr(daten["tmax"])
r_regen = daten["niederschlag"].corr(daten["niederschlag_mm"])
print(f"Korrelation Temperatur (dim_weather) mit Tageshöchsttemperatur (Open-Meteo): r = {zahl(r_temp, 3)}")
print(f"Korrelation Niederschlag (dim_weather) mit gemessenem Niederschlag: r = {zahl(r_regen, 3)}")

abb, achse = plt.subplots(figsize=(9, 4))
monat = daten.set_index("tag")[["temperatur", "tmax"]].resample("MS").mean()
achse.plot(monat.index, monat["temperatur"], label="dim_weather (synthetisch)")
achse.plot(monat.index, monat["tmax"], label="Open-Meteo (gemessen, Tageshöchstwert)")
achse.set_xlabel("Monat")
achse.set_ylabel("Temperatur in °C, Monatsmittel")
achse.set_title("Das eingebaute Wetter folgt der Jahreszeit, nicht dem gemessenen Tag")
achse.legend()
plt.show()
"""),
md("""
Der Bestand ist synthetisch: Die Temperatur korreliert mit dem gemessenen Tageshöchstwert
mit r = 0,791, weil beide Reihen demselben Jahresgang folgen. Beim Niederschlag verschwindet
die Korrelation auf r = 0,009, weil Regen keinem Jahresgang folgt — hier zeigt sich, dass der
Bestand die Jahreszeit trifft, nicht das Wetter eines einzelnen Tages. Das ist kein Fehler des
Datensatzes, aber eine Grenze, die man kennen muss, bevor man Wettereffekte interpretiert.

### Regression mit den externen Merkmalen
"""),
code("""
modell_extern = smf.ols("umsatz ~ tmax + niederschlag_mm + C(wochentag) + feiertag + ferien + heimspiel + C(ereignis) + C(jahr)",
                        data=daten).fit()
print(f"R² eingebaut: {zahl(modell.rsquared, 3)}, R² extern: {zahl(modell_extern.rsquared, 3)}")
pd.DataFrame({"koeffizient": modell_extern.params, "p_wert": modell_extern.pvalues}).loc[
    ["tmax", "niederschlag_mm", "feiertag", "ferien", "heimspiel"]].round(3)
"""),
md("""
Ferien haben keinen messbaren Effekt (p = 0,914) — der Generator kannte die Schulferien
nicht. Heimspiele dagegen zeigen einen signifikanten Koeffizienten von -273,16 € (p < 0,001);
ob das ein echter Effekt des Spieltags ist oder mit dem Wochentag zusammenhängt, an dem
Heimspiele stattfinden, klärt diese Regression allein nicht. Externe Merkmale wirken hier nur,
wenn die Zielgröße tatsächlich davon abhängt; bei echten Kassendaten wäre der Test derselbe,
das Ergebnis vermutlich ein anderes.

### Umsatz real statt nominal
"""),
code("""
jahre = lade_sql("SELECT jahr, umsatz FROM v_kennzahlen_jahr ORDER BY jahr").merge(vpi[["jahr", "vpi_2020_100"]], on="jahr")
jahre["umsatz_real_2020"] = jahre["umsatz"] / jahre["vpi_2020_100"] * 100
jahre["nominal_pct"] = jahre["umsatz"].pct_change() * 100
jahre["real_pct"] = jahre["umsatz_real_2020"].pct_change() * 100
jahre.round(1)
"""),
md("""
## Ergebnis

Wochentag und Ereignisse erklären den Tagesumsatz am stärksten. Niederschlag hat keinen
messbaren Effekt; die Temperatur dagegen ist in beiden Regressionen statistisch signifikant
(p < 0,001) und mit 41,64 € beziehungsweise 37,37 € je Grad kein kleiner Koeffizient — sie
korreliert mit dem gemessenen Tageshöchstwert aber nur über den gemeinsamen Jahresgang
(r = 0,791), den Tag selbst kennt der Bestand nicht. Ferien bringen nichts (p = 0,914), der
Heimspiel-Koeffizient ist dagegen signifikant. Der Verbraucherpreisindex zeigt, dass ein Teil
des nominalen Wachstums seit 2021 Preissteigerung ist.

## Was offen bleibt

Die Kickers-Daten decken die Regionalliga-Saisons ab 2022 nicht ab; wer sie braucht, pflegt
eine CSV von Hand nach. Der VPI ist ein Jahreswert — für Monatsreihen liefert Destatis
Monatsindizes über GENESIS-Online (Konto erforderlich). Ob der Heimspiel-Koeffizient einen
eigenen Effekt misst oder mit dem Wochentag zusammenhängt, an dem Heimspiele stattfinden,
klärt diese Regression nicht.
"""),
]

schreiben("05_wetter_und_ereignisse.ipynb", ZELLEN)
