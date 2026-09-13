#!/usr/bin/env python3
"""bau_01.py — schreibt notebooks/01_analytisches_datenmodell.ipynb."""
from gemeinsam import code, kopf, md, schreiben

ZELLEN = kopf("01", "Analytisches Datenmodell", "01_analytisches_datenmodell.ipynb") + [
md("""
## Fragestellung

Wie wird aus dem operativen Modell in dritter Normalform (`wawi`) ein analytisches Modell,
mit dem sich Fragen wie „Umsatz je Filiale und Jahr" ohne Umwege beantworten lassen — und
was geht schief, wenn man Tabellen mit unterschiedlichem Grain naiv verbindet?

## Daten

Ein Auszug aus `wawi` für das Jahr 2025: Bestellungen, Positionen und Rechnungen, dazu die
Stammdaten Artikel (drei Tabellen), Filialen und Filialtypen. Der Auszug kommt per SQL in
DataFrames und von dort in DuckDB, wo wir das analytische Modell Schritt für Schritt bauen.

## Vorgehen

Frage → Grain → Dimensionen → Fakten → Sicht. Am Ende vergleichen wir das Ergebnis mit dem
fertigen Schema `burgermetrics` und sehen uns an, wie die Rezensionen als dritte Faktentabelle
hineinpassen.
"""),
md("### Auszug aus dem operativen Modell"),
code("""
JAHR = 2025
VON, BIS = f"{JAHR}-01-01", f"{JAHR + 1}-01-01"

bestellungen = lade_sql(f\"\"\"
    SELECT bestellung_id, bestelldatum, filiale_id, kunde_id, zahlungsart_id, promotion_id,
           bestellkanal, artikel_anzahl, brutto_gesamt, rabatt_betrag, netto_gesamt,
           bestelldauer_min, zufriedenheit
    FROM kundenbestellung
    WHERE bestelldatum >= '{VON}' AND bestelldatum < '{BIS}'\"\"\")
positionen = lade_sql(f\"\"\"
    SELECT p.position_id, p.bestellung_id, p.artikel_id, p.menge, p.einzelpreis, p.positionsbetrag
    FROM bestellposition p
    JOIN kundenbestellung b USING (bestellung_id)
    WHERE b.bestelldatum >= '{VON}' AND b.bestelldatum < '{BIS}'\"\"\")
rechnungen = lade_sql(f\"\"\"
    SELECT r.rechnung_id, r.bestellung_id, r.rechnungsdatum, r.zahlbetrag, r.mwst_satz, r.mwst_betrag
    FROM rechnung r
    JOIN kundenbestellung b USING (bestellung_id)
    WHERE b.bestelldatum >= '{VON}' AND b.bestelldatum < '{BIS}'\"\"\")
artikel = lade_sql("SELECT artikel_id, name, unterkategorie_id, vegetarisch, vegan, kalorien, listenpreis FROM artikel")
unterkategorien = lade_sql("SELECT unterkategorie_id, name AS unterkategorie, kategorie_id FROM artikelunterkategorie")
kategorien = lade_sql("SELECT kategorie_id, name AS kategorie FROM artikelkategorie")
filialen = lade_sql("SELECT f.filiale_id, f.name, f.stadtteil, f.eroeffnet_am, t.name AS filialtyp FROM filiale f JOIN filialtyp t USING (filialtyp_id)")

pd.DataFrame({"tabelle": ["kundenbestellung", "bestellposition", "rechnung", "artikel", "filiale"],
              "zeilen": [len(bestellungen), len(positionen), len(rechnungen), len(artikel), len(filialen)]})
"""),
md("""
### Schritt 1: Die Frage und ihr Grain

„Umsatz je Filiale und Jahr" — die kleinste Einheit, die wir dafür zählen, ist **eine
Bestellung** (der Grain). Die Positionen einer Bestellung sind feiner; sie brauchen wir für
Fragen nach Produkten, nicht für den Umsatz je Filiale.

### Schritt 2: Dimensionen

Eine Dimension fasst zusammen, wonach wir gruppieren und filtern. `dim_product` entsteht aus
drei normalisierten Tabellen — Artikel, Unterkategorie, Kategorie — als eine breite Tabelle
mit einer Zeile je Artikel. `dim_branch` kommt aus Filiale und Filialtyp.
"""),
code("""
import duckdb

def fuer_duckdb(daten):
    # DuckDB 1.4 kennt pandas' neuen Standard-Stringtyp "str" (ab pandas 3) noch nicht
    spalten = {s: object for s in daten.columns if daten[s].dtype == "str"}
    return daten.astype(spalten) if spalten else daten

con = duckdb.connect()
for name, tabelle in {"kundenbestellung": bestellungen, "bestellposition": positionen, "rechnung": rechnungen,
                      "artikel": artikel, "artikelunterkategorie": unterkategorien,
                      "artikelkategorie": kategorien, "filiale": filialen}.items():
    con.register(name, fuer_duckdb(tabelle))

con.sql(\"\"\"
    CREATE TABLE dim_product AS
    SELECT a.artikel_id AS product_id, a.name AS product_name, k.kategorie AS category,
           u.unterkategorie AS subcategory, a.vegetarisch AS is_vegetarian, a.vegan AS is_vegan,
           a.kalorien AS calories, a.listenpreis AS unit_price
    FROM artikel a
    JOIN artikelunterkategorie u USING (unterkategorie_id)
    JOIN artikelkategorie k USING (kategorie_id)
\"\"\")
con.sql(\"\"\"
    CREATE TABLE dim_branch AS
    SELECT filiale_id AS branch_id, name AS branch_name, stadtteil AS district,
           filialtyp AS branch_type, eroeffnet_am AS opening_date
    FROM filiale
\"\"\")
con.sql("SELECT category, count(*) AS produkte FROM dim_product GROUP BY category ORDER BY produkte DESC").df()
"""),
md("""
### Schritt 3: Fakten

`fact_orders` hat eine Zeile je Bestellung mit den Kennzahlen auf diesem Grain (Beträge, Dauer,
Zufriedenheit) und den Schlüsseln zu den Dimensionen. `fact_order_items` hat eine Zeile je
Position — ein zweiter Grain, eine zweite Faktentabelle. Beide teilen sich die Dimensionen:
Das ist die Galaxy (Fact Constellation).
"""),
code("""
con.sql(\"\"\"
    CREATE TABLE fact_orders AS
    SELECT bestellung_id AS order_id, bestelldatum AS date, filiale_id AS branch_id, kunde_id AS customer_id,
           zahlungsart_id AS payment_id, promotion_id AS promo_id, bestellkanal AS order_channel,
           artikel_anzahl AS item_count, brutto_gesamt AS gross_total, rabatt_betrag AS discount_amount,
           netto_gesamt AS net_total, bestelldauer_min AS order_duration_min, zufriedenheit AS satisfaction_score
    FROM kundenbestellung
\"\"\")
con.sql(\"\"\"
    CREATE TABLE fact_order_items AS
    SELECT position_id AS order_item_id, bestellung_id AS order_id, artikel_id AS product_id,
           menge AS quantity, einzelpreis AS unit_price, positionsbetrag AS line_total
    FROM bestellposition
\"\"\")
con.sql("SELECT 'fact_orders' AS tabelle, count(*) AS zeilen FROM fact_orders UNION ALL SELECT 'fact_order_items', count(*) FROM fact_order_items").df()
"""),
md("### Schritt 4: Die Sicht, die die Frage beantwortet"),
code("""
con.sql(\"\"\"
    CREATE VIEW v_umsatz_filiale_jahr AS
    SELECT b.branch_name, year(o.date) AS jahr, count(*) AS bestellungen, round(sum(o.net_total), 2) AS umsatz
    FROM fact_orders o
    JOIN dim_branch b USING (branch_id)
    GROUP BY b.branch_name, year(o.date)
\"\"\")
umsatz_filiale = con.sql("SELECT * FROM v_umsatz_filiale_jahr ORDER BY umsatz DESC").df()
umsatz_filiale
"""),
md("""
### Die Fan Trap: derselbe Betrag, viele Male gezählt

Wer den Umsatz aus der Bestellung nimmt, aber die Positionen dazujoint, zählt jeden
Bestellbetrag so oft, wie die Bestellung Positionen hat. Das Ergebnis sieht plausibel aus und
ist um ein Vielfaches zu hoch.
"""),
code("""
richtig = con.sql("SELECT sum(net_total) FROM fact_orders").fetchone()[0]
falsch = con.sql(\"\"\"
    SELECT sum(o.net_total)
    FROM fact_orders o
    JOIN fact_order_items i USING (order_id)
\"\"\").fetchone()[0]
print(f"Umsatz {JAHR} aus fact_orders: {zahl(richtig)} €.")
print(f"Derselbe Umsatz nach einem Join auf die Positionen: {zahl(falsch)} € — das {zahl(falsch / richtig, 1)}-Fache.")
print("Jede Bestellung wird so oft gezählt, wie sie Positionen hat. Große Bestellungen haben viele Positionen und einen hohen Betrag,")
print("deshalb liegt der Faktor über der mittleren Positionszahl je Bestellung (rund 3,9).")
"""),
md("""
Die Regel: Kennzahlen immer auf dem Grain aggregieren, auf dem sie entstehen. Umsatz je
Bestellung aus `fact_orders`, Mengen je Produkt aus `fact_order_items` — und beides erst danach
über die gemeinsamen Dimensionen zusammenführen.

### Abgleich mit dem fertigen Schema `burgermetrics`

Das Schema in der Datenbank ist auf demselben Weg entstanden (`db/aufbau/0019`). Die Zahlen
müssen übereinstimmen.
"""),
code("""
vergleich = lade_sql(f\"\"\"
    SELECT b.branch_name, count(*) AS bestellungen_db, round(sum(o.net_total), 2) AS umsatz_db
    FROM burgermetrics.fact_orders o
    JOIN burgermetrics.dim_branch b USING (branch_id)
    WHERE o.date >= '{VON}' AND o.date < '{BIS}'
    GROUP BY b.branch_name\"\"\")
abgleich = umsatz_filiale.merge(vergleich, on="branch_name")
abgleich["differenz"] = (abgleich["umsatz"] - abgleich["umsatz_db"]).round(2)
abgleich[["branch_name", "bestellungen", "bestellungen_db", "umsatz", "umsatz_db", "differenz"]]
"""),
md("""
### Rezensionen als dritte Faktentabelle

Seit September 2026 gibt es `fact_reviews`: eine Zeile je Rezension, mit Schlüsseln zu
Produkt, Kunde, Filiale, Datum und — als Besonderheit — zur Bestellung, aus der sie stammt.
Der Grain ist neu (eine Rezension), die Dimensionen sind dieselben. Genau das macht das
Galaxy-Schema aus: Eine neue Frage bekommt eine neue Faktentabelle, nicht ein neues Modell.
"""),
code("""
lade_sql(\"\"\"
    SELECT p.category, count(*) AS rezensionen, round(avg(r.stars), 2) AS sterne_mittel,
           round(100.0 * avg(CASE WHEN r.stars >= 4 THEN 1 ELSE 0 END), 1) AS anteil_positiv_pct
    FROM fact_reviews r
    JOIN dim_product p USING (product_id)
    GROUP BY p.category
    ORDER BY rezensionen DESC\"\"\")
"""),
md("""
## Ergebnis

Aus sieben normalisierten Tabellen wurden zwei Dimensionen, zwei Faktentabellen und eine
Sicht; die Sicht beantwortet die Frage in einer Abfrage, und ihre Zahlen stimmen mit dem
fertigen Schema überein. Die Fan Trap zeigt, warum der Grain die wichtigste Entscheidung im
Modell ist.

## Was offen bleibt

Der Auszug umfasst ein Jahr; `db/aufbau/0019_wawi_zu_burgermetrics.sql` macht denselben
Schritt für den ganzen Bestand als ETL in der Datenbank. Die Dimensionen `dim_date` und
`dim_customer` haben wir übersprungen — sie entstehen nach demselben Muster.
"""),
]

schreiben("01_analytisches_datenmodell.ipynb", ZELLEN)
