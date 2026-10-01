# Freigabe E: Bereich „Rezensionen“ im POS — Implementierungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** In der Kasse (`web/pos.html`) öffnet ein Knopf „Rezensionen“ mit Zähler einen Bereich für die Moderation. Wer mit einem Supabase-Konto angemeldet ist und die Rolle `moderation` oder `qualitaet` hat, sieht die QS-Fälle, die zurückgehaltenen Rezensionen mit Gründen und Wahrscheinlichkeiten und die zuletzt getroffenen Entscheidungen. Freigeben, Ablehnen und Erledigen gehen über die Funktionen aus Phase A. Robert bekommt beide Rollen; die Abnahme machen Robert und Claude gemeinsam.

**Architecture:** `PostgrestQuelle` lernt die Anmeldung über den Anmeldedienst von Supabase (`/auth/v1/token?grant_type=password`). Solange sie gilt, schickt sie das Token statt des öffentlichen Schlüssels als `Authorization`. Die Moderationsmethoden laufen nur mit gültiger Anmeldung; eine abgelaufene melden sie mit einer festen Meldung. Reine Logik ohne DOM (Sortierung, Gründe, Balken, Statuszeile) steht im neuen Modul `web/js/moderation.js`. Die Darstellung lebt im Modulblock von `pos.html`, weil dort `quelle` existiert. Das Token liegt im `sessionStorage` des Tabs.

**Tech Stack:** Vanilla JavaScript (ES-Module), Supabase GoTrue (REST, ohne supabase-js), PostgREST, Node 24 (`node --test`), Python 3 (`web/tests/skripte_pruefen.py`), eingebauter Browser der Desktop-App für die gemeinsame Abnahme.

**Spec:** `docs/superpowers/specs/2026-09-30-rezensionen-jev-freigabe-design.md`, Abschnitte 8 (POS), 5.3 und 5.4 (Rechte, Sichten), 10 (Abnahme 3, 4, 9) und 11 (Phase E).

## Global Constraints

- Voraussetzungen: Phase A live, Phase D läuft (Rezensionen werden geprüft), Phase B gemergt.
- Die Kasse bleibt ohne Anmeldung, die Manager-PIN unverändert. Nur der Bereich „Rezensionen“ braucht ein Konto.
- **Claude legt keine Konten an und gibt keine Passwörter ein.** Robert meldet sich im eingebauten Browser selbst an. Rollen vergibt Claude über die Konto-ID aus `velocity.mitarbeiter`, erst nach Roberts Bestätigung im Chat; weder Konto-ID noch E-Mail-Adresse kommen ins Repo oder in die Ausgabe.
- Texte wörtlich: Knopf „Rezensionen“; ohne Rolle „Dieses Konto hat keine Rolle für die Moderation.“; abgelaufen „Die Anmeldung ist abgelaufen. Bitte neu anmelden.“; falsches Passwort „E-Mail oder Passwort stimmen nicht.“; Blöcke „Gesundheitsrisiken“, „Zurückgehalten“, „Zuletzt entschieden“; Knöpfe „Anmelden“, „Abmelden“, „Freigeben“, „Ablehnen“, „Erledigt“.
- Rezensionstext, Bemerkungen und Gründe nur mit `textContent`, nie mit `innerHTML`.
- Das Passwort verlässt das Formular nur im Request an `/auth/v1/token`; es wird nicht gespeichert, nicht geloggt und das Feld danach geleert. Im `sessionStorage` liegen nur Token, Ablaufzeit und die E-Mail zur Anzeige.
- Cache-Brecher: In `pos.html` alle Modul-Importe auf `?v=20261005` setzen; `moderation.js` mit derselben Nummer.
- Lehrcode: kurze Funktionen, deutsche Namen, ein Kommentar je Funktion. Deutsch mit echten Umlauten; Bezeichner, CSS-Klassen und IDs ASCII.
- Tests: `node --test "web/tests/*.test.mjs"`, `python3 web/tests/skripte_pruefen.py web/pos.html`. Integrationstests schreiben nie erfolgreich.
- Produktion: Testrezensionen der Abnahme entstehen über `rezension_anlegen()` und werden danach als `postgres` per ID gelöscht, nie über `uebungsrezensionen_loeschen()`.
- Commits: `git -c core.fileMode=false add <Dateien>` (nie `tableau/BurgerMetrics.twb`), deutsche Nachricht, zweiter Absatz `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Branch `bm-analyse`, am Ende ein PR auf `main`, Merge nur nach Roberts Zusage.
- Dateien im Repo schreibt der Executor per Bash (Heredoc oder Python), weil der Write-Hook sie außerhalb des Worktrees sperrt.

## Review Focus

1. **Token läuft während der Arbeit ab.** Nach einer Stunde antwortet PostgREST mit 401. Der Bereich muss dann zur Anmeldung wechseln, nicht eine rohe Fehlermeldung zeigen. Test: `abgelaufene Sitzung wird nicht übernommen, 401 meldet ab` (Task 1).
2. **Konto nur mit Rolle `qualitaet`.** Die Blöcke der Moderation bleiben dann verborgen, der QS-Block erscheint. Test: `meineRollen fragt hat_rolle je Rolle` (Task 1) und Abnahme-Schritt „nur qualitaet“ (Task 5).
3. **Doppelklick auf „Freigeben“.** Der zweite Aufruf darf keinen Fehler „schon entschieden“ zeigen, der die Moderatorin verwirrt. Der Knopf ist gesperrt, solange der Aufruf läuft. Test: Abnahme-Schritt „Doppelklick“ (Task 5).
4. **Escape im Bemerkungsfeld.** Die Kasse ignoriert Escape in Eingabefeldern. Das Fenster bleibt offen, und die Bemerkung geht nicht verloren. Test: Abnahme-Schritt „Escape“ (Task 5).
5. **Schmale Kopfleiste.** Bei 768 px ist die Kopfleiste schon voll. Der Knopf muss sichtbar und bedienbar bleiben (Symbol und Zähler, Text entfällt unter 400 px). Test: Abnahme-Schritt „Kopfleiste“ (Task 5).

---

## Dateistruktur

| Datei | Verantwortung |
|---|---|
| `web/js/datenquelle.js` (ändern) | Anmeldung, Token im `Authorization`-Kopf, neun Methoden für Moderation und Stand |
| `web/js/moderation.js` (neu) | reine Logik: Gründe, Risiko, Sortierung, Balken, Statuszeile, Zähler, Sitzung, Zeit |
| `web/tests/moderation.test.mjs` (neu) | Modultests für `moderation.js` |
| `web/tests/datenquelle.test.mjs` (ändern) | Anmeldung und Moderation mit nachgebildetem `fetch` |
| `web/tests/datenquelle_rezensionen.test.mjs` (ändern) | lebende API: Stand ohne Anmeldung lesbar, Moderation ohne Anmeldung abgewiesen |
| `web/pos.html` (ändern) | Knopf mit Zähler, Modal „Rezensionen“, CSS, Modulblock |
| `docs/05-anwendungen.md` (ändern) | Absatz „Rezensionen“ in 5.4 |

---

### Task 1: Anmeldung und Moderation in der Datenquelle

**Files:**
- Modify: `web/js/datenquelle.js`
- Test: `web/tests/datenquelle.test.mjs`, `web/tests/datenquelle_rezensionen.test.mjs`

**Interfaces:**
- Consumes: `/auth/v1/token?grant_type=password` und `/auth/v1/logout` (GoTrue); RPC `hat_rolle(p_rolle)`, `api_rezension_freigeben(rezension_id, bemerkung)`, `api_rezension_ablehnen(rezension_id, bemerkung)`, `api_qs_fall_erledigen(qs_fall_id, bemerkung)`; Sichten `v_moderation`, `v_qs_faelle`, `v_entscheidungen_letzte`, `v_pruefdienst_stand` aus Phase A.
- Produces (in `Datenquelle` beschrieben, in `PostgrestQuelle` umgesetzt):
  - `anmelden(email, passwort) → Promise<{token, gueltigBis}>`; Fehler `'E-Mail oder Passwort stimmen nicht.'` bei HTTP 400/401
  - `sitzungUebernehmen(sitzung) → boolean`, `angemeldet() → boolean`, `abmelden() → Promise<void>`
  - `meineRollen() → Promise<string[]>` (Teilmenge von `['moderation', 'qualitaet']`)
  - `moderationListe()`, `qsFaelle()`, `entscheidungenLetzte()` → `Promise<Array>` mit den Spalten der Sichten
  - `pruefdienstStand() → Promise<{letzte_pruefung, offen, aelteste_offene_min, zurueckgehalten, qs_offen} | null>` (ohne Anmeldung)
  - `rezensionFreigeben(rezensionId, bemerkung)`, `rezensionAblehnen(rezensionId, bemerkung)` → `Promise<{rezension_id, status}>`; `qsFallErledigen(qsFallId, bemerkung)` → `Promise<{qs_fall_id, erledigt_am}>`
  - Ohne gültige Anmeldung und bei HTTP 401 werfen die Moderationsmethoden `Error('Die Anmeldung ist abgelaufen. Bitte neu anmelden.')`.

- [ ] **Step 1: Tests mit nachgebildetem `fetch` anhängen**

Am Ende von `web/tests/datenquelle.test.mjs`:

```js
test('anmelden: Token aus der Antwort, danach als Authorization', async t => {
  const aufrufe = [];
  t.mock.method(globalThis, 'fetch', async (url, optionen) => {
    aufrufe.push({ url: String(url), optionen });
    if (String(url).includes('/auth/v1/token')) return antwort({ access_token: 'nutzer-token', expires_in: 3600 });
    return antwort([{ rezension_id: 1 }]);
  });
  const q = quelle();
  const sitzung = await q.anmelden('a@example.org', 'geheim');
  assert.equal(sitzung.token, 'nutzer-token');
  assert.ok(sitzung.gueltigBis > Date.now() + 3400 * 1000);
  assert.equal(new URL(aufrufe[0].url).searchParams.get('grant_type'), 'password');
  assert.deepEqual(JSON.parse(aufrufe[0].optionen.body), { email: 'a@example.org', password: 'geheim' });
  await q.moderationListe();
  assert.equal(aufrufe[1].optionen.headers.Authorization, 'Bearer nutzer-token');
  assert.equal(aufrufe[1].optionen.headers.apikey, 'test');
});

