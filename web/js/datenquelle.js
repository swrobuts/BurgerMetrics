/*
 * datenquelle.js — die Datenschnittstelle des Dashboards.
 *
 * Das Dashboard kennt AUSSCHLIESSLICH die Methoden dieses Moduls. Es kennt
 * keine Tabelle, keine Spalte, keinen Join und keine URL. Wer die Quelle
 * wechselt — auf MySQL, Snowflake, ein Lakehouse oder eine eigene API —,
 * schreibt eine neue Klasse mit denselben Methoden und traegt sie unten in
 * `waehleQuelle` ein. Am Dashboard aendert sich dabei keine Zeile.
 *
 * Der Vertrag ist absichtlich schmal: 34 benannte Fragen, jede liefert ein
 * Array von Objekten mit stabilen Feldnamen. Diese Namen sind die eigentliche
 * Schnittstelle — sie stehen serverseitig in db/aufbau/0005_semantik.sql.
 *
 * Kasse und Shop benutzen dasselbe Modul, aber einen anderen Teil davon: den
 * Artikelstamm und das Anlegen einer Bestellung. Beides geht gegen das
 * operative Schema wawi (db/aufbau/0016 bis 0019), nicht gegen das
 * Auswertungsmodell — das Warehouse wird aus dem operativen System beladen,
 * nicht umgekehrt. Der Bereich „Rezensionen“ der Kasse meldet sich dazu an;
 * nur seine Aufrufe (mitAnmeldung) tragen das Token, alle anderen den
 * öffentlichen Schlüssel.
 */

