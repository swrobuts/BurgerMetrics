# Phase 7: Verknüpfungen und Dokumentation — Implementierungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Startseite, README und Dokumentation des BM-Repos verweisen auf Rezensionen, Notebooks, Dash und das BM-Lab; die Seiten-Importe tragen den Versionsparameter; letzter PR der Reihe.

**Architecture:** Nur Verknüpfungen und Texte — keine neue Funktion. Vier Tasks: Startseite (`web/index.html` mit vierter Kachel, Tastenkürzel, Satz zu Notebooks/Dash) und Versionsparameter der Modul-Importe; Dokumentation (`README.md`, `db/README.md`, `docs/02`, `05`, `07`, `08`); Kleinigkeiten aus dem Endreview von Phase 6 (`dash/README.md`, `.env.example`, Spec §9.1); Abnahme mit Spec-Absatz und PR.

**Tech Stack:** HTML/CSS (Startseite), Markdown, Playwright-MCP für die Sichtprüfung, `node --test web/tests/*.test.mjs` und `python3 web/tests/skripte_pruefen.py` als Regressionsprüfung.

**Spec:** `docs/superpowers/specs/2026-09-12-bm-analyse-lernumgebung-design.md` §10 (Verknüpfungen), §11 (Übergabe je Phase: „`README.md` und `web/index.html` verweisen darauf“), §12 Punkt 7; dazu die Phase-7-Vormerkungen aus den Stand-Absätzen (Phase 3: „Die Bremse erreicht den Browser als HTTP 503 … die Dokumentation in Phase 7 nennt das“; Phase 6: Kachel, README, Doku; Endreview Phase 6: `dash/README.md`, `.env.example`, §9.1-Baum).

## Global Constraints