test('anmelden: falsches Passwort ergibt eine verständliche Meldung', async t => {
  t.mock.method(globalThis, 'fetch', async () => new Response('{"error":"invalid_grant"}', { status: 400 }));
  await assert.rejects(quelle().anmelden('a@example.org', 'falsch'), /E-Mail oder Passwort stimmen nicht/);
});

test('ohne Anmeldung: Moderation abgewiesen, Stand lesbar', async t => {
  t.mock.method(globalThis, 'fetch', async () => antwort([{ offen: 0, zurueckgehalten: 2, qs_offen: 1 }]));
  const q = quelle();
  await assert.rejects(q.moderationListe(), /abgelaufen/);
  await assert.rejects(q.rezensionFreigeben(1), /abgelaufen/);
  assert.deepEqual(await q.pruefdienstStand(), { offen: 0, zurueckgehalten: 2, qs_offen: 1 });
});

test('abgelaufene Sitzung wird nicht übernommen, 401 meldet ab', async t => {
  const q = quelle();
  assert.equal(q.sitzungUebernehmen({ token: 'alt', gueltigBis: Date.now() - 1 }), false);
  assert.equal(q.sitzungUebernehmen({ token: 'neu', gueltigBis: Date.now() + 60000 }), true);
  t.mock.method(globalThis, 'fetch', async () => new Response('{"message":"JWT expired"}', { status: 401 }));
  await assert.rejects(q.qsFaelle(), /abgelaufen/);
  assert.equal(q.angemeldet(), false);
});

test('Entscheidungen gehen mit Nummer und Bemerkung an die RPC', async t => {
  const aufrufe = [];
  t.mock.method(globalThis, 'fetch', async (url, optionen) => {
    aufrufe.push([new URL(url).pathname, JSON.parse(optionen.body)]);
    return antwort({ status: 'ok' });
  });
  const q = quelle();
  q.sitzungUebernehmen({ token: 't', gueltigBis: Date.now() + 60000 });
  await q.rezensionFreigeben('7', '');
  await q.rezensionAblehnen(8, 'Werbung');
  await q.qsFallErledigen(3, 'Filiale informiert');
  assert.deepEqual(aufrufe, [
    ['/rest/v1/rpc/api_rezension_freigeben', { rezension_id: 7, bemerkung: null }],
    ['/rest/v1/rpc/api_rezension_ablehnen', { rezension_id: 8, bemerkung: 'Werbung' }],
    ['/rest/v1/rpc/api_qs_fall_erledigen', { qs_fall_id: 3, bemerkung: 'Filiale informiert' }],
  ]);
});

test('meineRollen fragt hat_rolle je Rolle', async t => {
  t.mock.method(globalThis, 'fetch', async (url, optionen) =>
    antwort(JSON.parse(optionen.body).p_rolle === 'qualitaet'));
  const q = quelle();
  q.sitzungUebernehmen({ token: 't', gueltigBis: Date.now() + 60000 });
  assert.deepEqual(await q.meineRollen(), ['qualitaet']);
});

test('abmelden ruft logout und vergisst das Token', async t => {
  const pfade = [];
  t.mock.method(globalThis, 'fetch', async url => { pfade.push(new URL(url).pathname); return new Response(null, { status: 204 }); });
  const q = quelle();
  q.sitzungUebernehmen({ token: 't', gueltigBis: Date.now() + 60000 });
  await q.abmelden();
  assert.deepEqual(pfade, ['/auth/v1/logout']);
  assert.equal(q.angemeldet(), false);
});
```

Am Ende von `web/tests/datenquelle_rezensionen.test.mjs`:

```js
test('pruefdienstStand: ohne Anmeldung lesbar', async () => {
  const stand = await quelle.pruefdienstStand();
  for (const feld of ['offen', 'zurueckgehalten', 'qs_offen']) assert.equal(typeof stand[feld], 'number');
});

test('Moderation: ohne Anmeldung abgewiesen, noch vor dem Server', async () => {
  const frisch = waehleQuelle(QUELLE);
  await assert.rejects(frisch.moderationListe(), /abgelaufen/);
  await assert.rejects(frisch.rezensionFreigeben(1), /abgelaufen/);
});
```

- [ ] **Step 2: Tests laufen lassen, sie müssen scheitern**

Run: `node --test "web/tests/datenquelle*.test.mjs"`
Expected: FAIL mit `TypeError: q.anmelden is not a function`.

- [ ] **Step 3: `web/js/datenquelle.js` erweitern**

In der Klasse `Datenquelle` nach `rezensionStatus()` (Phase B) anfügen:

```js
  /** Anmeldung mit einem Supabase-Konto für die Moderation im POS.
   *  @returns {Promise<object>} token, gueltigBis (Millisekunden) */
  anmelden(email, passwort) { throw new Error('nicht umgesetzt'); }
  /** Übernimmt eine gespeicherte Anmeldung, wenn sie noch gilt; true bei Erfolg. */
  sitzungUebernehmen(sitzung) { throw new Error('nicht umgesetzt'); }
  /** Gilt die Anmeldung noch? */
  angemeldet() { throw new Error('nicht umgesetzt'); }
  /** Meldet ab und vergisst das Token. */
  abmelden() { throw new Error('nicht umgesetzt'); }
  /** Rollen des angemeldeten Kontos: 'moderation', 'qualitaet' oder keine. */
  meineRollen() { throw new Error('nicht umgesetzt'); }
  /** Zurückgehaltene und lange offene Shop-Rezensionen mit Jevs Wahrscheinlichkeiten (Rolle moderation). */
  moderationListe() { throw new Error('nicht umgesetzt'); }
  /** Offene QS-Fälle mit Text (Rolle qualitaet). */
  qsFaelle() { throw new Error('nicht umgesetzt'); }
  /** Die letzten 20 Entscheidungen (Rolle moderation). */
  entscheidungenLetzte() { throw new Error('nicht umgesetzt'); }
  /** Stand des Prüfdienstes ohne Texte, auch ohne Anmeldung: letzte_pruefung, offen,
   *  aelteste_offene_min, zurueckgehalten, qs_offen. */
  pruefdienstStand() { throw new Error('nicht umgesetzt'); }
  /** Gibt eine Shop-Rezension frei (Rolle moderation). */
  rezensionFreigeben(rezensionId, bemerkung) { throw new Error('nicht umgesetzt'); }
  /** Lehnt eine Shop-Rezension ab (Rolle moderation). */
  rezensionAblehnen(rezensionId, bemerkung) { throw new Error('nicht umgesetzt'); }
  /** Schließt einen QS-Fall (Rolle qualitaet). */
  qsFallErledigen(qsFallId, bemerkung) { throw new Error('nicht umgesetzt'); }
