# Freigabe B: Leseansicht im Shop — Implementierungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ein Klick auf die Sternzeile einer Produktkarte öffnet die Leseansicht. Sie zeigt den Mittelwert, die Verteilung der Sterne mit Filter und die freigegebenen Rezensionen, zehn je Seite, mit „Weitere laden“ und „Selbst bewerten“. Das Formular weist auf die Prüfung hin. Der Datenmodus zeigt den Status der eigenen Rezension.

**Architecture:** Der Shop kennt weiter nur Methoden von `Datenquelle`. Zwei neue Methoden (`rezensionenLesen`, `rezensionStatus`) bilden die Sichten `v_rezensionen_lesen` und `v_rezension_status` aus Phase A ab. Logik ohne DOM kommt in das vorhandene Modul `web/js/rezensionen.js` und wird mit `node --test` geprüft. `shop.html` bekommt ein zweites Modal nach dem Muster des Rezensionsformulars, die Brücken im Modulblock und die neuen Texte.

**Tech Stack:** Vanilla JavaScript (ES-Module und klassischer Skriptblock wie bisher), PostgREST über `fetch`, Node 24 (`node --test`), Python 3 für `web/tests/skripte_pruefen.py`, Playwright-MCP für die Abnahme im Browser.

**Spec:** `docs/superpowers/specs/2026-09-30-rezensionen-jev-freigabe-design.md`, Abschnitte 7 (Shop: Leseansicht), 10 (Abnahme 1) und 11 (Phase B).

## Global Constraints

- Voraussetzung: Phase A ist live (`0023` in der Produktion, Sichten `v_rezensionen_lesen`, `v_rezension_status`, Spalten `anzahl_1` bis `anzahl_5` in `v_rezension_produkt`).
- Deutsch mit echten Umlauten in neuen Kommentaren, Texten und Commits; Bezeichner, CSS-Klassen und IDs ASCII. Bestehende ASCII-Kommentare bleiben.
- Lehrcode: kurze Funktionen, deutsche Namen, ein Kommentar je Funktion.
- Der Shop kennt **ausschließlich** Methoden von `Datenquelle`; keine URL, keine Sicht, keine Spalte außerhalb von `web/js/datenquelle.js`.
- Rezensionstext wird **nur** mit `textContent` gesetzt, nie mit `innerHTML`, auch nicht über `logEvent()` (das `innerHTML` benutzt).
- Texte wörtlich: Hinweis im Formular „Rezensionen werden vor der Veröffentlichung geprüft.“; Bestätigung „Danke! Ihre Rezension wird geprüft und erscheint in Kürze.“; ohne freigegebene Rezension bleibt „noch keine Bewertung“; Knöpfe „Weitere laden“, „Selbst bewerten“, „Alle“; Datum als TT.MM.JJJJ.
- Zehn Rezensionen je Seite (`SEITENGROESSE = 10` in `rezensionen.js`).
- Cache-Brecher: In `shop.html` alle vier Modul-Importe von `?v=20260915` auf `?v=20261001` setzen. Andere Seiten bleiben unverändert; sie brauchen die neuen Methoden nicht.
- Keine neuen Abhängigkeiten, kein Build-Schritt.
- Tests: `node --test "web/tests/*.test.mjs"` und `python3 web/tests/skripte_pruefen.py`. Die Integrationstests schreiben nie erfolgreich.
- Commits: `git -c core.fileMode=false add <Dateien>` (nie `tableau/BurgerMetrics.twb`), deutsche Nachricht, zweiter Absatz `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Branch `bm-analyse`, am Ende ein PR auf `main`, Merge nur nach Roberts Zusage.
- Repo-Pfad wie in Plan A; Dateien im Repo schreibt der Executor per Bash (Heredoc oder Python), weil der Write-Hook sie außerhalb des Worktrees sperrt.

## Review Focus

1. **Schneller Filterwechsel.** Klickt jemand „5 ★“ und gleich „1 ★“, darf die späte Antwort des ersten Filters nicht in die Liste des zweiten geraten. `leseSeiteLaden()` verwirft Antworten, deren Artikel oder Filter nicht mehr gilt. Test: Abnahme-Schritt „schneller Filterwechsel“ (Task 4).
2. **Veralteter Bewertungsstand.** Die Zahlen der Verteilung stammen vom Laden der Seite. Gibt die Moderation inzwischen weitere frei, stimmt `anzahl` nicht mehr genau. „Weitere laden“ erscheint deshalb nur, wenn die letzte Seite voll war. Test: `anzahlFuer und weitereLaden` (Task 1).
3. **Artikel ohne freigegebene Rezension.** Die Sternzeile ist dann kein Knopf, der ein leeres Fenster öffnet, sondern bleibt „noch keine Bewertung“. Test: `verteilung(undefined)` in Task 1, Abnahme in Task 4.
4. **Escape bei zwei Fenstern.** Heute ruft jede Escape-Taste `closeReview()` auf, auch ohne offenes Formular, und springt mit dem Fokus zurück zum alten „Bewerten“-Knopf. Mit der Leseansicht schließt Escape nur das Fenster, das offen ist. Test: Abnahme-Schritt „Escape“ (Task 4).
5. **Handybreite.** Verteilung mit Balken und Prozent darf auf 375 px nicht waagerecht scrollen. Test: Abnahme-Schritt „Handybreite“ (Task 4).

---

## Dateistruktur

| Datei | Verantwortung |
|---|---|
| `web/js/rezensionen.js` (ändern) | neue reine Funktionen: `SEITENGROESSE`, `sterneText`, `anzahlText`, `verteilung`, `anteilText`, `statusText`, `anzahlFuer`, `weitereLaden`; `datensatzZeilen` mit Status |
| `web/tests/rezensionen.test.mjs` (ändern) | Modultests der neuen Funktionen |
| `web/js/datenquelle.js` (ändern) | `rezensionenLesen(artikelId, sterne, seite, groesse)`, `rezensionStatus(rezensionId)`; Beschreibung von `rezensionenProdukt()` und `kundenstimmen()` nachgezogen |
| `web/tests/datenquelle.test.mjs` (ändern) | Abfrage der neuen Methoden mit nachgebildetem `fetch` |
| `web/tests/datenquelle_rezensionen.test.mjs` (ändern) | Integrationstests der neuen Methoden gegen PostgREST |
| `web/shop.html` (ändern) | Sternzeile als Knopf, Modal „Rezensionen“, Hinweis und Bestätigung im Formular, Status im Datenmodus, Escape-Fix, Brücken im Modulblock, CSS |
| `docs/05-anwendungen.md` (ändern) | Absatz „Bewerten“ nachgezogen |

Stellen in `shop.html` werden über ihren Wortlaut gefunden. Zeilennummern in diesem Plan gelten für Stand `dec4521` und verschieben sich.

---

### Task 1: Reine Funktionen in `rezensionen.js`

**Files:**
- Modify: `web/js/rezensionen.js`
- Test: `web/tests/rezensionen.test.mjs`

**Interfaces:**
- Consumes: Zeilen aus `v_rezension_produkt` (`anzahl`, `sterne_mittel`, `anzahl_1` bis `anzahl_5`), Status aus Phase A.
- Produces:
  - `SEITENGROESSE = 10`
  - `sterneText(sterne) → string` (`4` → `'★★★★☆'`, Werte außerhalb 0–5 werden begrenzt)
  - `anzahlText(anzahl) → string` (`'1 Bewertung'`, `'1.234 Bewertungen'`, `'noch keine Bewertung'`)
  - `verteilung(zeile) → Array<{sterne, anzahl, anteil}>`, 5 Sterne zuerst, `anteil` zwischen 0 und 1
  - `anteilText(anteil) → string` (`0.384` → `'38 %'`)
  - `statusText(status) → string` (`offen` → `'wird geprüft'`, `freigegeben` → `'veröffentlicht'`, `zurueckgehalten` → `'zurückgehalten, wartet auf die Moderation'`, `abgelehnt` → `'abgelehnt'`, sonst `'unbekannt'`)
  - `anzahlFuer(zeile, sterne) → number` (ohne Filter `anzahl`, sonst `anzahl_<sterne>`)
  - `weitereLaden(geladen, gesamt, letzteSeite) → boolean`
  - `datensatzZeilen(rezension)` liefert als achte Zeile `['status', statusText(rezension.status)]`

- [ ] **Step 1: Tests anhängen**

Im Kopf von `web/tests/rezensionen.test.mjs` den Import erweitern:

```js
import { bewertungText, pruefeEingabe, zaehlerText, datumText, nachArtikel,
         stimmenNachArtikel, datensatzZeilen, normalisiereText, SEITENGROESSE, sterneText,
         anzahlText, verteilung, anteilText, statusText, anzahlFuer,
         weitereLaden } from '../js/rezensionen.js';
