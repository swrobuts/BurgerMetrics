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

test('letzteRezensionen: Status je Zeile, Text nur bei freigegebenen', async () => {
  const zeilen = await quelle.letzteRezensionen();
  assert.ok(Array.isArray(zeilen));
  for (const z of zeilen) {
    for (const feld of ['rezension_id', 'artikel', 'sterne', 'erstellt_am', 'im_warehouse', 'status']) {
      assert.ok(feld in z, `Feld ${feld} fehlt`);
    }
    assert.ok(['offen', 'freigegeben', 'zurueckgehalten', 'abgelehnt'].includes(z.status), `Status ${z.status}`);
    if (z.status !== 'freigegeben') assert.equal(z.inhalt, null);
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

// Ohne Anmeldung: dieselben Kopfzeilen wie der Shop, nur der öffentliche Schlüssel.
function kopf(art) {
  return {
    apikey: QUELLE.schluessel,
    Authorization: `Bearer ${QUELLE.schluessel}`,
    [art === 'GET' ? 'Accept-Profile' : 'Content-Profile']: 'wawi',
    'Content-Type': 'application/json',
  };
}

test('wawi.rezension zeigt ohne Anmeldung nur freigegebene Zeilen', async () => {
  const antwort = await fetch(`${QUELLE.url}/rest/v1/rezension?status=neq.freigegeben&select=rezension_id&limit=1`,
    { headers: kopf('GET') });
  assert.equal(antwort.status, 200);
  assert.deepEqual(await antwort.json(), []);
});

for (const [pfad, art, koerper] of [
  ['v_moderation?limit=1', 'GET', null],
  ['v_qs_faelle?limit=1', 'GET', null],
  ['v_freigabe_statistik?limit=1', 'GET', null],
  ['rpc/api_rezension_freigeben', 'POST', { rezension_id: 1 }],
  ['rpc/pruefung_offene_holen', 'POST', { p_anzahl: 1 }],
  ['rpc/pruefung_eintragen', 'POST', { rezension_id: 1, ergebnis: 'freigegeben' }],
]) {
  test(`ohne Anmeldung verschlossen: ${pfad}`, async () => {
    const antwort = await fetch(`${QUELLE.url}/rest/v1/${pfad}`, {
      method: art, headers: kopf(art), body: koerper ? JSON.stringify(koerper) : undefined });
    assert.ok([401, 403].includes(antwort.status), `HTTP ${antwort.status}`);
  });
}

test('pruefdienstStand ist ohne Anmeldung lesbar und ohne Text', async () => {
  const antwort = await fetch(`${QUELLE.url}/rest/v1/v_pruefdienst_stand`, { headers: kopf('GET') });
  assert.equal(antwort.status, 200);
  const [zeile] = await antwort.json();
  assert.deepEqual(Object.keys(zeile).sort(),
    ['aelteste_offene_min', 'letzte_pruefung', 'offen', 'qs_offen', 'zurueckgehalten']);
});