- **Repository und Zweig:** `/Users/robert/Library/CloudStorage/OneDrive-Persönlich/Vorlesungen/Datenbasierte Fallstudien/BurgerMetrics/BurgerMetrics_Website`, Branch `bm-analyse` (steht auf `main` = 285bf09). Commits: `git -c core.fileMode=false add …`, Nachricht deutsch, Trailer `Co-Authored-By: <ausführendes Modell> <noreply@anthropic.com>`. Ein PR auf `main` am Ende; Merge nur nach Rückfrage bei Robert. Nie in einem Worktree unter `BurgerMetrics/.claude/worktrees/` arbeiten; leitet das Edit-Werkzeug dorthin um, mit Python/Bash direkt im Repository schreiben und per `grep` verifizieren.
- **Sprache:** Deutsch, echte Umlaute, sachlich, „Sie“ in Lehrtexten, keine Ausrufezeichen, deutsche Anführungszeichen „…“ in Prosa; englische Fachbegriffe bleiben englisch. Bestehende Dokumente in ihrer eigenen Stimme fortschreiben (README: knappe Sätze, Tabellen; docs/: nummerierte Kapitel mit `---`-Trennern und „Weiter:“-Zeile), nichts umschreiben, was nicht Gegenstand des Tasks ist.
- **Fakten nur aus Quellen:** Zahlen und Verhalten aus `db/aufbau/0021_rezensionen.sql`, `db/README.md`, `web/js/rezensionen.js`/`shop.html`/`datenquelle.js`, `notebooks/README.md`, `dash/README.md`, `web/lab/README.md`, den Stand-Absätzen der Spec und den Validierungsberichten unter `docs/validierung-*-2026-09-15.md`. Verifizierte Fakten (Stand 15.09.2026): 10.000 Rezensionen in `wawi.rezension` und `burgermetrics.fact_reviews` (alle `source = 'simulation'`), CSV `dataset/fact_reviews.csv` in Git LFS; Generator `dataset/generate_reviews.py` (Sterne aus Zufriedenheit und Bestelldauer, Bausteintexte je Sternestufe) mit anschließender Glättung der Texte in Claude Code; Shop-Knopf „Bewerten“ → `wawi.rezension_anlegen(artikel_id, sterne, inhalt, filiale_id, sitzung)` per PostgREST-RPC unter der Rolle `anon` (Sterne 1–5, Text 5–500 Zeichen, 20 je Sitzung in zehn Minuten, 600 je Stunde; Bremse `ERRCODE 53400`, im Browser HTTP 503 mit der Meldung der Datenbank; Meldung nach dem Speichern `Gespeichert als wawi.rezension #…`); öffentlich sichtbar nur Aggregate (`v_rezension_produkt`: Ø Sterne, Anzahl, Anteil positiv), Besuchertexte erscheinen auf keiner Seite; Übernahme durch den Betreiber mit `uebernahme_aus_wawi()` (vier Rückgabespalten) nach `fact_reviews` (`source = 'shop'`), `uebungsrezensionen_loeschen()` räumt auf; `fact_reviews` ist die dritte Faktentabelle (Grain: eine Rezension) mit Fremdschlüsseln auf `dim_date`, `dim_customer`, `dim_product`, `dim_branch` und `fact_orders`; Rolle `studi_daba` (Kennwort `thws`) ohne EXECUTE auf `bestellung_anlegen`/`rezension_anlegen`. Notebooks: neun ausgeführte Notebooks `notebooks/00`–`08` (Zugang und Daten, analytisches Datenmodell, RFM und Kundensegmente, Warenkorb, Nachfrageprognose, Wetter und Ereignisse, Zufriedenheit, Ausreißer, Sentiment), Colab-fähig, `notebooks/README.md`; Dash-App `dash/app.py` mit vier Karten (`python3 dash/app.py` → `http://127.0.0.1:8050`); Notebook 00 startet in seiner letzten Codezelle nur die Karte „Umsatz je Monat“ mit Filialauswahl inline. BM-Lab: `web/lab/` mit acht Labs und 41 Übungen, PostgreSQL im Browser (PGlite), Adresse `https://swrobuts.github.io/BurgerMetrics/lab/`, Aufbau und Abnahme in `web/lab/README.md`.
- **Startseite:** Leitfarbe des Labs `#C2410C` (Spec §2.3) als `--orange`; Kachelraster vier Spalten, ab 1024 px zwei, mobil eine; Tastenkürzel `4`; relative Verweise (`lab/`), damit lokal und auf Pages dieselbe Seite läuft. Keine sonstige Änderung an Texten oder Gestaltung der Startseite.
- **Versionsparameter (Konvention aus Phase 3):** Pages liefert Dateien mit `max-age=600`; die Modul-Importe der HTML-Seiten tragen einen Versionsparameter, der bei Änderungen an `web/js/*.js` hochgezählt wird (`shop.html`: `?v=20260912`). Phase 7 gibt `pos.html`, `dashboard.html` und `abgleich.html` dieselbe Konvention mit `?v=20260915` und hebt `shop.html` auf `?v=20260915` (die Module `datenquelle.js`/`rezensionen.js` wurden am 15.09. geändert).
- **Deck:** Kein Foliendeck in Phase 7 (Roberts Ansage vom 15.09.2026): weder Neubau noch Bildschirmfoto; Roberts überarbeitete Fassung liegt unter `Vorlesungen/Übergreifend/Fallstudien/BurgerMetrics/` und bleibt unberührt.
- **Abnahme:** `node --test web/tests/*.test.mjs` und `python3 web/tests/skripte_pruefen.py` ohne Fehler; Startseite im Browser: vier Kacheln, Taste `4` öffnet `lab/`, Lab-Startseite „← Zur Fallstudie“ führt zurück; alle neuen Verweise in README/docs zeigen auf existierende Dateien oder Adressen (Link-Prüfung per Skript); Spec §11 Stand-Absatz Phase 7; PR ohne Merge.
- **Umgebung:** Node 26, Python `/Users/robert/miniforge3/bin/python3`, Playwright-MCP; kein `sleep` in Bash-Ketten; lokaler Server `cd web && python3 -m http.server 8731` im Hintergrund.

---

### Task 1: Startseite und Versionsparameter

**Files:**
- Modify: `web/index.html` (`:root`-Variablen Zeile 12–13, Kachel-CSS Zeilen 43–70, Media Queries Zeilen 134–160, Kachelblock Zeilen 188–223, Abschnitt „Analytics-Projektablauf“ Zeilen 226–282, Tastatur-Handler Zeilen 408–413)
- Modify: `web/pos.html:2294-2296`, `web/dashboard.html:3085-3091`, `web/abgleich.html:15-16`, `web/shop.html:6075-6079` (Modul-Importe)

- [ ] **Step 1: Vierte Kachel**