/** Der Fehlertext einer PostgREST-Antwort: das Feld message, sonst der rohe Text. */
async function meldungLesen(antwort) {
  const text = await antwort.text();
  try { return JSON.parse(text).message || text; } catch (_) { return text; }
}

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
  /** Artikelstamm fuer Shop und Kasse (operatives Schema): artikel_id, name,
   *  kategorie, unterkategorie, preis, preis_2017, kalorien, vegetarisch,
   *  vegan, allergene, gelistet_seit */
  speisekarte() { throw new Error('nicht umgesetzt'); }
  /** Standorte (operatives Schema): filiale_id, name, adresse, bezirk, plz,
   *  ort, breite, laenge, art, drive_through, spielplatz, parkplaetze,
   *  sitzplaetze, eroeffnet */
  filialliste() { throw new Error('nicht umgesetzt'); }
  /**
   * Eine Bestellung im operativen System anlegen — der einzige Schreibweg.
   * @param {object} bestellung  filiale_id, zahlungsart_id, bestellkanal
   *   ('Counter' | 'Drive-Through' | 'Kiosk' | 'App Order'), positionen
   *   [{artikel_id, menge}], quelle ('kasse' | 'shop'); optional sitzung,
   *   kunde_id, promotion_id, rabatt_betrag, mwst_satz.
   *   Preise schickt der Browser NICHT — sie kommen aus dem Stamm.
   * @returns {Promise<object>} bestellung_id, rechnung_id, bestelldatum,
   *   bestellzeit, positionen, artikel_anzahl, brutto_gesamt, rabatt_betrag,
   *   netto_gesamt, mwst_satz, mwst_betrag, quelle
   */
  bestellungAnlegen(bestellung) { throw new Error('nicht umgesetzt'); }
  /** Die juengsten Uebungsbestellungen: bestellung_id, quelle, sitzung,
   *  bestelldatum, bestellzeit, filiale, kanal, zahlungsart, artikel_anzahl,
   *  positionen, brutto_gesamt, rabatt_betrag, netto_gesamt, erfasst_am,
   *  im_warehouse */
  letzteBestellungen() { throw new Error('nicht umgesetzt'); }
  /** Bewertungsstand je Artikel, nur freigegebene Rezensionen: artikel_id, name,
   *  anzahl, sterne_mittel (eine Nachkommastelle, null ohne Rezension), letzte
   *  (Datum der jüngsten), anzahl_1 bis anzahl_5 — immer frisch geholt. */
  rezensionenProdukt() { throw new Error('nicht umgesetzt'); }
  /** Die drei jüngsten freigegebenen Rezensionen je Artikel, aus Simulation und
   *  Shop: artikel_id, rezension_id, sterne, inhalt, datum */
  kundenstimmen() { throw new Error('nicht umgesetzt'); }
  /**
   * Eine Rezension im operativen System anlegen — der zweite Schreibweg.
   * @param {object} rezension  artikel_id, sterne (1–5), inhalt (5–500 Zeichen
   *   nach Normalisierung: Leerraumfolgen ein Zeichen, Ränder weg); optional filiale_id, sitzung. Die Datenbank prüft alles und
   *   bremst: 20 je Sitzung und zehn Minuten, 600 je Stunde insgesamt.
   * @returns {Promise<object>} rezension_id, artikel, sterne, erstellt_am, quelle
   */
  rezensionAnlegen(rezension) { throw new Error('nicht umgesetzt'); }
  /** Die 50 jüngsten Shop-Rezensionen: rezension_id, sitzung, artikel, filiale,
   *  sterne, inhalt, erstellt_am, im_warehouse, status. inhalt ist Besuchertext,
   *  nur bei freigegebenen gefüllt und wird auf keiner Seite gerendert. */
  letzteRezensionen() { throw new Error('nicht umgesetzt'); }
  /** Freigegebene Rezensionen eines Artikels für die Leseansicht, neueste
   *  zuerst: artikel_id, rezension_id, sterne, inhalt, datum, erstellt_am,
   *  quelle, status. sterne filtert auf eine Sternzahl (1–5), null zeigt alle;
   *  seite zählt ab 1, groesse Rezensionen je Seite. */
  rezensionenLesen(artikelId, sterne, seite, groesse) { throw new Error('nicht umgesetzt'); }
  /** Status einer Shop-Rezension ohne Text: 'offen', 'freigegeben',
   *  'zurueckgehalten', 'abgelehnt' — oder null, wenn es sie nicht gibt. */
  rezensionStatus(rezensionId) { throw new Error('nicht umgesetzt'); }
  /** Anmeldung mit einem Supabase-Konto für die Moderation im POS.
   *  @returns {Promise<object>} token, gueltigBis (Millisekunden) */
  anmelden(email, passwort) { throw new Error('nicht umgesetzt'); }
  /** Übernimmt eine gespeicherte Anmeldung, wenn sie noch gilt; true bei Erfolg. */
  sitzungUebernehmen(sitzung) { throw new Error('nicht umgesetzt'); }
  /** Gilt die Anmeldung noch? */
  angemeldet() { throw new Error('nicht umgesetzt'); }
  /** Meldet ab und vergisst das Token. */
  abmelden() { throw new Error('nicht umgesetzt'); }
  /** Rollen des angemeldeten Kontos: 'moderation', 'qualitaet' oder keine. */
  meineRollen() { throw new Error('nicht umgesetzt'); }
  /** Zurückgehaltene und lange offene Shop-Rezensionen mit Jevs Wahrscheinlichkeiten (Rolle moderation). */
  moderationListe() { throw new Error('nicht umgesetzt'); }
  /** Offene QS-Fälle mit Text (Rolle qualitaet). */
  qsFaelle() { throw new Error('nicht umgesetzt'); }
  /** Die letzten 20 Entscheidungen (Rolle moderation). */
  entscheidungenLetzte() { throw new Error('nicht umgesetzt'); }
  /** Stand des Prüfdienstes ohne Texte, auch ohne Anmeldung: letzte_pruefung, offen,
   *  aelteste_offene_min, zurueckgehalten, qs_offen. */
  pruefdienstStand() { throw new Error('nicht umgesetzt'); }
  /** Gibt eine Shop-Rezension frei (Rolle moderation). */
  rezensionFreigeben(rezensionId, bemerkung) { throw new Error('nicht umgesetzt'); }
  /** Lehnt eine Shop-Rezension ab (Rolle moderation). */
  rezensionAblehnen(rezensionId, bemerkung) { throw new Error('nicht umgesetzt'); }
  /** Schließt einen QS-Fall (Rolle qualitaet). */
  qsFallErledigen(qsFallId, bemerkung) { throw new Error('nicht umgesetzt'); }
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
 * Uebersetzt jede Frage in genau einen GET auf eine Sicht — der
 * Semantikschicht (Schema burgermetrics) oder des operativen Modells
 * (Schema wawi). Das Schema waehlt der Header Accept-Profile; PostgREST
 * muss beide kennen (PGRST_DB_SCHEMAS, siehe db/README.md).
 */
export class PostgrestQuelle extends Datenquelle {
  constructor({ url, schluessel, schema = 'burgermetrics', schemaWawi = 'wawi' }) {
    super();
    this.url = url.replace(/\/$/, '');
    this.schluessel = schluessel;
    this.schema = schema;
    this.schemaWawi = schemaWawi;
    this.zwischenspeicher = new Map();
    this.sitzung = null;   // Anmeldung für die Moderation: token, gueltigBis
  }

