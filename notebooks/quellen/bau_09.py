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
           (LFS, "dataset/moderation_holdout_2.csv"), (LFS, "dataset/moderation_stichprobe.csv"),
           (ROH, "dataset/cache/moderation_jev.jsonl")]

def holen(quelle, pfad, wurzel):
    # Lädt eine Datei des Repos nach wurzel/pfad
    ziel = wurzel / pfad
    ziel.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(f"{quelle}/{pfad}", ziel)

WURZEL = Path("..").resolve()
QUELLE = "aus dem Repo"
if not (WURZEL / "bm_jev").exists():
    WURZEL = Path("bm_jev_projekt").resolve()
    QUELLE = "von GitHub geladen"
    for modul in MODULE:
        holen(ROH, f"bm_jev/{modul}.py", WURZEL)
    for quelle, pfad in DATEIEN:
        holen(quelle, pfad, WURZEL)
sys.path.insert(0, str(WURZEL))
from bm_jev import auswertung, fragen, jev, muster, regeln, testdaten
print("Paket bm_jev", QUELLE)
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

Vier Dateien, alle in `dataset/`:

- `moderation_testfaelle.csv`: 80 Rezensionen mit Soll-Werten für die sechs Fragen, die Muster und
  die Entscheidung. Darunter harte Kritik, die erscheinen soll, Beleidigungen, Namen von
  Mitarbeitenden, Werbung, Kontaktdaten, Themenfremdes, Anweisungen an das Prüfsystem,
  Gesundheitsrisiken und Grenzfälle. Zwölf Fälle beschreiben ein Gesundheitsrisiko: zehn in der
  eigenen Gruppe, zwei unter den Grenzfällen.
- `moderation_holdout.csv`: 24 weitere Fälle nach denselben Regeln, geschrieben vor der ersten
  Auswertung und mit Fragen-Stand 1 einmal ausgewertet.
- `moderation_holdout_2.csv`: 24 neue Fälle, geschrieben am 01.10.2026, bevor Jev den
  Fragen-Stand 2 gesehen hat.
- `moderation_stichprobe.csv`: 500 simulierte Rezensionen aus `fact_reviews.csv`, 100 je
  Sternzahl. Soll ist für alle „freigeben ohne QS-Fall“.

Nach welchen Regeln die Soll-Werte gesetzt sind, steht in `docs/moderation_konventionen.md`.
Claude hat Texte und Soll-Werte geschrieben; niemand hat sie unabhängig geprüft.
"""),
code("""
import pandas as pd

testfaelle = testdaten.lesen(testdaten.DATEIEN["testfaelle"])
holdout = testdaten.lesen(testdaten.DATEIEN["holdout"])
holdout_2 = testdaten.lesen(testdaten.DATEIEN["holdout_2"])
stichprobe = testdaten.lesen(testdaten.DATEIEN["stichprobe"])
print(f"{len(testfaelle)} Testfälle, {len(holdout)} und {len(holdout_2)} Holdout-Fälle, "
      f"{len(stichprobe)} simulierte Rezensionen.")
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

Die Tabelle zeigt den Fragen-Stand 2. Wie Stand 1 nach dem Themenbezug fragte und warum er
abgelöst wurde, steht im Abschnitt „Fragen-Stand 1 und 2“.
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

