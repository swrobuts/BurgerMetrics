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
           d.year AS jahr, d.month AS monat, d.day_name AS wochentag, d.is_holiday AS feiertag, d.holiday_name AS feiertagsname,
           d.special_event AS ereignis, w.temperature_celsius AS temperatur, w.precipitation_mm AS niederschlag,
           w.condition AS wetterlage
    FROM fact_orders o
    JOIN dim_date d ON d.date = o.date
    LEFT JOIN dim_weather w ON w.date = o.date
    GROUP BY o.date, d.year, d.month, d.day_name, d.is_holiday, d.holiday_name, d.special_event,
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
die Monate die Jahreszeit — damit Wetter und Kalender nicht den Trend und die Saison erklären
müssen. Referenz sind ein Montag ohne Ereignis.
"""),
md("""
### Zuerst mit Jahres-, aber ohne Monatskontrolle

Die Jahre fangen das Wachstum ab, die Monate die Jahreszeit; wir lassen die Monate hier
absichtlich zunächst weg.
"""),
code("""
import statsmodels.formula.api as smf

ohne_saison = smf.ols("umsatz ~ temperatur + niederschlag + C(wochentag, Treatment(reference='Monday')) + feiertag + C(ereignis, Treatment(reference='keines')) + C(jahr)", data=tage).fit()
pd.DataFrame({"koeffizient": ohne_saison.params, "p_wert": ohne_saison.pvalues}).loc[["temperatur", "niederschlag"]].round({"koeffizient": 2, "p_wert": 3})
"""),
code("""
import re
import statsmodels.formula.api as smf

def kurz(name):
    # Kürzt statsmodels-Bezeichner: C(ereignis, Treatment(reference='keines'))[T.Kiliani] → ereignis[Kiliani]
    treffer = re.match(r"C\((\w+).*\)\[T\.(.+)\]$", name)
    if treffer is None:
        return name
    return f"{treffer.group(1)}[{treffer.group(2)}]"

modell = smf.ols("umsatz ~ temperatur + niederschlag + C(wochentag, Treatment(reference='Monday')) + feiertag + C(ereignis, Treatment(reference='keines')) + C(monat) + C(jahr)", data=tage).fit()
koeffizienten = pd.DataFrame({"koeffizient": modell.params, "p_wert": modell.pvalues}).round({"koeffizient": 2, "p_wert": 3})
koeffizienten.index = [kurz(n) for n in koeffizienten.index]
print(f"R² = {zahl(modell.rsquared, 3)} auf {zahl(int(modell.nobs))} Tagen.")
koeffizienten.loc[[z for z in koeffizienten.index if not z.startswith("jahr[") and not z.startswith("monat[")]]
"""),
md("""
Gegenüber einem Montag ohne Ereignis liegen Freitag (1.155,05 €), Samstag (1.614,88 €),
Sonntag (953,30 €), Donnerstag (459,60 €) und Mittwoch (221,24 €) signifikant höher
(p < 0,001); nur der Dienstag unterscheidet sich nicht von Montag (-7,60 €, p = 0,860).
Kiliani liegt 1.139,77 € über einem Tag ohne Ereignis (p < 0,001). Mit Monat und Jahr in der
Regression sind weder Temperatur (p = 0,171) noch Niederschlag (p = 0,920) bei p < 0,05
signifikant. Mit Jahres-, aber ohne Monatskontrolle sieht das anders aus: Dort liegt die
Temperatur bei rund 41,64 € je Grad und ist signifikant (p < 0,001), Niederschlag bleibt ohne
Effekt (-5,37 €, p = 0,516) — der scheinbare Temperatureffekt war die Jahreszeit, die erst die
Monatskontrolle abfängt.

### Externe Quellen holen (oder aus der Datei lesen)

In Colab fehlt der Ordner `daten_extern/`; dann liest das Notebook die versionierten Dateien
aus GitHub und ruft die Anbieter nur, wenn auch das scheitert.
"""),
code("""
import requests
from pathlib import Path

DATEN = Path("daten_extern")
AKTUALISIEREN = False   # True: API-Quellen neu abrufen; kuratierte Dateien weiterhin lesen
GITHUB = "https://raw.githubusercontent.com/swrobuts/BurgerMetrics/main/notebooks/daten_extern"

def hole_oder_lies(name, holen=None):
    # Liest daten_extern/<name>.csv, wenn vorhanden; sonst die Fassung aus GitHub (so läuft das
    # Notebook in Colab); erst wenn auch die fehlt, ruft es den Anbieter und speichert die Antwort
    pfad = DATEN / f"{name}.csv"
    aktualisieren = AKTUALISIEREN and holen is not None
    if pfad.exists() and not aktualisieren:
        return pd.read_csv(pfad)
    if not aktualisieren:
        try:
            return pd.read_csv(f"{GITHUB}/{name}.csv")
        except Exception:
            pass
    if holen is None:
        raise FileNotFoundError(f"{name}.csv ist kuratiert und liegt weder lokal noch in GitHub vor")
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
vpi = hole_oder_lies("vpi_jahr")   # kuratiert, siehe daten_extern/README.md
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

def abweichung_vom_monatsmittel(spalte):
    # Abweichung jedes Tages vom Mittel seines Kalendermonats — der Tageseffekt ohne die Jahreszeit
    return spalte - spalte.groupby(daten["tag"].dt.month).transform("mean")

