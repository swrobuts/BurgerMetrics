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
| `aufbau/0008_summary_luecken.sql` | Umsatz je Altersgruppe, Anteil Heimatbezirk |
| `aufbau/0009_rfm_deterministisch.sql` | Zweitschlüssel für die Quintile, damit RFM reproduzierbar wird |
| `aufbau/0010_filiale_tabellenspalten.sql` | Drive-Through, Sitzplätze, Mietquote |
| `aufbau/0011_promotion_uplift.sql` | Warenkorb vor Rabatt statt des tautologischen ROI |
| `materialisieren.py` | wandelt die Sichten in materialisierte Sichten um; `--neu` frischt nur auf |

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
Management Summary. Die Seite lädt beim Aufruf 33 Sichten, baut daraus 91
Reihen und füllt 72 Kacheln und 30 Summary-Karten — in rund drei Sekunden.

| Datei | Aufgabe |
|---|---|
| `web/js/konfiguration.js` | die einzige Stelle mit einer Adresse |
| `web/js/datenquelle.js` | der Vertrag: 34 benannte Fragen; `PostgrestQuelle` als erste Umsetzung |
| `web/js/reihen.js` | übersetzt die Antworten in die Reihen, die Chart.js erwartet |
| `web/js/kacheln.js` | füllt Kennzahlkacheln und Management Summary |
| `web/js/texte.js` | baut die Deutungs- und Empfehlungstexte unter den Diagrammen |

### Drei Befunde, die erst der Umbau sichtbar gemacht hat

**Die RFM-Segmente waren nicht reproduzierbar.** Vier Abfragen hintereinander
lieferten vier Ergebnisse: Champions zwischen 4.179 und 4.187, Loyal zwischen
5.037 und 5.051. Ursache ist `ntile()`. Die Funktion füllt fünf gleich große
Fächer und muss dafür auch dort trennen, wo Werte gleich sind — an jeder
Quintilsgrenze stehen hunderte Kunden mit identischer Bestellhäufigkeit. Wer
davon ins vierte und wer ins fünfte Fach fällt, entschied die Reihenfolge des
Scans. `customer_id` als Zweitschlüssel in der `ORDER BY` macht die Zuordnung
eindeutig (`0009`).

**Der ROI der Aktionen ist keine Messung.** `roi = umsatz / rabattsumme` kürzt
sich zu `(1 − r) / r` — einer Funktion allein des Rabattsatzes, auf sechs
Nachkommastellen exakt für alle neun Aktionen. Drei Aktionen mit 10 Prozent
Rabatt haben deshalb denselben Wert 9,00, obwohl ihr Warenkorb vor Rabatt
zwischen 16,36 und 21,00 Euro liegt. Wer danach sortiert, sortiert nach dem
Rabattsatz und nennt es Wirtschaftlichkeit. `0011` stellt `uplift_pct` daneben:
den Warenkorb vor Rabatt gegen den Bestellwert ohne Aktion. Damit dreht sich
das Ergebnis — nicht der Student Discount steht am besten da, sondern App
Welcome (+8,0 Prozent Warenkorb, nach Rabatt −2,8 Prozent).

**Die Mietquote verglich Ungleiches.** Sie setzte eine Jahresmiete ins
Verhältnis zum kumulierten Umsatz aller Betriebsjahre und wies für die älteste
Filiale 2,4 Prozent aus. Auf das Jahr bezogen sind es 15,2 Prozent, und die
teuerste Lage ist nicht die, die die Tabelle nannte (`0010`).

### Warum die Semantikschicht materialisiert ist

Auf dem Entwicklungsrechner lief alles: 33 Sichten parallel, rund drei
Sekunden, kein Fehler. Von GitHub Pages aus fiel dieselbe Seite mit einer
Zeitgrenze aus (`57014 — canceling statement due to statement timeout`).

Die Ursache ist keine langsame Abfrage. Einzeln braucht keine Sicht mehr als
eine Sekunde; die teuerste, `v_produkt_jahr`, 0,9. Aber die Rolle `anon` hat
ein `statement_timeout` von drei Sekunden, und wenn 33 Aggregationen über
2,95 Millionen Positionen gleichzeitig starten, warten sie aufeinander: Jede
einzelne braucht dann rund sechs Sekunden, und zwei fallen aus.