In `:root` die Variable `--orange:#C2410C` ergänzen. Die `c-*`-Regeln um `c-orange` erweitern, nach dem Muster von `c-blue` (Zeilen 49–69): `.c-orange .card-cta{color:var(--orange);background:#FDF1E7;border:1px solid #f5c8b3}`, Hover `background:#f9dccb;border-color:#ee9f7c`, `.c-orange:hover{border-color:#f5c8b3}`, `.c-orange .card-top{background:var(--orange)}`, `.c-orange .card-icon{background:#FDF1E7;color:var(--orange)}`, `.c-orange .card-tag{background:#FDF1E7;color:var(--orange);border:1px solid #f5c8b3}`. Raster: `.cards{grid-template-columns:repeat(4,1fr)}`; bei `max-width:1024px` zwei Spalten (bestehende Regel Zeile 138 bleibt), bei `max-width:768px` eine (Zeile 141 bleibt). Nach der Dashboard-Kachel (Zeile 223) die vierte Kachel im selben Aufbau:

```html
    <a class="card c-orange" href="lab/">
      <div class="card-top"></div>
      <div class="card-header">
        <div class="card-icon"><i class="fa-solid fa-flask"></i></div>
        <div class="card-cta">Lab öffnen <span class="cta-arrow">→</span></div>
      </div>
      <div class="card-label">Lernumgebung</div>
      <h3>BM-Lab</h3>
      <p>Acht Labs mit 41 Übungen im Browser: Zugang, Daten, Datenmodell, Power BI, Tableau, Python, Data Mining, externe Daten — mit PostgreSQL im Browser, ohne Konto.</p>
      <span class="card-tag">Übungen · PGlite · Regal-Simulator</span>
    </a>
```

Die Struktur der drei vorhandenen Kacheln (Reihenfolge von `card-label`, `h3`, `p`, `card-tag`) vorher prüfen und exakt übernehmen; der Satz im `<p>` darf um höchstens eine Zeile von den Nachbarn abweichen. Kachelhöhen im Raster gleich (Grid), keine zusätzliche CSS-Klasse.

- [ ] **Step 2: Tastenkürzel und Satz zu Notebooks und Dash**

Im Handler (Zeile 408 ff.) `if(e.key==='4')location.href='lab/';` ergänzen. Im Abschnitt „Analytics-Projektablauf“ nach dem `.lead`-Absatz (oder als letzter Satz davon) ein Satz:

> Die neun Notebooks unter <a href="https://github.com/swrobuts/BurgerMetrics/tree/main/notebooks">notebooks/</a> und die Dash-App unter <a href="https://github.com/swrobuts/BurgerMetrics/tree/main/dash">dash/</a> führen diesen Ablauf mit Python gegen die Datenbank vor — vom Zugang mit dem Demo-Konto bis zur Sentiment-Analyse.

Falls die Seite an anderer Stelle die Tasten 1–3 erklärt (grep `Taste`, `kbd`, `Shortcut`), dort `4` ergänzen; sonst nichts weiter.

- [ ] **Step 3: Versionsparameter**

In `pos.html`, `dashboard.html`, `abgleich.html` an jeden `from './js/….js'` der Seiten-Importe `?v=20260915` anhängen; in `shop.html` die vier `?v=20260912` auf `?v=20260915` heben. Modul-interne Importe (innerhalb von `web/js/*.js`) bleiben unverändert (wie bei Phase 3).

- [ ] **Step 4: Prüfen**

```bash
cd web && node --test tests/*.test.mjs 2>&1 | tail -3 && /Users/robert/miniforge3/bin/python3 tests/skripte_pruefen.py | tail -3 && cd ..
grep -n "from './js/" web/pos.html web/dashboard.html web/abgleich.html web/shop.html | grep -vc "?v=20260915"   # → 0
```

Browser (Playwright-MCP, Server auf 8731): `http://localhost:8731/` — vier Kacheln nebeneinander (Breite ≥ 1100 px), Kachel „BM-Lab“ orange, Klick führt zu `/lab/`; Taste `4` auf der Startseite führt zu `/lab/`; bei 900 px Breite zwei Spalten, bei 600 px eine; `/pos.html`, `/dashboard.html`, `/abgleich.html`, `/shop.html` laden ohne Konsolenfehler (Datenquelle darf „Demo“/CSV sein). Bildschirmfotos in den SDD-Workspace.

- [ ] **Step 5: Commit**

`web: Startseite mit Kachel BM-Lab, Taste 4, Versionsparameter der Modul-Importe`

---

### Task 2: README und Dokumentation

