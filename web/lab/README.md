# BM-Lab

**Live:** [swrobuts.github.io/BurgerMetrics/lab/](https://swrobuts.github.io/BurgerMetrics/lab/) (nach dem Merge auf `main`)

Lernumgebung zur Fallstudie **BurgerMetrics** für das Modul Datenbasierte Fallstudien der THWS
Business School. Acht Labs führen vom Zugang zur Datenbank über die Wege zu den Daten und das
analytische Datenmodell zu den Werkzeugen Power BI, Tableau und Python bis zu Data Mining und
externen Daten – **41 Übungen** in sieben Formen, jede mit sofortiger Rückmeldung.

Die SQL-Übungen laufen gegen eine **echte PostgreSQL-Datenbank im Browser** (PGlite 0.5.5,
PostgreSQL 18.3 als WebAssembly): der Miniaturbestand der Fallstudie in den beiden Schemata
`wawi` (operativ) und `burgermetrics` (analytisch), Suchpfad `wawi, burgermetrics` wie in der
Datenbank der Fallstudie. Dazu ein **Shelf-Simulator** nach dem Vorbild von Power BI (Field Wells) und Tableau (Shelves).
Alles läuft als statische Seite ohne Build-Schritt, ohne Backend und ohne Anmeldung; der
Lernfortschritt bleibt im Browser (`localStorage`, Schlüssel `bm:fortschritt:<lab>`).

Die Umgebung ist aus der Lernumgebung WInf-SP abgeleitet (`Vorlesungen/Lernumgebungen/WInf-SP`,
nur lesen). Sie ist einsprachig deutsch und kennt keinen Terminal-Simulator, keinen
Deploy-Simulator und keine SQLite-Datenbank.

---

## Aufbau

```
web/lab/
  index.html                 Übersicht: acht Kacheln, Gesamtfortschritt, Verweise auf Startseite, Shop, Dashboard, Notebooks
  lab-01-zugang.html         Zugang und Datenbank                (6 Übungen)
  lab-02-daten.html          Daten beschaffen                    (5)
  lab-03-datenmodell.html    Analytisches Datenmodell            (5)
  lab-04-powerbi.html        Power BI                            (5)
  lab-05-tableau.html        Tableau                             (5)
  lab-06-python.html         Python und Colab                    (5)
  lab-07-datamining.html     Data Mining                         (5)
  lab-08-extern.html         Externe Daten und Sentiment         (5)
  assets/bm.css              Gestalt (aus winf.css, Palette der Spec §2.3: #C2410C, #9A3412, #ED7004, #FDF1E7, #7C2D12)
  assets/bm.js               Laufzeit (aus winf.js): LABS, Saatfolge, Übungsboxen, Shelf-Simulator, Fortschritt; nur Deutsch, Schlüssel bm:*
  assets/datenbank.js        Gemeinsame Saatfunktion und Warteschlange für vollständige SQL-Aufträge
  assets/sqlpruefung.js      Gemeinsamer Ergebnisvergleich für Browser und Abnahmelauf
  assets/jsonpruefung.js     Prüfung der JSON-Übungen (unverändert aus WInf-SP)
  assets/regal.js            Aggregation und Zielprüfung des Shelf-Simulators (aus WInf-SP; nur die zwei deutschen Prüfmeldungen auf Shelf umgestellt)
  assets/pglite/             PostgreSQL als WebAssembly (PGlite), lokal statt vom CDN (rund 19 MB)
  assets/tableau/            Neunzehn Bildschirmfotos von Tableau Desktop 2026.2 für Lab 05 (19.09. und 22.09.2026, rund 1,9 MB)
  assets/powerbi/            Zwanzig Bildschirmfotos von Power BI Desktop (August 2026) für Lab 04 (21.09.2026, rund 2,6 MB)
  data/wawi_mini.sql         Schema wawi: Kopie aus dataset/ (Kasse, Shop, Rezensionen)
  data/burgermetrics_mini.sql Schema burgermetrics: Kopie aus dataset/ (Galaxy-Schema mit fact_reviews)
  data/bm_sichten.sql        Sechs Sichten der Semantikschicht auf dem Miniaturbestand
  data/regal-bestellungen.json  2.000 Bestellungen 2025 aus obt_orders als flache Tabelle für den Shelf-Simulator
  data/uebungen/lab-0N.json  Befehlskarten, Übungen, Spielplätze je Lab
  vorlagen/                  Kopiervorlagen: Verbindungszeilen, Measures, Calculated Fields, Notebook-Zelle
  tools/verify.mjs           Abnahmelauf ohne Browser (siehe unten)
  tools/sql.mjs              SQL gegen die Browser-Datenbank auf der Kommandozeile ausprobieren
  tools/gen_daten.py         Erzeugt data/: Kopien der Mini-Skripte und die Shelf-Daten (Demo-Konto)
  README.md                  Diese Datei
```

Die Übungszahl je Lab steht in `LABS` (`assets/bm.js`); Seite, JSON und Vorlagen eines Labs
werden gemeinsam gepflegt.

---

## Lokal starten

Ein Server ist nötig, weil die Seite Module, JSON und WebAssembly per `fetch` lädt – `file://`
genügt nicht. Der Server läuft aus `web/`, weil das Lab unter `web/lab/` liegt und die
Verweise auf Startseite, Shop und Dashboard relativ nach oben zeigen:

```bash
cd web && python3 -m http.server 8731
# http://localhost:8731/lab/
```

---

## Hinweise für Autoren

Verbindlich ist der Leitfaden der Vorlage, `WInf-SP/tools/AUTORENLEITFADEN.md` (Aufbau der
Seite, Dramaturgie, Befehlskarten, Nachbildungen, Kopiervorlagen, JSON-Format) – mit vier
Abweichungen:

1. **Nur Deutsch.** Kein `<span lang="en">`, keine `en`-Felder im JSON, kein Sprachumschalter,
   keine `?lang=`-Verweise. Texte stehen direkt (`<p>…</p>`), JSON-Textfelder sind `{ "de": "…" }`.
   Der Abnahmelauf prüft, dass `de` vorhanden und `en` abwesend ist. Englische Fachbegriffe
   bleiben englisch (Measure, Extract, Grain, Fan Trap, Notebook, Runtime …).
2. **Die Fallstudie ist BurgerMetrics**, nicht Velo City: acht Filialen in Würzburg,
   754.513 Bestellungen 2017 bis 2026; im Lab liegt der Miniaturbestand (siehe „Daten“).
   Zugangsdaten: nur das Demo-Konto `studi_daba`/`thws` (öffentlich, nur lesend); das
   Betreiberkonto erscheint nirgends. Die Labs schreiben nie in die echte Datenbank;
   Schreibübungen laufen in PGlite.
3. **Kein Terminal, kein Deploy, kein SQLite.** Die Übungstypen sind `quiz`, `zuordnen`,
   `checkliste`, `sql`, `json`, `reihenfolge` und `regal`; die Seitendatenbank ist überall
   `data-datenbank="postgres"`, ein `engine`-Feld gibt es nicht.
4. **Betriebssystemwahl bleibt in der Laufzeit** (`bm:os`, Klassen `nur-mac`, `nur-win`,
   `nur-cmd`, `nur-unix`, `nur-windows`); Seiten zeigen sie nur, wenn sie OS-abhängige Zeilen
   haben.

Ein Lab besteht aus `lab-0N-name.html`, `data/uebungen/lab-0N.json` und seinen Kopiervorlagen
unter `vorlagen/` (Lab 04 und 05 zusätzlich aus den Bildschirmfotos unter `assets/powerbi/` und
`assets/tableau/`, die an die Stelle der Nachbildungen treten — geprüfte Oberfläche statt
gezeichneter, Ziffern im Bild, Legende darunter; das Power-BI-Projekt dazu liegt unter
`powerbi/`, die Tableau-Arbeitsmappe unter `tableau/` im Repository); nichts anderes wird angefasst (nicht `bm.js`, nicht `bm.css`, nicht
`index.html`, keine anderen Labs). Übungs-IDs `W0N-01` …, Befehlskarten `B01` …; die Zahl der
Übungen je Lab steht in `LABS` in `assets/bm.js`. Platzhalter, die die Laufzeit füllt:

| Platzhalter | Wirkung |
|---|---|
| `<div data-befehl="B01"></div>` | Befehlskarte aus `befehle.B01` |
| `<div data-uebung="W0N-01"></div>` | Übungsbox aus `uebungen[]` |
| `<div data-datenbank="postgres"></div>` | Datenbankband und Start der Datenbank – **genau einmal je Seite mit SQL-Übungen, oberhalb der ersten SQL-Übung** |
| `<div data-sql-konsole data-start="SELECT …"></div>` | freie SQL-Konsole (ohne Prüfknopf, ohne Fortschritt) |
| `<div data-json-konsole data-start='{ … }'></div>` | freie JSON-Werkbank (prüfen, formatieren) |
| `<div data-regal="name" data-variante="tableau\|powerbi"></div>` | freier Shelf-Simulator aus `spielplaetze.name` |
| `<div data-einordnung>`, `<div data-fortschritt>`, `<div data-lab-nav>` | Einordnung aus `LABS`, Fortschritt, Vor/Zurück |

SQL-Übungen werden am **Ergebnis** geprüft (Zeilenmenge), nicht am Text; bei verändernden
Anweisungen (`CREATE TABLE`, `INSERT`) vergleicht eine `kontrolle`-Abfrage. Vor jeder Prüfung
sät die Laufzeit die Datenbank neu, damit auch `CREATE TABLE`-Übungen wiederholbar sind. Der
Shelf-Simulator liest Felder und Daten aus `regal.felder` und `regal.daten` des Lab-JSON
(Daten: `data/regal-bestellungen.json`).

---

## Daten

Die Browser-Datenbank wird bei jedem Seitenaufruf in dieser **Saatfolge** gefüllt (identisch in
`assets/bm.js` und `tools/sql.mjs`; der Abnahmelauf vergleicht beide):

1. `CREATE SCHEMA wawi; SET search_path TO wawi;` → `data/wawi_mini.sql`
2. `CREATE SCHEMA burgermetrics; SET search_path TO burgermetrics;` → `data/burgermetrics_mini.sql`
3. `SET search_path TO wawi, burgermetrics;` → `data/bm_sichten.sql`
4. `SET search_path TO wawi, burgermetrics`

Kontrollzahlen des Miniaturbestands: **19 Bestellungen**, **55 Positionen**, Umsatz
**200,85 €**, **12 Rezensionen** (in beiden Schemata); die Fan Trap (Bestellungen mit
Positionen verknüpft und dann summiert) ergibt **649,16 €**, Faktor 3,23.

`data/` wird nicht von Hand fortgeschrieben: `tools/gen_daten.py` kopiert die Mini-Skripte aus
`dataset/` (die einzige Quelle der Wahrheit) und zieht die Shelf-Daten mit dem Demo-Konto aus
`burgermetrics.obt_orders`; nur `data/bm_sichten.sql` (sechs Sichten) ist eine gepflegte Datei.
Ändert sich `dataset/`, läuft `python3 web/lab/tools/gen_daten.py` aus dem
Repository-Wurzelverzeichnis erneut.

---

## Abnahmelauf

```bash
cd web/lab
node tools/verify.mjs
node --test tools/datenbank.test.mjs
```

Der Lauf braucht keinen Browser und prüft: Platzhalter und JSON deckungsgleich, Deutsch-Pflicht,
Übungszahlen wie in `LABS`, Antwortindizes, Zuordnungsziele, JSON-Lösungen bestehen ihre Regeln
(und die Starttexte nicht), Reihenfolge-Start ungleich Lösung, Shelf-Lösung erfüllt das Ziel,
Befehlskarten vollständig, verlinkte Dateien und Bilder vorhanden (Bilder mit Alternativtext), Seitenbausteine (`data-lab`, große
Nummer, Seitennavigation, Einordnung, Fortschritt, Navigation), genau ein Datenbankband je Seite
mit SQL-Übungen, keine Terminal-, Deploy- oder SQLite-Reste, keine Reste der Vorlage, die
Palette in `bm.css`, die Saatfolge in `bm.js` gegen `tools/sql.mjs`. Danach läuft **jede
SQL-Lösung in PGlite** gegen die frisch gesäte Datenbank: Sie darf nicht scheitern, liefert
Zeilen (oder ihre Kontrolle tut es), und der Starttext löst die Aufgabe nicht schon. Am Ende
sichert ein dritter Abschnitt die Prüfungen selbst ab. Ausgabe: `FEHL …` je Befund, zuletzt
`n Zusicherungen, m Fehler.`, Exit 1 bei Fehlern. PGlite schreibt unter Node eine Warnung zum
Modultyp auf stderr; sie ist bedeutungslos.

Die zusätzlichen Regressionstests prüfen Windows-kompatibles Laden von PGlite,
Zurücksetzen nach Schema-Namen mit Anführungszeichen, versetzte SQL-Prüfungen sowie
den Ergebnisvergleich. Browser und Abnahmelauf benutzen dafür dieselben Funktionen.
Eine laufende Prüfung, eine freie Abfrage und ein Reset werden als ganze Aufträge
nacheinander ausgeführt, damit ihre Zwischenschritte einander nicht verändern.

Eine Musterlösung vor dem Eintrag ins JSON ausprobieren:

```bash
cd web/lab
node tools/sql.mjs "SELECT jahr, bestellungen, umsatz FROM v_kennzahlen_jahr ORDER BY jahr" 2>/dev/null
node tools/sql.mjs --datei abfrage.sql 2>/dev/null
```

Sichtprüfung im Browser (Server wie oben): Kopf, Seitennavigation, alle Übungsboxen, das
Datenbankband erreicht „bereit“, eine SQL-Übung mit der Musterlösung durchspielen, Konsole ohne
Fehler.

---

## Veröffentlichen

Kein eigenes Setup: Der Merge auf `main` löst den vorhandenen Workflow
`.github/workflows/static.yml` aus, der `web/` samt `web/lab/` auf GitHub Pages ausliefert;
`web/.nojekyll` besteht bereits. Adresse danach: `https://swrobuts.github.io/BurgerMetrics/lab/`.
Das Paket unter `web/lab/` ist rund 20 MB groß, davon die PGlite-Dateien rund 19 MB; sie liegen im
Repository, damit die SQL-Übungen im Hörsaal an keinem fremden Dienst hängen.
