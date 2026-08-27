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
| `aufbau/0005_semantik.sql` | die Sichten der Semantikschicht |
| `aufbau/0006_semantik_ergaenzung.sql` | RFM, Kanal je Stunde, Niederschlag, Aktions-ROI |
| `aufbau/0007_kennzahlen_einzeln.sql` | Produkte je Jahr und die Einzelwerte der Kacheln |

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


---

## Das Dashboard liest ausschließlich hier

Seit der Umstellung steht im Quelltext von `web/dashboard.html` **keine
Nutzdatenzahl mehr**: keine der 88 Datenreihen, kein Kachelwert, kein Text der
Management Summary. Die Seite lädt beim Aufruf 33 Sichten, baut daraus 89
Reihen und füllt 72 Kacheln und 24 Summary-Karten — in rund drei Sekunden.

| Datei | Aufgabe |
|---|---|
| `web/js/konfiguration.js` | die einzige Stelle mit einer Adresse |
| `web/js/datenquelle.js` | der Vertrag: 33 benannte Fragen; `PostgrestQuelle` als erste Umsetzung |
| `web/js/reihen.js` | übersetzt die Antworten in die Reihen, die Chart.js erwartet |
| `web/js/kacheln.js` | füllt Kennzahlkacheln und Management Summary |

**Eine zweite Datenquelle** braucht eine Klasse mit denselben 33 Methoden und
einen Zweig in `waehleQuelle()`. Am Dashboard ändert sich dabei keine Zeile.
Wer MySQL, Snowflake oder ein Lakehouse anschließt, baut dort die Sichten nach
— die Feldnamen sind die Schnittstelle.

Fällt die Quelle aus, zeigt die Seite eine Meldung mit Fehlertext, Adresse und
Schema. Sie zeigt keine veralteten Zahlen, weil keine mehr da sind.

## Was sich gegenüber den einkodierten Werten geändert hat

29 Datenreihen und 48 von 72 Kacheln stimmen exakt mit dem alten Stand überein.
Die Abweichungen sind gewollt und hier begründet:

| Was | Alt | Neu | Grund |
|---|---|---|---|
| RFM-Segmente | Champions 4.082, at Risk 5.484, Verloren 4.396 | 4.194 / 4.998 / 4.998 | Die alten Größen ließen sich mit keiner Regel nachrechnen (4.396 „Verlorene" mit Ø 249 Tagen, obwohl nur 2.042 Kunden über 180 Tage inaktiv sind). `v_rfm_kunde` rechnet nach offengelegten Quintilsregeln neu. Champions treffen dabei fast exakt (Ø 44,4 Bestellungen gegen 44,7, Ø 837 € gegen 842 €). |
| Kohorten-Retention | 99,4 % | 96,3 % | Definiert als Anteil einer Kohorte, der im Folgejahr wieder kauft. Die alte Zahl ist ohne Definition nicht nachvollziehbar. |
| Simulationsbasis Marge | 4,43 Mio. €, 70,4 % | 4,23 Mio. €, 67,3 % | Die alte Zahl beruht auf jahresweise interpolierten Kosten zwischen `cost_price_2017` und `cost_price`; die Sicht rechnet mit `cost_price`. |
| Anteile mit Rundung | 23,3 %, 17,4 %, +21,6 % | 23,4 %, 17,5 %, +21,5 % | Kaufmännisch gerundet statt abgeschnitten (23,354 → 23,4). |
| Regelbezeichnungen | „Fries + Cola" | „M.Fries + Cola 0.5" | Die Sicht benennt das tatsächlich gemessene Paar. |

Nachgerechnet wird das im Browser: `web/abgleich.html` stellt die
Semantikschicht 29 Datenreihen des alten Dashboards gegenüber — **29 von 29
identisch**.