**Files:**
- Modify: `README.md` (Tabelle „Was wo liegt“ Zeilen 41–49, Abschnitt „Der große Weg“ Zeilen 81–88, „Die Kette“ Zeilen 90–107)
- Modify: `db/README.md` (Absatz „Was `anon` darf“ Zeilen 377–386)
- Modify: `docs/02-datenmodell.md` (§2.3 Diagramm Zeilen 99–139 und Tabelle Zeilen 141–150), `docs/05-anwendungen.md` (§5.5 Zeilen 100–108), `docs/07-lehrbezug.md` (neuer Abschnitt nach 7.6, Terminologie wird 7.8), `docs/08-entscheidungen.md` (neuer Eintrag E10 vor „Offene Punkte“, Zeile 151)

- [ ] **Step 1: `README.md`**

Tabelle „Was wo liegt“: Zeile `web/` → „Online-Shop, Kassensystem, BI-Dashboard und unter `web/lab/` die Lernumgebung BM-Lab“; neue Zeile `| \`web/lab/\` | Lernumgebung BM-Lab: acht Labs mit 41 Übungen im Browser, PostgreSQL per PGlite; \`web/lab/README.md\` |` nach `web/`. Nach „Der große Weg“ zwei neue Abschnitte gleicher Ebene (`###`):

**„Notebooks und Dash“** — drei bis fünf Sätze: neun ausgeführte Notebooks `notebooks/00`–`08` (Themen aufzählen), jedes läuft mit dem Demo-Konto lokal oder in Colab (`notebooks/README.md`); große Tabellen bleiben in der Datenbank, `lade_csv()` nur für Dimensionen (LFS-Budget); die Dash-App `dash/app.py` zeigt vier Karten aus der Semantikschicht (`dash/README.md`).

**„Lernumgebung“** — drei bis vier Sätze: BM-Lab unter <https://swrobuts.github.io/BurgerMetrics/lab/>, acht Labs, 41 Übungen, SQL-Übungen gegen PostgreSQL im Browser (PGlite, Miniaturbestand in beiden Schemata), Regal-Simulator für Power BI und Tableau, Aufbau und Abnahmelauf in `web/lab/README.md`.

„Die Kette“: Schritt 4 → „**Anwendungen** — Shop und Kasse lesen und schreiben in denselben operativen Kern, `web/`; seit `0021` nimmt der Shop auch Rezensionen entgegen (`wawi.rezension`)“; Schritt 5 → „… Galaxy-Schema mit drei Faktentabellen (`fact_orders`, `fact_order_items`, `fact_reviews`), `db/aufbau/`; der ETL-Schritt von `wawi` dorthin ist `db/aufbau/0019`, erweitert um Rezensionen in `0021`“.

- [ ] **Step 2: `db/README.md`**

Im Absatz „Was `anon` darf“ nach „… 600 je Stunde insgesamt.“ den Satz einfügen: „Greift die Bremse, meldet die Datenbank `ERRCODE 53400`; PostgREST gibt das als HTTP 503 weiter, und der Shop zeigt die Meldung der Datenbank.“ Sonst nichts (Rezensionsweg, `0021`-Zeile, `uebungsrezensionen_loeschen()` stehen schon).

- [ ] **Step 3: `docs/02-datenmodell.md`**

§2.3: im Mermaid-Diagramm `fact_reviews` als dritte Faktentabelle ergänzen — Knoten `REVIEWS[fact_reviews<br/>10.000 Zeilen<br/><b>Grain: eine Rezension</b>]` mit `style REVIEWS fill:#003E6D,color:#fff`, Kanten `DATE --> REVIEWS`, `CUSTOMER --> REVIEWS`, `BRANCH --> REVIEWS`, `PRODUCT --> REVIEWS`, `ORDERS -->|order_id| REVIEWS`; der Einleitungssatz „BurgerMetrics hat zwei, die sich Dimensionen teilen“ → „drei“ mit einem Halbsatz „seit September 2026 auch `fact_reviews` (Kapitel 5.5)“; Tabelle „Kennzahlen und Attribute“: in der Zeile „Inhalt“ `stars` ergänzen. Diagramm-Syntax mit dem Mermaid-MCP oder `npx -y @mermaid-js/mermaid-cli` prüfen (Fehlerfreiheit genügt).

- [ ] **Step 4: `docs/05-anwendungen.md`**

