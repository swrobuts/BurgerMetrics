# Phase 3: Shop-Rezensionen — Implementierungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Besucher des Kundenshops (`web/shop.html`) bewerten ein Produkt mit Sternen und Text; die Rezension landet über `wawi.rezension_anlegen()` im operativen System, der Bewertungsstand am Produkt kommt aus `wawi.v_rezension_produkt`, die Kundenstimmen aus `wawi.v_kundenstimmen`, und der Datenmodus zeigt den gespeicherten Datensatz.

**Architecture:** Der Shop kennt weiterhin nur die Methoden von `Datenquelle` (`web/js/datenquelle.js`); vier neue Methoden bilden die drei Sichten und die Schreibfunktion aus `0021` ab. Die Logik ohne DOM (Bewertungstext, Eingabeprüfung, Zähler, Gruppierung, Datensatzzeilen) liegt in einem neuen Modul `web/js/rezensionen.js` und wird mit `node --test` geprüft. `shop.html` bekommt die Bewertungszeile auf der Produktkarte, ein Modal mit Sternen, Textfeld, Filialwahl und Kundenstimmen, den Schreibweg `window.rezensionSpeichern` nach dem Muster von `window.bestellungSpeichern`, und im Datenmodus eine Anmerkung mit dem zuletzt gespeicherten Datensatz.

**Tech Stack:** Vanilla JavaScript (ES-Module + klassischer Skriptblock wie bisher), PostgREST über `fetch`, Node 26 (`node --test`) für die Modultests, Python 3 für den Syntaxprüfer der eingebetteten Skripte, Playwright-MCP oder Browser-Pane für die Abnahme im Browser.

**Spec:** `docs/superpowers/specs/2026-09-12-bm-analyse-lernumgebung-design.md`, Abschnitt 5 (Shop-Feature), dazu 3.1 (Sichten, `rezension_anlegen()`), 11 (Abnahme) und 12 (Reihenfolge).

## Global Constraints

