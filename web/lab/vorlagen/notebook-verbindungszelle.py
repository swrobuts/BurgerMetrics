# notebook-verbindungszelle.py — die Verbindungszelle der Fallstudien-Notebooks
#
# Quelle: notebooks/quellen/gemeinsam.py (VERBINDUNG). Dieselbe Zelle steht in jedem der
# neun Notebooks als zweite Codezelle, direkt unter der pip-Zelle:
#     %pip install -q sqlalchemy psycopg2-binary duckdb scikit-learn 'mlxtend>=0.23.2' statsmodels holidays dash
# In Colab: den Inhalt dieser Datei in eine Codezelle einfügen und ausführen.
# Lokal genügt notebooks/requirements.txt.
#
# Das Demo-Konto studi_daba/thws ist absichtlich öffentlich und liest nur; eigene
# Zugangsdaten gehören nicht in eine Zelle (Lab 06, Abschnitt „Zugangsdaten“).
# Stand 09/2026: pandas 3.0, SQLAlchemy 2.0, psycopg2 2.9.

import pandas as pd
from sqlalchemy import create_engine

VERBINDUNG = "postgresql+psycopg2://studi_daba:thws@supabase.butscher.cloud:5433/postgres"
engine = create_engine(VERBINDUNG)

def lade_sql(sql):
    # Führt eine Abfrage aus und gibt das Ergebnis als DataFrame zurück
    return pd.read_sql(sql, engine)

def lade_csv(name):
    # Liest eine CSV-Datei des Datensatzes direkt aus GitHub (Git LFS)
    url = f"https://media.githubusercontent.com/media/swrobuts/BurgerMetrics/main/dataset/{name}.csv"
    return pd.read_csv(url)

# Verbindungsprobe wie in Notebook 00: Rolle, Suchpfad, nur lesend
print(lade_sql("SELECT current_user, current_setting('search_path') AS suchpfad, "
               "current_setting('default_transaction_read_only') AS nur_lesen"))