```

In `PostgrestQuelle`:

1. Im Konstruktor nach `this.zwischenspeicher = new Map();` die Zeile `this.sitzung = null;   // Anmeldung für die Moderation: token, gueltigBis` einfügen.
2. In `hole()` und `rufe()` jeweils `Authorization: \`Bearer ${this.schluessel}\`,` ersetzen durch `Authorization: \`Bearer ${this.ausweis()}\`,`.
3. Nach der Methode `rufe()` einfügen:

```js
  /** Das Token für Authorization: die Anmeldung, solange sie gilt, sonst der öffentliche Schlüssel. */
  ausweis() {
    return this.angemeldet() ? this.sitzung.token : this.schluessel;
  }

  angemeldet() {
    return Boolean(this.sitzung && Date.now() < this.sitzung.gueltigBis);
  }

  /** Anmeldung beim Anmeldedienst von Supabase; das Passwort geht nur in diesen Request. */
  async anmelden(email, passwort) {
    const antwort = await fetch(`${this.url}/auth/v1/token?grant_type=password`, {
      method: 'POST',
      headers: { apikey: this.schluessel, 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password: passwort }),
    });
    if (antwort.status === 400 || antwort.status === 401) throw new Error('E-Mail oder Passwort stimmen nicht.');
    if (!antwort.ok) throw new Error(`anmelden: HTTP ${antwort.status}`);
    const daten = await antwort.json();
    // Eine Minute vor dem Ablauf gilt die Anmeldung schon als abgelaufen.
    this.sitzung = { token: daten.access_token,
                     gueltigBis: Date.now() + ((Number(daten.expires_in) || 3600) - 60) * 1000 };
    return this.sitzung;
  }

  sitzungUebernehmen(sitzung) {
    const gueltig = Boolean(sitzung && sitzung.token && Date.now() < Number(sitzung.gueltigBis));
    this.sitzung = gueltig ? { token: sitzung.token, gueltigBis: Number(sitzung.gueltigBis) } : null;
    return gueltig;
  }

  /** Meldet beim Anmeldedienst ab; das Token ist danach vergessen, auch wenn der Dienst nicht antwortet. */
  async abmelden() {
    if (this.angemeldet()) {
      try {
        await fetch(`${this.url}/auth/v1/logout`, {
          method: 'POST', headers: { apikey: this.schluessel, Authorization: `Bearer ${this.sitzung.token}` } });
      } catch (_) { /* abgemeldet wird trotzdem */ }
    }
    this.sitzung = null;
    this.zwischenspeicher.clear();
  }

  /** Führt einen Aufruf nur mit gültiger Anmeldung aus; HTTP 401 heißt: abgelaufen. */
  async mitAnmeldung(aufruf) {
    const abgelaufen = new Error('Die Anmeldung ist abgelaufen. Bitte neu anmelden.');
    if (!this.angemeldet()) {
      this.sitzung = null;
      throw abgelaufen;
    }
    try {
      return await aufruf();
    } catch (fehler) {
      if (/HTTP 401/.test(fehler.message)) {
        this.sitzung = null;
        throw abgelaufen;
      }
      throw fehler;
    }
  }
```

4. Nach den Methoden aus Phase B (`rezensionStatus`) einfügen:

```js
  meineRollen() {
    return this.mitAnmeldung(async () => {
      const rollen = [];
      for (const rolle of ['moderation', 'qualitaet']) {
        if (await this.rufe('hat_rolle', { p_rolle: rolle })) rollen.push(rolle);
      }
      return rollen;
    });
  }
  moderationListe()      { return this.mitAnmeldung(() => this.hole('v_moderation', '', { schema: this.schemaWawi, frisch: true })); }
  qsFaelle()             { return this.mitAnmeldung(() => this.hole('v_qs_faelle', '', { schema: this.schemaWawi, frisch: true })); }
  entscheidungenLetzte() { return this.mitAnmeldung(() => this.hole('v_entscheidungen_letzte', '', { schema: this.schemaWawi, frisch: true })); }
  async pruefdienstStand() {
    const [zeile] = await this.hole('v_pruefdienst_stand', '', { schema: this.schemaWawi, frisch: true });
    return zeile || null;
  }
  rezensionFreigeben(rezensionId, bemerkung) {
    return this.mitAnmeldung(() => this.rufe('api_rezension_freigeben',
      { rezension_id: Number(rezensionId), bemerkung: bemerkung || null }));
  }
  rezensionAblehnen(rezensionId, bemerkung) {
    return this.mitAnmeldung(() => this.rufe('api_rezension_ablehnen',
      { rezension_id: Number(rezensionId), bemerkung: bemerkung || null }));
  }
  qsFallErledigen(qsFallId, bemerkung) {
    return this.mitAnmeldung(() => this.rufe('api_qs_fall_erledigen',
      { qs_fall_id: Number(qsFallId), bemerkung: bemerkung || null }));
  }
```

- [ ] **Step 4: Tests laufen lassen**

Run: `node --test "web/tests/*.test.mjs"`
Expected: alle bestanden.

- [ ] **Step 5: Commit**

```bash
git -c core.fileMode=false add web/js/datenquelle.js web/tests/datenquelle.test.mjs web/tests/datenquelle_rezensionen.test.mjs
git commit -m "Freigabe E: Anmeldung über Supabase und Moderation in der Datenquelle" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Reine Logik in `moderation.js`

**Files:**
- Create: `web/js/moderation.js`
- Test: `web/tests/moderation.test.mjs`

**Interfaces:**
- Consumes: Zeilen aus `v_moderation` (`p_gesundheitsrisiko` … `p_themenbezug`, `qs_fall`, `erstellt_am`, `gruende`), `v_pruefdienst_stand`.
- Produces: `FRAGEN`, `GRUND_ERKLAERUNG`, `grundText(grund)`, `risikoWert(zeile)`, `nachRisiko(zeilen)`, `balken(zeile) → [{name, prozent}]`, `standText(stand) → {text, warnung}`, `zahlAmKnopf(stand) → number`, `sitzungGueltig(sitzung, jetzt = Date.now()) → boolean`, `zeitText(iso) → string`.

- [ ] **Step 1: Tests schreiben**

`web/tests/moderation.test.mjs`:

```js
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { FRAGEN, grundText, risikoWert, nachRisiko, balken, standText, zahlAmKnopf,
         sitzungGueltig, zeitText } from '../js/moderation.js';

const zeile = (werte = {}) => ({
  p_gesundheitsrisiko: 0.01, p_beleidigung: 0.01, p_personenbezug: 0.01, p_werbung: 0.01,
  p_anweisung: 0.01, p_themenbezug: 0.95, qs_fall: false, erstellt_am: '2026-10-01T10:00:00+00:00', ...werte });

test('grundText erklärt bekannte Gründe und lässt unbekannte stehen', () => {
  assert.match(grundText('Gesundheitsrisiko'), /^Gesundheitsrisiko: .*QS-Fall/);
  assert.match(grundText('Kontaktdaten oder Link'), /Telefonnummer/);
  assert.equal(grundText('neu'), 'neu');
});

