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