  async hole(sicht, abfrage = '', { schema = this.schema, frisch = false, seitenweise = false, token = this.schluessel } = {}) {
    const schluessel = schema + '.' + sicht + '?' + abfrage + (seitenweise ? '#alle' : '');
    if (!frisch && this.zwischenspeicher.has(schluessel)) return this.zwischenspeicher.get(schluessel);
    const daten = [];
    let gesamt;
    do {
      const parameter = new URLSearchParams(abfrage);
      if (seitenweise) {
        parameter.set('limit', '1000');
        parameter.set('offset', String(daten.length));
      }
      const antwort = await fetch(`${this.url}/rest/v1/${sicht}?${parameter}`, {
        headers: {
          apikey: this.schluessel,
          Authorization: `Bearer ${token}`,
          'Accept-Profile': schema,
          ...(seitenweise ? { Prefer: 'count=exact' } : {}),
        },
      });
      if (!antwort.ok) {
        throw new Error(`${sicht}: HTTP ${antwort.status} — ${await meldungLesen(antwort)}`);
      }
      // PostgreSQL-Zahlen sind bereits JSON-Zahlen. Numerischen Text (etwa
      // PLZ, Artikelname oder Rezension) unverändert lassen.
      const seite = await antwort.json();
      if (seitenweise) {
        const bereich = antwort.headers.get('Content-Range') || '';
        const treffer = /^(?:(\d+)-(\d+)|\*)\/(\d+)$/.exec(bereich);
        if (!treffer || (seite.length && (Number(treffer[1]) !== daten.length
            || Number(treffer[2]) - Number(treffer[1]) + 1 !== seite.length))) {
          throw new Error(`${sicht}: ungültiger Content-Range, Ergebnis möglicherweise unvollständig`);
        }
        gesamt = Number(treffer[3]);
        if (!seite.length && daten.length < gesamt) {
          throw new Error(`${sicht}: leere Folgeseite, Ergebnis unvollständig`);
        }
      }
      daten.push(...seite);
    } while (seitenweise && daten.length < gesamt);
    // Erst vollständige Ergebnisse speichern; ein Fehler beim Nachladen darf
    // beim nächsten Versuch keinen scheinbar erfolgreichen Teilbestand liefern.
    this.zwischenspeicher.set(schluessel, daten);
    return daten;
  }

  /**
   * Ruft eine Datenbankfunktion auf (PostgREST: POST /rpc/<name>). Der
   * Header Content-Profile waehlt das Schema; die Argumente gehen als JSON
   * mit den Parameternamen der Funktion. Das Token einer Anmeldung geht nur
   * mit, wenn der Aufruf es ausdrücklich übergibt (siehe mitAnmeldung).
   */
  async rufe(funktion, argumente, { schema = this.schemaWawi, token = this.schluessel } = {}) {
    const antwort = await fetch(`${this.url}/rest/v1/rpc/${funktion}`, {
      method: 'POST',
      headers: {
        apikey: this.schluessel,
        Authorization: `Bearer ${token}`,
        'Content-Profile': schema,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(argumente),
    });
    if (!antwort.ok) {
      // PostgREST verpackt RAISE EXCEPTION als {message, details, hint, code}.
      throw new Error(`${funktion}: HTTP ${antwort.status} — ${await meldungLesen(antwort)}`);
    }
    return antwort.json();
  }

  angemeldet() {
    return Boolean(this.sitzung && Date.now() < this.sitzung.gueltigBis);
  }

  /** Anmeldung beim Anmeldedienst von Supabase; das Passwort geht nur in diesen Request. */
  async anmelden(email, passwort) {
    const antwort = await fetch(`${this.url}/auth/v1/token?grant_type=password`, {
      method: 'POST',
      headers: { apikey: this.schluessel, 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password: passwort }),
    });
    if (antwort.status === 400 || antwort.status === 401) throw new Error('E-Mail oder Passwort stimmen nicht.');
    if (antwort.status === 429) throw new Error('Zu viele Anmeldeversuche. Bitte eine Minute warten.');
    if (!antwort.ok) throw new Error(`Der Anmeldedienst antwortet nicht (HTTP ${antwort.status}).`);
    const daten = await antwort.json();
    // Eine Minute vor dem Ablauf gilt die Anmeldung schon als abgelaufen.
    this.sitzung = { token: daten.access_token,
                     gueltigBis: Date.now() + ((Number(daten.expires_in) || 3600) - 60) * 1000 };
    return this.sitzung;
  }

  sitzungUebernehmen(sitzung) {
    const gueltig = Boolean(sitzung && sitzung.token && Date.now() < Number(sitzung.gueltigBis));
    this.sitzung = gueltig ? { token: sitzung.token, gueltigBis: Number(sitzung.gueltigBis) } : null;
    return gueltig;
  }

