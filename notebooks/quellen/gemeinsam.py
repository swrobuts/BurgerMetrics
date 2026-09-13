"""gemeinsam.py — Bausteine, die alle Notebooks der Fallstudie teilen.

Jedes Notebook entsteht aus einem Bauskript (bau_NN.py): Die Zellen stehen dort als
Python-Strings, dieses Modul schreibt sie mit nbformat als .ipynb. So bleibt der
Quelltext lesbar im Diff, und die ausgeführte Fassung mit Ausgaben liegt daneben.
"""
from pathlib import Path

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

REPO = "swrobuts/BurgerMetrics"
ORDNER = Path(__file__).resolve().parent.parent   # notebooks/

PAKETE = "sqlalchemy psycopg2-binary duckdb scikit-learn 'mlxtend>=0.23.2' statsmodels holidays dash"

VERBINDUNG = '''import pandas as pd
from sqlalchemy import create_engine

VERBINDUNG = "postgresql+psycopg2://studi_daba:thws@supabase.butscher.cloud:5433/postgres"
engine = create_engine(VERBINDUNG)

def lade_sql(sql):
    # Führt eine Abfrage aus und gibt das Ergebnis als DataFrame zurück
    return pd.read_sql(sql, engine)

def lade_csv(name):
    # Liest eine CSV-Datei des Datensatzes direkt aus GitHub (Git LFS)
    url = f"https://media.githubusercontent.com/media/swrobuts/BurgerMetrics/main/dataset/{name}.csv"
    return pd.read_csv(url)'''

HILFEN = '''def zahl(wert, nachkommastellen=0):
    # Zahl deutsch schreiben: Punkt als Tausendertrenner, Komma als Dezimaltrenner
    text = f"{wert:,.{nachkommastellen}f}"
    return text.replace(",", "X").replace(".", ",").replace("X", ".")'''


def md(text):
    """Eine Markdown-Zelle; führende und schließende Leerzeilen fallen weg."""
    return new_markdown_cell(text.strip())


def code(text):
    """Eine Codezelle; führende und schließende Leerzeilen fallen weg."""
    return new_code_cell(text.strip())


def kopf(nummer, titel, dateiname, pakete=PAKETE):
    """Die vier Kopfzellen: Titel mit Colab-Link, pip-Zelle, Verbindungszelle, Hilfsfunktion zahl()."""
    colab = f"https://colab.research.google.com/github/{REPO}/blob/main/notebooks/{dateiname}"
    titelzelle = (f"# {nummer} {titel}\n\n"
                  f"[![In Colab öffnen](https://colab.research.google.com/assets/colab-badge.svg)]({colab})\n\n"
                  "Fallstudie BurgerMetrics · Datenbasierte Fallstudien (THWS). "
                  "Die Datenbank ist mit dem Demo-Konto `studi_daba` lesend erreichbar; "
                  "nichts in diesem Notebook schreibt in die Datenbank.")
    pipzelle = (f"# In Colab einmal ausführen; lokal genügt notebooks/requirements.txt\n"
                f"%pip install -q {pakete}")
    return [md(titelzelle), code(pipzelle), code(VERBINDUNG), code(HILFEN)]


def schreiben(dateiname, zellen):
    """Schreibt die Zellen als Notebook nach notebooks/<dateiname>."""
    metadaten = {"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
                 "language_info": {"name": "python"}}
    nb = new_notebook(cells=zellen, metadata=metadaten)
    ziel = ORDNER / dateiname
    nbformat.write(nb, ziel)
    print(f"geschrieben: {ziel.name} mit {len(zellen)} Zellen")