- Nur Deutsch. Echte Umlaute (ü, ö, ä, ß) in neuen Kommentaren, Oberflächentexten und Commit-Nachrichten; Bezeichner (Funktionen, Variablen, CSS-Klassen, IDs) bleiben ASCII. Bestehende ASCII-Kommentare in `shop.html`/`datenquelle.js` bleiben unangetastet.
- Lehrcode für Anfänger: kurze Funktionen mit sprechenden deutschen Namen, ein kurzer Kommentar je Funktion (das Warum), keine cleveren Konstrukte, sachlicher Ton in allem, was Lehrmaterial ist. Der Shop selbst ist eine Demo-Kundenseite und behält seinen bestehenden Stil (Emoji im Event-Log dürfen bleiben).
- Der Shop kennt **ausschließlich** Methoden von `Datenquelle` — keine URL, keine Tabelle, keine Spalte außerhalb von `datenquelle.js`.
- Sicherheit (Spec 5): Besuchertexte (`inhalt` aus `v_rezension_letzte`, eigene Eingabe) werden **nirgends** gerendert. Alles Angezeigte an Rezensionstext kommt aus `v_kundenstimmen` (nur Simulation) und wird mit `textContent` gesetzt, nie mit `innerHTML`. Längen- und Ratenbegrenzung liegen in der Datenbank; der Client prüft nur, um die Meldung sofort zu zeigen.
- Anzeige-Regel am Produkt: `★ 4,3 · 128 Bewertungen` (eine Nachkommastelle, Dezimalkomma, Tausenderpunkt, Einzahl „1 Bewertung"); ohne Rezension `noch keine Bewertung`. Bestätigung: `Gespeichert als wawi.rezension #4711`. Fehler: die Meldung der Datenbank (`fehler.message`, wie bei der Bestellung).
- `web/abgleich.html` bleibt unverändert; `web/dashboard.html` bekommt **keine** Rezensionskarte; `web/pos.html` bleibt unverändert.
- Keine neuen Abhängigkeiten, kein Build-Schritt: Pages liefert `web/` unverändert aus.
- Datenbank: Schreibweg nur `wawi.rezension_anlegen(artikel_id, sterne, inhalt, filiale_id, sitzung)` (RPC, `Content-Profile: wawi`); Sichten `wawi.v_rezension_produkt` (`artikel_id, name, anzahl, sterne_mittel, letzte`), `wawi.v_kundenstimmen` (`artikel_id, rezension_id, sterne, inhalt, datum`), `wawi.v_rezension_letzte` (`rezension_id, sitzung, artikel, filiale, sterne, inhalt, erstellt_am, im_warehouse`); Rückgabe der Funktion `{rezension_id, artikel, sterne, erstellt_am, quelle}`. Bremsen: 20 je Sitzung und zehn Minuten, 600 je Stunde insgesamt; `sitzung` höchstens 100 Zeichen.
- Tests: `node --test "web/tests/*.test.mjs"` (Glob in Anführungszeichen — ein Verzeichnis als Argument funktioniert in Node 26 nicht) und `python3 web/tests/skripte_pruefen.py`; die Integrationstests laufen gegen die lebende Datenbank, schreiben aber nie erfolgreich (nur abgewiesene Aufrufe).
- Commits: `git -c core.fileMode=false add …` / `commit`, Nachricht deutsch, Trailer `Co-Authored-By: <ausführendes Modell> <noreply@anthropic.com>`. Arbeit auf Branch `bm-analyse` (steht auf `main`, Stand 42c95b6); am Ende ein PR auf `main`, Merge nur nach Rückfrage bei Robert.
- Der Stand muss nach dem Merge ohne weiteres Zutun live sein (Pages liefert `web/`; die Datenbank ist seit Phase 2 vorbereitet). Testrezensionen aus der Abnahme räumt `wawi.uebungsrezensionen_loeschen()` weg (Betreiber, nicht `anon`).

---

## Dateistruktur

| Datei | Verantwortung |
|---|---|
| `web/js/datenquelle.js` (ändern) | vier neue Fragen an das operative System: `rezensionenProdukt()`, `kundenstimmen()`, `rezensionAnlegen(r)`, `letzteRezensionen()` — abstrakt dokumentiert, in `PostgrestQuelle` umgesetzt |
| `web/js/rezensionen.js` (neu) | reine Logik ohne DOM: `bewertungText`, `pruefeEingabe`, `zaehlerText`, `datumText`, `nachArtikel`, `stimmenNachArtikel`, `datensatzZeilen` |
| `web/tests/rezensionen.test.mjs` (neu) | Modultests für `rezensionen.js` |
| `web/tests/datenquelle_rezensionen.test.mjs` (neu) | Integrationstests der vier Methoden gegen PostgREST (lesend; Schreibversuche, die die Datenbank abweist) |
| `web/tests/skripte_pruefen.py` (neu) | zieht jeden eingebetteten `<script>`-Block aus einer HTML-Datei und prüft ihn mit `node --check` |
| `web/shop.html` (ändern) | Bewertungszeile und Knopf auf der Karte, Modal, Speichern, Datenmodus-Anmerkung; Modulblock holt die Sichten und stellt die Brücken `window.REZENSIONEN`, `window.rezensionSpeichern`, `window.bewertungenLaden`, `window.letzteRezensionenLaden` bereit |

Wo Schritte sagen „nach dem Block X einfügen", ist der Block anhand seines Wortlauts zu finden — Zeilennummern in diesem Plan sind Stand 42c95b6 und verschieben sich mit jeder Aufgabe.

---

### Task 1: Datenquelle — vier Rezensionsmethoden mit Integrationstest

**Files:**
- Modify: `web/js/datenquelle.js` (abstrakte Klasse nach `letzteBestellungen()`, `PostgrestQuelle` nach `letzteBestellungen()`)
- Test: `web/tests/datenquelle_rezensionen.test.mjs`

**Interfaces:**
- Consumes: `hole(sicht, abfrage, {schema, frisch})`, `rufe(funktion, argumente, {schema})` aus `PostgrestQuelle`; die Sichten und die Funktion aus `db/aufbau/0021_rezensionen.sql`.
- Produces: `quelle.rezensionenProdukt()` → `Promise<Array<{artikel_id, name, anzahl, sterne_mittel, letzte}>>` (immer frisch); `quelle.kundenstimmen()` → `Promise<Array<{artikel_id, rezension_id, sterne, inhalt, datum}>>`; `quelle.rezensionAnlegen({artikel_id, sterne, inhalt, filiale_id?, sitzung?})` → `Promise<{rezension_id, artikel, sterne, erstellt_am, quelle}>` (wirft `Error` mit der Datenbankmeldung); `quelle.letzteRezensionen()` → `Promise<Array<{rezension_id, sitzung, artikel, filiale, sterne, inhalt, erstellt_am, im_warehouse}>>` (immer frisch).

- [ ] **Step 1: Test schreiben**

`web/tests/datenquelle_rezensionen.test.mjs`:

```js
// Integrationstests gegen die lebende Datenbank: lesen, und Schreibversuche,
// die die Datenbank abweisen muss. Es wird nie erfolgreich geschrieben.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { QUELLE } from '../js/konfiguration.js';
import { waehleQuelle } from '../js/datenquelle.js';

const quelle = waehleQuelle(QUELLE);

test('rezensionenProdukt: eine Zeile je Artikel mit Bewertungsstand', async () => {
  const zeilen = await quelle.rezensionenProdukt();
  assert.ok(zeilen.length >= 50, `nur ${zeilen.length} Artikel`);
  const z = zeilen.find(x => x.anzahl > 0);
  assert.equal(typeof z.artikel_id, 'number');
  assert.equal(typeof z.name, 'string');
  assert.ok(z.sterne_mittel >= 1 && z.sterne_mittel <= 5, `sterne_mittel ${z.sterne_mittel}`);
  assert.match(String(z.letzte), /^\d{4}-\d{2}-\d{2}$/);
});

test('kundenstimmen: höchstens drei je Artikel, Sterne 1 bis 5, Text vorhanden', async () => {
  const zeilen = await quelle.kundenstimmen();
  const jeArtikel = new Map();
  for (const z of zeilen) jeArtikel.set(z.artikel_id, (jeArtikel.get(z.artikel_id) || 0) + 1);
  assert.ok(jeArtikel.size >= 50, `nur ${jeArtikel.size} Artikel mit Stimmen`);
  assert.ok([...jeArtikel.values()].every(n => n <= 3));
  assert.ok(zeilen.every(z => z.sterne >= 1 && z.sterne <= 5 && String(z.inhalt).length >= 5));
});

test('letzteRezensionen: Liste mit den Feldern der Sicht', async () => {
  const zeilen = await quelle.letzteRezensionen();
  assert.ok(Array.isArray(zeilen));
  for (const z of zeilen) {
    for (const feld of ['rezension_id', 'artikel', 'sterne', 'erstellt_am', 'im_warehouse']) {
      assert.ok(feld in z, `Feld ${feld} fehlt`);
    }
  }
});

test('rezensionAnlegen: die Datenbank weist ungültige Sterne ab', async () => {
  await assert.rejects(
    quelle.rezensionAnlegen({ artikel_id: 1, sterne: 9, inhalt: 'Ein Test, der nicht gespeichert werden darf.' }),
    /sterne muss zwischen 1 und 5/);
});

test('rezensionAnlegen: die Datenbank weist zu kurzen Text ab', async () => {
  await assert.rejects(
    quelle.rezensionAnlegen({ artikel_id: 1, sterne: 4, inhalt: 'kurz' }),
    /5 bis 500 Zeichen/);
});
```

- [ ] **Step 2: Test laufen lassen — muss scheitern**

Run: `node --test "web/tests/datenquelle_rezensionen.test.mjs"`
Expected: 5 Tests scheitern mit `TypeError: quelle.rezensionenProdukt is not a function` (bzw. für die anderen Methoden).

- [ ] **Step 3: Methoden in der abstrakten Klasse dokumentieren**

In `web/js/datenquelle.js`, direkt nach der Zeile `letzteBestellungen() { throw new Error('nicht umgesetzt'); }` einfügen:

```js
  /** Bewertungsstand je Artikel (operatives Schema, über alle Quellen):
   *  artikel_id, name, anzahl, sterne_mittel (eine Nachkommastelle, null ohne
   *  Rezension), letzte (Datum der jüngsten Rezension) — immer frisch geholt,
   *  weil sich der Stand nach jeder gespeicherten Rezension ändert. */
  rezensionenProdukt() { throw new Error('nicht umgesetzt'); }
  /** Die drei jüngsten Simulationstexte je Artikel — das Einzige, was der Shop
   *  an Rezensionstext zeigt: artikel_id, rezension_id, sterne, inhalt, datum */
  kundenstimmen() { throw new Error('nicht umgesetzt'); }
  /**
   * Eine Rezension im operativen System anlegen — der zweite Schreibweg.
   * @param {object} rezension  artikel_id, sterne (1–5), inhalt (5–500 Zeichen
   *   nach Trim); optional filiale_id, sitzung. Die Datenbank prüft alles und
   *   bremst: 20 je Sitzung und zehn Minuten, 600 je Stunde insgesamt.
   * @returns {Promise<object>} rezension_id, artikel, sterne, erstellt_am, quelle
   */
  rezensionAnlegen(rezension) { throw new Error('nicht umgesetzt'); }
  /** Die 50 jüngsten Shop-Rezensionen: rezension_id, sitzung, artikel, filiale,
   *  sterne, inhalt, erstellt_am, im_warehouse. inhalt ist Besuchertext und
   *  wird auf keiner Seite gerendert. */
  letzteRezensionen() { throw new Error('nicht umgesetzt'); }
```

- [ ] **Step 4: Methoden in `PostgrestQuelle` umsetzen**

Direkt nach der Zeile `letzteBestellungen() { return this.hole('v_bestellung_letzte', '', { schema: this.schemaWawi, frisch: true }); }` einfügen:

```js
  rezensionenProdukt() { return this.hole('v_rezension_produkt', 'order=artikel_id', { schema: this.schemaWawi, frisch: true }); }
  kundenstimmen()      { return this.hole('v_kundenstimmen', 'order=artikel_id,rezension_id.desc', { schema: this.schemaWawi }); }
  rezensionAnlegen(r)  { return this.rufe('rezension_anlegen', r); }
  letzteRezensionen()  { return this.hole('v_rezension_letzte', '', { schema: this.schemaWawi, frisch: true }); }
```

- [ ] **Step 5: Test laufen lassen — muss bestehen**

Run: `node --test "web/tests/datenquelle_rezensionen.test.mjs"`
Expected: `# pass 5`, `# fail 0`.

- [ ] **Step 6: Commit**

```bash
git -c core.fileMode=false add web/js/datenquelle.js web/tests/datenquelle_rezensionen.test.mjs
git -c core.fileMode=false commit -m "web: Datenquelle kennt Rezensionen — vier Methoden auf die Sichten und die Schreibfunktion aus 0021" -m "Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 2: `rezensionen.js` — Logik ohne DOM, mit Modultests

**Files:**
- Create: `web/js/rezensionen.js`
- Test: `web/tests/rezensionen.test.mjs`

**Interfaces:**
- Consumes: nichts (reines Modul).
- Produces: `bewertungText(zeile)` → string; `pruefeEingabe({sterne, inhalt})` → string[] (leer = in Ordnung); `zaehlerText(inhalt)` → `"37 / 500"`; `datumText(iso)` → `"31.03.2026"`; `nachArtikel(zeilen)` → `Map<artikel_id, zeile>`; `stimmenNachArtikel(zeilen)` → `Map<artikel_id, zeile[]>` (höchstens drei); `datensatzZeilen(rezension)` → `Array<[feld, wert]>` ohne `inhalt`.

- [ ] **Step 1: Tests schreiben**

`web/tests/rezensionen.test.mjs`:

```js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { bewertungText, pruefeEingabe, zaehlerText, datumText, nachArtikel,
         stimmenNachArtikel, datensatzZeilen } from '../js/rezensionen.js';

test('bewertungText: Mittel mit Komma, Anzahl mit Tausenderpunkt, Einzahl', () => {
  assert.equal(bewertungText({ anzahl: 128, sterne_mittel: 4.3 }), '★ 4,3 · 128 Bewertungen');
  assert.equal(bewertungText({ anzahl: 1, sterne_mittel: 5 }), '★ 5,0 · 1 Bewertung');
  assert.equal(bewertungText({ anzahl: 1234, sterne_mittel: 3.66 }), '★ 3,7 · 1.234 Bewertungen');
});

test('bewertungText: ohne Rezension', () => {
  assert.equal(bewertungText({ anzahl: 0, sterne_mittel: null }), 'noch keine Bewertung');
  assert.equal(bewertungText(undefined), 'noch keine Bewertung');
});

test('pruefeEingabe: dieselben Regeln wie rezension_anlegen()', () => {
  assert.deepEqual(pruefeEingabe({ sterne: 4, inhalt: 'Guter Burger, schnell serviert.' }), []);
  assert.deepEqual(pruefeEingabe({ sterne: 0, inhalt: 'Guter Burger.' }), ['Bitte 1 bis 5 Sterne wählen.']);
  assert.deepEqual(pruefeEingabe({ sterne: 3, inhalt: '  ok  ' }), ['Der Text braucht mindestens 5 Zeichen.']);
  assert.deepEqual(pruefeEingabe({ sterne: 3, inhalt: 'x'.repeat(501) }), ['Der Text darf höchstens 500 Zeichen haben.']);
  assert.equal(pruefeEingabe({ sterne: undefined, inhalt: '' }).length, 2);
});

test('zaehlerText zählt nach Trim', () => {
  assert.equal(zaehlerText('  Hallo  '), '5 / 500');
  assert.equal(zaehlerText(''), '0 / 500');
  assert.equal(zaehlerText(undefined), '0 / 500');
});

test('datumText: ISO-Datum als Tag.Monat.Jahr', () => {
  assert.equal(datumText('2026-03-31'), '31.03.2026');
  assert.equal(datumText('2026-03-31T18:00:00+00:00'), '31.03.2026');
  assert.equal(datumText(null), '');
});

test('nachArtikel und stimmenNachArtikel', () => {
  const stand = nachArtikel([{ artikel_id: 1, anzahl: 2 }, { artikel_id: 2, anzahl: 0 }]);
  assert.equal(stand.get(2).anzahl, 0);
  const stimmen = stimmenNachArtikel([
    { artikel_id: 1, inhalt: 'a' }, { artikel_id: 1, inhalt: 'b' },
    { artikel_id: 1, inhalt: 'c' }, { artikel_id: 1, inhalt: 'd' }, { artikel_id: 2, inhalt: 'e' }]);
  assert.equal(stimmen.get(1).length, 3);
  assert.equal(stimmen.get(2)[0].inhalt, 'e');
  assert.equal(stimmen.get(3), undefined);
});

test('datensatzZeilen: ohne inhalt, mit Warehouse-Hinweis', () => {
  const zeilen = datensatzZeilen({ rezension_id: 4711, artikel: 'Classic Burger', filiale: null,
    sterne: 4, inhalt: 'GEHEIM', erstellt_am: '2026-09-12T18:33:47+00:00',
    sitzung: 'shop-ab12cd', im_warehouse: false });
  assert.ok(!zeilen.map(z => z[0]).includes('inhalt'));
  assert.ok(!JSON.stringify(zeilen).includes('GEHEIM'));
  assert.deepEqual(zeilen[0], ['rezension_id', '4711']);
  assert.deepEqual(zeilen[2], ['filiale', '—']);
  assert.deepEqual(zeilen[3], ['sterne', '★★★★']);
  assert.equal(zeilen[4][1], '12.9.2026, 20:33:47');
  assert.match(zeilen[6][1], /^nein/);
  assert.equal(datensatzZeilen({ rezension_id: 1, sterne: 5, im_warehouse: true })[6][1], 'ja');
});
```

- [ ] **Step 2: Tests laufen lassen — müssen scheitern**

Run: `node --test "web/tests/rezensionen.test.mjs"`
Expected: Abbruch mit `Cannot find module '…/web/js/rezensionen.js'`.

- [ ] **Step 3: Modul schreiben**

`web/js/rezensionen.js`:

```js
/*
 * rezensionen.js — die Logik hinter Bewertungszeile und Rezensionsformular
 * des Shops, ohne DOM. So lässt sie sich mit `node --test` prüfen, und
 * shop.html kümmert sich nur um die Darstellung.
 */

/** Formatiert den Bewertungsstand eines Artikels: „★ 4,3 · 128 Bewertungen". */
export function bewertungText(zeile) {
  if (!zeile || !zeile.anzahl) return 'noch keine Bewertung';
  const mittel = Number(zeile.sterne_mittel).toLocaleString('de-DE',
    { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  const wort = zeile.anzahl === 1 ? 'Bewertung' : 'Bewertungen';
  return `★ ${mittel} · ${Number(zeile.anzahl).toLocaleString('de-DE')} ${wort}`;
}

/** Prüft die Eingabe vor dem Senden — dieselben Regeln wie rezension_anlegen(),
 *  damit die Meldung sofort erscheint und nicht erst aus der Datenbank. */
export function pruefeEingabe({ sterne, inhalt }) {
  const befunde = [];
  const s = Number(sterne);
  if (!Number.isInteger(s) || s < 1 || s > 5) befunde.push('Bitte 1 bis 5 Sterne wählen.');
  const text = String(inhalt ?? '').trim();
  if (text.length < 5) befunde.push('Der Text braucht mindestens 5 Zeichen.');
  if (text.length > 500) befunde.push('Der Text darf höchstens 500 Zeichen haben.');
  return befunde;
}

/** Zähler unter dem Textfeld: „37 / 500" — gezählt wie die Datenbank, nach Trim. */
export function zaehlerText(inhalt) {
  return `${String(inhalt ?? '').trim().length} / 500`;
}

/** Ein ISO-Datum (auch mit Uhrzeit) als Tag.Monat.Jahr. */
export function datumText(iso) {
  if (!iso) return '';
  const [jahr, monat, tag] = String(iso).slice(0, 10).split('-');
  return `${tag}.${monat}.${jahr}`;
}

/** Bewertungsstand je artikel_id nachschlagbar machen. */
export function nachArtikel(zeilen) {
  return new Map(zeilen.map(z => [z.artikel_id, z]));
}

/** Kundenstimmen je artikel_id gruppieren — höchstens drei, wie die Sicht. */
export function stimmenNachArtikel(zeilen) {
  const karte = new Map();
  for (const z of zeilen) {
    if (!karte.has(z.artikel_id)) karte.set(z.artikel_id, []);
    if (karte.get(z.artikel_id).length < 3) karte.get(z.artikel_id).push(z);
  }
  return karte;
}

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
  ];
}
```

- [ ] **Step 4: Tests laufen lassen — müssen bestehen**

Run: `node --test "web/tests/rezensionen.test.mjs"`
Expected: `# pass 7`, `# fail 0`.

- [ ] **Step 5: Commit**

```bash
git -c core.fileMode=false add web/js/rezensionen.js web/tests/rezensionen.test.mjs
git -c core.fileMode=false commit -m "web: rezensionen.js — Bewertungstext, Eingabeprüfung, Zähler, Datensatzzeilen, mit Modultests" -m "Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 3: Produktkarte — Bewertungszeile aus `v_rezension_produkt`, Syntaxprüfer für eingebettete Skripte

**Files:**
- Create: `web/tests/skripte_pruefen.py`
- Modify: `web/shop.html` — erster `<style>`-Block (nach `.menu-card-desc { … }`), klassischer Skriptblock (`let BRANCHES`, `renderMenu`, `window.shopStarten`), Modulblock am Dateiende (Imports, `Promise.all`, `shopStarten`-Aufruf)

**Interfaces:**
- Consumes: `quelle.rezensionenProdukt()`, `quelle.kundenstimmen()` (Task 1); `bewertungText`, `nachArtikel`, `stimmenNachArtikel` (Task 2).
- Produces: globale Brücke `window.REZENSIONEN = { bewertungText, pruefeEingabe, zaehlerText, datumText, datensatzZeilen }`; im klassischen Block `let BEWERTUNGEN` (`Map<artikel_id, zeile>`), `let STIMMEN` (`Map<artikel_id, zeile[]>`), `bewertungVon(id)`, `bewertungKlasse(id)`; `window.shopStarten(artikel, filialen, bewertungen, stimmen)`; auf jeder Karte ein `<span class="rating-text" data-rating="<artikel_id>">`.

- [ ] **Step 1: Syntaxprüfer anlegen**

`web/tests/skripte_pruefen.py`:

```python
#!/usr/bin/env python3
"""skripte_pruefen.py — prüft jeden eingebetteten <script>-Block einer HTML-Datei mit `node --check`.

    python3 web/tests/skripte_pruefen.py                # web/shop.html
    python3 web/tests/skripte_pruefen.py web/pos.html   # eine andere Seite

Der Browser meldet einen Syntaxfehler erst beim Laden der Seite, und dann
fehlt still die ganze Funktion. So fällt er vor dem Commit auf.
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def bloecke(html):
    """Liefert (nummer, ist_modul, quelltext) je eingebettetem Skript; externe (src=) werden übersprungen."""
    aus = []
    for nummer, treffer in enumerate(re.finditer(r'<script([^>]*)>(.*?)</script>', html, re.S), 1):
        attribute, code = treffer.group(1), treffer.group(2)
        if 'src=' in attribute or not code.strip():
            continue
        aus.append((nummer, 'type="module"' in attribute, code))
    return aus


def pruefe(datei):
    """Schreibt jeden Block in eine Datei (.mjs für Module) und lässt node --check darüber laufen."""
    fehler = 0
    for nummer, modul, code in bloecke(Path(datei).read_text(encoding='utf-8')):
        with tempfile.NamedTemporaryFile('w', suffix='.mjs' if modul else '.js',
                                         delete=False, encoding='utf-8') as f:
            f.write(code)
            pfad = f.name
        lauf = subprocess.run(['node', '--check', pfad], capture_output=True, text=True)
        if lauf.returncode:
            fehler += 1
            print(f'FEHLER in Skriptblock {nummer} ({"Modul" if modul else "klassisch"}):\n{lauf.stderr.strip()}')
    print(f'{datei}: {fehler} Block(e) mit Syntaxfehler')
    return fehler


if __name__ == '__main__':
    sys.exit(1 if pruefe(sys.argv[1] if len(sys.argv) > 1 else 'web/shop.html') else 0)
```

Run: `python3 web/tests/skripte_pruefen.py`
Expected: `web/shop.html: 0 Block(e) mit Syntaxfehler` (Stand vor der Änderung — der Prüfer selbst muss laufen).

- [ ] **Step 2: CSS der Bewertungszeile**

In `web/shop.html`, im ersten `<style>`-Block direkt nach dem Block `.menu-card-desc { … }` einfügen:

```css
/* Bewertungszeile: Stand aus wawi.v_rezension_produkt; der Knopf öffnet das Formular */
.menu-card-rating {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  font-size: .8rem;
  margin-bottom: 10px;
}
.menu-card-rating .rating-text { color: var(--gold); font-weight: 600; }
.menu-card-rating .rating-text.leer { color: var(--stone-400); font-weight: 400; }
.bewerten-btn {
  font-size: .78rem;
  font-weight: 600;
  color: var(--red);
  background: none;
  padding: 6px 0;
  cursor: pointer;
  text-decoration: underline;
  text-underline-offset: 2px;
}
.bewerten-btn:hover { color: var(--red-light); }
```

- [ ] **Step 3: Klassischer Block — Bewertungsstand halten und auf der Karte zeigen**

a) Nach `let BRANCHES = [];   // wird aus v_filialliste geladen` einfügen:

```js
let BEWERTUNGEN = new Map();   // artikel_id -> Zeile aus wawi.v_rezension_produkt
let STIMMEN = new Map();       // artikel_id -> bis zu drei Kundenstimmen (nur Simulation)
```

b) Direkt vor `function renderMenu(filter) {` einfügen:

```js
// Bewertungstext einer Karte; die Formatierung liegt in js/rezensionen.js
// (Modul), der klassische Block erreicht sie über window.REZENSIONEN.
function bewertungVon(artikelId) {
  return window.REZENSIONEN ? window.REZENSIONEN.bewertungText(BEWERTUNGEN.get(artikelId)) : '';
}

// „leer" färbt die Zeile grau, solange ein Artikel keine Rezension hat.
function bewertungKlasse(artikelId) {
  const zeile = BEWERTUNGEN.get(artikelId);
  return zeile && zeile.anzahl ? '' : 'leer';
}
```

c) In `renderMenu`, direkt nach der Zeile `<div class="menu-card-name">${p.name}</div>` einfügen:

```html
        <div class="menu-card-rating">
          <span class="rating-text ${bewertungKlasse(p.id)}" data-rating="${p.id}">${bewertungVon(p.id)}</span>
        </div>
```

d) `window.shopStarten` bekommt zwei weitere Argumente. Alt:

```js
window.shopStarten = function(artikel, filialen) {
  PRODUCTS = artikel;
  BRANCHES = filialen;
```

Neu:

```js
window.shopStarten = function(artikel, filialen, bewertungen, stimmen) {
  PRODUCTS = artikel;
  BRANCHES = filialen;
  BEWERTUNGEN = bewertungen || new Map();
  STIMMEN = stimmen || new Map();
```

- [ ] **Step 4: Modulblock — Sichten holen und Brücke setzen**

a) Nach der Zeile `import { bildVon, bildUrl, BESCHREIBUNGEN, OEFFNUNGSZEITEN, ANFAHRT } from './js/darstellung.js';` einfügen:

```js
import { bewertungText, pruefeEingabe, zaehlerText, datumText, nachArtikel,
         stimmenNachArtikel, datensatzZeilen } from './js/rezensionen.js';
```

b) Nach `window.bildUrl = bildUrl;` einfügen:

```js
// Die Rezensionslogik ebenso — der klassische Block ruft sie über window.REZENSIONEN.
window.REZENSIONEN = { bewertungText, pruefeEingabe, zaehlerText, datumText, datensatzZeilen };
```

c) Die Abfrage erweitern. Alt:

```js
  const [karte, filialen, einzel] = await Promise.all([
    quelle.speisekarte(), quelle.filialliste(), quelle.einzelwerte()]);
```

Neu:

```js
  // Bewertungsstand und Kundenstimmen kommen mit derselben Abfrage wie die
  // Speisekarte — beides aus dem operativen Schema, nichts steht im Quelltext.
  const [karte, filialen, einzel, bewertungsstand, stimmen] = await Promise.all([
    quelle.speisekarte(), quelle.filialliste(), quelle.einzelwerte(),
    quelle.rezensionenProdukt(), quelle.kundenstimmen()]);
```

d) Den Start erweitern. Alt:

```js
  window.shopStarten(artikel, standorte);
  console.info(`Shop: ${artikel.length} Artikel und ${standorte.length} Filialen `
             + `aus ${QUELLE.art} geladen.`);
```

Neu:

```js
  window.shopStarten(artikel, standorte, nachArtikel(bewertungsstand), stimmenNachArtikel(stimmen));
  console.info(`Shop: ${artikel.length} Artikel, ${standorte.length} Filialen und `
             + `${bewertungsstand.filter(b => b.anzahl > 0).length} Artikel mit Bewertung `
             + `aus ${QUELLE.art} geladen.`);
```

- [ ] **Step 5: Syntax prüfen**

Run: `python3 web/tests/skripte_pruefen.py && node --test "web/tests/*.test.mjs"`
Expected: `0 Block(e) mit Syntaxfehler`; `# pass 12`, `# fail 0`.

- [ ] **Step 6: Im Browser prüfen**

Entwicklungsserver starten (im Hintergrund): `python3 web/dev_server.py 8899`. Dann mit dem Playwright-MCP (`browser_navigate` auf `http://localhost:8899/shop.html`, `browser_snapshot`) oder dem Browser-Pane prüfen:
- Die Karte „Cola 0.5l" zeigt `★ 3,7 · 692 Bewertungen` (Stand 12.09.2026; die Zahl darf um Abnahme-Rezensionen abweichen), die Zeile ist goldfarben.
- Ein Artikel ohne Rezension (z. B. ein Extra) zeigt grau `noch keine Bewertung`.
- Die Browser-Konsole meldet `Shop: 57 Artikel, 8 Filialen und 5x Artikel mit Bewertung aus postgrest geladen.` und keinen Fehler.

Steht kein Browser-Werkzeug zur Verfügung: Status `DONE_WITH_CONCERNS` mit dem Hinweis „Browserprüfung offen" — der Controller prüft dann selbst.

- [ ] **Step 7: Commit**

```bash
git -c core.fileMode=false add web/shop.html web/tests/skripte_pruefen.py
git -c core.fileMode=false commit -m "shop: Bewertungszeile auf der Produktkarte aus wawi.v_rezension_produkt; Syntaxprüfer für eingebettete Skripte" -m "Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 4: Modal „Bewerten" — Sterne, Textfeld mit Zähler, Filialwahl, Kundenstimmen

**Files:**
- Modify: `web/shop.html` — erster `<style>`-Block (vor dem ersten `</style>`), HTML nach dem Block `<div class="modal-overlay" id="orderModal"> … </div>`, klassischer Skriptblock (nach `function closeModal() { … }`), `renderMenu` (Knopf)

**Interfaces:**
- Consumes: `BEWERTUNGEN`, `STIMMEN`, `bewertungVon`, `bewertungKlasse` (Task 3); `window.REZENSIONEN.zaehlerText`, `.datumText` (Task 2/3); `PRODUCTS`, `BRANCHES`, `logEvent` (bestehend).
- Produces: `openReview(artikelId)`, `closeReview()`, `sterneAnzeigen(n)`, `reviewZaehler()`, `stimmenAnzeigen(artikelId)`; Elemente `#reviewModal`, `#reviewForm`, `#sterneWahl` (Radios `name="sterne"`, Werte 1–5), `#reviewText`, `#reviewZaehler`, `#reviewBranch`, `#reviewMeldung`, `#reviewSenden`, `#reviewStimmen`, `#reviewProduct`, `#reviewStand`; Variable `reviewProduktId`.

- [ ] **Step 1: CSS des Modals**

Vor dem ersten `</style>` in `web/shop.html` einfügen:

```css
/* ── Rezension: Formular im Modal ────────────────────────────────────────── */
.review-box { text-align: left; max-width: 520px; padding: 40px; position: relative; max-height: 92vh; overflow-y: auto; }
.review-close { position: absolute; top: 12px; right: 16px; font-size: 1.6rem; line-height: 1; background: none; color: var(--stone-400); cursor: pointer; }
.review-close:hover { color: var(--charcoal); }
.review-box h3 { text-align: center; }
.review-product { font-family: var(--font-display); font-size: 1.4rem; letter-spacing: .5px; text-align: center; }
.review-stand { text-align: center; color: var(--gold); font-weight: 600; font-size: .9rem; margin-bottom: 16px; }
.review-stand.leer { color: var(--stone-400); font-weight: 400; }
.sterne-wahl { border: none; padding: 0; margin: 0 0 12px; display: flex; gap: 4px; align-items: center; flex-wrap: wrap; }
.sterne-wahl legend { font-size: .8rem; font-weight: 600; color: var(--stone-600); margin-bottom: 4px; width: 100%; }
.sterne-wahl input { position: absolute; opacity: 0; width: 1px; height: 1px; }
.sterne-wahl label { font-size: 2rem; line-height: 1; color: var(--stone-200); cursor: pointer; transition: color .15s; }
.sterne-wahl label.aktiv { color: var(--gold); }
.sterne-wahl input:focus-visible + label { outline: 2px solid var(--red); outline-offset: 2px; border-radius: 4px; }
.review-label { display: block; font-size: .8rem; font-weight: 600; color: var(--stone-600); margin: 10px 0 4px; }
#reviewText { width: 100%; border: 1px solid var(--stone-200); border-radius: var(--radius); padding: 10px 12px; font: inherit; font-size: .9rem; resize: vertical; }
#reviewText:focus { outline: 2px solid var(--gold); border-color: transparent; }
.review-zaehler { text-align: right; font-size: .75rem; color: var(--stone-400); margin-top: 2px; }
#reviewBranch { width: 100%; border: 1px solid var(--stone-200); border-radius: var(--radius); padding: 10px 12px; font: inherit; font-size: .9rem; background: var(--white); }
.review-meldung { min-height: 1.4em; font-size: .85rem; margin: 10px 0; color: var(--stone-600); }
.review-meldung.ok { color: #166534; font-weight: 600; }
.review-meldung.err { color: var(--red); font-weight: 600; }
#reviewSenden { width: 100%; justify-content: center; }
.review-stimmen { margin-top: 24px; border-top: 1px solid var(--stone-200); padding-top: 16px; }
.review-stimmen h4 { font-size: .8rem; letter-spacing: 1.5px; text-transform: uppercase; color: var(--gold); margin-bottom: 8px; }
.review-stimmen ul { list-style: none; padding: 0; margin: 0; display: grid; gap: 10px; max-height: 220px; overflow-y: auto; }
.stimme { font-size: .85rem; color: var(--stone-600); line-height: 1.5; }
.stimme-kopf { color: var(--gold); font-weight: 600; font-size: .8rem; }
.stimme p { margin: 2px 0 0; }
.stimme.leer { color: var(--stone-400); }
@media (max-width: 600px) { .review-box { padding: 28px 20px; } .review-stimmen ul { max-height: 160px; } }
```

- [ ] **Step 2: HTML des Modals**

Direkt nach dem schließenden `</div>` des Blocks `<div class="modal-overlay" id="orderModal">` (also vor `<!-- ===================== TOAST ===================== -->`) einfügen:

```html
<!-- ===================== REZENSION ===================== -->
<div class="modal-overlay" id="reviewModal" role="dialog" aria-modal="true" aria-labelledby="reviewTitle">
  <div class="modal-box review-box">
    <button type="button" class="review-close" onclick="closeReview()" aria-label="Schließen">&times;</button>
    <h3 id="reviewTitle">Bewerten</h3>
    <div class="review-product" id="reviewProduct"></div>
    <div class="review-stand" id="reviewStand"></div>
    <form id="reviewForm" onsubmit="return false">
      <fieldset class="sterne-wahl" id="sterneWahl">
        <legend>Sterne</legend>
        <input type="radio" name="sterne" id="stern1" value="1"><label for="stern1" title="1 Stern">★</label>
        <input type="radio" name="sterne" id="stern2" value="2"><label for="stern2" title="2 Sterne">★</label>
        <input type="radio" name="sterne" id="stern3" value="3"><label for="stern3" title="3 Sterne">★</label>
        <input type="radio" name="sterne" id="stern4" value="4"><label for="stern4" title="4 Sterne">★</label>
        <input type="radio" name="sterne" id="stern5" value="5"><label for="stern5" title="5 Sterne">★</label>
      </fieldset>
      <label for="reviewText" class="review-label">Ihre Rezension</label>
      <textarea id="reviewText" maxlength="500" rows="4" placeholder="Was hat gepasst, was nicht? 5 bis 500 Zeichen." oninput="reviewZaehler()"></textarea>
      <div class="review-zaehler" id="reviewZaehler">0 / 500</div>
      <label for="reviewBranch" class="review-label">Filiale</label>
      <select id="reviewBranch"></select>
      <div class="review-meldung" id="reviewMeldung" aria-live="polite"></div>
      <button type="submit" class="btn btn-primary" id="reviewSenden">Senden</button>
    </form>
    <div class="review-stimmen">
      <h4>Kundenstimmen</h4>
      <ul id="reviewStimmen"></ul>
    </div>
  </div>
</div>
```

- [ ] **Step 3: Knopf auf der Karte**

In `renderMenu` den Block aus Task 3 erweitern. Alt:

```html
        <div class="menu-card-rating">
          <span class="rating-text ${bewertungKlasse(p.id)}" data-rating="${p.id}">${bewertungVon(p.id)}</span>
        </div>
```

Neu:

```html
        <div class="menu-card-rating">
          <span class="rating-text ${bewertungKlasse(p.id)}" data-rating="${p.id}">${bewertungVon(p.id)}</span>
          <button type="button" class="bewerten-btn" onclick="openReview(${p.id})">Bewerten</button>
        </div>
```

- [ ] **Step 4: JavaScript des Modals**

Im klassischen Skriptblock direkt nach `function closeModal() { … }` einfügen:

```js
// =============================================================================
// REZENSION — Modal mit Sternen, Text, Filiale und Kundenstimmen
// =============================================================================
let reviewProduktId = null;   // der Artikel, der gerade bewertet wird

// Öffnet das Formular für einen Artikel: Stand, Filiale aus dem Warenkorb,
// Kundenstimmen aus der Simulation. Das Formular startet leer.
function openReview(artikelId) {
  const produkt = PRODUCTS.find(p => p.id === artikelId);
  if (!produkt) return;
  reviewProduktId = artikelId;
  document.getElementById('reviewProduct').textContent = produkt.name;
  reviewStandAnzeigen();
  document.getElementById('reviewForm').reset();
  sterneAnzeigen(0);
  reviewZaehler();
  reviewMeldung('', '');
  document.getElementById('reviewSenden').disabled = false;
  filialwahlFuellen();
  stimmenAnzeigen(artikelId);
  document.getElementById('reviewModal').classList.add('open');
  document.getElementById('stern1').focus();
  logEvent('REVIEW_OPEN', `Bewerten: ${produkt.name}`, 'Formular geöffnet · Ziel: wawi.rezension');
}

function closeReview() {
  document.getElementById('reviewModal').classList.remove('open');
}

// Bewertungsstand des offenen Artikels im Modal (auch nach dem Speichern).
function reviewStandAnzeigen() {
  const stand = document.getElementById('reviewStand');
  stand.textContent = bewertungVon(reviewProduktId);
  stand.className = 'review-stand ' + bewertungKlasse(reviewProduktId);
}

// Färbt die Sterne bis zur gewählten Zahl; die Auswahl selbst liegt in den
// Radios, deshalb bleibt sie mit der Tastatur bedienbar.
function sterneAnzeigen(anzahl) {
  document.querySelectorAll('#sterneWahl label').forEach((label, i) => {
    label.classList.toggle('aktiv', i < anzahl);
  });
}

function reviewZaehler() {
  const text = document.getElementById('reviewText').value;
  document.getElementById('reviewZaehler').textContent = window.REZENSIONEN.zaehlerText(text);
}

// Meldung unter dem Formular: '' (neutral), 'ok' oder 'err'.
function reviewMeldung(art, text) {
  const el = document.getElementById('reviewMeldung');
  el.className = 'review-meldung' + (art ? ' ' + art : '');
  el.textContent = text;
}

// Filialwahl aus derselben Liste wie der Warenkorb, dort gewählte Filiale vorbelegt.
function filialwahlFuellen() {
  const wahl = document.getElementById('reviewBranch');
  wahl.textContent = '';
  const keine = document.createElement('option');
  keine.value = '';
  keine.textContent = 'keine Angabe';
  wahl.appendChild(keine);
  for (const f of BRANCHES) {
    const o = document.createElement('option');
    o.value = f.id;
    o.textContent = f.name;
    wahl.appendChild(o);
  }
  const warenkorb = document.getElementById('cartBranch');
  if (warenkorb && warenkorb.value) wahl.value = warenkorb.value;
}

// Kundenstimmen: nur Simulationstexte aus wawi.v_kundenstimmen, immer per
// textContent — nie innerHTML, weil hier Text aus der Datenbank steht.
function stimmenAnzeigen(artikelId) {
  const liste = document.getElementById('reviewStimmen');
  liste.textContent = '';
  const stimmen = STIMMEN.get(artikelId) || [];
  if (!stimmen.length) {
    const li = document.createElement('li');
    li.className = 'stimme leer';
    li.textContent = 'Noch keine Kundenstimme zu diesem Produkt.';
    liste.appendChild(li);
    return;
  }
  for (const s of stimmen) {
    const li = document.createElement('li');
    li.className = 'stimme';
    const kopf = document.createElement('div');
    kopf.className = 'stimme-kopf';
    kopf.textContent = '★'.repeat(s.sterne) + '☆'.repeat(5 - s.sterne) + ' · ' + window.REZENSIONEN.datumText(s.datum);
    const text = document.createElement('p');
    text.textContent = s.inhalt;
    li.appendChild(kopf);
    li.appendChild(text);
    liste.appendChild(li);
  }
}

document.getElementById('sterneWahl').addEventListener('change', e => sterneAnzeigen(Number(e.target.value)));
document.getElementById('reviewModal').addEventListener('click', e => { if (e.target.id === 'reviewModal') closeReview(); });
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeReview(); });
```

- [ ] **Step 5: Syntax prüfen**

Run: `python3 web/tests/skripte_pruefen.py`
Expected: `0 Block(e) mit Syntaxfehler`.

- [ ] **Step 6: Im Browser prüfen**

Entwicklungsserver (`python3 web/dev_server.py 8899`), dann `http://localhost:8899/shop.html`:
- Auf der Karte „Classic Burger" den Knopf **Bewerten** klicken: Modal öffnet sich mit Produktname, Bewertungsstand (goldfarben) und drei Kundenstimmen (Sterne, Datum, Text).
- Klick auf den vierten Stern färbt vier Sterne gold; Pfeiltasten wechseln die Auswahl (Radios); Tab erreicht Textfeld, Filiale, Senden.
- Textfeld: der Zähler zählt mit (`12 / 500`); die Filiale ist mit der Warenkorbfiliale vorbelegt (Standard: Europastern).
- Escape, Klick außerhalb und das × schließen das Modal. Senden tut noch nichts (Task 5).

Fallback wie in Task 3: ohne Browser-Werkzeug `DONE_WITH_CONCERNS`.

- [ ] **Step 7: Commit**

```bash
git -c core.fileMode=false add web/shop.html
git -c core.fileMode=false commit -m "shop: Modal Bewerten — Sterne als Radiogruppe, Textfeld mit Zähler, Filialwahl, Kundenstimmen per textContent" -m "Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 5: Speichern über `window.rezensionSpeichern`, Bestätigung, Fehler, Stand neu laden

**Files:**
- Modify: `web/shop.html` — Modal-HTML (`onsubmit`), klassischer Skriptblock (nach `stimmenAnzeigen`), Modulblock (nach `window.bestellungSpeichern = …`)

**Interfaces:**
- Consumes: `quelle.rezensionAnlegen(r)`, `quelle.rezensionenProdukt()` (Task 1); `nachArtikel` (Task 2); `SITZUNG`, `window.REZENSIONEN.pruefeEingabe` (Task 3); `reviewProduktId`, `reviewMeldung`, `reviewStandAnzeigen`, `sterneAnzeigen`, `reviewZaehler` (Task 4).
- Produces: `window.rezensionSpeichern(rezension)` → `Promise<{rezension_id, artikel, sterne, erstellt_am, quelle}>` (ergänzt `sitzung: SITZUNG`); `window.bewertungenLaden()` → `Promise<Map<artikel_id, zeile>>`; `window.letzteRezensionenLaden()` → `Promise<zeile[]>`; im klassischen Block `submitReview(event)`, `bewertungenAktualisieren()`.

- [ ] **Step 1: Modulblock — Schreibweg und Nachladen**

Nach dem Block

```js
  window.bestellungSpeichern = (bestellung) =>
    quelle.bestellungAnlegen({ ...bestellung, sitzung: SITZUNG });
```

einfügen:

```js
  // Der zweite Schreibweg: submitReview (klassischer Block) ruft ihn. Die
  // Sitzungskennung ist dieselbe wie bei Bestellungen, damit eine Gruppe ihre
  // Rezensionen in wawi.v_rezension_letzte wiederfindet.
  window.rezensionSpeichern = (rezension) =>
    quelle.rezensionAnlegen({ ...rezension, sitzung: SITZUNG });
  // Nach dem Speichern wird der Bewertungsstand neu geholt — die Sicht rechnet,
  // nicht der Browser.
  window.bewertungenLaden = async () => nachArtikel(await quelle.rezensionenProdukt());
  window.letzteRezensionenLaden = () => quelle.letzteRezensionen();
```

- [ ] **Step 2: Formular an `submitReview` hängen**

Im Modal-HTML `<form id="reviewForm" onsubmit="return false">` ersetzen durch `<form id="reviewForm" onsubmit="submitReview(event)">`.

- [ ] **Step 3: Klassischer Block — `submitReview` und `bewertungenAktualisieren`**

Direkt nach `function stimmenAnzeigen(artikelId) { … }` einfügen:

```js
// Sendet die Rezension: erst die Prüfung im Browser (sofortige Meldung), dann
// rezension_anlegen() in der Datenbank, die ihrerseits prüft und bremst.
// Die Rezensionsnummer vergibt die Datenbank.
function submitReview(event) {
  event.preventDefault();
  const gewaehlt = document.querySelector('#sterneWahl input:checked');
  const eingabe = {
    sterne: gewaehlt ? Number(gewaehlt.value) : 0,
    inhalt: document.getElementById('reviewText').value,
  };
  const befunde = window.REZENSIONEN.pruefeEingabe(eingabe);
  if (befunde.length) { reviewMeldung('err', befunde.join(' ')); return; }
  if (!window.rezensionSpeichern) { reviewMeldung('err', 'Keine Verbindung zum operativen System.'); return; }

  const filiale = document.getElementById('reviewBranch').value;
  const rezension = {
    artikel_id: reviewProduktId,
    sterne:     eingabe.sterne,
    inhalt:     eingabe.inhalt.trim(),
    filiale_id: filiale ? Number(filiale) : null,
  };
  const knopf = document.getElementById('reviewSenden');
  knopf.disabled = true;
  reviewMeldung('', 'Wird gespeichert …');

  window.rezensionSpeichern(rezension).then(antwort => {
    reviewMeldung('ok', `Gespeichert als wawi.rezension #${antwort.rezension_id}`);
    document.getElementById('reviewForm').reset();
    sterneAnzeigen(0);
    reviewZaehler();
    return bewertungenAktualisieren();
  }).catch(fehler => {
    // Die Meldung der Datenbank, z. B. die Bremse — nichts wird umformuliert.
    reviewMeldung('err', fehler.message);
  }).finally(() => {
    knopf.disabled = false;
  });
}

// Bewertungsstand aller Karten und des offenen Modals neu aus der Sicht holen.
async function bewertungenAktualisieren() {
  if (!window.bewertungenLaden) return;
  BEWERTUNGEN = await window.bewertungenLaden();
  document.querySelectorAll('[data-rating]').forEach(el => {
    const artikelId = Number(el.dataset.rating);
    el.textContent = bewertungVon(artikelId);
    el.classList.toggle('leer', bewertungKlasse(artikelId) === 'leer');
  });
  if (reviewProduktId !== null) reviewStandAnzeigen();
}
```

- [ ] **Step 4: Syntax prüfen**

Run: `python3 web/tests/skripte_pruefen.py`
Expected: `0 Block(e) mit Syntaxfehler`.

- [ ] **Step 5: Im Browser prüfen (schreibt eine Rezension in die lebende Datenbank)**

Entwicklungsserver, `http://localhost:8899/shop.html`, Karte „Classic Burger" → **Bewerten**:
- Senden ohne Sterne und mit leerem Text: rote Meldung `Bitte 1 bis 5 Sterne wählen. Der Text braucht mindestens 5 Zeichen.` — kein Aufruf an die Datenbank.
- Vier Sterne, Text `Abnahme Phase 3: guter Burger, schnell serviert.`, Filiale Europastern, Senden: grüne Meldung `Gespeichert als wawi.rezension #<Nummer>`; das Formular ist leer; der Stand im Modal und auf der Karte „Classic Burger" zählt eine Bewertung mehr als vorher.
- Die Nummer notieren und im Report nennen — der Controller räumt am Ende der Phase mit `wawi.uebungsrezensionen_loeschen()` auf.

Fallback wie in Task 3: ohne Browser-Werkzeug `DONE_WITH_CONCERNS`.

- [ ] **Step 6: Commit**

```bash
git -c core.fileMode=false add web/shop.html
git -c core.fileMode=false commit -m "shop: Rezension speichern über rezension_anlegen() — Prüfung im Browser, Meldung der Datenbank, Stand neu geladen" -m "Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 6: Datenmodus — Anmerkung „Rezension → wawi.rezension → ETL → fact_reviews" und der gespeicherte Datensatz

**Files:**
- Modify: `web/shop.html` — erster `<style>`-Block (nach `.data-annotation .da-advantage strong { … }`), HTML im Abschnitt `<section class="menu section-pad" id="menu">` (nach der Anmerkung „MARKET BASKET ANALYSIS"), klassischer Skriptblock (`EVENT_CONFIG`, `submitReview`, neue Funktion `datensatzAnzeigen`)

**Interfaces:**
- Consumes: `window.letzteRezensionenLaden()` (Task 5), `window.REZENSIONEN.datensatzZeilen` (Task 2/3), `logEvent`, `EVENT_CONFIG` (bestehend).
- Produces: `datensatzAnzeigen(rezensionId)`; Element `<dl id="daRezension">`; Ereignisarten `REVIEW`, `REVIEW_OPEN`.

- [ ] **Step 1: CSS des Datensatzes**

Nach der Zeile `.data-annotation .da-advantage strong { color: #FFC060; }` einfügen:

```css
/* Der zuletzt gespeicherte Datensatz in der Datenperspektive: Feld → Wert, ohne inhalt */
.da-datensatz { display: grid; grid-template-columns: max-content 1fr; gap: 2px 10px; margin: 6px 0 10px; font-family: 'Courier New', monospace; font-size: .78rem; }
.da-datensatz dt { color: #7DE0FF; }
.da-datensatz dd { margin: 0; color: #fff; word-break: break-word; }
.da-datensatz dd.leer { grid-column: 1 / -1; color: rgba(255,255,255,.55); }
```

- [ ] **Step 2: Anmerkung im Speisekarten-Abschnitt**

Direkt nach dem schließenden `</div>` der Anmerkung mit dem Titel `MARKET BASKET ANALYSIS` (vor dem `</div>` und `</section>` des Abschnitts `id="menu"`) einfügen:

```html
    <div class="data-annotation" style="bottom:40px;right:20px;animation-delay:.3s;">
      <div class="data-annotation-header">
        <div class="data-annotation-icon da-icon-collect"><i class="fa-solid fa-star"></i></div>
        <div class="data-annotation-title">REZENSIONEN</div>
      </div>
      Jede Bewertung im Shop ist ein Datensatz im operativen System; der ETL-Lauf übernimmt ihn ins Warehouse:
      <div class="data-schema-mini" style="display:block;background:transparent;border:none;padding:0;margin:8px 0;text-align:left;">
        <span class="schema-box">Rezension</span><span class="schema-arrow">→</span>
        <span class="schema-box">wawi.rezension</span><span class="schema-arrow">→</span>
        <span class="schema-box">ETL</span><span class="schema-arrow">→</span>
        <span class="schema-box schema-box-fact">fact_reviews</span>
      </div>
      Zuletzt in dieser Sitzung gespeichert:
      <dl class="da-datensatz" id="daRezension"><dd class="leer">noch keine Rezension</dd></dl>
      <span class="da-metric">stars</span>
      <span class="da-metric">review_text</span>
      <span class="da-metric">source = shop</span><br><br>
      → 10.000 simulierte Rezensionen liegen bereits in <code>fact_reviews</code> (Sentiment-Analyse). Besuchertexte zeigt der Shop nicht an; die Kundenstimmen kommen aus der Simulation.
    </div>
```

- [ ] **Step 3: Ereignisarten und Datensatz im klassischen Block**

a) In `EVENT_CONFIG` nach der Zeile `VIEW:      { icon: 'ev-icon-view',   emoji: '👁️' },` einfügen:

```js
  REVIEW_OPEN: { icon: 'ev-icon-view', emoji: '📝' },
  REVIEW:      { icon: 'ev-icon-view', emoji: '⭐' },
```

b) Direkt nach `async function bewertungenAktualisieren() { … }` einfügen:

```js
// Zeigt den gespeicherten Datensatz in der Datenperspektive — aus der Sicht
// wawi.v_rezension_letzte, nicht aus dem Formular, damit zu sehen ist, was
// wirklich in der Datenbank steht. Ohne inhalt: Besuchertext wird nicht gerendert.
async function datensatzAnzeigen(rezensionId) {
  const dl = document.getElementById('daRezension');
  if (!dl || !window.letzteRezensionenLaden) return;
  try {
    const zeilen = await window.letzteRezensionenLaden();
    const rezension = zeilen.find(z => Number(z.rezension_id) === Number(rezensionId));
    if (!rezension) return;
    dl.textContent = '';
    for (const [feld, wert] of window.REZENSIONEN.datensatzZeilen(rezension)) {
      const dt = document.createElement('dt');
      dt.textContent = feld;
      const dd = document.createElement('dd');
      dd.textContent = wert;
      dl.appendChild(dt);
      dl.appendChild(dd);
    }
  } catch (fehler) {
    console.warn('Datensatz der Rezension:', fehler);
  }
}
```

c) In `submitReview` den Erfolgszweig erweitern. Alt:

```js
    reviewZaehler();
    return bewertungenAktualisieren();
```

Neu:

```js
    reviewZaehler();
    logEvent('REVIEW', 'Rezension gespeichert',
      `INSERT INTO wawi.rezension · #${antwort.rezension_id} · ${'★'.repeat(antwort.sterne)} ${antwort.artikel}`);
    datensatzAnzeigen(antwort.rezension_id);
    return bewertungenAktualisieren();
```

- [ ] **Step 4: Syntax prüfen**

Run: `python3 web/tests/skripte_pruefen.py`
Expected: `0 Block(e) mit Syntaxfehler`.

- [ ] **Step 5: Im Browser prüfen (schreibt eine Rezension)**

Entwicklungsserver, `http://localhost:8899/shop.html`, Schalter **DATA VIEW** einschalten:
- Im Speisekarten-Abschnitt erscheint die Anmerkung REZENSIONEN mit der Kette und `noch keine Rezension`.
- „Cola 0.5l" → Bewerten → fünf Sterne, Text `Abnahme Phase 3: Datenmodus, kalt und spritzig.`, Senden: Meldung grün; im Event-Stream steht `⭐ Rezension gespeichert — INSERT INTO wawi.rezension · #<Nummer> · ★★★★★ Cola 0.5l`; die Anmerkung zeigt `rezension_id`, `artikel Cola 0.5l`, `filiale`, `sterne ★★★★★`, `erstellt_am`, `sitzung shop-…`, `im_warehouse nein — erst nach dem ETL-Lauf` — und **keinen** Text der Rezension.
- Nummer im Report nennen (Aufräumen durch den Controller).

- [ ] **Step 6: Commit**

```bash
git -c core.fileMode=false add web/shop.html
git -c core.fileMode=false commit -m "shop: Datenperspektive zeigt die Kette Rezension → wawi.rezension → ETL → fact_reviews und den gespeicherten Datensatz" -m "Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 7: Abnahme, Aufräumen, Pull Request

**Files:**
- Modify: `docs/superpowers/specs/2026-09-12-bm-analyse-lernumgebung-design.md` (Abschnitt 11, Absatz „Stand 12. September 2026")

- [ ] **Step 1: Alle Prüfungen in einem Lauf**

```bash
node --test "web/tests/*.test.mjs"          # 12 Tests
python3 web/tests/skripte_pruefen.py        # 0 Block(e) mit Syntaxfehler
python3 -m pytest dataset/tests -q          # 29 passed (unverändert)
git status --short                          # leer
git diff --stat main -- web/abgleich.html web/dashboard.html web/pos.html   # leer: unverändert
```

- [ ] **Step 2: Abnahme im Browser nach Spec 11 (Zeile „Shop")**

Auf `http://localhost:8899/shop.html` in einem frischen Tab: eine Rezension zu „Classic Burger" speichern (drei Sterne, Text `Abnahme Phase 3, Task 7: solide, nichts Besonderes.`), danach:
- Meldung `Gespeichert als wawi.rezension #<N>`; Ø am Produkt (Karte und Modal) aktualisiert.
- Datenmodus: Datensatz `#<N>` mit `im_warehouse nein`.
- Über den MCP-Server `burgermetrics-db` (Controller): `SELECT rezension_id, artikel, sterne, im_warehouse FROM wawi.v_rezension_letzte` zeigt `#<N>` und die Rezensionen aus Task 5 und 6; dann `SELECT * FROM wawi.uebungsrezensionen_loeschen()` → `(0, k)` mit k = Zahl der Abnahme-Rezensionen; danach `SELECT count(*) FROM wawi.rezension WHERE quelle = 'shop'` → 0 und `SELECT * FROM wawi.etl_probe()` → 0/0 je Tabelle.

Der Controller führt diesen Schritt selbst aus (Browser-Pane und MCP), falls der Implementierer kein Browser-Werkzeug hat.

- [ ] **Step 3: Abnahmestand in der Spec**

In Abschnitt 11 den Absatz „**Stand 12. September 2026 (Phase 2):** …" um einen Absatz ergänzen:

```markdown
**Stand 12. September 2026 (Phase 3):** Shop abgenommen — Rezension im Browser gespeichert, in `v_rezension_letzte` sichtbar, Ø am Produkt aktualisiert, `uebungsrezensionen_loeschen()` räumt auf, Datenmodus zeigt den Datensatz. Von der Übergabe je Phase ist damit auch „Shop auf Pages mit Bewertungsfunktion" erfüllt, sobald der PR auf `main` ist.
```

```bash
git -c core.fileMode=false add docs/superpowers/specs/2026-09-12-bm-analyse-lernumgebung-design.md
git -c core.fileMode=false commit -m "spec: Abnahmestand Phase 3 vermerkt" -m "Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

- [ ] **Step 4: Push und PR**

```bash
git push origin bm-analyse
gh pr create --base main --head bm-analyse --title "Phase 3: Shop — Rezensionen schreiben und lesen" --body-file - <<'EOF'
## Was
- `web/js/datenquelle.js`: vier Methoden auf `wawi.v_rezension_produkt`, `v_kundenstimmen`, `v_rezension_letzte` und `rezension_anlegen()`; Integrationstests gegen PostgREST
- `web/js/rezensionen.js`: Bewertungstext, Eingabeprüfung, Zähler, Datensatzzeilen — ohne DOM, mit `node --test`
- `web/shop.html`: Bewertungszeile auf jeder Karte, Modal **Bewerten** (Sterne als Radiogruppe, Text 5–500 Zeichen, Filiale aus dem Warenkorb, drei Kundenstimmen aus der Simulation), Speichern über `window.rezensionSpeichern`, Datenperspektive mit der Kette `Rezension → wawi.rezension → ETL → fact_reviews` und dem gespeicherten Datensatz
- `web/tests/skripte_pruefen.py`: Syntaxprüfer für eingebettete Skripte

## Sicherheit
- Besuchertexte werden nirgends gerendert; Kundenstimmen kommen aus `v_kundenstimmen` (nur Simulation) und werden per `textContent` gesetzt
- Längen- und Ratenbegrenzung in der Datenbank (`0021`); der Browser prüft nur für die sofortige Meldung

## Abnahme
- Rezension im Browser gespeichert, `v_rezension_letzte` zeigt sie, Ø am Produkt aktualisiert, Datenmodus zeigt den Datensatz; `uebungsrezensionen_loeschen()` hat aufgeräumt, `etl_probe()` 0/0
- `abgleich.html`, `dashboard.html`, `pos.html` unverändert

Spec: docs/superpowers/specs/2026-09-12-bm-analyse-lernumgebung-design.md · Plan: docs/superpowers/plans/2026-09-12-phase-3-shop-rezensionen.md

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
```

- [ ] **Step 5: Merge nur nach Rückfrage bei Robert**

Nach seiner Zusage: `gh pr merge <Nummer> --merge --delete-branch=false`, dann `git checkout main && git pull --ff-only origin main && git checkout bm-analyse && git merge --ff-only main`. Pages-Lauf abwarten (`gh run list --branch main --limit 1` → `completed success`) und auf `https://swrobuts.github.io/BurgerMetrics/shop.html` prüfen, dass die Karten den Bewertungsstand zeigen und **Bewerten** das Modal öffnet (nichts speichern).

---

## Selbstprüfung des Plans (durchgeführt)

- **Spec-Abdeckung (Abschnitt 5):** `datenquelle.js` mit vier Methoden → Task 1; „★ 4,3 · 128 Bewertungen" / „noch keine Bewertung" auf der Karte → Task 2 (Text) und 3 (Anzeige); Knopf **Bewerten**, Modal mit fünf Sternen (Radiogruppe, Tastatur), Textfeld mit Zähler 5–500, Filialwahl vorbelegt aus `cartBranch`, drei Kundenstimmen → Task 4; `window.rezensionSpeichern` mit `sitzung: SITZUNG`, Bestätigung „Gespeichert als `wawi.rezension #4711`", Ø neu geladen, Fehler mit Datenbankmeldung → Task 5; Datenmodus-Anmerkung und Datensatz → Task 6; Sicherheit (nur `v_kundenstimmen`, `textContent`, Begrenzung in der Datenbank) → Global Constraints, Task 4 und 6; `abgleich.html`/`dashboard.html` unverändert → Task 7 Step 1. Spec 11 („Shop") und „Übergabe je Phase" (Shop auf Pages) → Task 7. „Detail" in Spec 5 („Karte und Detail") ist das Modal — der Shop hat keine eigene Produktdetailseite.
- **Platzhalter:** keine; die Rezensionsnummern der Abnahme sind Laufzeitwerte und als `#<N>` gekennzeichnet.
- **Schnittstellen:** `shopStarten(artikel, filialen, bewertungen, stimmen)` in Task 3 (Definition) und Task 3 Modulblock (Aufruf) gleich; `window.REZENSIONEN` trägt genau die fünf Funktionen, die der klassische Block nutzt (`bewertungText` Task 3, `zaehlerText`/`datumText` Task 4, `pruefeEingabe` Task 5, `datensatzZeilen` Task 6); `nachArtikel`/`stimmenNachArtikel` nur im Modulblock; `reviewMeldung(art, text)` in Task 4 definiert, in Task 5 mit `''`, `'ok'`, `'err'` gerufen; `datensatzAnzeigen` in Task 6 definiert und dort in `submitReview` eingehängt; Feldnamen der Sichten (`anzahl`, `sterne_mittel`, `datum`, `inhalt`, `im_warehouse`) in Task 1, 2 und 6 identisch mit `0021`.
