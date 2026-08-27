/*
 * datenquelle.js — die Datenschnittstelle des Dashboards.
 *
 * Das Dashboard kennt AUSSCHLIESSLICH die Methoden dieses Moduls. Es kennt
 * keine Tabelle, keine Spalte, keinen Join und keine URL. Wer die Quelle
 * wechselt — auf MySQL, Snowflake, ein Lakehouse oder eine eigene API —,
 * schreibt eine neue Klasse mit denselben Methoden und traegt sie unten in
 * `waehleQuelle` ein. Am Dashboard aendert sich dabei keine Zeile.
 *
 * Der Vertrag ist absichtlich schmal: 33 benannte Fragen, jede liefert ein
 * Array von Objekten mit stabilen Feldnamen. Diese Namen sind die eigentliche
 * Schnittstelle — sie stehen serverseitig in db/aufbau/0005_semantik.sql.
 */

/** Basisklasse: beschreibt den Vertrag und dokumentiert jede Frage. */
export class Datenquelle {
  /** @returns {Promise<Array>} je Jahr: jahr, bestellungen, umsatz, aov, bruttoumsatz, rabatt */
  kennzahlenJahr() { throw new Error('nicht umgesetzt'); }
  /** @returns {Promise<Array>} je Monat: monat ('YYYY-MM'), bestellungen, umsatz */
  umsatzMonat() { throw new Error('nicht umgesetzt'); }
  /** je Filiale: branch_name, district, branch_type, size_sqm, opening_date,
   *  monthly_rent_eur, bestellungen, umsatz, aov, zufriedenheit, jahre */
  filialen() { throw new Error('nicht umgesetzt'); }
  /** je Produkt: product_name, category, subcategory, menge, positionsumsatz */
  produkte() { throw new Error('nicht umgesetzt'); }
  /** je Kategorie: category, menge, positionsumsatz */
  kategorien() { throw new Error('nicht umgesetzt'); }
  /** je Jahr: jahr, anteil_pct (vegetarisch/vegan innerhalb Kategorie Burger) */
  veggieAnteil() { throw new Error('nicht umgesetzt'); }
  /** je Jahr und Kanal: jahr, kanal, bestellungen, umsatz, aov, anteil_pct */
  kanaeleJahr() { throw new Error('nicht umgesetzt'); }
  /** je Jahr und Zahlart: jahr, zahlart, bestellungen, anteil_pct */
  zahlartenJahr() { throw new Error('nicht umgesetzt'); }
  /** je Wochentag: wochentag, nr, bestellungen, umsatz */
  wochentage() { throw new Error('nicht umgesetzt'); }
  /** je Stunde: stunde, bestellungen, umsatz, zufriedenheit */
  stunden() { throw new Error('nicht umgesetzt'); }
  /** Wochentag × Stunde: wochentag, stunde, bestellungen */
  heatmap() { throw new Error('nicht umgesetzt'); }
  /** je Altersgruppe: altersgruppe, kunden */
  kundenAlter() { throw new Error('nicht umgesetzt'); }
  /** Artikelstamm fuer Shop und Kasse: artikel_id, name, kategorie,
   *  unterkategorie, preis, preis_2017, kalorien, vegetarisch, vegan,
   *  allergene, gelistet_seit */
  speisekarte() { throw new Error('nicht umgesetzt'); }
  /** Standorte: filiale_id, name, adresse, bezirk, plz, ort, breite, laenge,
   *  art, drive_through, spielplatz, parkplaetze, sitzplaetze, eroeffnet */
  filialliste() { throw new Error('nicht umgesetzt'); }
  /** je Altersgruppe: altersgruppe, kunden, bestellungen, umsatz, umsatzanteil_pct */
  alterUmsatz() { throw new Error('nicht umgesetzt'); }
  /** eine Zeile: bestellungen, aus_heimatbezirk, anteil_pct, filialbezirke, wohnbezirke */
  heimatbezirk() { throw new Error('nicht umgesetzt'); }
  /** je Treuestufe: stufe, kunden */
  kundenLoyalty() { throw new Error('nicht umgesetzt'); }
  /** je Bezirk: bezirk, kunden */
  kundenBezirke() { throw new Error('nicht umgesetzt'); }
  /** je Filiale: branch_name, branch_type, mitarbeiter, umsatz_je_ma,
   *  bestellungen_je_ma, zufriedenheit, dauer */
  personalFilialen() { throw new Error('nicht umgesetzt'); }
  /** je Rolle: rolle, anzahl, stundenlohn */
  personalRollen() { throw new Error('nicht umgesetzt'); }
  /** je Kanal: kanal, bestellungen, zufriedenheit */
  zufriedenheitKanal() { throw new Error('nicht umgesetzt'); }
  /** je Dauerklasse: dauer_klasse, nr, zufriedenheit, bestellungen */
  zufriedenheitDauer() { throw new Error('nicht umgesetzt'); }
  /** je Aktion: aktion, art, rabatt_pct, bestellungen, umsatz, aov,
   *  zufriedenheit, rabattsumme */
  promotionen() { throw new Error('nicht umgesetzt'); }
  /** je Wetterlage: wetterlage, tage, umsatz_je_tag, bestellungen_je_tag */
  wetterLagen() { throw new Error('nicht umgesetzt'); }
  /** je Temperaturklasse: klasse, von, bis, tage, umsatz_je_tag, bestellungen_je_tag */
  wetterTemperatur() { throw new Error('nicht umgesetzt'); }
  /** je Tag: tag, wetterlage, temperatur, niederschlag, bestellungen, umsatz */
  wetterTage() { throw new Error('nicht umgesetzt'); }
  /** je Kohorte und Jahr: kohorte, jahr, aktive, kohortengroesse */
  kohorten() { throw new Error('nicht umgesetzt'); }
  /** die 15 gezeigten Regeln: nr, regel, produkt_a, produkt_b, gemeinsam,
   *  support_pct, konfidenz_pct, lift */
  warenkorbRegeln() { throw new Error('nicht umgesetzt'); }
  /** je Burger: produkt, preis, kosten, menge, umsatz */
  simulationBasis() { throw new Error('nicht umgesetzt'); }
  /** je RFM-Segment: segment, kunden, anteil_pct, recency_tage, frequenz,
   *  lebenswert, umsatz_gesamt */
  rfmSegmente() { throw new Error('nicht umgesetzt'); }
  /** je Stunde und Kanal: stunde, kanal, bestellungen, anteil_pct */
  kanaeleStunde() { throw new Error('nicht umgesetzt'); }
  /** Die fuenf meistbestellten Artikel je Bestellkanal. */
  kanalProdukte() { throw new Error('nicht umgesetzt'); }
  /** je Niederschlagsklasse: klasse, nr, tage, umsatz_je_tag, bestellungen_je_tag */
  wetterRegen() { throw new Error('nicht umgesetzt'); }
  /** je Aktion mit Wirtschaftlichkeit: aktion, …, baseline_aov, roi */
  promotionenRoi() { throw new Error('nicht umgesetzt'); }
  /** je Jahr und Produkt: jahr, product_name, category, menge, positionsumsatz, anteil_pct */
  produkteJahr() { throw new Error('nicht umgesetzt'); }
  /** Einzelwerte: kennung, wert, vergleich, anzahl */
  einzelwerte() { throw new Error('nicht umgesetzt'); }
  /** weitere Einzelwerte mit Textfeld: kennung, wert, vergleich, anzahl, text */
  einzelwerteZusatz() { throw new Error('nicht umgesetzt'); }
}

