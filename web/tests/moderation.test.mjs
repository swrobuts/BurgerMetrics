import { test } from 'node:test';
import assert from 'node:assert/strict';
import { FRAGEN, grundText, risikoWert, nachRisiko, balken, standText, zahlAmKnopf,
         sitzungGueltig, zeitText, fehlerText } from '../js/moderation.js';

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

test('fehlerText: ohne Funktionsname und HTTP-Code, Netzfehler auf Deutsch', () => {
  assert.equal(fehlerText(new Error('api_rezension_freigeben: HTTP 500 — über die Rezension 7 ist schon entschieden (freigegeben)')),
               'Über die Rezension 7 ist schon entschieden (freigegeben)');
  assert.equal(fehlerText(new TypeError('Failed to fetch')), 'Keine Verbindung zur Datenbank.');
  assert.equal(fehlerText(new TypeError('NetworkError when attempting to fetch resource.')), 'Keine Verbindung zur Datenbank.');
  assert.equal(fehlerText(new TypeError('Load failed')), 'Keine Verbindung zur Datenbank.');
  assert.equal(fehlerText(new Error('E-Mail oder Passwort stimmen nicht.')), 'E-Mail oder Passwort stimmen nicht.');
});