```

Am Ende anfügen:

```js
test('sterneText: gefüllte und leere Sterne, begrenzt auf 0 bis 5', () => {
  assert.equal(sterneText(4), '★★★★☆');
  assert.equal(sterneText(0), '☆☆☆☆☆');
  assert.equal(sterneText(7), '★★★★★');
  assert.equal(sterneText(undefined), '☆☆☆☆☆');
});

test('anzahlText: Einzahl, Tausenderpunkt, keine Bewertung', () => {
  assert.equal(anzahlText(1), '1 Bewertung');
  assert.equal(anzahlText(1234), '1.234 Bewertungen');
  assert.equal(anzahlText(0), 'noch keine Bewertung');
  assert.equal(anzahlText(undefined), 'noch keine Bewertung');
});

test('verteilung: fünf Stufen, 5 Sterne zuerst, Anteile ergeben zusammen 1', () => {
  const stufen = verteilung({ anzahl: 10, anzahl_1: 1, anzahl_2: 0, anzahl_3: 2, anzahl_4: 3, anzahl_5: 4 });
  assert.deepEqual(stufen.map(s => s.sterne), [5, 4, 3, 2, 1]);
  assert.deepEqual(stufen.map(s => s.anzahl), [4, 3, 2, 0, 1]);
  assert.ok(Math.abs(stufen.reduce((s, x) => s + x.anteil, 0) - 1) < 1e-9);
  assert.deepEqual(verteilung(undefined).map(s => s.anteil), [0, 0, 0, 0, 0]);
  assert.deepEqual(verteilung({ anzahl: 0 }).map(s => s.anzahl), [0, 0, 0, 0, 0]);
});

test('anteilText: ganze Prozent', () => {
  assert.equal(anteilText(0.384), '38 %');
  assert.equal(anteilText(0), '0 %');
  assert.equal(anteilText(1), '100 %');
});

test('statusText: Status in Worten', () => {
  assert.equal(statusText('offen'), 'wird geprüft');
  assert.equal(statusText('freigegeben'), 'veröffentlicht');
  assert.equal(statusText('zurueckgehalten'), 'zurückgehalten, wartet auf die Moderation');
  assert.equal(statusText('abgelehnt'), 'abgelehnt');
  assert.equal(statusText('xyz'), 'unbekannt');
});

test('anzahlFuer und weitereLaden: Filter und volle Seiten', () => {
  assert.equal(SEITENGROESSE, 10);
  const zeile = { anzahl: 25, anzahl_5: 12 };
  assert.equal(anzahlFuer(zeile, null), 25);
  assert.equal(anzahlFuer(zeile, 5), 12);
  assert.equal(anzahlFuer(undefined, 5), 0);
  assert.equal(weitereLaden(10, 25, 10), true);
  assert.equal(weitereLaden(20, 25, 10), true);
  assert.equal(weitereLaden(25, 25, 5), false);
  assert.equal(weitereLaden(10, 25, 7), false);   // Seite nicht voll: der Stand ist veraltet
});

test('datensatzZeilen: Status als achte Zeile, in Worten', () => {
  const zeilen = datensatzZeilen({ rezension_id: 1, sterne: 5, im_warehouse: false, status: 'offen' });
  assert.deepEqual(zeilen[7], ['status', 'wird geprüft']);
});
```

- [ ] **Step 2: Tests laufen lassen, sie müssen scheitern**

Run: `node --test web/tests/rezensionen.test.mjs`
Expected: FAIL mit `SyntaxError: The requested module '../js/rezensionen.js' does not provide an export named 'SEITENGROESSE'`.

- [ ] **Step 3: Funktionen in `web/js/rezensionen.js` ergänzen**

In `datensatzZeilen` nach der Zeile mit `['im_warehouse', …]` die Zeile `['status', statusText(rezension.status)],` einfügen. Die Funktion lautet danach:

```js
/** Der gespeicherte Datensatz für die Datenperspektive — ohne inhalt, denn
 *  Besuchertext wird nirgends gerendert. */