/**
 * PostgREST-Adapter (Supabase, selbstgehostet).
 * Uebersetzt jede Frage in genau einen GET auf eine Sicht der Semantikschicht.
 */
export class PostgrestQuelle extends Datenquelle {
  constructor({ url, schluessel, schema = 'burgermetrics' }) {
    super();
    this.url = url.replace(/\/$/, '');
    this.schluessel = schluessel;
    this.schema = schema;
    this.zwischenspeicher = new Map();
  }

  async hole(sicht, abfrage = '') {
    const schluessel = sicht + '?' + abfrage;
    if (this.zwischenspeicher.has(schluessel)) return this.zwischenspeicher.get(schluessel);
    const antwort = await fetch(`${this.url}/rest/v1/${sicht}?${abfrage}`, {
      headers: {
        apikey: this.schluessel,
        Authorization: `Bearer ${this.schluessel}`,
        'Accept-Profile': this.schema,
      },
    });
    if (!antwort.ok) {
      throw new Error(`${sicht}: HTTP ${antwort.status} — ${await antwort.text()}`);
    }
    // PostgREST liefert numeric als Zeichenkette; einmal zentral umwandeln,
    // damit im Dashboard nirgends Number(...) noetig ist.
    const daten = (await antwort.json()).map(zahlenWandeln);
    this.zwischenspeicher.set(schluessel, daten);
    return daten;
  }

