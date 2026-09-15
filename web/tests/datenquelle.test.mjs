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
