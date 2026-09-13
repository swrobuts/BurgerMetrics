#!/usr/bin/env python3
"""app.py — Dash-App zur Fallstudie BurgerMetrics: vier Karten aus der Semantikschicht.

    python3 dash/app.py            # http://127.0.0.1:8050

Verbindung aus der Umgebungsvariable DATABASE_URL; ohne sie das Demo-Konto studi_daba
(nur lesend). Jede Karte liest genau eine Sicht — dieselben Zahlen wie das Dashboard,
weil beide dieselbe Definition benutzen.
"""
import os

import pandas as pd
import plotly.express as px
from dash import Dash, Input, Output, dcc, html
from sqlalchemy import create_engine

DATABASE_URL = os.environ.get("DATABASE_URL",
                              "postgresql+psycopg2://studi_daba:thws@supabase.butscher.cloud:5433/postgres")
engine = create_engine(DATABASE_URL)


def lade_sql(sql):
    """Führt eine Abfrage aus und gibt das Ergebnis als DataFrame zurück."""
    return pd.read_sql(sql, engine)


def zahl(wert, nachkommastellen=0):
    """Formatiert eine Zahl deutsch: Punkt als Tausendertrenner, Komma als Dezimaltrenner."""
    text = f"{wert:,.{nachkommastellen}f}"
    return text.replace(",", "X").replace(".", ",").replace("X", ".")


def lade_kennzahlen():
    """Die vier Kacheln: drei Werte für 2025 aus v_kennzahlen_jahr, die Zufriedenheit aus v_kennzahl_einzeln."""
    jahr = lade_sql("SELECT bestellungen, umsatz, aov FROM v_kennzahlen_jahr WHERE jahr = 2025").iloc[0]
    zufriedenheit = lade_sql("SELECT wert FROM v_kennzahl_einzeln WHERE kennung = 'zufriedenheit_2025'").iloc[0, 0]
    return {
        "Umsatz 2025": zahl(jahr["umsatz"] / 1_000_000, 2) + " Mio. €",
        "Bestellungen 2025": zahl(jahr["bestellungen"]),
        "Ø Bestellwert 2025": zahl(jahr["aov"], 2) + " €",
        "Zufriedenheit 2025": zahl(zufriedenheit, 2) + " von 5",
    }


def lade_umsatz_monat(branch_id):
    """Umsatz je Monat: ohne Filiale aus der Sicht, mit Filiale aus fact_orders gerechnet."""
    if branch_id is None:
        return lade_sql("SELECT monat, umsatz FROM v_umsatz_monat ORDER BY monat")
    return lade_sql(f"""
        SELECT to_char(date, 'YYYY-MM') AS monat, sum(net_total) AS umsatz
        FROM fact_orders WHERE branch_id = {int(branch_id)}
        GROUP BY 1 ORDER BY 1""")


def lade_filialen():
    """Filialen für die Auswahl."""
    return lade_sql("SELECT branch_id, branch_name FROM v_filiale ORDER BY branch_id")


def lade_kanaele():
    """Kanalanteile je Jahr."""
    return lade_sql("SELECT jahr, kanal, anteil_pct FROM v_kanal_jahr ORDER BY jahr, kanal")


def lade_rezensionen():
    """Ø Sterne je Produkt aus der materialisierten Sicht, nur Produkte mit Rezensionen."""
    return lade_sql("""
        SELECT product_name, category, anzahl, sterne_mittel
        FROM burgermetrics.v_rezension_produkt WHERE anzahl > 0
        ORDER BY sterne_mittel DESC, anzahl DESC""")


def kachel(titel, wert):
    """Eine Kennzahlkachel."""
    return html.Div([html.Div(titel, className="kachel-titel"), html.Div(wert, className="kachel-wert")], className="kachel")


def figur_umsatz(branch_id):
    """Linie Umsatz je Monat, wahlweise für eine Filiale."""
    daten = lade_umsatz_monat(branch_id)
    figur = px.line(daten, x="monat", y="umsatz", labels={"monat": "Monat", "umsatz": "Umsatz in €"})
    figur.update_layout(margin=dict(l=40, r=20, t=20, b=40), yaxis_rangemode="tozero")
    return figur


def figur_kanaele():
    """Gestapelte Balken: Anteil der Kanäle je Jahr."""
    figur = px.bar(lade_kanaele(), x="jahr", y="anteil_pct", color="kanal",
                   labels={"jahr": "Jahr", "anteil_pct": "Anteil in %", "kanal": "Kanal"})
    figur.update_layout(margin=dict(l=40, r=20, t=20, b=40), barmode="stack")
    return figur


def figur_rezensionen():
    """Balken: Ø Sterne je Produkt, die zwanzig meistbewerteten Produkte."""
    daten = lade_rezensionen().sort_values("anzahl", ascending=False).head(20).sort_values("sterne_mittel")
    figur = px.bar(daten, x="sterne_mittel", y="product_name", orientation="h", color="category",
                   hover_data=["anzahl"], labels={"sterne_mittel": "Ø Sterne", "product_name": "Produkt", "category": "Kategorie"})
    figur.update_layout(margin=dict(l=40, r=20, t=20, b=40), xaxis_range=[0, 5], height=560)
    return figur


def baue_app():
    """Baut Layout und Callback; getrennt von app.run, damit der Test die App prüfen kann."""
    dash_app = Dash(__name__, title="BurgerMetrics — Dash")
    filialen = lade_filialen()
    kennzahlen = lade_kennzahlen()
    dash_app.layout = html.Div([
        html.H1("BurgerMetrics — vier Karten aus der Semantikschicht"),
        html.Div([kachel(t, w) for t, w in kennzahlen.items()], id="kacheln", className="kacheln"),
        html.Div([
            html.H2("Umsatz je Monat"),
            dcc.Dropdown(id="filiale", clearable=False, value="alle",
                         options=[{"label": "Alle Filialen", "value": "alle"}]
                         + [{"label": z.branch_name, "value": int(z.branch_id)} for z in filialen.itertuples()]),
            dcc.Graph(id="linie-umsatz"),
        ], id="karte-umsatz", className="karte"),
        html.Div([html.H2("Kanalanteile je Jahr"), dcc.Graph(figure=figur_kanaele())], id="karte-kanaele", className="karte"),
        html.Div([html.H2("Ø Sterne je Produkt (die 20 meistbewerteten)"), dcc.Graph(figure=figur_rezensionen())],
                 id="karte-rezensionen", className="karte"),
        html.P("Quelle: Sichten v_kennzahlen_jahr, v_kennzahl_einzeln, v_umsatz_monat, v_kanal_jahr, v_rezension_produkt; "
               "Filialfilter über fact_orders.", className="quelle"),
    ], className="seite")

    @dash_app.callback(Output("linie-umsatz", "figure"), Input("filiale", "value"))
    def zeichne_umsatz(wahl):
        # Zeichnet die Linie neu, sobald die Filiale wechselt
        return figur_umsatz(None if wahl == "alle" else wahl)

    return dash_app


if __name__ == "__main__":
    baue_app().run(debug=False, port=8050)
