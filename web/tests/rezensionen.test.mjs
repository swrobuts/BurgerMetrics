import { test } from 'node:test';
import assert from 'node:assert/strict';
import { bewertungText, pruefeEingabe, zaehlerText, datumText, nachArtikel,
         stimmenNachArtikel, datensatzZeilen, normalisiereText, SEITENGROESSE, sterneText,
         anzahlText, verteilung, anteilText, statusText, anzahlFuer,
         weitereLaden } from '../js/rezensionen.js';

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

test('normalisiereText, pruefeEingabe und zaehlerText zählen wie die Datenbank (Leerraumfolgen = ein Leerzeichen)', () => {
  assert.equal(normalisiereText('a          b'), 'a b');
  assert.equal(normalisiereText(' Zeile\n\n zwei \t drei '), 'Zeile zwei drei');
  assert.deepEqual(pruefeEingabe({ sterne: 3, inhalt: 'a          b' }), ['Der Text braucht mindestens 5 Zeichen.']);
  assert.deepEqual(pruefeEingabe({ sterne: 3, inhalt: 'abcde' + ' '.repeat(600) + 'fghij' }), []);
  assert.equal(zaehlerText('a          b'), '3 / 500');
});

test('Emoji zählen wie PostgreSQL als ein Zeichen statt zwei UTF-16-Einheiten', () => {
  assert.equal(zaehlerText('🍔'.repeat(5)), '5 / 500');
  assert.deepEqual(pruefeEingabe({ sterne: 4, inhalt: '🍔🍔🍔' }), ['Der Text braucht mindestens 5 Zeichen.']);
  assert.deepEqual(pruefeEingabe({ sterne: 4, inhalt: '🍔'.repeat(500) }), []);
  assert.deepEqual(pruefeEingabe({ sterne: 4, inhalt: '🍔'.repeat(501) }), ['Der Text darf höchstens 500 Zeichen haben.']);
});

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