export function datensatzZeilen(rezension) {
  const wann = rezension.erstellt_am
    ? new Date(rezension.erstellt_am).toLocaleString('de-DE', { timeZone: 'Europe/Berlin' })
    : '';
  return [
    ['rezension_id', String(rezension.rezension_id)],
    ['artikel', String(rezension.artikel ?? '')],
    ['filiale', rezension.filiale ? String(rezension.filiale) : '—'],
    ['sterne', '★'.repeat(Number(rezension.sterne) || 0)],
    ['erstellt_am', wann],
    ['sitzung', String(rezension.sitzung ?? '')],
    ['im_warehouse', rezension.im_warehouse ? 'ja' : 'nein — erst nach dem ETL-Lauf'],
    ['status', statusText(rezension.status)],
  ];
}
```

Am Ende der Datei anfügen:

```js
/** So viele Rezensionen holt die Leseansicht auf einmal. */
export const SEITENGROESSE = 10;

/** Sterne als Zeichen: 4 → „★★★★☆“. Werte außerhalb 0 bis 5 werden begrenzt. */
export function sterneText(sterne) {
  const zahl = Math.min(5, Math.max(0, Math.round(Number(sterne) || 0)));
  return '★'.repeat(zahl) + '☆'.repeat(5 - zahl);
}

/** Zahl der Bewertungen in Worten: „1 Bewertung“, „1.234 Bewertungen“. */
export function anzahlText(anzahl) {
  const zahl = Number(anzahl) || 0;
  if (!zahl) return 'noch keine Bewertung';
  return `${zahl.toLocaleString('de-DE')} ${zahl === 1 ? 'Bewertung' : 'Bewertungen'}`;
}

/** Verteilung der Sterne aus einer Zeile von v_rezension_produkt, 5 Sterne zuerst.
 *  anteil liegt zwischen 0 und 1 und ist 0, solange es keine Rezension gibt. */
export function verteilung(zeile) {
  const gesamt = Number(zeile?.anzahl) || 0;
  return [5, 4, 3, 2, 1].map(sterne => {
    const anzahl = Number(zeile?.[`anzahl_${sterne}`]) || 0;
    return { sterne, anzahl, anteil: gesamt ? anzahl / gesamt : 0 };
  });
}

/** Ein Anteil als ganze Prozent: 0,384 → „38 %“. */
export function anteilText(anteil) {
  return `${Math.round((Number(anteil) || 0) * 100)} %`;
}

/** Der Status einer Shop-Rezension in Worten, für den Datenmodus. */
export function statusText(status) {
  const worte = {
    offen: 'wird geprüft',
    freigegeben: 'veröffentlicht',
    zurueckgehalten: 'zurückgehalten, wartet auf die Moderation',
    abgelehnt: 'abgelehnt',
  };
  return worte[status] || 'unbekannt';
}

/** Wie viele freigegebene Rezensionen passen zum Filter? Ohne Filter alle. */
export function anzahlFuer(zeile, sterne) {
  if (!zeile) return 0;
  return Number(sterne ? zeile[`anzahl_${sterne}`] : zeile.anzahl) || 0;
}

/** Soll „Weitere laden“ erscheinen? Nur wenn der Stand mehr kennt und die
 *  letzte Seite voll war — sonst sind die Zahlen vom Laden der Seite veraltet. */
export function weitereLaden(geladen, gesamt, letzteSeite) {
  return geladen < gesamt && letzteSeite === SEITENGROESSE;
}
```

- [ ] **Step 4: Tests laufen lassen**

Run: `node --test web/tests/rezensionen.test.mjs`
Expected: alle bestanden (`16` Tests, davon `7` neu).

- [ ] **Step 5: Commit**

```bash
git -c core.fileMode=false add web/js/rezensionen.js web/tests/rezensionen.test.mjs
git commit -m "Freigabe B: Verteilung, Sterne und Status in rezensionen.js" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Zwei neue Methoden der Datenquelle

**Files:**
- Modify: `web/js/datenquelle.js`
- Test: `web/tests/datenquelle.test.mjs`, `web/tests/datenquelle_rezensionen.test.mjs`

**Interfaces:**
- Consumes: `hole(sicht, abfrage, {schema, frisch})`; Sichten `wawi.v_rezensionen_lesen`, `wawi.v_rezension_status`, `wawi.v_rezension_produkt` aus Phase A.
- Produces:
  - `quelle.rezensionenLesen(artikelId, sterne = null, seite = 1, groesse = 10) → Promise<Array<{artikel_id, rezension_id, sterne, inhalt, datum, erstellt_am, quelle, status}>>`, neueste zuerst, immer frisch.
  - `quelle.rezensionStatus(rezensionId) → Promise<string | null>`.

- [ ] **Step 1: Test mit nachgebildetem `fetch` anhängen**

Am Ende von `web/tests/datenquelle.test.mjs`:

```js
test('rezensionenLesen: Filter, Sortierung und Seite als PostgREST-Abfrage', async t => {
  const aufrufe = [];
  t.mock.method(globalThis, 'fetch', async (url, optionen) => {
    aufrufe.push({ url: new URL(url), kopf: optionen.headers });
    return antwort([]);
  });
  await quelle().rezensionenLesen(7, 4, 2);
  await quelle().rezensionenLesen(7, null, 1, 5);
  const [erste, zweite] = aufrufe;
  assert.equal(erste.url.pathname, '/rest/v1/v_rezensionen_lesen');
  assert.equal(erste.url.searchParams.get('artikel_id'), 'eq.7');
  assert.equal(erste.url.searchParams.get('sterne'), 'eq.4');
  assert.equal(erste.url.searchParams.get('order'), 'erstellt_am.desc,rezension_id.desc');
  assert.equal(erste.url.searchParams.get('limit'), '10');
  assert.equal(erste.url.searchParams.get('offset'), '10');
  assert.equal(erste.kopf['Accept-Profile'], 'wawi');
  assert.equal(zweite.url.searchParams.get('sterne'), null);
  assert.equal(zweite.url.searchParams.get('limit'), '5');
  assert.equal(zweite.url.searchParams.get('offset'), '0');
});

test('rezensionStatus: Status der Zeile oder null', async t => {
  const antworten = [[{ rezension_id: 5, status: 'offen' }], []];
  t.mock.method(globalThis, 'fetch', async () => antwort(antworten.shift()));
  assert.equal(await quelle().rezensionStatus(5), 'offen');
  assert.equal(await quelle().rezensionStatus(6), null);
});
```

- [ ] **Step 2: Integrationstests anhängen**

Am Ende von `web/tests/datenquelle_rezensionen.test.mjs`:

