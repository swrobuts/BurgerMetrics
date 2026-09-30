#!/usr/bin/env python3
"""bau_09.py — schreibt notebooks/09_rezensionen_freigeben.ipynb."""
from gemeinsam import code, kopf, md, schreiben

ZELLEN = kopf("09", "Rezensionen freigeben", "09_rezensionen_freigeben.ipynb") + [
md("""
## Fragestellung

Im Shop schreiben Besucherinnen und Besucher Rezensionen. Welche dürfen ohne den Blick eines
Menschen erscheinen, welche muss jemand prüfen, und welche gehen an die Qualitätssicherung?
Ein Prüfdienst fragt dafür Jev, ein System-One-Modell von TypeSafe: sechs Ja-Nein-Fragen je
Rezension, jede Antwort eine Wahrscheinlichkeit für „ja“. Entscheiden tun Regeln im Code, nicht
das Modell. Dieses Notebook prüft Fragen und Regeln an Testfällen, deren richtige Antwort vorher
feststand.

Fehler sind unterschiedlich teuer. Die Beträge sind Annahmen, keine Messung:

| Fehler | Kosten |
|---|---|
| Gesundheitsrisiko nicht als QS-Fall erkannt | 500 € |
| Problematische Rezension automatisch veröffentlicht | 200 € |
| Harmlose Rezension unnötig zurückgehalten oder unnötiger QS-Fall | 1 € |
"""),
code("""
# Das Paket bm_jev ist dasselbe wie im Prüfdienst. Im Repo liegt es eine Ebene
# höher; in Colab holt diese Zelle Paket, Testdaten und Cache einmal von GitHub.
import sys
import urllib.request
from pathlib import Path

ROH = "https://raw.githubusercontent.com/swrobuts/BurgerMetrics/main"
LFS = "https://media.githubusercontent.com/media/swrobuts/BurgerMetrics/main"
MODULE = ["__init__", "fragen", "muster", "regeln", "jev", "testdaten", "auswertung", "umgebung"]
DATEIEN = [(LFS, "dataset/moderation_testfaelle.csv"), (LFS, "dataset/moderation_holdout.csv"),
           (LFS, "dataset/moderation_stichprobe.csv"), (ROH, "dataset/cache/moderation_jev.jsonl")]

def holen(quelle, pfad, wurzel):
    # Lädt eine Datei des Repos nach wurzel/pfad
    ziel = wurzel / pfad
    ziel.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(f"{quelle}/{pfad}", ziel)

WURZEL = Path("..").resolve()
if not (WURZEL / "bm_jev").exists():
    WURZEL = Path("bm_jev_projekt").resolve()
    for modul in MODULE:
        holen(ROH, f"bm_jev/{modul}.py", WURZEL)
    for quelle, pfad in DATEIEN:
        holen(quelle, pfad, WURZEL)
sys.path.insert(0, str(WURZEL))
from bm_jev import auswertung, fragen, jev, muster, regeln, testdaten
print("Paket bm_jev aus", WURZEL)
"""),
code("""
# NUR_CACHE = True liest nur gespeicherte Antworten und verbraucht keine Tokens.
# Mit False gehen fehlende Anfragen an Jev; dafür muss TYPESAFE_API_KEY gesetzt sein.
NUR_CACHE = True
print("Modell:", jev.MODELL, "· Fragen-Stand:", fragen.FRAGEN_STAND,
      "· Fingerabdruck:", fragen.fingerabdruck(), "· Regeln:", regeln.REGEL_VERSION)
"""),
md("""
## Daten

Drei Dateien, alle in `dataset/`:

- `moderation_testfaelle.csv`: 80 Rezensionen mit Soll-Werten für die sechs Fragen, die Muster und
  die Entscheidung. Darunter harte Kritik, die erscheinen soll, Beleidigungen, Namen von
  Mitarbeitenden, Werbung, Kontaktdaten, Themenfremdes, Anweisungen an das Prüfsystem, zehn
  Gesundheitsrisiken und Grenzfälle.
- `moderation_holdout.csv`: 24 weitere Fälle nach denselben Regeln, geschrieben vor der ersten
  Auswertung und erst im Abschnitt „Holdout“ ausgewertet.
- `moderation_stichprobe.csv`: 500 simulierte Rezensionen aus `fact_reviews.csv`, 100 je
  Sternzahl. Soll ist für alle „freigeben ohne QS-Fall“.

Nach welchen Regeln die Soll-Werte gesetzt sind, steht in `docs/moderation_konventionen.md`.
Claude hat Texte und Soll-Werte geschrieben; niemand hat sie unabhängig geprüft.
"""),
code("""
import pandas as pd

testfaelle = testdaten.lesen(testdaten.DATEIEN["testfaelle"])
holdout = testdaten.lesen(testdaten.DATEIEN["holdout"])
stichprobe = testdaten.lesen(testdaten.DATEIEN["stichprobe"])
print(f"{len(testfaelle)} Testfälle, {len(holdout)} Holdout-Fälle, {len(stichprobe)} simulierte Rezensionen.")
pd.DataFrame(testfaelle).groupby("gruppe").agg(
    faelle=("fall_id", "size"),
    zurueckhalten=("soll_entscheidung", lambda s: int((s == "zurueckgehalten").sum())),
    qs_faelle=("soll_qs_fall", "sum")).sort_values("faelle", ascending=False)
"""),
code("""
# Je Gruppe ein Beispiel mit der Soll-Entscheidung
pd.set_option("display.max_colwidth", None)
pd.DataFrame(testfaelle)[["fall_id", "gruppe", "text", "soll_entscheidung"]].groupby("gruppe").head(1)
"""),
md("""
## Vorgehen

Jede Rezension geht in einem Request an Jev, mit sechs Fragen vom Typ Noul: ja oder nein, die
Antwort ist eine Wahrscheinlichkeit für „ja“. Jev sieht nur den Text und den Produktnamen. Vorher
sucht Code nach E-Mail-Adressen, Telefonnummern und Links; solche Zeichenketten gehören zu Jevs
bekannten Schwächen. Aus Wahrscheinlichkeiten und Mustern entscheiden fünf Regeln: freigeben oder
zurückhalten, dazu bei einem Gesundheitsrisiko ein QS-Fall. Ablehnen kann nur ein Mensch.

### Die Fragen an Jev
"""),
code("""
pd.DataFrame([{"Frage": name, "Anweisung": q["instructions"], "ja heißt": q["criteria"]["true"],
               "nein heißt": q["criteria"]["false"]} for name, q in fragen.FRAGEN.items()])
"""),
md("""
Der State ist klein: Text und Produkt. Sterne, Filiale und Zeitpunkt bleiben draußen, weil keine
der Fragen sie braucht. So sieht ein Request aus:
"""),
code("""
import json

beispiel = jev.anfrage(testfaelle[0]["text"], testfaelle[0]["produkt"])
print(json.dumps({"state": beispiel["state"], "model": beispiel["model"],
                  "questions": {"gesundheitsrisiko": beispiel["questions"]["gesundheitsrisiko"]}},
                 ensure_ascii=False, indent=2))
"""),
md("""
### Lauf aus dem Cache

Die Antworten liegen in `dataset/cache/moderation_jev.jsonl`. Ein Lauf kostet nichts, solange
Modell, State und Wortlaut der Fragen gleich bleiben.
"""),
code("""
cache = jev.Cache(testdaten.WURZEL / "dataset" / "cache" / "moderation_jev.jsonl")
schluessel = None if NUR_CACHE else jev.api_schluessel()

def mit_antworten(zeilen):
    # Ergänzt jede Zeile um die Mustertreffer und Jevs Wahrscheinlichkeiten
    return [{**z, "muster": muster.treffer(z["text"]),
             "p": jev.beurteilen(z["text"], z["produkt"], cache=cache, api_key=schluessel).wahrscheinlichkeiten}
            for z in zeilen]

lauf = mit_antworten(testfaelle)
stichprobe_lauf = mit_antworten(stichprobe)
print(f"{len(lauf)} Testfälle und {len(stichprobe_lauf)} simulierte Rezensionen beurteilt.")
"""),
code("""
import matplotlib.pyplot as plt

abb, achsen = plt.subplots(2, 3, figsize=(11, 6), sharex=True, sharey=True)
for achse, frage in zip(achsen.flat, testdaten.FRAGEN):
    for soll, farbe, name in ((0, "#9CA3AF", "Soll nein"), (1, "#1E3A8A", "Soll ja")):
        werte = [z["p"][frage] for z in lauf if z[f"soll_{frage}"] == soll]
        achse.hist(werte, bins=20, range=(0, 1), color=farbe, alpha=0.85, label=name)
    achse.set_title(frage)
    achse.spines[["top", "right"]].set_visible(False)
achsen.flat[0].legend(frameon=False)
abb.supxlabel("Wahrscheinlichkeit für „ja“")
plt.tight_layout()
plt.show()
"""),
md("""
Liegen die blauen Balken rechts und die grauen links, trennt die Frage gut. Überlappen sie, hilft
keine Schwelle.

### Regeln und Confusion Matrices

Die Regeln aus `bm_jev/regeln.py`, in dieser Reihenfolge; alle zutreffenden Gründe werden
festgehalten:

1. Muster gefunden: zurückhalten, Grund „Kontaktdaten oder Link“.
2. Gesundheitsrisiko ab seiner Schwelle: QS-Fall und zurückhalten.
3. Beleidigung, Personenbezug, Werbung oder Anweisung ab der Verstoß-Schwelle: zurückhalten mit
   dieser Frage als Grund.
4. Eine dieser vier zwischen Unsicherheits- und Verstoß-Schwelle oder Themenbezug unter seiner
   Schwelle: zurückhalten, Grund „unsicher“.
5. Sonst freigeben.
"""),
code("""
pd.Series(regeln.SCHWELLEN, name="Schwelle").to_frame()
"""),
code("""
bewertet = auswertung.bewerten(lauf)
zeilen = []
for frage in testdaten.FRAGEN:
    schwelle = auswertung.schwelle_fuer(frage)
    k = auswertung.konfusion(bewertet, frage, schwelle)
    zeilen.append({"Frage": frage, "Schwelle": schwelle, **k,
                   "Recall": auswertung.recall(k), "Präzision": auswertung.praezision(k)})
pd.DataFrame(zeilen).round(2)
"""),
md("""
`tp`: Soll ja, Jev über der Schwelle. `fn`: Soll ja, Jev darunter, also übersehen. `fp`: Soll
nein, Jev darüber. `tn`: beide nein. Der Recall sagt, welcher Anteil der echten Fälle erkannt
wurde; die Präzision, welcher Anteil der Treffer stimmt. Für die Entscheidung zählen die Fragen
zusammen:
"""),
code("""
k = auswertung.konfusion_entscheidung(bewertet)
qs = auswertung.konfusion_qs(bewertet)
print("Entscheidung, positiv heißt zurückhalten:", k)
print(f"Gesundheitsrisiken als QS-Fall erkannt: {qs['tp']} von {qs['tp'] + qs['fn']} "
      f"(Recall {auswertung.recall(qs):.2f})")
print(f"Fehlerkosten auf den Testfällen: {auswertung.kosten(bewertet)} €")
"""),
code("""
fehler = [{"Fall": z["fall_id"], "Gruppe": z["gruppe"], "Text": z["text"],
           "Gründe": ", ".join(z["ist_gruende"]), "Fehler": z["fehler"]}
          for z in bewertet if z["fehler"]]
pd.DataFrame(fehler) if fehler else "Keine Fehlentscheidung."
"""),
md("""
### Schwellen durchspielen

Welche Schwellen wären auf den Testfällen am günstigsten? Das Gitter probiert 144 Kombinationen;
die Kosten zählen nach der Tabelle oben. Eine andere Kombination wird nur übernommen, wenn sie
mindestens 200 € spart oder einen verpassten Gesundheitsfall vermeidet. Kleinere Unterschiede
auf 80 Fällen wären Zufall.
"""),
code("""
ergebnisse = pd.DataFrame(auswertung.schwellen_durchspielen(lauf, auswertung.gitter()))
print(f"Aktuelle Schwellen: {auswertung.kosten(bewertet)} €; "
      f"günstigste Kombination: {ergebnisse['kosten'].min()} €")
ergebnisse.head(10)
"""),
md("""
### Holdout

Der Holdout wird genau einmal ausgewertet, mit den Schwellen, die oben feststehen. Was er zeigt,
ändert die Schwellen nicht mehr; sonst wäre er kein Holdout.
"""),
code("""
holdout_bewertet = auswertung.bewerten(mit_antworten(holdout))
k = auswertung.konfusion_entscheidung(holdout_bewertet)
qs = auswertung.konfusion_qs(holdout_bewertet)
print("Entscheidung, positiv heißt zurückhalten:", k)
print(f"Gesundheitsrisiken als QS-Fall erkannt: {qs['tp']} von {qs['tp'] + qs['fn']}")
print(f"Fehlerkosten im Holdout: {auswertung.kosten(holdout_bewertet)} €")
fehler = [{"Fall": z["fall_id"], "Text": z["text"], "Gründe": ", ".join(z["ist_gruende"]),
           "Fehler": z["fehler"]} for z in holdout_bewertet if z["fehler"]]
pd.DataFrame(fehler) if fehler else "Keine Fehlentscheidung im Holdout."
"""),
md("""
### Unnötige Zurückhaltungen in der Simulation

Die simulierten Rezensionen sind harmlos; jede Zurückhaltung kostet eine Moderatorin Zeit.
"""),
code("""
stichprobe_bewertet = auswertung.bewerten(stichprobe_lauf)
je_stern = pd.DataFrame([{"Sterne": int(z["gruppe"][-1]),
                          "zurückgehalten": z["ist_entscheidung"] == "zurueckgehalten",
                          "QS-Fall": z["ist_qs_fall"]} for z in stichprobe_bewertet])
je_stern.groupby("Sterne").mean().mul(100).round(1).add_suffix(" in %")
"""),
code("""
gehalten = [{"Fall": z["fall_id"], "Sterne": z["gruppe"][-1], "Text": z["text"],
             "Gründe": ", ".join(z["ist_gruende"])}
            for z in stichprobe_bewertet if z["ist_entscheidung"] == "zurueckgehalten"]
print(f"{len(gehalten)} von {len(stichprobe_bewertet)} simulierten Rezensionen zurückgehalten.")
pd.DataFrame(gehalten).head(15) if gehalten else "Keine Zurückhaltung."
"""),
md("""
### Live-Zahlen aus dem Shop

Seit der Prüfdienst läuft, zählt `wawi.v_freigabe_statistik` die Shop-Rezensionen je Tag und
Status, ohne Texte. Das Demo-Konto darf die Sicht lesen.
"""),
code("""
try:
    live = lade_sql("SELECT tag, status, anzahl FROM wawi.v_freigabe_statistik ORDER BY tag, status")
except Exception as fehler:
    live = None
    print("Live-Zahlen nicht erreichbar:", type(fehler).__name__)
if live is not None and len(live):
    display(live.pivot_table(index="tag", columns="status", values="anzahl", fill_value=0).tail(14))
elif live is not None:
    print("Noch keine Shop-Rezensionen.")
"""),
md("""
## Ergebnis

Auf den 80 Testfällen erkennen die Regeln 12 von 12 Gesundheitsrisiken als QS-Fall (Recall 1,0)
und veröffentlichen keine problematische Rezension. 19 harmlose Fälle halten sie unnötig zurück;
die Fehlerkosten liegen bei 19 €. Die Schwellen bleiben bei den Startwerten, weil keine Kombination
mindestens 200 € spart: Die günstigste, mit einem Themenbezug ab 0,6, kostet 7 € und vermeidet
keinen verpassten Gesundheitsfall. Im Holdout, einmal ausgewertet, erkennen die Regeln 3 von 3
Gesundheitsrisiken, veröffentlichen keine problematische Rezension und kommen auf 5 €
Fehlerkosten. Von 500 simulierten Rezensionen halten sie 254 zurück (50,8 Prozent), fast immer
mit dem Grund „unsicher“: Bei 244 davon liegt nur die Wahrscheinlichkeit für den Themenbezug
unter 0,8, etwa bei kurzen Urteilen über Geschmack, Temperatur oder Portion eines Produkts. Der
Median dieser Wahrscheinlichkeit liegt in der Stichprobe genau bei 0,8.
"""),
md("""
## Was offen bleibt

- Die Soll-Werte hat Claude gesetzt; niemand hat sie unabhängig geprüft. Ein zweites Urteil je
  Fall würde zeigen, wo schon Menschen uneins sind.
- 80 Testfälle und 24 im Holdout sind wenig. Ein einzelner Fall verschiebt den Recall beim
  Gesundheitsrisiko um mehrere Prozentpunkte.
- Jev ist vor allem auf Englisch trainiert; die Fragen sind deutsch. Die Messung gilt für diese
  Fragen, nicht allgemein.
- Die Fehlerkosten sind Annahmen. Andere Beträge führen zu anderen Schwellen.
- Echte Besucher schreiben anders als die Testfälle. Die Live-Zahlen zeigen, wie oft der Dienst
  zurückhält; ob er dabei richtig liegt, sieht erst die Moderation im POS.
- Die Schwelle für den Themenbezug bestimmt die Arbeit der Moderation: Bei 0,8 hält der Dienst
  die Hälfte der simulierten Rezensionen zurück, bei 0,6 wären es 60 von 500, auf den Testfällen
  ohne verpassten Gesundheitsfall und ohne veröffentlichte problematische Rezension. Die
  Kostentabelle setzt eine unnötige Zurückhaltung mit 1 € an; ob das die Arbeit der Moderation
  trifft, entscheidet der Betrieb, nicht dieses Notebook.
"""),
]

schreiben("09_rezensionen_freigeben.ipynb", ZELLEN)
