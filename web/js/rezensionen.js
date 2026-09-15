/*
 * rezensionen.js — die Logik hinter Bewertungszeile und Rezensionsformular
 * des Shops, ohne DOM. So lässt sie sich mit `node --test` prüfen, und
 * shop.html kümmert sich nur um die Darstellung.
 */

/** Leerraum wie die Datenbank behandeln: Folgen zu einem Leerzeichen, Ränder weg —
 *  rezension_anlegen() misst genau diesen Text. */
export function normalisiereText(inhalt) {
  return String(inhalt ?? '').replace(/\s+/g, ' ').trim();
}

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
  const sterneZahl = Number(sterne);
  if (!Number.isInteger(sterneZahl) || sterneZahl < 1 || sterneZahl > 5) befunde.push('Bitte 1 bis 5 Sterne wählen.');
  const text = normalisiereText(inhalt);
  const laenge = [...text].length; // Unicode-Zeichen wie PostgreSQL char_length
  if (laenge < 5) befunde.push('Der Text braucht mindestens 5 Zeichen.');
  if (laenge > 500) befunde.push('Der Text darf höchstens 500 Zeichen haben.');
  return befunde;
}

/** Zähler unter dem Textfeld: „37 / 500" — gezählt wie die Datenbank: Leerraumfolgen als ein Zeichen, Ränder weg. */
export function zaehlerText(inhalt) {
  return `${[...normalisiereText(inhalt)].length} / 500`;
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