§5.5 nach dem Absatz zur Filialkarte ein Absatz „Bewerten“: Knopf „Bewerten“ auf der Produktkarte öffnet ein Modal (Sterne, Text, Filiale); Speichern ruft `wawi.rezension_anlegen()` per PostgREST-RPC unter `anon` auf; die Prüfungen (Sterne 1–5, Text 5–500 Zeichen, 20 je Sitzung in zehn Minuten, 600 je Stunde) liegen in der Funktion, der Browser prüft nur vor; Bremse → HTTP 503 mit der Meldung der Datenbank; öffentlich nur Aggregate (`v_rezension_produkt`), kein Besuchertext auf einer Seite; `web/js/rezensionen.js` mit Tests `node --test web/tests/*.test.mjs`; Übernahme ins Auswertungsmodell bewusst durch den Betreiber (`uebernahme_aus_wawi()`), Rücksetzen `uebungsrezensionen_loeschen()`.

- [ ] **Step 5: `docs/07-lehrbezug.md`**

Neuer Abschnitt `## 7.7 Datenbasierte Fallstudien: Notebooks, Dash und BM-Lab` nach 7.6 (bisheriges 7.7 wird 7.8, Verweise darauf anpassen — grep `7.7`): Modul „Datenbasierte Fallstudien“ nutzt den Bestand mit dem Demo-Konto; Tabelle Notebook → Lerngegenstand (00 Zugang und Daten, 01 analytisches Datenmodell, 02 RFM/K-Means, 03 Warenkorb/Apriori, 04 Prognose, 05 Wetter und Ereignisse, 06 Zufriedenheit/Klassifikation, 07 Ausreißer, 08 Sentiment); Dash als Beispiel einer Anwendung auf der Semantikschicht; BM-Lab mit Tabelle Lab → Inhalt (01 Zugang, 02 Daten, 03 Datenmodell, 04 Power BI, 05 Tableau, 06 Python und Colab, 07 Data Mining, 08 Externe Daten und Sentiment) und Adresse; ein Satz, dass die Labs im Browser gegen einen Miniaturbestand laufen und die Notebooks gegen die echte Datenbank.

- [ ] **Step 6: `docs/08-entscheidungen.md`**

Neuer Eintrag `## E10 — Rezensionen als dritte Faktentabelle, geladen über CSV (September 2026) {#e10}` im Format von E9 (Frage, Erwogen-Tabelle, Gewählt, Preis): Frage — woher kommen 10.000 Rezensionen mit Text, und wie kommen sie ins Modell; Erwogen — echte Texte sammeln (kein Bestand, Datenschutz), reine Zufallstexte (ohne Zusammenhang zur Zufriedenheit), Generator mit Bausteinen plus Glättung der Texte (gewählt); Gewählt — Generator `dataset/generate_reviews.py` (Sterne aus Zufriedenheit und Bestelldauer), Glättung in Claude Code, Ladeweg über `dataset/fact_reviews.csv` (LFS) wie die übrigen Fakten, `source = 'simulation'`; Besuchertexte aus dem Shop erscheinen auf keiner Seite, nur Aggregate; Übernahme in `fact_reviews` bewusst manuell; Preis — synthetische Texte, an denen ein Sentiment-Modell zu gut abschneidet (Notebook 08: TF-IDF 100 %), und ein zweiter Schreibweg, der eine Bremse braucht. Verweis auf `docs/validierung-nur-lesezugang-2026-09-15.md` für die Rechte.

- [ ] **Step 7: Verweise prüfen und Commit**

```bash
/Users/robert/miniforge3/bin/python3 - <<'PY'
import re, pathlib
wurzel = pathlib.Path('.')
for datei in ['README.md', 'db/README.md', 'docs/02-datenmodell.md', 'docs/05-anwendungen.md', 'docs/07-lehrbezug.md', 'docs/08-entscheidungen.md']:
    t = pathlib.Path(datei).read_text(encoding='utf-8')
    for ziel in re.findall(r'\]\(([^)#]+)(?:#[^)]*)?\)', t):
        if ziel.startswith('http'): continue
        p = (pathlib.Path(datei).parent / ziel).resolve()
        if not p.exists(): print('FEHLT', datei, '->', ziel)
print('fertig')
PY
```

Commit: `docs: Rezensionen, Notebooks, Dash und BM-Lab in README und Dokumentation`

---

### Task 3: Kleinigkeiten aus dem Endreview von Phase 6

**Files:**
- Modify: `dash/README.md` (Zeilen 12–14), `.env.example`, `docs/superpowers/specs/2026-09-12-bm-analyse-lernumgebung-design.md` (§9.1-Baum)

