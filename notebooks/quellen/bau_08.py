#!/usr/bin/env python3
"""bau_08.py — schreibt notebooks/08_sentiment_rezensionen.ipynb."""
from gemeinsam import PAKETE, code, kopf, md, schreiben

ZELLEN = kopf("08", "Sentiment der Rezensionen", "08_sentiment_rezensionen.ipynb", pakete=PAKETE + " transformers torch") + [
md("""
## Fragestellung

Lässt sich aus dem Text einer Rezension lesen, ob sie positiv oder negativ ist — und was
sagt das Sentiment über Kanal, Wartezeit, Filiale und Produkt?

## Daten

`fact_reviews`: 10.000 deutsche Rezensionen mit Sternen (1 bis 5), jede an eine bewertete
Bestellung gehängt. Die Texte sind simuliert (Generator mit Satzbausteinen, danach sprachlich
geglättet, siehe `dataset/README.md`). Polarität: 1–2 Sterne negativ, 4–5 positiv; die
3-Sterne-Texte bleiben als „unentschieden" außen vor.

## Vorgehen

Vorverarbeitung (Kleinschreibung, Umlaute, Stoppwörter), eine Wortliste als Grundlinie,
dann TF-IDF mit logistischer Regression und einer Konfusionsmatrix, zum Vergleich ein
vortrainiertes deutsches BERT-Modell auf einer Stichprobe. Zum Schluss das Sentiment gegen
Kanal, Bestelldauer, Filiale und Produkt.
"""),
code("""
rezensionen = lade_sql(\"\"\"
    SELECT r.review_id, r.stars, r.review_text, r.order_id, p.product_name, p.category, b.branch_name,
           o.order_channel, o.order_duration_min
    FROM fact_reviews r
    JOIN dim_product p USING (product_id)
    JOIN dim_branch b USING (branch_id)
    JOIN fact_orders o USING (order_id)
    ORDER BY r.review_id\"\"\")
print(f"{zahl(len(rezensionen))} Rezensionen.")
rezensionen["stars"].value_counts().sort_index().rename("anzahl").to_frame().T
"""),
md("""
### Vorverarbeitung

Kleinschreibung, Umlaute in einheitlicher Schreibweise (ae, oe, ue, ss — ein Teil der Texte
ist so geschrieben), alles außer Buchstaben entfernen, Stoppwörter streichen.
"""),
code("""
import re

STOPPWOERTER = set(\"\"\"der die das und oder aber ein eine einen einem einer ich wir es war waren ist sind hat hatte
haben mit von zu im in am an auf fuer den dem des nicht auch noch sehr so wie bei nach aus als dass sich mir uns
man mal dann wieder einfach ganz hier dort dieser diese dieses zum zur ueber um bis was wenn wer\"\"\".split())

def normalisiere(text):
    # Einheitliche Schreibweise: klein, Umlaute als ae/oe/ue/ss, nur Buchstaben und Leerzeichen
    text = text.lower()
    for umlaut, ersatz in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        text = text.replace(umlaut, ersatz)
    return re.sub(r"[^a-z\\s]", " ", text)

def ohne_stoppwoerter(text):
    # Entfernt Stoppwörter, damit Zählungen die inhaltlichen Wörter treffen
    return " ".join(wort for wort in text.split() if wort not in STOPPWOERTER)

rezensionen["text_norm"] = rezensionen["review_text"].map(normalisiere).map(ohne_stoppwoerter)
polar = rezensionen[rezensionen["stars"] != 3].copy()
polar["positiv"] = (polar["stars"] >= 4).astype(int)
polar[["stars", "review_text", "text_norm"]].head(3)
"""),
md("### Grundlinie: eine Wortliste"),
code("""
POSITIV = set(\"\"\"gelungen lecker frisch schnell freundlich empfehlen perfekt zufrieden begeistert gut gerne wunderbar
hervorragend richtig angenehm knusprig saftig ausgezeichnet toll super klasse ueberzeugt ueberzeugend gepasst\"\"\".split())
NEGATIV = set(\"\"\"kalt lauwarm matschig lange warten enttaeuscht enttaeuschend schlecht nie teuer fettig wenig leider zaeh
trocken falsch fehlte schal aergerlich unfreundlich vergessen aergert katastrophal schlechter\"\"\".split())

def wortliste(text):
    # Positive Wörter zählen minus negative; das Vorzeichen ist die Polarität
    woerter = text.split()
    return sum(w in POSITIV for w in woerter) - sum(w in NEGATIV for w in woerter)

polar["score"] = polar["text_norm"].map(wortliste)
polar["wortliste_positiv"] = (polar["score"] > 0).astype(int)
treffer = (polar["wortliste_positiv"] == polar["positiv"]).mean() * 100
unentschieden = (polar["score"] == 0).mean() * 100
print(f"Die Wortliste trifft {zahl(treffer, 1)} Prozent; {zahl(unentschieden, 1)} Prozent der Texte enthalten kein Wort der Liste "
      f"und zählen als negativ.")
pd.crosstab(polar["positiv"].map({0: "ist negativ", 1: "ist positiv"}),
            polar["wortliste_positiv"].map({0: "Wortliste negativ", 1: "Wortliste positiv"}))
"""),
md("### TF-IDF und logistische Regression"),
code("""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, classification_report

X_lern, X_test, y_lern, y_test = train_test_split(polar["text_norm"], polar["positiv"], test_size=0.25,
                                                  random_state=2026, stratify=polar["positiv"])
vektor = TfidfVectorizer(ngram_range=(1, 2), min_df=3)
modell = LogisticRegression(max_iter=1000).fit(vektor.fit_transform(X_lern), y_lern)
vorhersage = modell.predict(vektor.transform(X_test))
print(classification_report(y_test, vorhersage, target_names=["negativ", "positiv"], digits=3))
pd.DataFrame(confusion_matrix(y_test, vorhersage), index=["ist negativ", "ist positiv"],
             columns=["vorhergesagt negativ", "vorhergesagt positiv"])
"""),
code("""
# Welche Wörter tragen am stärksten? Die größten und kleinsten Koeffizienten.
gewichte = pd.Series(modell.coef_[0], index=vektor.get_feature_names_out())
pd.DataFrame({"positiv": gewichte.nlargest(10).index, "negativ": gewichte.nsmallest(10).index})
"""),
md("""
Die Trefferquote liegt bei nahezu 100 Prozent — zu gut, um wahr zu sein, und das ist der
Punkt: Die Texte stammen aus einem Generator mit festen Bausteinen, und die Glättung hat die
Wortwahl nur begrenzt verändert. Ein Modell, das die Bausteine lernt, kennt die Antwort. Bei
echten Rezensionen liegen solche Modelle typischerweise zwischen 85 und 92 Prozent.

### Was macht das Modell mit den 3-Sterne-Texten?
"""),
code("""
mittlere = rezensionen[rezensionen["stars"] == 3]
wahrscheinlichkeit = modell.predict_proba(vektor.transform(mittlere["text_norm"]))[:, 1]
print(f"{zahl(len(mittlere))} Texte mit drei Sternen: {zahl((wahrscheinlichkeit >= 0.5).mean() * 100, 1)} Prozent würden als positiv "
      f"eingeordnet, die mittlere Wahrscheinlichkeit liegt bei {zahl(wahrscheinlichkeit.mean(), 2)}.")
pd.Series(wahrscheinlichkeit).describe().round(2).to_frame("p_positiv").T
"""),
md("""
### Vergleich: vortrainiertes deutsches BERT-Modell

`oliverguhr/german-sentiment-bert` hat diese Texte nie gesehen. Auf einer Stichprobe von 500
Texten aus dem Prüfdatensatz zeigt sich, wie ein allgemeines Modell ohne Bausteinwissen
abschneidet. Das Modell antwortet mit `positive`, `negative` oder `neutral`; `neutral` zählt
als Fehler, weil die Texte eine Polarität haben.
"""),
code("""
import os
os.environ.setdefault("HF_HUB_VERBOSITY", "error")
import warnings
warnings.filterwarnings("ignore")
from transformers.utils import logging as hf_logging
hf_logging.set_verbosity_error()
from transformers import pipeline

klassifikator = pipeline("text-classification", model="oliverguhr/german-sentiment-bert", truncation=True)
stichprobe = polar.loc[X_test.index].sample(500, random_state=2026)
antworten = klassifikator(stichprobe["review_text"].tolist(), batch_size=16)
stichprobe["bert"] = [antwort["label"] for antwort in antworten]
stichprobe["bert_positiv"] = (stichprobe["bert"] == "positive").astype(int)
stichprobe["lr_positiv"] = modell.predict(vektor.transform(stichprobe["text_norm"]))
bert_treffer = ((stichprobe["bert"] == "positive") & (stichprobe["positiv"] == 1)
                | (stichprobe["bert"] == "negative") & (stichprobe["positiv"] == 0)).mean() * 100
lr_treffer = (stichprobe["lr_positiv"] == stichprobe["positiv"]).mean() * 100
print(f"Auf denselben 500 Texten: BERT {zahl(bert_treffer, 1)} Prozent, TF-IDF mit logistischer Regression {zahl(lr_treffer, 1)} Prozent.")
pd.crosstab(stichprobe["positiv"].map({0: "ist negativ", 1: "ist positiv"}), stichprobe["bert"])
"""),
md("### Sentiment gegen Kanal, Bestelldauer, Filiale und Produkt"),
code("""
# Vorhersage für alle 10.000 Texte mit dem TF-IDF-Modell (Wahrscheinlichkeit für „positiv")
rezensionen["p_positiv"] = modell.predict_proba(vektor.transform(rezensionen["text_norm"]))[:, 1]
rezensionen["dauer_klasse"] = pd.cut(rezensionen["order_duration_min"], bins=[0, 5, 10, 15, 60],
                                     labels=["bis 5 min", "6–10 min", "11–15 min", "über 15 min"])

def anteil_positiv(spalte):
    # Anteil positiv vorhergesagter Texte und mittlere Sterne je Ausprägung
    return (rezensionen.groupby(spalte, observed=True)
            .agg(rezensionen=("review_id", "size"), anteil_positiv_pct=("p_positiv", lambda p: (p >= 0.5).mean() * 100),
                 sterne_mittel=("stars", "mean")).round(2))

anteil_positiv("order_channel")
"""),
code("""
anteil_positiv("dauer_klasse")
"""),
code("""
anteil_positiv("branch_name").sort_values("anteil_positiv_pct", ascending=False)
"""),
code("""
anteil_positiv("category").sort_values("anteil_positiv_pct", ascending=False)
"""),
code("""
import matplotlib.pyplot as plt

produkte = anteil_positiv("product_name").sort_values("anteil_positiv_pct")
abb, achse = plt.subplots(figsize=(9, 6))
achse.barh(produkte.index[-15:], produkte["anteil_positiv_pct"].iloc[-15:])
achse.set_xlabel("Anteil positiver Rezensionen in %")
achse.set_xlim(0, 100)
achse.set_title("Die Produkte mit dem höchsten Anteil positiver Rezensionen")
plt.tight_layout()
plt.show()
"""),
md("""
## Ergebnis

Die Wortliste trifft 71,6 Prozent der Texte; bei 32,7 Prozent enthält der Text kein Wort aus
einer der beiden Listen, und diese Texte zählen als negativ. TF-IDF mit logistischer Regression
liegt nahezu bei 100 Prozent — zu gut, um wahr zu sein, weil die Texte simuliert sind und das
Modell die Bausteine des Generators lernt: Auf derselben Stichprobe von 500 Texten wie beim
BERT-Vergleich erreicht es 100,0 Prozent. BERT, das diese Bausteine nie gesehen hat, kommt auf
94,2 Prozent — niedriger, aber deutlich höher, als man für Texte mit uneindeutiger Sprache
erwarten würde, ein Hinweis darauf, dass die generierten Rezensionen ihre Polarität sehr
eindeutig formulieren. Der Anteil positiver Rezensionen fällt mit der Bestelldauer (78,63
Prozent bis 5 Minuten, 41,67 Prozent über 15 Minuten) und unterscheidet sich zwischen den
Kanälen (68,61 Prozent am Counter, 82,70 Prozent bei App-Bestellungen) — genau wie die Sterne,
aus denen der Generator die Texte gebaut hat.

## Was offen bleibt

Echte Rezensionen aus dem Shop (`source = 'shop'`) fehlen noch im Bestand; sobald sie da
sind, wird das Modell an Texten geprüft, die kein Generator geschrieben hat. Die Stoppwortliste
ist kurz und die Wortliste klein — beides ließe sich aus den Koeffizienten des Modells
erweitern.
"""),
]

schreiben("08_sentiment_rezensionen.ipynb", ZELLEN)