def mit_antworten(zeilen, wortlaut=fragen.FRAGEN):
    # Ergänzt jede Zeile um die Mustertreffer und Jevs Wahrscheinlichkeiten zum gewählten Fragen-Stand
    return [{**z, "muster": muster.treffer(z["text"]),
             "p": jev.beurteilen(z["text"], z["produkt"], cache=cache, api_key=schluessel,
                                 fragen=wortlaut).wahrscheinlichkeiten}
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
auf 80 Fällen wären Zufall. Lockern kann diese Regel auf 31 harmlosen Fällen nie: Weniger strenge
Schwellen sparen höchstens die Kosten der unnötig zurückgehaltenen Fälle. Für Fragen-Stand 2 war
deshalb vorab festgelegt, dass die Schwellen bleiben; das Gitter zeigt nur, wie empfindlich die
Kosten auf sie reagieren.
"""),
code("""
ergebnisse = pd.DataFrame(auswertung.schwellen_durchspielen(lauf, auswertung.gitter()))
print(f"Aktuelle Schwellen: {auswertung.kosten(bewertet)} €; "
      f"günstigste Kombination: {ergebnisse['kosten'].min()} €")
ergebnisse.head(10)
"""),
md("""
### Holdouts

Ein Holdout wird genau einmal ausgewertet, mit den Schwellen und Fragen, die vorher feststehen.
Was er zeigt, ändert nichts mehr; sonst wäre er kein Holdout. Der erste Holdout (`H001`–`H024`)
wurde am 30.09.2026 mit Fragen-Stand 1 ausgewertet und ist damit verbraucht. Für Fragen-Stand 2
gibt es den zweiten (`Z001`–`Z024`), geschrieben, bevor Jev die neue Frage gesehen hat.
"""),
code("""
def holdout_zeigen(zeilen, wortlaut, name):
    # Wertet einen Holdout mit einem Fragen-Stand aus und zeigt Zählungen und Fehlentscheidungen
    bewertet = auswertung.bewerten(mit_antworten(zeilen, wortlaut))
    k = auswertung.konfusion_entscheidung(bewertet)
    qs = auswertung.konfusion_qs(bewertet)
    print(f"{name}: Entscheidung, positiv heißt zurückhalten: {k}")
    print(f"{name}: Gesundheitsrisiken als QS-Fall erkannt: {qs['tp']} von {qs['tp'] + qs['fn']}, "
          f"Fehlerkosten {auswertung.kosten(bewertet)} €")
    fehler = [{"Fall": z["fall_id"], "Text": z["text"], "Gründe": ", ".join(z["ist_gruende"]),
               "Fehler": z["fehler"]} for z in bewertet if z["fehler"]]
    return pd.DataFrame(fehler) if fehler else "Keine Fehlentscheidung."

holdout_zeigen(holdout, fragen.FRAGEN_STAND_1, "Erster Holdout, Stand 1")
"""),
code("""
holdout_zeigen(holdout_2, fragen.FRAGEN, "Zweiter Holdout, Stand 2")
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
def ausloeser(p):
    # Die Werte, die eine Regel auslösen: Themenbezug unter seiner Schwelle, sonst ab der Unsicherheit
    return ", ".join(f"{frage} {wert:.2f}" for frage, wert in p.items()
                     if (frage == "themenbezug" and wert < regeln.SCHWELLEN["themenbezug"])
                     or (frage != "themenbezug" and wert >= regeln.SCHWELLEN["unsicher"]))

gehalten = [{"Fall": z["fall_id"], "Sterne": z["gruppe"][-1], "Text": z["text"],
             "Gründe": ", ".join(z["ist_gruende"]), "Werte": ausloeser(z["p"])}
            for z in stichprobe_bewertet if z["ist_entscheidung"] == "zurueckgehalten"]
print(f"{len(gehalten)} von {len(stichprobe_bewertet)} simulierten Rezensionen zurückgehalten.")
pd.DataFrame(gehalten).head(15) if gehalten else "Keine Zurückhaltung."
"""),
md("""
## Fragen-Stand 1 und 2

Mit Stand 1 fragte Jev, ob es in `rezension.text` um einen Besuch, ein Produkt, das Personal oder
den Service von BurgerMetrics geht. Die simulierten Rezensionen nennen die Kette fast nie; sie
urteilen über „den Burger“ oder „die Pommes“. Jev kannte nur Text und Produktnamen und erfuhr
nicht, dass jede Rezension aus dem Shop von BurgerMetrics stammt. Stand 2 sagt es in der Frage.
Die übrigen fünf Fragen und alle Schwellen blieben gleich.

Bevor Jev Stand 2 sah, stand fest, wann er Stand 1 ablöst: alle zwölf Gesundheitsrisiken der
Testfälle erkannt, keine problematische Rezension veröffentlicht, höchstens 19 € Fehlerkosten und
in der Stichprobe weniger als 254 von 500 zurückgehalten; danach der zweite Holdout ohne
verpasstes Gesundheitsrisiko und ohne veröffentlichte problematische Rezension
(`docs/moderation_konventionen.md`). Beide Stände liegen im Cache, der Vergleich kostet nichts.
"""),
code("""
pd.DataFrame([{"Stand": stand, "Frage nach dem Themenbezug": wortlaut["themenbezug"]["instructions"]}
              for stand, wortlaut in (("1", fragen.FRAGEN_STAND_1), ("2", fragen.FRAGEN))])
"""),
code("""
def kennzahlen(zeilen, wortlaut):
    # Die Zahlen der Ablöse-Kriterien für einen Datensatz und einen Fragen-Stand
    bewertet = auswertung.bewerten(mit_antworten(zeilen, wortlaut))
    qs = auswertung.konfusion_qs(bewertet)
    fehler = [z["fehler"] for z in bewertet]
    harmlos = sum(z["soll_entscheidung"] == "freigegeben" for z in bewertet)
    return {"QS erkannt": f"{qs['tp']} von {qs['tp'] + qs['fn']}",
            "problematisch veröffentlicht": fehler.count("problem_veroeffentlicht"),
            "harmlos zurückgehalten": f"{fehler.count('unnoetig_zurueckgehalten')} von {harmlos}",
            "Fehlerkosten in €": auswertung.kosten(bewertet)}

STAENDE = (("1", fragen.FRAGEN_STAND_1), ("2", fragen.FRAGEN))
pd.DataFrame([{"Daten": name, "Stand": stand, **kennzahlen(zeilen, wortlaut)}
              for name, zeilen in (("Testfälle", testfaelle), ("Zweiter Holdout", holdout_2),
                                   ("Stichprobe", stichprobe))
              for stand, wortlaut in STAENDE])
"""),
code("""
# Wahrscheinlichkeit für den Themenbezug in der Stichprobe: untere Perzentile je Stand
themenbezug = pd.DataFrame({f"Stand {stand}": [z["p"]["themenbezug"] for z in mit_antworten(stichprobe, wortlaut)]
                            for stand, wortlaut in STAENDE})
themenbezug.quantile([0.01, 0.05, 0.1, 0.25, 0.5]).round(2).rename_axis("Perzentil")
"""),
code("""
# Die übrigen fünf Fragen: Wie weit weichen ihre Antworten zwischen den Ständen ab?
stand_1 = mit_antworten(testfaelle, fragen.FRAGEN_STAND_1)
pd.Series({frage: max(abs(a["p"][frage] - b["p"][frage]) for a, b in zip(stand_1, lauf))
           for frage in testdaten.FRAGEN if frage != "themenbezug"}, name="größte Abweichung").round(2).to_frame()
"""),
md("""
Stand 2 erfüllt alle vorab festgelegten Bedingungen. Auf den Testfällen erkennt er weiter 12 von
12 Gesundheitsrisiken und veröffentlicht keine problematische Rezension; unnötig zurückgehalten
bleibt einer von 31 harmlosen Fällen, die Fehlerkosten fallen von 19 € auf 1 €. Im zweiten
Holdout entscheidet Stand 2 alle 24 Fälle richtig; Stand 1 hätte dort 6 von 12 harmlosen Fällen
zurückgehalten. In der Stichprobe hält Stand 2 noch 9 von 500 Rezensionen zurück statt 254. Das
1-Prozent-Perzentil der Wahrscheinlichkeit für den Themenbezug steigt dort von 0,38 auf 0,86, der
Median von 0,80 auf 0,95. Themenfremde Texte und reine Anweisungen hält Stand 2 weiter zurück:
Kein Testfall mit Soll „nein“ erreicht die Schwelle (`fp` 0 in der Confusion Matrix oben). Die
übrigen fünf Fragen antworten im geänderten Request fast gleich, aber nicht exakt; die größte
Abweichung liegt bei 0,07.
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

Mit Fragen-Stand 2 erkennen die Regeln auf den 80 Testfällen 12 von 12 Gesundheitsrisiken als
QS-Fall (Recall 1,0) und veröffentlichen keine problematische Rezension. Von 31 harmlosen Fällen
halten sie einen unnötig zurück; die Fehlerkosten liegen bei 1 €, mit Stand 1 waren es 19 €. Im
zweiten Holdout, einmal ausgewertet, entscheiden sie alle 24 Fälle richtig, darunter 3 von 3
Gesundheitsrisiken. Von 500 simulierten Rezensionen halten sie 9 zurück statt 254. Den Unterschied
macht ein Satz in der Frage nach dem Themenbezug: Die Rezension stammt aus dem Shop von
BurgerMetrics. Die Schwellen sind die Startwerte; das Gitter findet keine Kombination unter 1 €.
"""),
md("""
## Was offen bleibt

- Die Soll-Werte hat Claude gesetzt; niemand hat sie unabhängig geprüft. Ein zweites Urteil je
  Fall würde zeigen, wo schon Menschen uneins sind.
- 80 Testfälle und je 24 Fälle in zwei Holdouts sind wenig. Ein einzelner Fall verschiebt den
  Recall beim Gesundheitsrisiko um mehrere Prozentpunkte.
- Jev ist vor allem auf Englisch trainiert; die Fragen sind deutsch. Die Messung gilt für diese
  Fragen, nicht allgemein.
- Die Fehlerkosten sind Annahmen. Andere Beträge führen zu anderen Schwellen.
- Echte Besucher schreiben anders als die Testfälle. Die Live-Zahlen zeigen, wie oft der Dienst
  zurückhält; ob er dabei richtig liegt, sieht erst die Moderation im POS.
- Die Frage nach dem Themenbezug wurde nach einem Befund auf Testfällen und Stichprobe
  umformuliert. Der zweite Holdout bestätigt den neuen Stand, ist mit 24 Fällen aber klein, und
  auch seine Texte hat Claude geschrieben.
- Eine geänderte Frage verschiebt die Antworten der anderen leicht (hier bis 0,07). Wer eine
  Frage ändert, prüft deshalb alle sechs neu.
"""),
]

schreiben("09_rezensionen_freigeben.ipynb", ZELLEN)