test('risikoWert: höchste Wahrscheinlichkeit, fehlender Themenbezug zählt, ohne Prüfung 0', () => {
  assert.equal(risikoWert(zeile({ p_werbung: 0.7 })), 0.7);
  assert.ok(Math.abs(risikoWert(zeile({ p_themenbezug: 0.1 })) - 0.9) < 1e-9);
  assert.equal(risikoWert({ p_themenbezug: null }), 0);
});

test('nachRisiko: QS-Fälle zuerst, dann höchstes Risiko, dann ältere zuerst', () => {
  const a = zeile({ rezension_id: 1, p_werbung: 0.6 });
  const b = zeile({ rezension_id: 2, qs_fall: true, p_gesundheitsrisiko: 0.5 });
  const c = zeile({ rezension_id: 3, p_beleidigung: 0.9 });
  const d = zeile({ rezension_id: 4, p_werbung: 0.6, erstellt_am: '2026-10-01T09:00:00+00:00' });
  assert.deepEqual(nachRisiko([a, b, c, d]).map(z => z.rezension_id), [2, 3, 4, 1]);
});

test('balken: sechs Werte in Prozent, ohne Prüfung keine', () => {
  const werte = balken(zeile({ p_gesundheitsrisiko: 0.456 }));
  assert.equal(werte.length, FRAGEN.length);
  assert.deepEqual(werte[0], { name: 'Gesundheitsrisiko', prozent: 46 });
  assert.deepEqual(balken({ p_themenbezug: null }), []);
});

test('standText warnt ab fünf Minuten Wartezeit', () => {
  const ruhig = standText({ offen: 1, aelteste_offene_min: 2, zurueckgehalten: 3, qs_offen: 0 });
  assert.deepEqual(ruhig, { text: '1 offen · 3 zurückgehalten · 0 QS-Fälle', warnung: false });
  const lang = standText({ offen: 2, aelteste_offene_min: 7, zurueckgehalten: 0, qs_offen: 1 });
  assert.equal(lang.warnung, true);
  assert.match(lang.text, /seit 7 Minuten/);
  assert.equal(standText(null).warnung, true);
});

test('zahlAmKnopf und sitzungGueltig', () => {
  assert.equal(zahlAmKnopf({ zurueckgehalten: 3, qs_offen: 2 }), 5);
  assert.equal(zahlAmKnopf(null), 0);
  assert.equal(sitzungGueltig({ token: 't', gueltigBis: 2000 }, 1000), true);
  assert.equal(sitzungGueltig({ token: 't', gueltigBis: 1000 }, 1000), false);
  assert.equal(sitzungGueltig(null), false);
});

test('zeitText: Tag, Monat und Uhrzeit in Berlin', () => {
  assert.equal(zeitText('2026-10-01T12:05:00+00:00'), '01.10., 14:05');
  assert.equal(zeitText(null), '');
});
```

- [ ] **Step 2: Tests laufen lassen, sie müssen scheitern**

Run: `node --test web/tests/moderation.test.mjs`
Expected: FAIL mit `Cannot find module '…/web/js/moderation.js'`.

- [ ] **Step 3: `web/js/moderation.js` schreiben**

```js
/*
 * moderation.js — die Logik hinter dem Bereich „Rezensionen“ der Kasse, ohne DOM.
 * So lässt sie sich mit `node --test` prüfen, und pos.html kümmert sich nur um
 * die Darstellung.
 */

/** Die sechs Fragen an Jev: Spalte in v_moderation und Name für die Balken. */
export const FRAGEN = [
  ['p_gesundheitsrisiko', 'Gesundheitsrisiko'],
  ['p_beleidigung', 'Beleidigung'],
  ['p_personenbezug', 'Personenbezug'],
  ['p_werbung', 'Werbung'],
  ['p_anweisung', 'Anweisung'],
  ['p_themenbezug', 'Themenbezug'],
];

/** Was ein Grund bedeutet, in einem Satz für die Moderation. */
export const GRUND_ERKLAERUNG = {
  'Kontaktdaten oder Link': 'Der Text enthält eine E-Mail-Adresse, Telefonnummer oder einen Link.',
  'Gesundheitsrisiko': 'Der Text beschreibt eine mögliche Gefahr durch Essen oder Getränke; ein QS-Fall ist angelegt.',
  'Beleidigung': 'Jev hält eine Beleidigung oder Drohung für wahrscheinlich.',
  'Personenbezug': 'Jev hält es für wahrscheinlich, dass eine Person erkennbar ist.',
  'Werbung': 'Jev hält Werbung oder eine Aufforderung zur Kontaktaufnahme für wahrscheinlich.',
  'Anweisung': 'Der Text versucht wahrscheinlich, die Prüfung zu steuern.',
  'unsicher': 'Jev ist sich nicht sicher, oder der Text passt nicht zu BurgerMetrics.',
  'Prüfung nicht möglich': 'Jev war dreimal nicht erreichbar.',
  'Tageslimit erreicht': 'Das Tageslimit für Anfragen an Jev war erreicht.',
};

/** Ein Grund mit seiner Erklärung; unbekannte Gründe bleiben, wie sie sind. */
export function grundText(grund) {
  return GRUND_ERKLAERUNG[grund] ? `${grund}: ${GRUND_ERKLAERUNG[grund]}` : String(grund);
}

/** Das höchste Risiko einer Zeile: Gesundheit, Verstöße und fehlender Themenbezug; ohne Prüfung 0. */
export function risikoWert(zeile) {
  if (zeile.p_themenbezug === null || zeile.p_themenbezug === undefined) return 0;
  const werte = [zeile.p_gesundheitsrisiko, zeile.p_beleidigung, zeile.p_personenbezug,
                 zeile.p_werbung, zeile.p_anweisung].map(w => Number(w) || 0);
  werte.push(1 - Number(zeile.p_themenbezug));
  return Math.max(...werte);
}

/** QS-Fälle zuerst, dann höchstes Risiko, bei gleichem Risiko die ältere Rezension zuerst. */
export function nachRisiko(zeilen) {
  return [...zeilen].sort((a, b) => {
    if (Boolean(a.qs_fall) !== Boolean(b.qs_fall)) return a.qs_fall ? -1 : 1;
    if (risikoWert(a) !== risikoWert(b)) return risikoWert(b) - risikoWert(a);
    return Date.parse(a.erstellt_am) - Date.parse(b.erstellt_am);
  });
}

/** Die sechs Wahrscheinlichkeiten in ganzen Prozent; ohne Prüfung keine. */
export function balken(zeile) {
  if (zeile.p_themenbezug === null || zeile.p_themenbezug === undefined) return [];
  return FRAGEN.map(([feld, name]) => ({ name, prozent: Math.round((Number(zeile[feld]) || 0) * 100) }));
}

/** Die Statuszeile aus v_pruefdienst_stand; warnt, wenn eine Rezension fünf Minuten oder länger wartet. */
export function standText(stand) {
  if (!stand) return { text: 'Stand des Prüfdienstes unbekannt.', warnung: true };
  const text = `${stand.offen} offen · ${stand.zurueckgehalten} zurückgehalten · ${stand.qs_offen} QS-Fälle`;
  const minuten = Number(stand.aelteste_offene_min) || 0;
  if (stand.offen > 0 && minuten >= 5) {
    return { text: `${text} · Die älteste offene Rezension wartet seit ${minuten} Minuten; läuft der Prüfdienst?`,
             warnung: true };
  }
  return { text, warnung: false };
}

/** Zahl am Knopf: zurückgehaltene Rezensionen plus offene QS-Fälle. */
export function zahlAmKnopf(stand) {
  if (!stand) return 0;
  return (Number(stand.zurueckgehalten) || 0) + (Number(stand.qs_offen) || 0);
}

