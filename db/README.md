# Datenbank: Schemata `burgermetrics` und `wawi`

Der Bestand liegt seit August 2026 in einer selbstgehosteten **Supabase**-Instanz
(PostgreSQL 17.6) auf dem VPS. Die CSV-Dateien in [`../dataset/`](../dataset/)
bleiben die Quelle der Wahrheit; die Datenbank ist ihr Abbild.

Eine Instanz, zwei Schemata:

| Schema | Modell | Wer liest | Wer schreibt |
|---|---|---|---|
| `wawi` | operatives Warenwirtschaftsmodell, 3NF, deutsche Namen (wie `dataset/wawi_mini.sql`) | Kasse und Shop: Artikelstamm, Filialliste | Kasse und Shop: Bestellungen, über `wawi.bestellung_anlegen()` |
| `burgermetrics` | Galaxy-Schema mit Semantikschicht | Dashboard | der Ladelauf: CSV-Import und `burgermetrics.uebernahme_aus_wawi()` |

Der Weg zwischen beiden ist der ETL-Schritt aus Kapitel 2 der Dokumentation —
hier nicht als Behauptung, sondern als Funktion (`0019`).

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
| `aufbau/0012_diagrammwerte.sql` | Basislinie der Zufriedenheit — die letzte Zahl, die noch im Skript stand |
| `aufbau/0013_operative_sichten.sql` | Speisekarte und Filialliste für Shop und Kasse |
| `aufbau/0014_kanal_produkte.sql` | Die fünf meistbestellten Artikel je Kanal — ersetzt die letzte Musterdatenliste |
| `aufbau/0015_warenkorb_richtung.sql` | Richtung der Assoziationsregeln — die Konfidenz gehörte bei drei Paaren zur Gegenrichtung |
| `aufbau/0016_wawi_schema.sql` | Schema `wawi`: 15 Tabellen in 3NF, Stammdaten aus den Dimensionen übernommen |
| `aufbau/0017_wawi_bestand.sql` | die historischen Bestellungen einmalig ins operative Schema — Bestellung, Position, Rechnung |
| `aufbau/0018_wawi_sichten_und_schreiben.sql` | `v_speisekarte`, `v_filialliste`, `v_bestellung_letzte` und die Schreibfunktion `bestellung_anlegen()`; Rechte |
| `aufbau/0019_wawi_zu_burgermetrics.sql` | ETL `wawi` → `burgermetrics`: stg-Sichten, `uebernahme_aus_wawi()`, `etl_probe()`, `uebungsbestellungen_loeschen()` |
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

* **Die Schema-Liste hat zwei mögliche Quellen, und die Datenbank gewinnt.**
  PostgREST liest `PGRST_DB_SCHEMAS` aus der Container-Umgebung, also aus
  `/root/supabase/docker/.env`. Steht aber an der Rolle `authenticator` eine
  Einstellung `pgrst.db_schemas` (`ALTER ROLE … SET`), hat **die** Vorrang —
  nicht die Umgebung, wie hier lange behauptet. Genau so lag es auf der
  Instanz: Eine alte Rollen-Einstellung überstimmte die `.env`, und nach dem
  Eintrag von `wawi` meldete PostgREST weiter `Invalid schema: wawi` und
  zählte in der Fehlermeldung die alte Liste auf, ohne `storage` und
  `graphql_public`. Die Rollen-Einstellung ist entfernt
  (`ALTER ROLE authenticator RESET pgrst.db_schemas`); seither ist die
  `.env` die einzige Quelle. Prüfen, falls es wieder hakt:

  ```sql
  SELECT unnest(rolconfig) FROM pg_roles WHERE rolname = 'authenticator';
  ```

  Die Liste in der `.env` **ergänzen, nicht ersetzen**: Auf der Instanz
  laufen weitere Projekte, deren Schemata dort ebenfalls stehen. Seit `0016`
  gehören `burgermetrics` und `wawi` beide hinein. Der Browser wählt das
  Schema je Anfrage über `Accept-Profile` (lesen) und `Content-Profile`
  (Funktionsaufruf).