- [ ] **Step 1: `dash/README.md`** — „In Colab läuft dieselbe App als letzte Zelle …“ → „In Colab startet die letzte Codezelle von `notebooks/00_zugang_und_daten.ipynb` mit `app.run(jupyter_mode="inline")` die Karte „Umsatz je Monat“ mit Filialauswahl; die vollständige App mit vier Karten läuft lokal.“
- [ ] **Step 2: `.env.example`** — nach den `PG*`-Zeilen: `# Für dash/app.py (optional; ohne die Variable nutzt die App das Demo-Konto studi_daba):` und `DATABASE_URL=postgresql+psycopg2://BENUTZER:KENNWORT@supabase.butscher.cloud:5433/postgres`.
- [ ] **Step 3: Spec §9.1** — im Baum unter `tools/verify.mjs, tools/sql.mjs` eine Zeile `tools/gen_daten.py          kopiert die Mini-Skripte, schreibt data/regal-bestellungen.json (Demo-Konto)`; im selben Baum `assets/pruefung.js, jsonpruefung.js, regal.js   unverändert übernommen` → `assets/jsonpruefung.js, regal.js   unverändert übernommen (pruefung.js entfällt, siehe Stand Phase 6)`.
- [ ] **Step 4: Commit:** `docs: dash/README, .env.example, Spec §9.1 (Endreview Phase 6)`

---

### Task 4: Abnahme, Spec-Absatz, PR

**Files:**
- Modify: `docs/superpowers/specs/2026-09-12-bm-analyse-lernumgebung-design.md` (§11: Absatz „Stand <Datum> (Phase 7)“ nach dem Phase-6-Absatz)

- [ ] **Step 1: Abnahmelauf** — `node --test web/tests/*.test.mjs`, `python3 web/tests/skripte_pruefen.py`, `node web/lab/tools/verify.mjs 2>/dev/null | tail -1` (unverändert 782/0), Link-Skript aus Task 2 Schritt 7; Browser: Startseite (vier Kacheln, Taste 4), `lab/` („← Zur Fallstudie“ → Startseite), `shop.html` lädt mit `?v=20260915`.
- [ ] **Step 2: Spec-Absatz** — „**Stand <Datum> (Phase 7):** Verknüpfungen abgenommen — …“ mit: Kachel und Taste 4, Satz zu Notebooks/Dash, Versionsparameter `?v=20260915` auf allen vier Seiten, README-Abschnitte und Tabelle, `db/README.md` (503), docs 02/05/07/08 (fact_reviews im Diagramm, Shop-Feature, Abschnitt 7.7, E10), `dash/README.md`, `.env.example`, §9.1-Baum; kein Foliendeck in Phase 7 (Roberts Entscheidung); damit ist die Übergabe je Phase aus §11 vollständig erfüllt.
- [ ] **Step 3: Commit, Push, PR** — `spec: Abnahmestand Phase 7 (Verknüpfungen)`; `git push origin bm-analyse`; nach dem Endreview des Zweigs `gh pr create --base main --head bm-analyse --title "Phase 7: Verknüpfungen und Dokumentation"` mit Body (Inhalt, Abnahme, Hinweis Deck) und Trailer „🤖 Generated with [Claude Code](https://claude.com/claude-code)“. Kein Merge.

---

## Selbstprüfung des Plans

**Spec §10 Abdeckung:** `web/index.html` Kachel/Raster/Taste/Satz — T1; `README.md` Abschnitte, Tabelle, Kette — T2; `db/README.md` — T2 (nur 503; Rest existiert seit Phase 2); docs 02/05/07/08 — T2; `slides/README.md` — entfällt (kein Deck in Phase 7, Roberts Ansage); `web/lab/index.html`-Rückverweise und `web/lab/README.md` — seit Phase 6 vorhanden (T4 prüft); `Vorlesungen/Lernumgebungen/BM-Lab.md` — seit Phase 6 vorhanden. §11 Übergabe: „`README.md` und `web/index.html` verweisen darauf“ — T1/T2. Phase-3-Vormerkung 503 — T2. Endreview-Phase-6-Punkte — T3. Versionsparameter — T1.

**Platzhalter:** `<Datum>` im Spec-Absatz (T4) und `<ausführendes Modell>` im Trailer sind vom Ausführenden zu setzen; sonst keine.

**Namen:** Kachelklasse `c-orange` (Spec §10) ↔ T1; Adresse `https://swrobuts.github.io/BurgerMetrics/lab/` ↔ T2/T4; Versionsparameter `?v=20260915` ↔ T1/T4.