/** Gilt eine gespeicherte Anmeldung noch? */
export function sitzungGueltig(sitzung, jetzt = Date.now()) {
  return Boolean(sitzung && sitzung.token && jetzt < Number(sitzung.gueltigBis));
}

/** Tag, Monat und Uhrzeit in Berlin: „01.10., 14:05“. */
export function zeitText(iso) {
  if (!iso) return '';
  return new Date(iso).toLocaleString('de-DE', { timeZone: 'Europe/Berlin', day: '2-digit',
                                                 month: '2-digit', hour: '2-digit', minute: '2-digit' });
}
```

- [ ] **Step 4: Tests laufen lassen**

Run: `node --test web/tests/moderation.test.mjs`
Expected: `7` bestanden. Liefert Node für `zeitText` ein anderes Trennzeichen als `01.10., 14:05` (ICU-Version), den erwarteten Wert im Test an die tatsächliche Ausgabe von `toLocaleString` anpassen, nicht die Funktion.

- [ ] **Step 5: Commit**

```bash
git -c core.fileMode=false add web/js/moderation.js web/tests/moderation.test.mjs
git commit -m "Freigabe E: Logik der Moderation ohne DOM" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Knopf, Modal und Darstellung in `pos.html`

**Files:**
- Modify: `web/pos.html`

**Interfaces:**
- Consumes: `openModal(id)`, `closeAllModals()` aus dem klassischen Block; aus Task 1 die Methoden der Datenquelle; aus Task 2 `nachRisiko`, `balken`, `grundText`, `standText`, `zahlAmKnopf`, `sitzungGueltig`, `zeitText`.
- Produces: globale Funktionen `rezensionenOeffnen()`, `rezensionenAnmelden(ereignis)`, `rezensionenAbmelden()`; Modul-Funktion `moderationEinrichten(quelle)`.

- [ ] **Step 1: CSS anfügen**

Vor `</style>` (Ende des Stilblocks, Zeile 840 im Stand `dec4521`) einfügen:

```css
/* === REZENSIONEN (Moderation) === */
.header-rezensionen{gap:8px;cursor:pointer;font-family:inherit}
.rz-zahl{background:var(--red);color:#fff;border-radius:10px;font-size:12px;font-weight:800;padding:1px 7px;line-height:18px}
.rz-zahl[hidden]{display:none}
.rz-modal{width:760px}
.rz-kopf-rechts{display:flex;align-items:center;gap:10px}
.rz-konto{font-size:12px;color:var(--text-light)}
.rz-abmelden{background:none;border:1px solid var(--border);border-radius:6px;padding:6px 10px;font-size:12px;cursor:pointer;color:var(--text);min-height:32px}
.rz-abmelden[hidden]{display:none}
.rz-anmeldung{display:grid;gap:8px;max-width:360px}
.rz-anmeldung[hidden]{display:none}
.rz-anmeldung p{font-size:13px;color:var(--text-light)}
.rz-anmeldung label{font-size:12px;font-weight:700;color:var(--text-light)}
.rz-anmeldung input,.rz-aktionen input{padding:10px 12px;border:1px solid var(--border);border-radius:var(--radius);font-size:14px;min-height:44px}
.rz-knopf-primaer{background:var(--green);color:#fff;border:none;border-radius:var(--radius);padding:10px 16px;font-weight:700;cursor:pointer;min-height:44px}
.rz-knopf-warnung{background:#fff;color:var(--red);border:1.5px solid var(--red);border-radius:var(--radius);padding:10px 16px;font-weight:700;cursor:pointer;min-height:44px}
.rz-knopf-primaer:disabled,.rz-knopf-warnung:disabled{opacity:.5;cursor:not-allowed}
.rz-meldung{font-size:13px;color:var(--red);min-height:1.2em}
.rz-stand{font-size:13px;color:var(--text-light);margin-bottom:4px}
.rz-stand.warnung{color:var(--red);font-weight:700}
#rezensionenModal h4{font-size:13px;font-weight:700;color:var(--text-light);text-transform:uppercase;letter-spacing:.5px;margin:16px 0 8px}
.rz-liste{list-style:none;padding:0;margin:0;display:grid;gap:10px}
.rz-eintrag{border:1px solid var(--border);border-radius:10px;padding:12px}
.rz-eintrag.rz-qs{border-left:4px solid var(--red)}
.rz-kopf{font-size:12px;color:var(--text-light);margin-bottom:4px}
.rz-text{font-size:14px;color:var(--dark);margin-bottom:8px;word-break:break-word}
.rz-gruende{margin:0 0 8px 18px;font-size:12px;color:var(--text)}
.rz-balken{display:grid;grid-template-columns:9em 1fr 3.5em;gap:4px 8px;align-items:center;font-size:12px;color:var(--text-light);margin-bottom:8px}
.rz-spur{height:6px;background:#e5e7eb;border-radius:3px;overflow:hidden}
.rz-spur span{display:block;height:100%;background:var(--dark)}
.rz-aktionen{display:flex;gap:8px;flex-wrap:wrap}
.rz-aktionen input{flex:1;min-width:160px}
.rz-klein li{font-size:12px;color:var(--text-light);padding:4px 0;border-bottom:1px solid #f3f4f6}
.rz-leer{font-size:13px;color:var(--text-light)}
.rz-ohne-rolle{font-size:14px;color:var(--text)}
@media (max-width: 599px){.rz-balken{grid-template-columns:7.5em 1fr 3em}}
```

- [ ] **Step 2: Knopf in der Kopfleiste**

Vor der Zeile `<a href="dashboard.html" class="header-dash" aria-label="Dashboard"><span class="dash-text">Dashboard</span></a>` einfügen:

```html
    <button type="button" class="header-dash header-rezensionen" id="rzKnopf" onclick="rezensionenOeffnen()" aria-label="Rezensionen prüfen">
      <i class="fa-solid fa-comments" aria-hidden="true"></i><span class="dash-text">Rezensionen</span><span class="rz-zahl" id="rzZahl" hidden></span>
    </button>
```

- [ ] **Step 3: Modal-Markup**

Nach dem Block `<!-- Extras Modal -->` (nach dessen schließendem `</div>`, vor `<script>`) einfügen:

```html
<!-- Rezensionen: Moderation und Qualitätssicherung -->
<div class="modal-overlay" id="rezensionenModal">
  <div class="modal rz-modal" role="dialog" aria-modal="true" aria-labelledby="rzTitel">
    <div class="modal-header">
      <h3 id="rzTitel">Rezensionen</h3>
      <div class="rz-kopf-rechts">
        <span class="rz-konto" id="rzKonto"></span>
        <button type="button" class="rz-abmelden" id="rzAbmelden" onclick="rezensionenAbmelden()" hidden>Abmelden</button>
        <button class="modal-close" onclick="closeAllModals()" aria-label="Schließen">✕</button>
      </div>
    </div>
    <div class="modal-body">
      <form id="rzAnmeldung" class="rz-anmeldung" onsubmit="rezensionenAnmelden(event)" hidden>
        <p>Anmeldung mit dem Supabase-Konto. Ohne die Rolle moderation oder qualitaet bleibt der Bereich leer.</p>
        <label for="rzEmail">E-Mail</label>
        <input id="rzEmail" type="email" autocomplete="username" required>
        <label for="rzPasswort">Passwort</label>
        <input id="rzPasswort" type="password" autocomplete="current-password" required>
        <button type="submit" class="rz-knopf-primaer">Anmelden</button>
        <p class="rz-meldung" id="rzAnmeldeMeldung" role="alert"></p>
      </form>
      <p class="rz-ohne-rolle" id="rzOhneRolle" hidden>Dieses Konto hat keine Rolle für die Moderation.</p>
      <div id="rzArbeit" hidden>
        <p class="rz-stand" id="rzStand"></p>
        <section id="rzQsBlock" hidden>
          <h4>Gesundheitsrisiken</h4>
          <ul class="rz-liste" id="rzQsListe"></ul>
        </section>
        <section id="rzModBlock" hidden>
          <h4>Zurückgehalten</h4>
          <ul class="rz-liste" id="rzModListe"></ul>
        </section>
        <section id="rzEntschiedenBlock" hidden>
          <h4>Zuletzt entschieden</h4>
          <ul class="rz-liste rz-klein" id="rzEntschiedenListe"></ul>
        </section>
        <p class="rz-meldung" id="rzMeldung" role="status"></p>
      </div>
    </div>
  </div>
</div>
```

