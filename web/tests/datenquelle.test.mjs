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
