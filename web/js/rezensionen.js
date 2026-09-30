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

/** Der gespeicherte Datensatz für die Datenperspektive — ohne inhalt: Besuchertext
 *  erscheint nur in Leseansicht und Kundenstimmen, und erst nach der Freigabe. */
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
    ['status', statusText(rezension.status)],
  ];
}

/** So viele Rezensionen holt die Leseansicht auf einmal. */
export const SEITENGROESSE = 10;

/** Sterne als Zeichen: 4 → „★★★★☆“. Werte außerhalb 0 bis 5 werden begrenzt. */
export function sterneText(sterne) {
  const zahl = Math.min(5, Math.max(0, Math.round(Number(sterne) || 0)));
  return '★'.repeat(zahl) + '☆'.repeat(5 - zahl);
}

/** Zahl der Bewertungen in Worten: „1 Bewertung“, „1.234 Bewertungen“. */
export function anzahlText(anzahl) {
  const zahl = Number(anzahl) || 0;
  if (!zahl) return 'noch keine Bewertung';
  return `${zahl.toLocaleString('de-DE')} ${zahl === 1 ? 'Bewertung' : 'Bewertungen'}`;
}

/** Verteilung der Sterne aus einer Zeile von v_rezension_produkt, 5 Sterne zuerst.
 *  anteil liegt zwischen 0 und 1 und ist 0, solange es keine Rezension gibt. */
export function verteilung(zeile) {
  const gesamt = Number(zeile?.anzahl) || 0;
  return [5, 4, 3, 2, 1].map(sterne => {
    const anzahl = Number(zeile?.[`anzahl_${sterne}`]) || 0;
    return { sterne, anzahl, anteil: gesamt ? anzahl / gesamt : 0 };
  });
}

/** Ein Anteil als ganze Prozent: 0,384 → „38 %“. */
export function anteilText(anteil) {
  return `${Math.round((Number(anteil) || 0) * 100)} %`;
}

/** Der Status einer Shop-Rezension in Worten, für den Datenmodus. */
export function statusText(status) {
  const worte = {
    offen: 'wird geprüft',
    freigegeben: 'veröffentlicht',
    zurueckgehalten: 'zurückgehalten, wartet auf die Moderation',
    abgelehnt: 'abgelehnt',
  };
  return worte[status] || 'unbekannt';
}

/** Wie viele freigegebene Rezensionen passen zum Filter? Ohne Filter alle. */
export function anzahlFuer(zeile, sterne) {
  if (!zeile) return 0;
  return Number(sterne ? zeile[`anzahl_${sterne}`] : zeile.anzahl) || 0;
}

/** Soll „Weitere laden“ erscheinen? Nur wenn der Stand mehr kennt und die
 *  letzte Seite voll war — sonst sind die Zahlen vom Laden der Seite veraltet. */
export function weitereLaden(geladen, gesamt, letzteSeite) {
  return geladen < gesamt && letzteSeite === SEITENGROESSE;
}

/** Name der Sternzeile für Screenreader: erst der sichtbare Text, dann was ein Klick tut. */
export function sternzeileName(zeile, produkt) {
  const sichtbar = bewertungText(zeile);
  return zeile && zeile.anzahl ? `${sichtbar} – Rezensionen zu ${produkt} lesen` : `${sichtbar} – ${produkt}`;
}