Das Markup steht vor dem klassischen Skriptblock; dessen Bindung „Close modals on overlay click“ erfasst das neue Modal damit.

- [ ] **Step 4: Modulblock: Importe, Einrichtung, Aufruf**

Im `<script type="module">` die drei Importzeilen ersetzen durch:

```js
import { QUELLE } from './js/konfiguration.js?v=20261005';
import { waehleQuelle } from './js/datenquelle.js?v=20261005';
import { bildVon, bildUrl, SCHNELLWAHL } from './js/darstellung.js?v=20261005';
import { nachRisiko, balken, grundText, standText, zahlAmKnopf, sitzungGueltig,
         zeitText } from './js/moderation.js?v=20261005';
```

Vor der Zeile `const schirm = document.createElement('div');` einfügen:

```js
// ===== REZENSIONEN: Moderation und Qualitätssicherung =====
// Die Kasse bleibt ohne Anmeldung; nur dieser Bereich braucht ein Supabase-Konto
// mit der Rolle moderation oder qualitaet. Das Token lebt nur in diesem Tab.
// Rezensionstext, Gründe und Bemerkungen nur per textContent.
const ANMELDUNG = 'bm-pos-anmeldung';

function moderationEinrichten(quelle) {
  // Stellt eine Anmeldung aus diesem Tab wieder her, solange sie gilt.
  let konto = '';
  try {
    const gespeichert = JSON.parse(sessionStorage.getItem(ANMELDUNG) || 'null');
    if (sitzungGueltig(gespeichert) && quelle.sitzungUebernehmen(gespeichert)) konto = gespeichert.email || '';
  } catch (_) { /* ohne sessionStorage bleibt der Bereich abgemeldet */ }

  // Zeigt genau einen der drei Zustände: anmeldung, ohneRolle, arbeit.
  function zeigen(zustand) {
    document.getElementById('rzAnmeldung').hidden = zustand !== 'anmeldung';
    document.getElementById('rzOhneRolle').hidden = zustand !== 'ohneRolle';
    document.getElementById('rzArbeit').hidden = zustand !== 'arbeit';
    document.getElementById('rzAbmelden').hidden = zustand === 'anmeldung';
    document.getElementById('rzKonto').textContent = zustand === 'anmeldung' ? '' : konto;
  }

  // Schreibt eine Meldung in das Feld mit dieser ID.
  function melden(id, text) {
    document.getElementById(id).textContent = text;
  }

  // Zahl am Knopf aus v_pruefdienst_stand, auch ohne Anmeldung.
  async function zahlAktualisieren() {
    try {
      const stand = await quelle.pruefdienstStand();
      const zahl = zahlAmKnopf(stand);
      const feld = document.getElementById('rzZahl');
      feld.textContent = String(zahl);
      feld.hidden = zahl === 0;
      return stand;
    } catch (fehler) {
      console.warn('Stand des Prüfdienstes:', fehler);
      return null;
    }
  }

  // Abgelaufene Anmeldung: zurück zum Formular, mit Hinweis; true, wenn es das war.
  function abgelaufen(fehler) {
    if (!/abgelaufen/.test(fehler.message)) return false;
    try { sessionStorage.removeItem(ANMELDUNG); } catch (_) { /* nichts gespeichert */ }
    zeigen('anmeldung');
    melden('rzAnmeldeMeldung', fehler.message);
    return true;
  }

  // Lädt Rollen, Stand, QS-Fälle, zurückgehaltene und zuletzt entschiedene Rezensionen.
  async function laden() {
    if (!quelle.angemeldet()) { zeigen('anmeldung'); return; }
    try {
      const rollen = await quelle.meineRollen();
      if (!rollen.length) { zeigen('ohneRolle'); return; }
      zeigen('arbeit');
      const hinweis = standText(await zahlAktualisieren());
      const zeile = document.getElementById('rzStand');
      zeile.textContent = hinweis.text;
      zeile.classList.toggle('warnung', hinweis.warnung);
      const moderation = rollen.includes('moderation');
      const qualitaet = rollen.includes('qualitaet');
      qsAnzeigen(qualitaet ? await quelle.qsFaelle() : [], qualitaet);
      moderationAnzeigen(moderation ? nachRisiko(await quelle.moderationListe()) : [], moderation);
      entschiedenAnzeigen(moderation ? await quelle.entscheidungenLetzte() : [], moderation);
    } catch (fehler) {
      if (!abgelaufen(fehler)) melden('rzMeldung', fehler.message);
    }
  }

  // Ein Absatz mit Klasse; der Inhalt nur als textContent.
  function absatz(klasse, text) {
    const p = document.createElement('p');
    p.className = klasse;
    p.textContent = text;
    return p;
  }

  // Bemerkungsfeld und Knöpfe unter einem Eintrag; jeder Knopf bekommt die Bemerkung.
  function aktionen(knoepfe) {
    const zeile = document.createElement('div');
    zeile.className = 'rz-aktionen';
    const bemerkung = document.createElement('input');
    bemerkung.type = 'text';
    bemerkung.maxLength = 500;
    bemerkung.placeholder = 'Bemerkung (optional)';
    bemerkung.setAttribute('aria-label', 'Bemerkung');
    zeile.appendChild(bemerkung);
    for (const [text, klasse, aktion] of knoepfe) {
      const knopf = document.createElement('button');
      knopf.type = 'button';
      knopf.className = klasse;
      knopf.textContent = text;
      knopf.onclick = () => ausfuehren(zeile, () => aktion(bemerkung.value.trim()));
      zeile.appendChild(knopf);
    }
    return zeile;
  }

  // Sperrt alle Knöpfe eines Eintrags, führt die Entscheidung aus und lädt danach neu.
  async function ausfuehren(zeile, aktion) {
    const knoepfe = zeile.querySelectorAll('button');
    knoepfe.forEach(k => { k.disabled = true; });
    try {
      await aktion();
      melden('rzMeldung', '');
      await laden();
    } catch (fehler) {
      if (!abgelaufen(fehler)) melden('rzMeldung', fehler.message);
      knoepfe.forEach(k => { k.disabled = false; });
    }
  }

  // Block „Gesundheitsrisiken“: Fall, Produkt, Filiale, Zeit, Text, Erledigt.
  function qsAnzeigen(zeilen, sichtbar) {
    const liste = document.getElementById('rzQsListe');
    liste.textContent = '';
    document.getElementById('rzQsBlock').hidden = !sichtbar;
    if (!zeilen.length) { liste.appendChild(absatz('rz-leer', 'Keine offenen QS-Fälle.')); return; }
    for (const z of zeilen) {
      const li = document.createElement('li');
      li.className = 'rz-eintrag rz-qs';
      li.appendChild(absatz('rz-kopf',
        `QS-Fall ${z.qs_fall_id} · ${z.artikel} · ${z.filiale || 'ohne Filiale'} · ${zeitText(z.erstellt_am)}`));
      li.appendChild(absatz('rz-text', z.inhalt));
      li.appendChild(aktionen([['Erledigt', 'rz-knopf-primaer', b => quelle.qsFallErledigen(z.qs_fall_id, b)]]));
      liste.appendChild(li);
    }
  }

  // Block „Zurückgehalten“: Gründe mit Erklärung, Balken, Freigeben und Ablehnen.
  function moderationAnzeigen(zeilen, sichtbar) {
    const liste = document.getElementById('rzModListe');
    liste.textContent = '';
    document.getElementById('rzModBlock').hidden = !sichtbar;
    if (!zeilen.length) { liste.appendChild(absatz('rz-leer', 'Nichts zurückgehalten.')); return; }
    for (const z of zeilen) {
      const li = document.createElement('li');
      li.className = 'rz-eintrag' + (z.qs_fall ? ' rz-qs' : '');
      const wartet = z.status === 'offen' ? ' · wartet noch auf den Prüfdienst' : '';
      li.appendChild(absatz('rz-kopf',
        `#${z.rezension_id} · ${'★'.repeat(z.sterne)} · ${z.artikel} · ${zeitText(z.erstellt_am)}${wartet}`));
      li.appendChild(absatz('rz-text', z.inhalt));
      const gruende = document.createElement('ul');
      gruende.className = 'rz-gruende';
      for (const grund of z.gruende || []) {
        const eintrag = document.createElement('li');
        eintrag.textContent = grundText(grund);
        gruende.appendChild(eintrag);
      }
      li.appendChild(gruende);
      li.appendChild(balkenAnzeigen(z));
      li.appendChild(aktionen([
        ['Freigeben', 'rz-knopf-primaer', b => quelle.rezensionFreigeben(z.rezension_id, b)],
        ['Ablehnen', 'rz-knopf-warnung', b => quelle.rezensionAblehnen(z.rezension_id, b)],
      ]));
      liste.appendChild(li);
    }
  }

  // Sechs schmale Balken mit Prozentwert; ohne Prüfung bleibt der Rahmen leer.
  function balkenAnzeigen(zeile) {
    const rahmen = document.createElement('div');
    rahmen.className = 'rz-balken';
    for (const b of balken(zeile)) {
      const name = document.createElement('span');
      name.textContent = b.name;
      const spur = document.createElement('span');
      spur.className = 'rz-spur';
      const fuellung = document.createElement('span');
      fuellung.style.width = `${b.prozent}%`;
      spur.appendChild(fuellung);
      const wert = document.createElement('span');
      wert.textContent = `${b.prozent} %`;
      rahmen.append(name, spur, wert);
    }
    return rahmen;
  }

  // Liste „Zuletzt entschieden“, nur lesend.
  function entschiedenAnzeigen(zeilen, sichtbar) {
    const liste = document.getElementById('rzEntschiedenListe');
    liste.textContent = '';
    document.getElementById('rzEntschiedenBlock').hidden = !sichtbar || !zeilen.length;
    for (const z of zeilen) {
      const li = document.createElement('li');
      li.textContent = `${zeitText(z.entschieden_am)} · #${z.rezension_id} ${z.entscheidung} · ${z.artikel}`
        + (z.bemerkung ? ` · ${z.bemerkung}` : '');
      liste.appendChild(li);
    }
  }

  window.rezensionenOeffnen = () => {
    openModal('rezensionenModal');
    laden();
  };

  window.rezensionenAnmelden = async (ereignis) => {
    ereignis.preventDefault();
    melden('rzAnmeldeMeldung', '');
    const email = document.getElementById('rzEmail').value.trim();
    const passwortFeld = document.getElementById('rzPasswort');
    try {
      const sitzung = await quelle.anmelden(email, passwortFeld.value);
      konto = email;
      try { sessionStorage.setItem(ANMELDUNG, JSON.stringify({ ...sitzung, email })); } catch (_) { /* nur dieser Aufruf */ }
      await laden();
    } catch (fehler) {
      melden('rzAnmeldeMeldung', fehler.message);
    } finally {
      passwortFeld.value = '';
    }
  };

  window.rezensionenAbmelden = async () => {
    await quelle.abmelden();
    try { sessionStorage.removeItem(ANMELDUNG); } catch (_) { /* nichts gespeichert */ }
    konto = '';
    zeigen('anmeldung');
  };

  zahlAktualisieren();
  setInterval(zahlAktualisieren, 60000);
}
```

Nach der Zeile `window.kasseStarten(artikel);` im `try`-Block einfügen:

```js
  moderationEinrichten(quelle);