```js
test('rezensionenProdukt: die Verteilung ergibt zusammen die Anzahl', async () => {
  const zeilen = await quelle.rezensionenProdukt();
  for (const z of zeilen) {
    const summe = [1, 2, 3, 4, 5].reduce((s, n) => s + z[`anzahl_${n}`], 0);
    assert.equal(summe, z.anzahl, `Artikel ${z.artikel_id}`);
  }
});

test('rezensionenLesen: zehn freigegebene, neueste zuerst, Seiten und Filter', async () => {
  const stand = (await quelle.rezensionenProdukt()).find(z => z.anzahl > 20);
  const seite1 = await quelle.rezensionenLesen(stand.artikel_id, null, 1);
  assert.equal(seite1.length, 10);
  assert.ok(seite1.every(z => z.status === 'freigegeben' && z.artikel_id === stand.artikel_id));
  for (let i = 1; i < seite1.length; i++) {
    assert.ok(Date.parse(seite1[i - 1].erstellt_am) >= Date.parse(seite1[i].erstellt_am));
  }
  const seite2 = await quelle.rezensionenLesen(stand.artikel_id, null, 2);
  assert.ok(!seite2.some(z => seite1.some(y => y.rezension_id === z.rezension_id)));
  const fuenf = await quelle.rezensionenLesen(stand.artikel_id, 5, 1);
  assert.ok(fuenf.length > 0 && fuenf.every(z => z.sterne === 5));
});

test('rezensionStatus: eine unbekannte Rezension ergibt null', async () => {
  assert.equal(await quelle.rezensionStatus(2147483647), null);
});
```

- [ ] **Step 3: Tests laufen lassen, sie müssen scheitern**

Run: `node --test "web/tests/datenquelle*.test.mjs"`
Expected: FAIL mit `TypeError: quelle(...).rezensionenLesen is not a function`.

- [ ] **Step 4: Methoden in `web/js/datenquelle.js` ergänzen**

In der Klasse `Datenquelle` die Beschreibungen von `rezensionenProdukt()` und `kundenstimmen()` ersetzen und nach `letzteRezensionen()` zwei Methoden anfügen:

```js
  /** Bewertungsstand je Artikel, nur freigegebene Rezensionen: artikel_id, name,
   *  anzahl, sterne_mittel (eine Nachkommastelle, null ohne Rezension), letzte
   *  (Datum der jüngsten), anzahl_1 bis anzahl_5 — immer frisch geholt. */
  rezensionenProdukt() { throw new Error('nicht umgesetzt'); }
  /** Die drei jüngsten freigegebenen Rezensionen je Artikel, aus Simulation und
   *  Shop: artikel_id, rezension_id, sterne, inhalt, datum */
  kundenstimmen() { throw new Error('nicht umgesetzt'); }
```

```js
  /** Freigegebene Rezensionen eines Artikels für die Leseansicht, neueste
   *  zuerst: artikel_id, rezension_id, sterne, inhalt, datum, erstellt_am,
   *  quelle, status. sterne filtert auf eine Sternzahl (1–5), null zeigt alle;
   *  seite zählt ab 1, groesse Rezensionen je Seite. */
  rezensionenLesen(artikelId, sterne, seite, groesse) { throw new Error('nicht umgesetzt'); }
  /** Status einer Shop-Rezension ohne Text: 'offen', 'freigegeben',
   *  'zurueckgehalten', 'abgelehnt' — oder null, wenn es sie nicht gibt. */
  rezensionStatus(rezensionId) { throw new Error('nicht umgesetzt'); }
```

In `PostgrestQuelle` nach der Zeile `letzteRezensionen()  { … }` einfügen:

```js
  rezensionenLesen(artikelId, sterne = null, seite = 1, groesse = 10) {
    const abfrage = new URLSearchParams({
      artikel_id: `eq.${Number(artikelId)}`,
      order: 'erstellt_am.desc,rezension_id.desc',
      limit: String(groesse),
      offset: String((Math.max(1, Number(seite)) - 1) * groesse),
    });
    if (sterne) abfrage.set('sterne', `eq.${Number(sterne)}`);
    return this.hole('v_rezensionen_lesen', abfrage.toString(), { schema: this.schemaWawi, frisch: true });
  }
  async rezensionStatus(rezensionId) {
    const [zeile] = await this.hole('v_rezension_status', `rezension_id=eq.${Number(rezensionId)}`,
      { schema: this.schemaWawi, frisch: true });
    return zeile ? zeile.status : null;
  }
```

- [ ] **Step 5: Tests laufen lassen**

Run: `node --test "web/tests/*.test.mjs"`
Expected: alle bestanden.

- [ ] **Step 6: Commit**