`materialisieren.py` legt jede Sicht als Tabelle ab. Die Definition bleibt, wo
sie war — in `aufbau/*.sql`; das Skript liest sie mit `pg_get_viewdef` aus,
räumt in umgekehrter Abhängigkeitsreihenfolge ab und legt in richtiger neu an.
Die Reihenfolge kommt aus `pg_depend`, nicht aus einer Liste im Kopf.

Danach lädt die Seite in **281 Millisekunden** statt in drei Sekunden. Der
Preis ist der übliche: Die Werte sind so alt wie der letzte Lauf. Für diesen
Bestand ist das folgenlos, im Betrieb liefe das Skript nach dem nächtlichen
Abzug — `python3 db/materialisieren.py --neu`.

**Lehre daraus:** Ein Test auf dem Entwicklungsrechner prüft die Anwendung,
nicht den Betrieb. Der Fehler trat erst auf, als die Seite dort lief, wo sie
hingehört.

### Auch die Fließtexte rechnen

Der erste Durchgang nahm den Kacheln und Datenreihen ihre festen Zahlen, ließ
aber die Deutungs- und Empfehlungstexte unter den Diagrammen stehen. Das war
zu wenig: In 104 Textfeldern standen weiterhin echte Werte als Buchstaben im
HTML — darunter Sätze über 5.484 abwanderungsgefährdete Kunden, während das
Diagramm daneben bereits 4.998 zeichnete. Ein Text, der der Grafik über sich
widerspricht, ist schlimmer als kein Text: Er sieht aus wie eine Quelle.

`texte.js` baut diese Felder jetzt aus denselben Sichten, aus denen die
Diagramme kommen. Der Schlüssel ist ein `data-txt`-Attribut in der Form
`<canvas-id>.<feld>`. Sätze **ohne** Zahlen bleiben im HTML — sie sind
Methodik, keine Daten, und altern nicht.

Dasselbe gilt für die sieben Datentabellen (`tabellen.js`, 60 Zeilen aus
265 getippten Zellen) und den Maßnahmenplan der Management Summary
(`aktionen.js`, 18 Karten). Im sichtbaren HTML stehen jetzt noch **zwei**
Zahlen: die Anfangsstellungen der beiden Schieberegler in der Simulation. Das
ist Bedienzustand, keine Aussage über das Geschäft.

Beim Nachrechnen fielen über sechzig Aussagen durch, die sich nicht halten
ließen. Die folgenreichsten: Die App galt als „effizientester Kanal wegen des
höchsten Bestellwerts" — sie hat 2025 den **niedrigsten**. Das Tagesverlaufs-
Profil („Drive-Through morgens 35 Prozent, App abends 22 Prozent") existiert
nicht; der Kanalmix ist über alle 18 Öffnungsstunden nahezu konstant. Die
Altersgruppen unterscheiden sich in der Bestellhäufigkeit praktisch nicht
(29,9 bis 30,4 je Kunde) — der Unterschied liegt allein im Bestellwert. Und
das Streudiagramm „Temperatur gegen Tagesumsatz" zeichnete Bestellungen.

**Eine zweite Datenquelle** braucht eine Klasse mit denselben 34 Methoden und
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
| Zweitstärkste Altersgruppe | „gefolgt von 35–44 J." | 18–24 J. | `v_alter_umsatz` misst nach: 25–34 J. führen mit 24,1 %, danach kommen 18–24 J. mit 20,4 % vor 35–44 J. mit 20,0 %. |
| Umsatzanteil der beiden Spitzengruppen | „> 50 %" | 44,6 % | Summe der beiden gemessenen Anteile. |
| Personalspreizung | „3× Spreizung" | 3,2× | Aus `v_personal_filiale` gerechnet statt gerundet angegeben. |

Die letzten drei standen auf breiten Karten, die beim Ausräumen der Zahlen
zunächst ohne `data-ms` blieben und deshalb leer aufliefen. Sie sind
nachgezogen; die Prüfung „keine leere Kachel" deckt jetzt alle 30 Karten ab.

Nachgerechnet wird das im Browser: `web/abgleich.html` stellt die
Semantikschicht 29 Datenreihen des alten Dashboards gegenüber — **29 von 29
identisch**.