```

- [ ] **Step 5: Syntax und Tests prüfen**

Run: `python3 web/tests/skripte_pruefen.py web/pos.html && node --test "web/tests/*.test.mjs"`
Expected: `web/pos.html: 0 Block(e) mit Syntaxfehler`, alle Tests bestanden.

- [ ] **Step 6: Commit**

```bash
git -c core.fileMode=false add web/pos.html
git commit -m "Freigabe E: Bereich Rezensionen im POS mit Anmeldung, QS-Fällen und Moderation" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Rollen für Roberts Konto

**Files:** keine Änderungen im Repo.

**Interfaces:**
- Consumes: `velocity.mitarbeiter` (Spalten `vorname`, `nachname`, `auth_uid`); `wawi_intern.mitarbeiter_rolle`.
- Produces: Roberts Konto mit den Rollen `moderation` und `qualitaet`.

- [ ] **Step 1: Konto finden, ohne ID oder E-Mail auszugeben**

```bash
python3 - <<'PY'
import sys
sys.path.insert(0, "db")
from skript_ausfuehren import verbinde
con = verbinde(); cur = con.cursor()
cur.execute("""SELECT m.vorname, m.nachname, m.personalnummer, m.auth_uid IS NOT NULL
               FROM velocity.mitarbeiter m WHERE m.nachname = 'Butscher'""")
print(cur.fetchall())
con.close()
PY
```

Expected: eine Zeile mit Vorname, Nachname, Personalnummer und `True`.

- [ ] **Step 2: Robert fragen**

Im Chat: „Für die Moderation im POS würde ich die Rollen moderation und qualitaet an dein Konto aus der VeloCity-WaWi hängen (Mitarbeiter <Vorname> Butscher, Personalnummer <Nummer>). Passt das?“ Erst nach einem klaren Ja weiter.

- [ ] **Step 3: Rollen vergeben**

```bash
python3 - <<'PY'
import sys
sys.path.insert(0, "db")
from skript_ausfuehren import verbinde
con = verbinde(); cur = con.cursor()
cur.execute("""INSERT INTO wawi_intern.mitarbeiter_rolle (konto, rolle)
               SELECT m.auth_uid, r.rolle
               FROM   velocity.mitarbeiter m
               CROSS  JOIN (VALUES ('moderation'), ('qualitaet')) AS r(rolle)
               WHERE  m.nachname = 'Butscher' AND m.auth_uid IS NOT NULL
               ON CONFLICT DO NOTHING""")
print("neu vergeben:", cur.rowcount)
cur.execute("SELECT rolle FROM wawi_intern.mitarbeiter_rolle ORDER BY rolle")
print([z[0] for z in cur.fetchall()])
con.commit(); con.close()
PY
```

Expected: `neu vergeben: 2`, `['moderation', 'qualitaet']`.

---

### Task 5: Gemeinsame Abnahme im eingebauten Browser

**Files:** keine Änderungen im Repo.

**Interfaces:**
- Consumes: POS lokal ausgeliefert; laufender Prüfdienst; Roberts Anmeldung.
- Produces: geprüfte Abnahmekriterien 3, 4 und 9; aufgeräumte Testrezensionen.

- [ ] **Step 1: POS lokal ausliefern und im eingebauten Browser öffnen**

In `.claude/launch.json` des Arbeitsverzeichnisses der Sitzung (anlegen, falls es fehlt) eine Konfiguration eintragen:

```json
{
  "version": "0.0.1",
  "configurations": [
    {
      "name": "bm-web",
      "runtimeExecutable": "python3",
      "runtimeArgs": ["-m", "http.server", "8765", "--directory",
                      "/Users/robert/Library/CloudStorage/OneDrive-Persönlich/Vorlesungen/Datenbasierte Fallstudien/BurgerMetrics/BurgerMetrics_Website/web"],
      "port": 8765
    }
  ]
}
```

Dann `preview_start` mit `name: "bm-web"` und danach `navigate` auf `http://localhost:8765/pos.html`. Mit `tabs_context` prüfen, dass der Browserbereich sichtbar ist; sonst Robert bitten, ihn mit Cmd+Shift+B einzublenden.

- [ ] **Step 2: Kopfleiste ohne Anmeldung**