* **Eine geänderte `.env` braucht `up -d`, nicht `restart`.**
  `docker compose restart` startet den Container mit seiner alten Umgebung
  neu; die Datei wird erst beim Neuerzeugen gelesen. Das fiel beim Eintrag
  von `wawi` auf: Nach `restart` meldete PostgREST weiter `Invalid schema:
  wawi` und zählte in der Fehlermeldung die alte Liste auf.
* **`PGRST_DB_CHANNEL_ENABLED=false`** — `NOTIFY pgrst, 'reload schema'`
  bewirkt daher nichts. Nach jeder Änderung an Sichten oder Funktionen
  genügt ein Neustart, nach einer Änderung an `.env` muss der Container neu
  erzeugt werden:

```bash
cd /root/supabase/docker
cp .env .env.bak
sed -i 's/^\(PGRST_DB_SCHEMAS=.*\)$/\1,wawi/' .env     # anhängen, nicht ersetzen
grep ^PGRST_DB_SCHEMAS .env
docker compose up -d rest                                # liest .env neu
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

### Nachgebaut und gegengerechnet

Die Kette ist nicht nur beschrieben, sondern geprüft. Aus dem Repository-Stand
heraus — nicht aus der Arbeitskopie — wurde die gesamte Datenbank in ein
zweites Schema neu aufgebaut: Tabellen anlegen, 3,7 Millionen Zeilen aus den
CSV-Dateien laden, `obt_orders` erzeugen, Rechte setzen, alle elf
SQL-Dateien fahren.

Dann wurden beide Schemata Objekt für Objekt verglichen — nicht die
Zeilenzahl, sondern eine Prüfsumme über den sortierten Inhalt jeder Tabelle
und jeder Sicht:

**49 von 49 Objekten wertgleich.** Kein Unterschied in einer einzigen Zeile.

Das schließt die RFM-Segmentierung ein, die vor `0009` bei jeder Abfrage
andere Größen lieferte. Sie ist jetzt über einen vollständigen Neuaufbau in
einem anderen Schema hinweg reproduzierbar — das ist der eigentliche Beleg
dafür, dass der Zweitschlüssel wirkt.

Dabei fiel ein Fehler in `0004_sicherheit.sql` auf: Die Datei enthielt ein
`ALTER ROLE authenticator SET pgrst.db_schemas`. Das verlangt Rechte, die
niemand hat, der die Kette nicht als Superuser fährt — und es wirkt ohnehin
nicht, weil PostgREST seine Schemaliste aus der Container-Umgebung liest. Der
Schritt steht jetzt als Betriebsanweisung im Kommentar, nicht als SQL.

### Shop und Kasse lesen und schreiben im operativen Schema

Bis August 2026 trugen beide Oberflächen ihren Katalog als Liste im
Quelltext: 33 Artikel je Seite, mit Preisen. Der Abgleich gegen `dim_product`
ergab, dass **kein einziger Preis stimmte** — weder mit dem Preis von 2017
noch mit dem aktuellen. Der Classic Burger kostete an der Kasse 4,99 €, in
der Datenbank 4,49 € (2017) beziehungsweise 5,90 € (heute). 13 Artikel der
Kasse und 3 des Shops existierten im Datenmodell überhaupt nicht.

Das war nicht nur unordentlich. Die Fallstudie behauptet, Shop und Kasse
teilten sich denselben Kern — das ist die Aussage der Folie „Beide
Anwendungen schreiben in denselben Kern". Solange die Kataloge auseinander
liefen, war sie falsch.

Der erste Umbau ließ beide Seiten `v_speisekarte` und `v_filialliste` aus
`burgermetrics` lesen. Das behob die Preise, drehte aber die Richtung um:
Die operativen Anwendungen lasen aus dem Auswertungsmodell — aus
`dim_product`, einer denormalisierten Dimension —, und geschrieben wurde
nirgends. Die Kasse zeigte im Datenmodus die Zeile, die in `fact_orders`
entstehen würde, und warf sie dann weg.

Seit `0016` gibt es das operative Schema `wawi` mit dem 3NF-Modell aus
`dataset/wawi_mini.sql`, befüllt mit denselben Stammdaten und dem ganzen
Bestand. Beide Seiten lesen Speisekarte und Filialliste jetzt von dort, und
**jeder Bon und jede Shop-Bestellung wird gespeichert**: Bestellung,
Positionen und Rechnung in einer Transaktion, über die Funktion
`wawi.bestellung_anlegen()`. Der Browser schickt Artikel, Mengen, Zahlart und
Rabatt — keine Preise; die nimmt die Funktion aus `wawi.artikel`. Die Antwort
trägt die Belegnummer, die Kasse druckt sie unter den Bon, der Shop zeigt sie
statt der bisherigen Zufallsnummer `BM-2024-######`.