  /** Meldet ab: erst hier (Token vergessen), dann nur diese Sitzung beim Anmeldedienst, ohne zu warten. */
  abmelden() {
    const token = this.angemeldet() ? this.sitzung.token : null;
    this.sitzung = null;
    this.zwischenspeicher.clear();
    if (token) {
      fetch(`${this.url}/auth/v1/logout?scope=local`, {
        method: 'POST', headers: { apikey: this.schluessel, Authorization: `Bearer ${token}` } })
        .catch(() => { /* abgemeldet ist schon, auch ohne Antwort */ });
    }
  }

  /** Führt einen Aufruf nur mit gültiger Anmeldung aus und gibt ihm das Token; HTTP 401 heißt: abgelaufen. */
  async mitAnmeldung(aufruf) {
    const abgelaufen = new Error('Die Anmeldung ist abgelaufen. Bitte neu anmelden.');
    if (!this.angemeldet()) {
      this.sitzung = null;
      throw abgelaufen;
    }
    try {
      return await aufruf(this.sitzung.token);
    } catch (fehler) {
      if (/HTTP 401/.test(fehler.message)) {
        this.sitzung = null;
        throw abgelaufen;
      }
      throw fehler;
    }
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
  speisekarte()        { return this.hole('v_speisekarte', '', { schema: this.schemaWawi }); }
  filialliste()        { return this.hole('v_filialliste', '', { schema: this.schemaWawi }); }
  bestellungAnlegen(b) { return this.rufe('bestellung_anlegen', b); }
  letzteBestellungen() { return this.hole('v_bestellung_letzte', '', { schema: this.schemaWawi, frisch: true }); }
  rezensionenProdukt() { return this.hole('v_rezension_produkt', 'order=artikel_id', { schema: this.schemaWawi, frisch: true }); }
  kundenstimmen()      { return this.hole('v_kundenstimmen', 'order=artikel_id,rezension_id.desc', { schema: this.schemaWawi }); }
  rezensionAnlegen(r)  { return this.rufe('rezension_anlegen', r); }
  letzteRezensionen()  { return this.hole('v_rezension_letzte', '', { schema: this.schemaWawi, frisch: true }); }
  rezensionenLesen(artikelId, sterne = null, seite = 1, groesse = 10) {
    const abfrage = new URLSearchParams({
      artikel_id: `eq.${Number(artikelId)}`,
      order: 'erstellt_am.desc,rezension_id.desc',
      limit: String(groesse),
      offset: String((Math.max(1, Number(seite)) - 1) * groesse),
    });
    if (sterne) abfrage.set('sterne', `eq.${Number(sterne)}`);
    return this.hole('v_rezensionen_lesen', abfrage.toString(), { schema: this.schemaWawi, frisch: true });
  }
  async rezensionStatus(rezensionId) {
    const [zeile] = await this.hole('v_rezension_status', `rezension_id=eq.${Number(rezensionId)}`,
      { schema: this.schemaWawi, frisch: true });
    return zeile ? zeile.status : null;
  }
  meineRollen() {
    return this.mitAnmeldung(async token => {
      const rollen = [];
      for (const rolle of ['moderation', 'qualitaet']) {
        if (await this.rufe('hat_rolle', { p_rolle: rolle }, { token })) rollen.push(rolle);
      }
      return rollen;
    });
  }
  moderationListe()      { return this.mitAnmeldung(token => this.hole('v_moderation', '', { schema: this.schemaWawi, frisch: true, token })); }
  qsFaelle()             { return this.mitAnmeldung(token => this.hole('v_qs_faelle', '', { schema: this.schemaWawi, frisch: true, token })); }
  entscheidungenLetzte() { return this.mitAnmeldung(token => this.hole('v_entscheidungen_letzte', '', { schema: this.schemaWawi, frisch: true, token })); }
  async pruefdienstStand() {
    const [zeile] = await this.hole('v_pruefdienst_stand', '', { schema: this.schemaWawi, frisch: true });
    return zeile || null;
  }
  rezensionFreigeben(rezensionId, bemerkung) {
    return this.mitAnmeldung(token => this.rufe('api_rezension_freigeben',
      { rezension_id: Number(rezensionId), bemerkung: bemerkung || null }, { token }));
  }
  rezensionAblehnen(rezensionId, bemerkung) {
    return this.mitAnmeldung(token => this.rufe('api_rezension_ablehnen',
      { rezension_id: Number(rezensionId), bemerkung: bemerkung || null }, { token }));
  }
  qsFallErledigen(qsFallId, bemerkung) {
    return this.mitAnmeldung(token => this.rufe('api_qs_fall_erledigen',
      { qs_fall_id: Number(qsFallId), bemerkung: bemerkung || null }, { token }));
  }
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
  wetterTage()         { return this.hole('v_wetter_tag', 'order=tag', { seitenweise: true }); }
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