```bash
git -c core.fileMode=false add web/js/datenquelle.js web/tests/datenquelle.test.mjs web/tests/datenquelle_rezensionen.test.mjs
git commit -m "Freigabe B: rezensionenLesen() und rezensionStatus() in der Datenquelle" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Leseansicht, Hinweis und Status in `shop.html`

**Files:**
- Modify: `web/shop.html`

**Interfaces:**
- Consumes: `window.REZENSIONEN` (erweitert um die Funktionen aus Task 1), `BEWERTUNGEN`, `PRODUCTS`, `openReview()`, `reviewAusloeser`, `dataMode`, `logEvent()`; aus Task 2 `quelle.rezensionenLesen()`, `quelle.rezensionStatus()`.
- Produces: globale Funktionen `openLesen(artikelId)`, `closeLesen()`, `leseFiltern(sterne)`, `leseSeiteLaden()`, `leseZuBewerten()`; Brücken `window.rezensionenLesenLaden(artikelId, sterne, seite)`, `window.rezensionStatusLaden(rezensionId)`.

- [ ] **Step 1: CSS anfügen**

Vor dem schließenden `</style>` nach der Zeile `@media (max-width: 600px) { .review-box { padding: 28px 20px; } .review-stimmen ul { max-height: 160px; } }` einfügen:

```css
/* ── Rezensionen lesen: Sternzeile als Knopf, Verteilung, Filter, Liste ─────── */
.rating-knopf { background: none; border: none; padding: 6px 0; font: inherit; cursor: pointer; text-align: left; text-decoration: underline; text-decoration-color: transparent; text-underline-offset: 2px; }
.rating-knopf:hover:not(:disabled), .rating-knopf:focus-visible { text-decoration-color: currentColor; }
.rating-knopf:disabled { cursor: default; }
.review-hinweis { font-size: .8rem; color: var(--stone-600); text-align: center; margin: -8px 0 12px; }
.lese-kopf { display: flex; align-items: baseline; justify-content: center; gap: 10px; margin: 4px 0 12px; flex-wrap: wrap; }
.lese-mittel { font-family: var(--font-display); font-size: 2.6rem; line-height: 1; color: var(--gold); }
.lese-sterne { color: var(--gold); letter-spacing: 1px; }
.lese-anzahl { color: var(--stone-600); font-size: .9rem; }
.lese-verteilung { display: grid; gap: 4px; margin-bottom: 8px; }
.lese-stufe { display: grid; grid-template-columns: 3.2em 1fr 7.5em; align-items: center; gap: 8px; background: none; border: 1px solid transparent; border-radius: var(--radius); padding: 6px 8px; font: inherit; font-size: .85rem; color: var(--stone-600); cursor: pointer; text-align: left; min-height: 40px; }
.lese-stufe:hover:not(:disabled) { border-color: var(--stone-200); }
.lese-stufe[aria-pressed="true"] { border-color: var(--gold); background: var(--cream); }
.lese-stufe:disabled { cursor: default; opacity: .55; }
.lese-stufe:focus-visible { outline: 2px solid var(--red); outline-offset: 2px; }
.lese-stufe-name { color: var(--gold); font-weight: 600; white-space: nowrap; }
.lese-balken { height: 8px; background: var(--stone-200); border-radius: 4px; overflow: hidden; }
.lese-balken-fuellung { display: block; height: 100%; background: var(--gold); }
.lese-stufe-zahl { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
.lese-filter { display: flex; justify-content: space-between; align-items: center; font-size: .85rem; color: var(--stone-600); margin: 4px 0 8px; }
.lese-filter[hidden] { display: none; }
.lese-alle { background: none; border: none; color: var(--red); font-weight: 600; text-decoration: underline; cursor: pointer; padding: 10px 0; font: inherit; }
.lese-liste { list-style: none; margin: 8px 0 0; display: grid; gap: 12px; border-top: 1px solid var(--stone-200); padding: 12px 0 0; }
.lese-daten { display: none; font-family: 'Courier New', monospace; font-size: .72rem; color: var(--stone-400); margin-top: 2px; word-break: break-word; }
body.data-mode .lese-daten { display: block; }
.lese-weiter { width: 100%; justify-content: center; margin-top: 12px; background: var(--white); border: 1px solid var(--stone-200); color: var(--charcoal); }
.lese-weiter[hidden] { display: none; }
.lese-selbst { width: 100%; justify-content: center; margin-top: 12px; }
@media (max-width: 600px) { .lese-stufe { grid-template-columns: 2.8em 1fr 6.5em; } .lese-mittel { font-size: 2.2rem; } }
```

- [ ] **Step 2: Sternzeile der Karte als Knopf**

In `renderMenu` die Zeile

```js
          <span class="rating-text ${bewertungKlasse(p.id)}" data-rating="${p.id}">${bewertungVon(p.id)}</span>
```

ersetzen durch

```js
          <button type="button" class="rating-text rating-knopf ${bewertungKlasse(p.id)}" data-rating="${p.id}" onclick="openLesen(${p.id})" ${bewertungKlasse(p.id) ? 'disabled' : ''} aria-label="Rezensionen zu ${p.name} lesen">${bewertungVon(p.id)}</button>
```

In `bewertungenAktualisieren()` nach der Zeile `el.classList.toggle('leer', bewertungKlasse(artikelId) === 'leer');` einfügen:

```js
    el.disabled = bewertungKlasse(artikelId) === 'leer';
```

- [ ] **Step 3: Hinweis im Formular und Bestätigung**

Im Markup von `#reviewModal` nach `<div class="review-stand" id="reviewStand"></div>` einfügen:

```html
    <p class="review-hinweis">Rezensionen werden vor der Veröffentlichung geprüft.</p>
```

In `submitReview` die Zeile

```js
    reviewMeldung('ok', `Gespeichert als wawi.rezension #${antwort.rezension_id}`);
```

ersetzen durch

```js
    reviewMeldung('ok', 'Danke! Ihre Rezension wird geprüft und erscheint in Kürze.');
```

und die Zeile `datensatzAnzeigen(antwort.rezension_id);` ersetzen durch

```js
    datensatzAnzeigen(antwort.rezension_id);
    statusBeobachten(antwort.rezension_id);
```

In `stimmenAnzeigen` die Zeile

```js
    kopf.textContent = '★'.repeat(s.sterne) + '☆'.repeat(5 - s.sterne) + ' · ' + window.REZENSIONEN.datumText(s.datum);
```

ersetzen durch

```js
    kopf.textContent = window.REZENSIONEN.sterneText(s.sterne) + ' · ' + window.REZENSIONEN.datumText(s.datum);
```

- [ ] **Step 4: Markup des neuen Modals**

Direkt nach `#reviewModal` einfügen, also nach den drei schließenden `</div>`, die auf `<ul id="reviewStimmen"></ul>` folgen:

```html
<!-- ===================== REZENSIONEN LESEN ===================== -->
<div class="modal-overlay" id="leseModal" role="dialog" aria-modal="true" aria-labelledby="leseTitel">
  <div class="modal-box review-box lese-box">
    <button type="button" class="review-close" onclick="closeLesen()" aria-label="Schließen">&times;</button>
    <h3 id="leseTitel">Rezensionen</h3>
    <div class="review-product" id="leseProdukt"></div>
    <div class="lese-kopf">
      <span class="lese-mittel" id="leseMittel"></span>
      <span class="lese-sterne" id="leseSterne"></span>
      <span class="lese-anzahl" id="leseAnzahl"></span>
    </div>
    <div class="lese-verteilung" id="leseVerteilung" role="group" aria-label="Nach Sternen filtern"></div>
    <div class="lese-filter" id="leseFilter" hidden>
      <span id="leseFilterText"></span>
      <button type="button" class="lese-alle" onclick="leseFiltern(null)">Alle</button>
    </div>
    <ul class="lese-liste" id="leseListe" aria-live="polite"></ul>
    <div class="review-meldung" id="leseMeldung"></div>
    <button type="button" class="btn lese-weiter" id="leseWeiter" onclick="leseSeiteLaden()" hidden>Weitere laden</button>
    <button type="button" class="btn btn-primary lese-selbst" onclick="leseZuBewerten()">Selbst bewerten</button>
  </div>
</div>
```

- [ ] **Step 5: Datenmodus-Anmerkung nachziehen**

In der Anmerkung „REZENSIONEN“ die Zeile

```html
      <span class="schema-box">wawi.rezension</span><span class="schema-arrow">→</span>
```

ersetzen durch

```html
      <span class="schema-box">wawi.rezension</span><span class="schema-arrow">→</span>
      <span class="schema-box">Freigabe</span><span class="schema-arrow">→</span>
```

und den Satz „Besuchertexte zeigt der Shop nicht an; die Kundenstimmen kommen aus der Simulation.“ ersetzen durch „Besuchertexte erscheinen erst nach der Freigabe; bis dahin steht hier nur ihr Status.“

- [ ] **Step 6: JavaScript der Leseansicht im klassischen Block**

Die Zeile

```js
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeReview(); });
```

ersetzen durch

```js
document.getElementById('leseModal').addEventListener('click', e => { if (e.target.id === 'leseModal') closeLesen(); });
// Escape schließt nur ein offenes Rezensionsfenster; sonst sprang der Fokus
// bei jeder Escape-Taste zum zuletzt benutzten „Bewerten“-Knopf.
document.addEventListener('keydown', e => {
  if (e.key !== 'Escape') return;
  if (document.getElementById('reviewModal').classList.contains('open')) closeReview();
  else if (document.getElementById('leseModal').classList.contains('open')) closeLesen();
});

// =============================================================================
// REZENSIONEN LESEN — Verteilung, Filter und Liste der freigegebenen Rezensionen
// =============================================================================
let leseProduktId = null;   // der Artikel, dessen Rezensionen offen sind
let leseSterne = null;      // Filter: 1 bis 5 oder null für alle
let leseSeite = 0;          // zuletzt geladene Seite
let leseGeladen = 0;        // Zahl der angezeigten Rezensionen
let leseAusloeser = null;   // bekommt beim Schließen den Fokus zurück
let statusUhr = null;       // Abfrage des Status der zuletzt gespeicherten Rezension

// Öffnet die Leseansicht eines Artikels: Kopf, Verteilung, erste Seite.
function openLesen(artikelId) {
  const produkt = PRODUCTS.find(p => p.id === artikelId);
  if (!produkt || !window.REZENSIONEN) return;
  leseProduktId = artikelId;
  leseSterne = null;
  leseAusloeser = document.activeElement;
  document.getElementById('leseProdukt').textContent = produkt.name;
  document.getElementById('leseFilter').hidden = true;
  leseKopfAnzeigen();
  leseVerteilungAnzeigen();
  leseListeLeeren();
  document.getElementById('leseModal').classList.add('open');
  document.querySelector('#leseModal .review-close').focus();
  leseSeiteLaden();
  logEvent('REVIEW_READ', `Rezensionen: ${produkt.name}`, 'SELECT … FROM wawi.v_rezensionen_lesen · nur freigegebene');
}

// Schließt die Leseansicht und gibt den Fokus an die Sternzeile zurück.
function closeLesen() {
  document.getElementById('leseModal').classList.remove('open');
  if (leseAusloeser && typeof leseAusloeser.focus === 'function') leseAusloeser.focus();
}

// Mittelwert groß, daneben die Sterne und die Zahl der Bewertungen.
function leseKopfAnzeigen() {
  const zeile = BEWERTUNGEN.get(leseProduktId);
  const mittel = zeile && zeile.anzahl ? Number(zeile.sterne_mittel) : 0;
  document.getElementById('leseMittel').textContent = mittel
    ? mittel.toLocaleString('de-DE', { minimumFractionDigits: 1, maximumFractionDigits: 1 })
    : '–';
  document.getElementById('leseSterne').textContent = window.REZENSIONEN.sterneText(mittel);
  document.getElementById('leseAnzahl').textContent = window.REZENSIONEN.anzahlText(zeile && zeile.anzahl);
}

// Fünf Zeilen, 5 Sterne oben: Balken, Anzahl und Anteil. Ein Klick filtert.
function leseVerteilungAnzeigen() {
  const ziel = document.getElementById('leseVerteilung');
  ziel.textContent = '';
  for (const stufe of window.REZENSIONEN.verteilung(BEWERTUNGEN.get(leseProduktId))) {
    const knopf = document.createElement('button');
    knopf.type = 'button';
    knopf.className = 'lese-stufe';
    knopf.disabled = stufe.anzahl === 0;
    knopf.setAttribute('aria-pressed', String(leseSterne === stufe.sterne));
    knopf.setAttribute('aria-label',
      `${stufe.sterne} ${stufe.sterne === 1 ? 'Stern' : 'Sterne'}: ${stufe.anzahl} Bewertungen — nur diese zeigen`);
    knopf.onclick = () => leseFiltern(stufe.sterne);
    const name = document.createElement('span');
    name.className = 'lese-stufe-name';
    name.textContent = `${stufe.sterne} ★`;
    const balken = document.createElement('span');
    balken.className = 'lese-balken';
    const fuellung = document.createElement('span');
    fuellung.className = 'lese-balken-fuellung';
    fuellung.style.width = `${Math.round(stufe.anteil * 100)}%`;
    balken.appendChild(fuellung);
    const zahl = document.createElement('span');
    zahl.className = 'lese-stufe-zahl';
    zahl.textContent = `${stufe.anzahl.toLocaleString('de-DE')} · ${window.REZENSIONEN.anteilText(stufe.anteil)}`;
    knopf.append(name, balken, zahl);
    ziel.appendChild(knopf);
  }
}

// Filtert auf eine Sternzahl (oder alle) und lädt die erste Seite neu.
function leseFiltern(sterne) {
  leseSterne = sterne;
  document.getElementById('leseFilter').hidden = sterne === null;
  document.getElementById('leseFilterText').textContent = sterne ? `Nur ${sterne} ★` : '';
  leseVerteilungAnzeigen();
  leseListeLeeren();
  leseSeiteLaden();
}

// Leert Liste, Meldung und Seitenzähler.
function leseListeLeeren() {
  document.getElementById('leseListe').textContent = '';
  leseMeldung('');
  leseSeite = 0;
  leseGeladen = 0;
  document.getElementById('leseWeiter').hidden = true;
}

// Holt die nächste Seite aus der Datenbank und hängt sie an die Liste.
async function leseSeiteLaden() {
  if (!window.rezensionenLesenLaden) { leseMeldung('Keine Verbindung zum operativen System.'); return; }
  const produkt = leseProduktId, sterne = leseSterne, seite = leseSeite + 1;
  const weiter = document.getElementById('leseWeiter');
  weiter.disabled = true;
  try {
    const zeilen = await window.rezensionenLesenLaden(produkt, sterne, seite);
    // Wurden Artikel oder Filter inzwischen gewechselt, gilt diese Antwort nicht mehr.
    if (produkt !== leseProduktId || sterne !== leseSterne) return;
    const liste = document.getElementById('leseListe');
    for (const z of zeilen) liste.appendChild(leseEintrag(z));
    leseSeite = seite;
    leseGeladen += zeilen.length;
    if (!leseGeladen) leseMeldung('Zu diesem Filter gibt es noch keine veröffentlichte Rezension.');
    const gesamt = window.REZENSIONEN.anzahlFuer(BEWERTUNGEN.get(produkt), sterne);
    weiter.hidden = !window.REZENSIONEN.weitereLaden(leseGeladen, gesamt, zeilen.length);
  } catch (fehler) {
    leseMeldung(fehler.message);
  } finally {
    weiter.disabled = false;
  }
}

// Ein Eintrag: Sterne und Datum, darunter der Text; im Datenmodus Nummer,
// Quelle und Status. Nur textContent, weil hier Besuchertext steht.
function leseEintrag(z) {
  const li = document.createElement('li');
  li.className = 'stimme';
  const kopf = document.createElement('div');
  kopf.className = 'stimme-kopf';
  kopf.textContent = window.REZENSIONEN.sterneText(z.sterne) + ' · ' + window.REZENSIONEN.datumText(z.datum);
  const text = document.createElement('p');
  text.textContent = z.inhalt;
  const daten = document.createElement('div');
  daten.className = 'lese-daten';
  daten.textContent = `wawi.rezension #${z.rezension_id} · quelle: ${z.quelle} · status: ${z.status}`;
  li.append(kopf, text, daten);
  return li;
}

