import { test } from 'node:test';
import assert from 'node:assert/strict';
import { PostgrestQuelle } from '../js/datenquelle.js';

const quelle = () => new PostgrestQuelle({ url: 'https://example.invalid', schluessel: 'test' });
const antwort = (daten, bereich) => new Response(JSON.stringify(daten), {
  headers: bereich ? { 'Content-Range': bereich } : {},
});

test('GET und RPC erhalten die JSON-Datentypen, auch bei numerischem Text', async t => {
  const zeile = { artikel_id: 1, name: '007', plz: '01067', inhalt: '12345',
    sitzung: '00001', sterne_mittel: 4.5, anzahl: 12, letzte: null };
  t.mock.method(globalThis, 'fetch', async () => antwort([zeile]));
  assert.deepEqual(await quelle().speisekarte(), [zeile]);
  assert.deepEqual(await quelle().rufe('probe', {}), [zeile]);
});

test('RPC darf auch null zurückgeben', async t => {
  t.mock.method(globalThis, 'fetch', async () => antwort(null));
  assert.equal(await quelle().rufe('probe', {}), null);
});

test('Wettertage werden auch bei kleinem Serverlimit vollständig geladen und gecacht', async t => {
  const daten = Array.from({ length: 5 }, (_, i) => ({ tag: `2025-01-0${i + 1}`, umsatz: i + 1 }));
  const offsets = [];
  t.mock.method(globalThis, 'fetch', async (url, optionen) => {
    const params = new URL(url).searchParams;
    assert.equal(params.get('order'), 'tag');
    const offset = Number(params.get('offset') || 0);
    offsets.push(offset);
    const seite = daten.slice(offset, offset + 2);
    return antwort(seite, `${offset}-${offset + seite.length - 1}/5`);
  });
  const q = quelle();
  assert.deepEqual(await q.wetterTage(), daten);
  assert.deepEqual(await q.wetterTage(), daten);
  assert.deepEqual(offsets, [0, 2, 4]);
});

test('Fehler auf einer Folgeseite speichern kein unvollständiges Ergebnis', async t => {
  let fehler = true;
  t.mock.method(globalThis, 'fetch', async url => {
    const offset = Number(new URL(url).searchParams.get('offset') || 0);
    if (offset && fehler) return new Response('ausgefallen', { status: 503 });
    return antwort([{ tag: `2025-01-0${offset + 1}` }], `${offset}-${offset}/2`);
  });
  const q = quelle();
  await assert.rejects(q.wetterTage(), /503/);
  fehler = false;
  assert.equal((await q.wetterTage()).length, 2);
});

test('Eine leere Wetter-Sicht liefert eine leere Liste', async t => {
  const mock = t.mock.method(globalThis, 'fetch', async () => antwort([], '*/0'));
  assert.deepEqual(await quelle().wetterTage(), []);
  assert.equal(mock.mock.callCount(), 1);
});

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