  kennzahlenJahr()     { return this.hole('v_kennzahlen_jahr', 'order=jahr'); }
  umsatzMonat()        { return this.hole('v_umsatz_monat', 'order=monat'); }
  filialen()           { return this.hole('v_filiale', 'order=umsatz.desc'); }
  produkte()           { return this.hole('v_produkt', 'order=positionsumsatz.desc'); }
  kategorien()         { return this.hole('v_kategorie', 'order=positionsumsatz.desc'); }
  veggieAnteil()       { return this.hole('v_veggie_anteil', 'order=jahr'); }
  kanaeleJahr()        { return this.hole('v_kanal_jahr', 'order=jahr,bestellungen.desc'); }
  zahlartenJahr()      { return this.hole('v_zahlart_jahr', 'order=jahr,bestellungen.desc'); }
  wochentage()         { return this.hole('v_wochentag', 'order=nr'); }
  stunden()            { return this.hole('v_stunde', 'order=stunde'); }
  heatmap()            { return this.hole('v_heatmap', ''); }
  kundenAlter()        { return this.hole('v_kunde_alter', 'order=altersgruppe'); }
  speisekarte()        { return this.hole('v_speisekarte', ''); }
  filialliste()        { return this.hole('v_filialliste', ''); }
  alterUmsatz()        { return this.hole('v_alter_umsatz', 'order=umsatz.desc'); }
  heimatbezirk()       { return this.hole('v_heimatbezirk', ''); }
  kundenLoyalty()      { return this.hole('v_kunde_loyalty', ''); }
  kundenBezirke()      { return this.hole('v_kunde_bezirk', 'order=kunden.desc'); }
  personalFilialen()   { return this.hole('v_personal_filiale', 'order=umsatz_je_ma'); }
  personalRollen()     { return this.hole('v_personal_rolle', 'order=nr'); }
  zufriedenheitKanal() { return this.hole('v_zufriedenheit_kanal', 'order=zufriedenheit.desc'); }
  zufriedenheitDauer() { return this.hole('v_zufriedenheit_dauer', 'order=nr'); }
  promotionen()        { return this.hole('v_promotion', 'order=bestellungen.desc'); }
  wetterLagen()        { return this.hole('v_wetter_lage', 'order=umsatz_je_tag.desc'); }
  wetterTemperatur()   { return this.hole('v_wetter_temperatur', 'order=klasse'); }
  wetterTage()         { return this.hole('v_wetter_tag', 'order=tag'); }
  kohorten()           { return this.hole('v_kohorte', 'order=kohorte,jahr'); }
  warenkorbRegeln()    { return this.hole('v_warenkorb_auswahl', 'order=nr'); }
  simulationBasis()    { return this.hole('v_simulation_basis', 'order=umsatz.desc'); }
  rfmSegmente()        { return this.hole('v_rfm_segment', 'order=umsatz_gesamt.desc'); }
  kanaeleStunde()      { return this.hole('v_kanal_stunde', 'order=stunde,kanal'); }
  kanalProdukte()      { return this.hole('v_kanal_produkt', 'order=kanal,rang'); }
  wetterRegen()        { return this.hole('v_wetter_regen', 'order=nr'); }
  promotionenRoi()     { return this.hole('v_promotion_roi', 'order=roi.desc'); }
  produkteJahr()       { return this.hole('v_produkt_jahr', 'jahr=eq.2025&order=menge.desc'); }
  einzelwerte()        { return this.hole('v_kennzahl_einzeln', ''); }
  einzelwerteZusatz()  { return this.hole('v_kennzahl_zusatz', ''); }
}

/** Wandelt Zahlen-Zeichenketten (PostgREST numeric) in echte Zahlen. */
function zahlenWandeln(zeile) {
  const aus = {};
  for (const [k, v] of Object.entries(zeile)) {
    aus[k] = (typeof v === 'string' && v !== '' && !isNaN(v)) ? Number(v) : v;
  }
  return aus;
}

/**
 * Waehlt die Quelle. Hier — und nur hier — steht, woher die Zahlen kommen.
 * Eine zweite Quelle braucht eine Klasse mit denselben Methoden und einen
 * Zweig in dieser Funktion.
 */
export function waehleQuelle(konfiguration) {
  switch (konfiguration.art) {
    case 'postgrest':
      return new PostgrestQuelle(konfiguration);
    default:
      throw new Error(`Unbekannte Quellenart: ${konfiguration.art}`);
  }
}
