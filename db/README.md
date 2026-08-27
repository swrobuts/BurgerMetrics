# Datenbank: Schema `burgermetrics`

Der Bestand liegt seit August 2026 in einer selbstgehosteten **Supabase**-Instanz
(PostgreSQL 17.6) auf dem VPS. Die CSV-Dateien in [`../dataset/`](../dataset/)
bleiben die Quelle der Wahrheit; die Datenbank ist ihr Abbild.

## Aufbau in fünf Schritten

| Datei | Inhalt |
|---|---|
| `aufbau/0001_schema_und_dimensionen.sql` | Schema und die zehn Dimensionstabellen |
| `aufbau/0002_fakten.sql` | `fact_orders` (Grain: Bestellung) und `fact_order_items` (Grain: Position), Fremdschlüssel, Indizes |
| `lade_csv.py` | lädt die zwölf CSV-Dateien per `COPY`, eine Transaktion, alles oder nichts |
| `aufbau/0003_obt.sql` | `obt_orders` — **nicht hochgeladen**, sondern im Server aus dem Galaxy-Schema erzeugt |
| `aufbau/0004_sicherheit.sql` | Grants, Row Level Security (nur `SELECT`) |
| `aufbau/0005_semantik.sql` | die 26 Sichten der Semantikschicht |

```bash
cp .env.example .env      # und Zugangsdaten eintragen
python3 db/lade_csv.py    # 3.704.595 Zeilen, rund 110 Sekunden
```

Die SQL-Dateien sind idempotent: Sie laufen zweimal hintereinander fehlerfrei.

## Warum eine Semantikschicht

Das Dashboard kennt **keine Tabelle, keine Spalte, keinen Join** — es fragt nur
die Sichten `v_*`. Jede Kennzahl ist dort genau einmal definiert:

| Kennzahl | Definition |
|---|---|
| `umsatz` | `SUM(net_total)` — Nettobetrag **nach** Rabatt |
| `bestellungen` | `COUNT(*)` auf Bestellebene |
| `aov` | `AVG(net_total)` |
| `positionsumsatz` | `SUM(line_total)` — Bruttobetrag auf Positionsebene |

Wer die Quelle wechselt — MySQL, Snowflake, ein Lakehouse —, muss genau diese
Sichten nachbauen. Sonst nichts. Das ist der ganze Vertrag.

**`v_warenkorb_regeln` ist materialisiert.** Die Selbstverknüpfung über 2,95
Millionen Positionen braucht 4,4 Sekunden und reißt damit das
`statement_timeout` der Rolle `anon`; materialisiert antwortet sie in 20
Millisekunden. Nach einem Neuladen der Daten auffrischen:

```sql
REFRESH MATERIALIZED VIEW burgermetrics.v_warenkorb_regeln;
```

## Betriebswissen: PostgREST

Zwei Eigenheiten der Instanz, beide hart erarbeitet:

* **Die Schema-Liste kommt aus der Container-Umgebung**, nicht aus der
  Datenbank. `ALTER ROLE authenticator SET pgrst.db_schemas = …` bleibt
  wirkungslos, weil Umgebungsvariablen in PostgREST Vorrang haben. Das Schema
  wird in `/root/supabase/docker/.env` bei `PGRST_DB_SCHEMAS` eingetragen.
* **`PGRST_DB_CHANNEL_ENABLED=false`** — `NOTIFY pgrst, 'reload schema'`
  bewirkt daher nichts. Nach jeder Schemaänderung:

```bash
ssh vps "cd /root/supabase/docker && docker compose restart rest"
```

## Prüfung

`web/abgleich.html` stellt die Semantikschicht 29 Datenreihen des alten
Dashboards gegenüber und meldet jede Abweichung. Stand: **29 von 29 identisch.**

Beim Abgleich fielen zwei Sachen auf, die ohne die Migration unentdeckt
geblieben wären:

* **`categoryRevenue` war falsch.** Breakfast stand mit 120.642 € statt
  243.865 €, Extra mit 21.596 € statt 54.968 € — beide etwa halbiert. Gegen die
  CSV-Dateien nachgerechnet und im Dashboard korrigiert.
* **Kohorten hängen an `dim_customer.first_visit_year`**, nicht an der ersten
  Bestellung in `fact_orders`. Die Zahlen gehen weit auseinander (Kohorte 2017:
  1.502 gegen 9.575), weil der Erstbesuch dem ersten erfassten Kauf vorausgehen
  kann. `v_kohorte` folgt der Definition des Dashboards.