// Meldung unter der Liste: leer, Hinweis oder Fehler der Datenquelle.
function leseMeldung(text) {
  document.getElementById('leseMeldung').textContent = text;
}

// Wechselt von der Leseansicht zum Formular; der Fokus kehrt später zur Sternzeile zurück.
function leseZuBewerten() {
  const ausloeser = leseAusloeser;
  document.getElementById('leseModal').classList.remove('open');
  openReview(leseProduktId);
  reviewAusloeser = ausloeser;
}

// Fragt im Datenmodus alle zehn Sekunden den Status der eigenen Rezension ab,
// solange das Formular offen ist und die Prüfung aussteht.
function statusBeobachten(rezensionId) {
  clearInterval(statusUhr);
  statusUhr = setInterval(async () => {
    const offen = document.getElementById('reviewModal').classList.contains('open');
    if (!offen || !dataMode || !window.rezensionStatusLaden) { clearInterval(statusUhr); return; }
    try {
      const status = await window.rezensionStatusLaden(rezensionId);
      statusEintragen(status);
      if (status !== 'offen') clearInterval(statusUhr);
    } catch (fehler) {
      console.warn('Status der Rezension:', fehler);
    }
  }, 10000);
}

// Ersetzt im Datensatz der Datenperspektive den Wert der Zeile „status“.
function statusEintragen(status) {
  const dl = document.getElementById('daRezension');
  if (!dl) return;
  const dt = [...dl.querySelectorAll('dt')].find(e => e.textContent === 'status');
  if (dt && dt.nextElementSibling) dt.nextElementSibling.textContent = window.REZENSIONEN.statusText(status);
}
```

- [ ] **Step 7: Ereignis für das Protokoll im Datenmodus**

In `EVENT_CONFIG` nach der Zeile `REVIEW:      { icon: 'ev-icon-view', emoji: '⭐' },` einfügen:

```js
  REVIEW_READ: { icon: 'ev-icon-view', emoji: '📖' },