r_temp_tag = abweichung_vom_monatsmittel(daten["temperatur"]).corr(abweichung_vom_monatsmittel(daten["tmax"]))
print(f"Ohne Jahreszeit (Abweichung vom Monatsmittel): r = {zahl(r_temp_tag, 3)}")

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
Der Bestand ist synthetisch: Die Rohkorrelation zwischen Temperatur (dim_weather) und dem
gemessenen Tageshöchstwert ist mit r = 0,791 hoch, weil beide Reihen demselben Jahresgang
folgen. Rechnet man die Abweichung vom Mittel des jeweiligen Kalendermonats — also ohne
Jahreszeit —, verschwindet die Korrelation auf r = -0,054: Der Bestand trifft die Jahreszeit,
nicht das Wetter eines einzelnen Tages. Niederschlag korreliert schon in der Rohfassung kaum
(r = 0,009), weil Regen keinem Jahresgang folgt. Das ist kein Fehler des Datensatzes, aber eine
Grenze, die man kennen muss, bevor man Wettereffekte interpretiert.

### Regression mit den externen Merkmalen
"""),
code("""
modell_extern = smf.ols("umsatz ~ tmax + niederschlag_mm + C(wochentag, Treatment(reference='Monday')) + feiertag + ferien + heimspiel + C(ereignis, Treatment(reference='keines')) + C(monat) + C(jahr)",
                        data=daten).fit()
print(f"R² eingebaut: {zahl(modell.rsquared, 3)}, R² extern: {zahl(modell_extern.rsquared, 3)}")
pd.DataFrame({"koeffizient": modell_extern.params, "p_wert": modell_extern.pvalues}).loc[
    ["tmax", "niederschlag_mm", "feiertag", "ferien", "heimspiel"]].round({"koeffizient": 2, "p_wert": 3})
"""),
md("### Gegenprobe: Heimspieltage gegen vergleichbare Tage"),
code("""
def abweichung_von_vergleichstagen(daten):
    # Abstand jedes Tages vom Mittel der Tage mit gleichem Wochentag im selben Monat und Jahr —
    # ein Vergleich ohne Modellannahmen; Feiertage und Ereignistage bleiben außen vor
    ohne_sondertage = daten[(daten["feiertag"] == 0) & (daten["ereignis"] == "keines")].copy()
    zellmittel = ohne_sondertage.groupby(["jahr", "monat", "wochentag"])["umsatz"].transform("mean")
    ohne_sondertage["abweichung"] = ohne_sondertage["umsatz"] - zellmittel
    return ohne_sondertage

gegenprobe = abweichung_von_vergleichstagen(daten)
gegenprobe.groupby("heimspiel").agg(tage=("abweichung", "size"), abweichung_mittel=("abweichung", "mean")).round(1)
"""),
md("""
Mit Monat und Jahr im Modell ist tmax bei p < 0,05 nicht mehr signifikant (5,20 €,
p = 0,074), Niederschlag weiterhin ohne Effekt (0,64 €, p = 0,834), Ferien bleiben nicht
messbar (-31,76 €, p = 0,367). Die Regression zeigt für Heimspiele -251,50 € (p < 0,001); die
Gegenprobe direkt darunter zeigt aber keinen negativen Unterschied: Heimspieltage liegen im
Schnitt 40,3 € über vergleichbaren Tagen (gleicher Wochentag, Monat und Jahr, ohne Feiertage
und Ereignistage), sonstige Tage -1,3 €. Der Regressionskoeffizient ist ein Artefakt der
additiven Monats- und Jahreskontrolle, die das Zusammenspiel von Wachstum und Saison nicht
abbilden kann — die Kickers-Saisons liegen gehäuft in frühen Jahren und außerhalb des Sommers.
Ein Heimspieleffekt ist damit nicht belegt, wie es für einen Generator zu erwarten ist, der die
Spieltermine nicht kannte.

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

Wochentag und Ereignisse erklären den Tagesumsatz am stärksten: Gegenüber einem Montag ohne
Ereignis liegen alle Wochentage außer Dienstag signifikant höher, Kiliani liegt 1.139,77 € über
einem Tag ohne Ereignis. Sobald Monat und Jahr die Saison und den Trend abfangen, ist weder die
eingebaute noch die gemessene Temperatur bei p < 0,05 signifikant (p = 0,171 beziehungsweise
p = 0,074); mit Jahres-, aber ohne Monatskontrolle liegt die eingebaute Temperatur dagegen
bei rund 41,64 € je Grad und ist signifikant (p < 0,001) — der scheinbare Wettereffekt war die
Jahreszeit, die erst die Monatskontrolle abfängt. Die Rohkorrelation von Temperatur und
gemessenem Tageshöchstwert liegt bei r = 0,791, ohne Jahreszeit (Abweichung vom Monatsmittel)
bei r = -0,054. Ferien bleiben ohne messbaren Effekt; die
Regression zeigt für Heimspiele -251,50 € (p < 0,001), doch die Gegenprobe an vergleichbaren
Tagen (gleicher Wochentag, Monat und Jahr) zeigt keinen negativen Unterschied (40,3 € gegenüber
-1,3 €) — der Koeffizient ist ein Artefakt der additiven Monats- und Jahreskontrolle, kein
belegter Heimspieleffekt. Der Verbraucherpreisindex zeigt, dass ein Teil des nominalen Wachstums seit 2021 Preissteigerung
ist.

## Was offen bleibt

Die Kickers-Daten decken die Regionalliga-Saisons ab 2022 nicht ab; wer sie braucht, pflegt
eine CSV von Hand nach. Der VPI ist ein Jahreswert — für Monatsreihen liefert Destatis
Monatsindizes über GENESIS-Online (Konto erforderlich). Ob 81 Heimspieltage ausreichen, um
einen kleinen echten Effekt sicher von Null zu unterscheiden, bleibt offen; mit mehr
Spieltagen oder echten Kassendaten wäre die Gegenprobe schärfer.
"""),
]

schreiben("05_wetter_und_ereignisse.ipynb", ZELLEN)