Per `read_page`/`find`: Der Knopf „Rezensionen“ steht vor „Dashboard“; der Zähler zeigt die Zahl aus `v_pruefdienst_stand` oder ist verborgen, wenn sie 0 ist. Die Kasse funktioniert wie vorher (einen Artikel antippen, Bestellung erscheint; nicht bezahlen).

Mit `resize_window` 768 × 1024 und 375 × 812 prüfen: Der Knopf ist sichtbar und anklickbar (unter 400 px nur Symbol und Zähler). Danach `resize_window` mit `preset: "desktop"`.

- [ ] **Step 3: Testrezensionen anlegen und prüfen lassen**

Mit dem Skript aus Plan D, Task 5, Step 1 drei Rezensionen mit der Sitzung `abnahme-e` anlegen, IDs in `$ABNAHME` (Scratchpad) ablegen: `personenbezug` („Abnahme E: Kassiererin Anna am Hauptbahnhof war super freundlich.“), `werbung` („Abnahme E: Bessere Burger gibt es auf burgerblog.de“), `gesundheit` („Abnahme E: Im Salat war ein Stück Plastik.“). Keine Beleidigung: Die freigegebene Rezension steht danach kurz öffentlich im Shop. 60 Sekunden warten (Monitor); alle drei sind `zurueckgehalten`, die dritte mit QS-Fall.

- [ ] **Step 4: Robert meldet sich an**

Im Chat: „Bitte öffne im Browserbereich rechts oben ‚Rezensionen‘ und melde dich mit deinem Konto aus der VeloCity-WaWi an. Ich gebe nichts ein.“ Warten, bis Robert „angemeldet“ meldet. Danach per `read_page` prüfen: Statuszeile, Block „Gesundheitsrisiken“ mit dem Plastik-Fall, Block „Zurückgehalten“ mit allen drei (QS-Fall zuoberst, Gründe mit Erklärung, sechs Balken), „Zuletzt entschieden“ verborgen oder mit älteren Einträgen.

- [ ] **Step 5: Freigeben, Ablehnen, Erledigen, Doppelklick, Escape**

Im Browserbereich (Claude klickt, Robert sieht zu):

1. **Escape:** In das Bemerkungsfeld der Werbung „Abnahme“ tippen, Escape drücken: Fenster bleibt offen, Text bleibt stehen.
2. **Ablehnen:** Bei der Werbung „Ablehnen“. Der Eintrag verschwindet aus „Zurückgehalten“ und erscheint unter „Zuletzt entschieden“ mit „abgelehnt · … · Abnahme“.
3. **Doppelklick:** Beim Personenbezug zweimal schnell auf „Freigeben“ (`computer` mit `double_click`). Genau eine Entscheidung, keine Fehlermeldung „schon entschieden“ im Meldungsfeld.
4. **Erledigen:** Beim QS-Fall „Erledigt“. Der Block „Gesundheitsrisiken“ zeigt „Keine offenen QS-Fälle.“; die Rezension selbst bleibt unter „Zurückgehalten“, weil nur die Moderation über sie entscheidet.
5. Stand in der Datenbank lesen (als `postgres`, wie Plan D, Task 5, Step 2): `werbung` `abgelehnt`, `personenbezug` `freigegeben`, `gesundheit` `zurueckgehalten`, QS-Fall mit `erledigt_am`; `wawi_intern.rezension_entscheidung` hat genau eine Zeile je entschiedener Rezension.
6. Im Shop (`https://swrobuts.github.io/BurgerMetrics/shop.html`, Classic Burger, Leseansicht) steht der freigegebene Text „Abnahme E: Kassiererin Anna …“, die beiden anderen nicht. Die Freigabe durch einen Menschen wirkt also sofort. Den Text danach gleich aufräumen (Step 7).

- [ ] **Step 6: Nur qualitaet, dann ohne Rolle**

Roberts Rolle `moderation` kurz entziehen (`DELETE FROM wawi_intern.mitarbeiter_rolle WHERE rolle = 'moderation' AND konto = (SELECT auth_uid FROM velocity.mitarbeiter WHERE nachname = 'Butscher')`), Bereich neu öffnen: nur der Block „Gesundheitsrisiken“ ist sichtbar. Dann auch `qualitaet` entziehen: „Dieses Konto hat keine Rolle für die Moderation.“ Beide Rollen wieder vergeben (Task 4, Step 3) und prüfen: Arbeitsbereich wieder da.

- [ ] **Step 7: Abmelden und aufräumen**

„Abmelden“ klicken: Formular erscheint, `sessionStorage` enthält keinen Eintrag `bm-pos-anmeldung` (per `javascript_tool` prüfen: `sessionStorage.getItem('bm-pos-anmeldung') === null`). Testrezensionen mit dem Aufräumskript aus Plan D, Task 5, Step 7 löschen (`gelöscht: 3 von 3`). Den Vorschau-Server mit `preview_stop` beenden.

---

### Task 6: Doku und PR

**Files:**
- Modify: `docs/05-anwendungen.md`

- [ ] **Step 1: Absatz in Abschnitt 5.4**

Am Ende von Abschnitt „## 5.4 POS-Terminal“ (vor der Zeile `## 5.5 Online-Shop`) einfügen:

```markdown
**Rezensionen.** Der Knopf „Rezensionen“ in der Kopfleiste zeigt, wie viele Rezensionen zurückgehalten sind und wie viele QS-Fälle offen sind (`v_pruefdienst_stand`, ohne Anmeldung). Der Bereich dahinter braucht ein Supabase-Konto mit der Rolle `moderation` oder `qualitaet` (`wawi_intern.mitarbeiter_rolle`); die Anmeldung geht an den Anmeldedienst von Supabase, das Token lebt im `sessionStorage` des Tabs und gilt eine Stunde. Die Moderation sieht die zurückgehaltenen Rezensionen mit Gründen und Jevs Wahrscheinlichkeiten und entscheidet über `api_rezension_freigeben()` und `api_rezension_ablehnen()`; die Qualitätssicherung schließt Hinweise auf Gesundheitsrisiken mit `api_qs_fall_erledigen()`. Wartet eine offene Rezension länger als fünf Minuten, warnt die Statuszeile, dass der Prüfdienst womöglich steht. Die Logik steht in `web/js/moderation.js`; Kasse und Manager-PIN sind davon unberührt.
```

- [ ] **Step 2: Tests, Commit, Push, PR**

```bash
node --test "web/tests/*.test.mjs" && python3 web/tests/skripte_pruefen.py web/pos.html && python3 web/tests/skripte_pruefen.py
```

Expected: alle Tests bestanden, beide Seiten `0 Block(e) mit Syntaxfehler`.

```bash
git -c core.fileMode=false add docs/05-anwendungen.md
git commit -m "Freigabe E: Doku des Bereichs Rezensionen im POS" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
git push origin bm-analyse
gh pr create --repo swrobuts/BurgerMetrics --base main --head bm-analyse \
  --title "Freigabe E: Moderation der Rezensionen im POS" \
  --body "$(cat <<'EOF'
Phase E der Spezifikation docs/superpowers/specs/2026-09-30-rezensionen-jev-freigabe-design.md.

- Knopf „Rezensionen“ mit Zähler in der Kopfleiste der Kasse; Kasse und Manager-PIN unverändert
- Anmeldung über den Anmeldedienst von Supabase, Token im sessionStorage, Abmelden, Hinweis bei Ablauf
- QS-Fälle erledigen, zurückgehaltene Rezensionen mit Gründen und Balken freigeben oder ablehnen, zuletzt entschieden
- Rollen moderation und qualitaet für Roberts Konto über die Konto-ID (nicht im Repo)
- gemeinsame Abnahme im Browser, Testrezensionen gelöscht; node --test und skripte_pruefen.py grün

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

Den PR mit `get_status` prüfen und gegebenenfalls mit `bind_pr` binden. Robert um die Zusage zum Merge bitten. Nach dem Merge `https://swrobuts.github.io/BurgerMetrics/pos.html` öffnen und prüfen, dass Knopf und Zähler erscheinen.