```

- [ ] **Step 8: Modulblock: Importe, Brücken, Cache-Brecher**

Im `<script type="module">` die vier Importzeilen ersetzen durch:

```js
import { QUELLE } from './js/konfiguration.js?v=20261001';
import { waehleQuelle } from './js/datenquelle.js?v=20261001';
import { bildVon, bildUrl, BESCHREIBUNGEN, OEFFNUNGSZEITEN, ANFAHRT } from './js/darstellung.js?v=20261001';
import { bewertungText, pruefeEingabe, zaehlerText, datumText, nachArtikel,
         stimmenNachArtikel, datensatzZeilen, SEITENGROESSE, sterneText, anzahlText,
         verteilung, anteilText, statusText, anzahlFuer, weitereLaden } from './js/rezensionen.js?v=20261001';
```

Die Zeile `window.REZENSIONEN = { bewertungText, pruefeEingabe, zaehlerText, datumText, datensatzZeilen };` ersetzen durch:

```js
window.REZENSIONEN = { bewertungText, pruefeEingabe, zaehlerText, datumText, datensatzZeilen,
                       sterneText, anzahlText, verteilung, anteilText, statusText, anzahlFuer,
                       weitereLaden };
```

Nach der Zeile `window.letzteRezensionenLaden = () => quelle.letzteRezensionen();` einfügen:

```js
    // Die Leseansicht holt seitenweise; die Seitengröße steht in rezensionen.js.
    window.rezensionenLesenLaden = (artikelId, sterne, seite) =>
      quelle.rezensionenLesen(artikelId, sterne, seite, SEITENGROESSE);
    // Der Datenmodus fragt den Status der eigenen Rezension ab, ohne Text.
    window.rezensionStatusLaden = (rezensionId) => quelle.rezensionStatus(rezensionId);
```

- [ ] **Step 9: Syntax aller Skriptblöcke und Tests prüfen**

Run: `python3 web/tests/skripte_pruefen.py && node --test "web/tests/*.test.mjs"`
Expected: `web/shop.html: 0 Block(e) mit Syntaxfehler`, alle Tests bestanden.

- [ ] **Step 10: Commit**

```bash
git -c core.fileMode=false add web/shop.html
git commit -m "Freigabe B: Leseansicht im Shop, Hinweis auf die Prüfung, Status im Datenmodus" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Abnahme im Browser, Doku, PR

**Files:**
- Modify: `docs/05-anwendungen.md`

**Interfaces:**
- Consumes: den fertigen Shop, lokal ausgeliefert; die Produktionsdatenbank.
- Produces: geprüfte Leseansicht; PR „Freigabe B“.

- [ ] **Step 1: Shop lokal ausliefern**