Was Kasse und Shop schreiben, trägt `quelle = 'kasse'` beziehungsweise
`'shop'` und eine Sitzungskennung; der kuratierte Bestand trägt
`quelle = 'bestand'`. `wawi.v_bestellung_letzte` zeigt die jüngsten fünfzig
Übungsbestellungen und ob der ETL-Schritt sie schon übernommen hat.

**Der ETL-Schritt läuft nicht von allein.** Das Dashboard zeigt den
kuratierten Bestand mit seinen 754.513 Belegen; jede Übungsstunde würde seine
Zahlen verändern. Die Übernahme ist deshalb ein bewusster Aufruf durch
`postgres`, wie ein nächtlicher Ladelauf im Betrieb:

```sql
SELECT * FROM burgermetrics.uebernahme_aus_wawi();   -- neue Belege ins Galaxy-Schema
SELECT * FROM wawi.etl_probe();                      -- muss 0 und 0 je Tabelle liefern
SELECT * FROM wawi.uebungsbestellungen_loeschen();   -- Übung zurücksetzen, Bestand bleibt
```

Danach `python3 db/materialisieren.py --neu`, sonst zeigt das Dashboard den
alten Stand. `etl_probe()` ist der Gleichheitsbeweis aus
`dataset/wawi_zu_analytisch.sql`, nur über den ganzen Bestand statt über 19
Belege: die symmetrische Differenz von `stg_fact_orders` gegen `fact_orders`
und von `stg_fact_order_items` gegen `fact_order_items`.

**Was `anon` darf:** beide Schemata lesen und genau diese eine Funktion
aufrufen. Kein `INSERT` auf eine Tabelle, kein Aufruf der drei
Betriebsfunktionen. Die Funktion prüft Filiale, Zahlart, Kanal, Artikel und
Mengen, fasst doppelte Artikel zusammen und lehnt mehr als sechzig Belege je
Sitzung und zehn Minuten ab. Ein öffentlich beschreibbarer Bestand ohne diese
Bremse wäre eine Einladung.

Beide Seiten sind ES-Module und benutzen dieselbe `datenquelle.js` wie das
Dashboard. Sie zeigen alle 57 Artikel statt 33 und melden denselben
Fehlerschirm, wenn die Quelle fehlt.

**Was bewusst in den Seiten bleibt** (`web/js/darstellung.js`): Produktbilder,
Beschreibungstexte, Öffnungszeiten, Anfahrtsbeschreibungen und die
Schnellwahl der Kasse. Nichts davon ist ein Messwert, nichts steht in einer
CSV-Datei. Sie in die Datenbank zu schreiben, nur damit alles aus einer
Quelle kommt, wäre der umgekehrte Fehler. Die Datei ist die Probe darauf:
Man darf darin alles ändern, ohne dass eine Zahl im Dashboard anders wird.

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