Run (im Hintergrund): `python3 -m http.server 8765 --directory web`
Expected: `Serving HTTP on :: port 8765`.

- [ ] **Step 2: Abnahme auf dem Desktop (Playwright-MCP, 1280 × 800)**

`http://localhost:8765/shop.html` öffnen, warten, bis die Speisekarte geladen ist, und nacheinander prüfen:

1. **Sternzeile.** Eine Karte mit Bewertungen zeigt „★ x,y · n Bewertungen“ als Knopf. Ein Klick öffnet „Rezensionen“ mit Produktname, großem Mittelwert, Sternen und „n Bewertungen“.
2. **Verteilung.** Fünf Zeilen, 5 ★ oben. Die Summe der fünf Zahlen ist n (per `browser_evaluate` die Zahlen aus `.lese-stufe-zahl` lesen und addieren).
3. **Liste.** Zehn Einträge mit Sternen, Datum TT.MM.JJJJ und Text; „Weitere laden“ ist sichtbar, wenn n > 10. Ein Klick hängt zehn weitere an, ohne Doppelte (Rezensions-IDs aus dem Datenmodus vergleichen).
4. **Filter.** Ein Klick auf „1 ★“ zeigt „Nur 1 ★“ und „Alle“, die Liste enthält nur Einträge mit `★☆☆☆☆`. „Alle“ hebt den Filter auf.
5. **Schneller Filterwechsel.** In `browser_evaluate` nacheinander ohne Warten `leseFiltern(5); leseFiltern(1);` aufrufen, dann zwei Sekunden warten: Die Liste enthält nur Einträge mit einem Stern.
6. **Escape.** Mit offener Leseansicht Escape drücken: Das Fenster schließt, der Fokus steht auf der Sternzeile. Danach noch einmal Escape: Nichts passiert, und das Formular öffnet sich nicht.
7. **Selbst bewerten.** Öffnet das Formular des Artikels mit dem Hinweis „Rezensionen werden vor der Veröffentlichung geprüft.“.
8. **Ohne Bewertung.** Gibt es einen Artikel mit `anzahl = 0` (per `browser_evaluate` in `BEWERTUNGEN` suchen), zeigt seine Karte „noch keine Bewertung“ als nicht klickbaren Text. Gibt es keinen, `BEWERTUNGEN.set(<id>, {artikel_id: <id>, anzahl: 0})` setzen, `renderMenu('all')` aufrufen und prüfen.
9. **Datenmodus.** DATA VIEW einschalten: Jeder Eintrag zeigt „wawi.rezension #… · quelle: … · status: freigegeben“.
10. **Konsole.** Keine Fehler in `browser_console_messages`.

- [ ] **Step 3: Handybreite (375 × 812)**

Fenster auf 375 × 812 setzen, Seite neu laden, Leseansicht öffnen. `document.documentElement.scrollWidth <= window.innerWidth` ist `true`; die Verteilung zeigt Balken, Zahl und Prozent in einer Zeile. Screenshot ablegen im Scratchpad.

- [ ] **Step 4: Eine Rezension absenden, Status prüfen, aufräumen**

Im Datenmodus eine Rezension absenden (vier Sterne, „Abnahme Phase B, wird gleich gelöscht.“). Erwartet: Meldung „Danke! Ihre Rezension wird geprüft und erscheint in Kürze.“; die Anmerkung REZENSIONEN zeigt den Datensatz mit `status` „wird geprüft“; die Leseansicht zeigt den Text nicht. Die Rezensions-ID aus dem Datensatz ablesen und die Rezension danach löschen (`<ID>` durch die Zahl ersetzen):

```bash
REZENSION_ID=<ID> python3 - <<'PY'
import os, sys
sys.path.insert(0, "db")
from skript_ausfuehren import verbinde
REZENSION_ID = int(os.environ["REZENSION_ID"])
con = verbinde(); cur = con.cursor()
cur.execute("DELETE FROM wawi.rezension WHERE rezension_id = %s AND quelle = 'shop' RETURNING rezension_id",
            (REZENSION_ID,))
print("gelöscht:", cur.fetchall())
con.commit(); con.close()
PY
```

Expected: `gelöscht: [(<ID>,)]`. Den HTTP-Server beenden.

- [ ] **Step 5: `docs/05-anwendungen.md` nachziehen**

Im Absatz, der mit „**Bewerten.**“ beginnt, den Satz „Im Shop sichtbar sind nur Aggregate (`v_rezension_produkt`) und die drei jüngsten Simulationstexte je Artikel (`v_kundenstimmen`); ein Besuchertext erscheint auf keiner Seite.“ ersetzen durch:

„Ein Klick auf die Sternzeile öffnet die Leseansicht: Mittelwert, Verteilung der Sterne mit Filter (`v_rezension_produkt`) und die freigegebenen Rezensionen, zehn je Seite (`v_rezensionen_lesen`). Besuchertexte erscheinen erst nach der Freigabe (Status in `wawi.rezension`, siehe `db/README.md`); bis dahin zeigt der Datenmodus nur ihren Status (`v_rezension_status`).“

- [ ] **Step 6: Commit, Push, PR**

```bash
git -c core.fileMode=false add docs/05-anwendungen.md
git commit -m "Freigabe B: Doku der Leseansicht" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
git push origin bm-analyse
gh pr create --repo swrobuts/BurgerMetrics --base main --head bm-analyse \
  --title "Freigabe B: Rezensionen im Shop lesen" \
  --body "$(cat <<'EOF'
Phase B der Spezifikation docs/superpowers/specs/2026-09-30-rezensionen-jev-freigabe-design.md.

- Sternzeile der Produktkarte öffnet die Leseansicht: Mittelwert, Verteilung mit Filter, zehn Rezensionen je Seite, „Weitere laden“, „Selbst bewerten“
- nur freigegebene Rezensionen, Text nur per textContent
- Formular mit Hinweis auf die Prüfung, neue Bestätigung, Status der eigenen Rezension im Datenmodus
- Escape schließt nur ein offenes Rezensionsfenster
- node --test und skripte_pruefen.py grün; Abnahme im Browser auf Desktop und 375 px

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

Den PR mit `get_status` des Desktop-PR-Werkzeugs prüfen und gegebenenfalls mit `bind_pr` binden. Robert um die Zusage zum Merge bitten. Erst nach dem Merge ist die Leseansicht auf Pages live; danach `https://swrobuts.github.io/BurgerMetrics/shop.html` einmal öffnen und Schritt 2.1 bis 2.3 wiederholen.
