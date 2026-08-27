/*
 * reihen.js — übersetzt die Antworten der Semantikschicht in die Datenreihen,
 * die die Diagramme des Dashboards erwarten.
 *
 * Diese Datei ist die einzige Stelle, an der Feldnamen der Datenquelle auf
 * Reihennamen des Dashboards treffen. Sie enthält keine Fachlogik: Was eine
 * Kennzahl bedeutet, steht serverseitig in db/aufbau/0005_semantik.sql. Hier
 * wird nur umsortiert, beschriftet und in die Form gebracht, die Chart.js
 * braucht.
 */

/** Holt alle 33 Sichten parallel. */
export async function ladeAlles(quelle) {
  const fragen = {
    kennzahlenJahr: quelle.kennzahlenJahr(), umsatzMonat: quelle.umsatzMonat(),
    filialen: quelle.filialen(), produkte: quelle.produkte(),
    kategorien: quelle.kategorien(), veggie: quelle.veggieAnteil(),
    kanaeleJahr: quelle.kanaeleJahr(), zahlartenJahr: quelle.zahlartenJahr(),
    wochentage: quelle.wochentage(), stunden: quelle.stunden(),
    heatmap: quelle.heatmap(), kundenAlter: quelle.kundenAlter(),
    alterUmsatz: quelle.alterUmsatz(), heimatbezirk: quelle.heimatbezirk(),
    kundenLoyalty: quelle.kundenLoyalty(), kundenBezirke: quelle.kundenBezirke(),
    personalFilialen: quelle.personalFilialen(), personalRollen: quelle.personalRollen(),
    zufriedenheitKanal: quelle.zufriedenheitKanal(), zufriedenheitDauer: quelle.zufriedenheitDauer(),
    promotionen: quelle.promotionenRoi(), wetterLagen: quelle.wetterLagen(),
    wetterTemperatur: quelle.wetterTemperatur(), wetterTage: quelle.wetterTage(),
    wetterRegen: quelle.wetterRegen(), kohorten: quelle.kohorten(),
    warenkorb: quelle.warenkorbRegeln(), simulation: quelle.simulationBasis(),
    rfm: quelle.rfmSegmente(), kanaeleStunde: quelle.kanaeleStunde(),
    produkteJahr: quelle.produkteJahr(), einzelwerte: quelle.einzelwerte(),
    einzelwerteZusatz: quelle.einzelwerteZusatz(),
  };
  const namen = Object.keys(fragen);
  const werte = await Promise.all(Object.values(fragen));
  return Object.fromEntries(namen.map((n, i) => [n, werte[i]]));
}

const WOCHENTAG_KURZ = { Monday: 'Mo', Tuesday: 'Di', Wednesday: 'Mi', Thursday: 'Do',
                         Friday: 'Fr', Saturday: 'Sa', Sunday: 'So' };
const KANAL_KURZ = { 'Counter': 'Counter', 'Drive-Through': 'Drive-Through',
                     'App Order': 'App', 'Kiosk': 'Kiosk' };
const LOYALTY_TEXT = { None: 'Kein Programm', Bronze: 'Bronze', Silver: 'Silber', Gold: 'Gold' };
const ALTERSFOLGE = ['<18', '18-24', '25-34', '35-44', '45-54', '55-64', '65+'];

const r2 = (v, n = 2) => v === null || v === undefined ? null : Math.round(v * 10 ** n) / 10 ** n;

/** Baut aus den geladenen Sichten alle Reihen des Dashboards. */
export function baueReihen(d) {
  const R = {};

  // ── Zeitreihen ──────────────────────────────────────────────────────────
  R.mLabels  = d.umsatzMonat.map(x => x.monat);
  R.mRevenue = d.umsatzMonat.map(x => Math.round(x.umsatz));

  const jahre = d.kennzahlenJahr;
  const letztes = jahre.length - 1;
  R.yearLabels  = jahre.map((x, i) => i === letztes ? `${x.jahr}*` : String(x.jahr));
  R.yearRevenue = jahre.map(x => Math.round(x.umsatz));
  R.yearOrders  = jahre.map(x => x.bestellungen);
  R.yearAOV     = jahre.map(x => r2(x.aov));
  R.paymentYears = jahre.map(x => String(x.jahr));

  // Veränderungsraten je Jahr — aus den Jahreswerten, nicht getrennt gepflegt.
  const yoy = (reihe) => reihe.slice(1, 9).map((v, i) => r2((v / reihe[i] - 1) * 100, 1));
  R.revYoY = yoy(R.yearRevenue);
  R.ordYoY = yoy(R.yearOrders);
  R.aovYoY = yoy(R.yearAOV);

  // ── Filialen ────────────────────────────────────────────────────────────
  R.branchLabels  = d.filialen.map(x => x.branch_name);
  R.branchRevenue = d.filialen.map(x => Math.round(x.umsatz));
  R.branchAOV     = d.filialen.map(x => r2(x.aov));
  R.branchYears   = d.filialen.map(x => x.betriebsjahre);

  // ── Produkte ────────────────────────────────────────────────────────────
  R.topProducts        = d.produkte.slice(0, 15).map(x => x.product_name);
  R.topProductRevenue  = d.produkte.slice(0, 15).map(x => Math.round(x.positionsumsatz));
  R.categories         = d.kategorien.map(x => x.category);
  R.categoryRevenue    = d.kategorien.map(x => Math.round(x.positionsumsatz));
  R.veggieYears        = d.veggie.map(x => String(x.jahr));
  R.veggiePercent      = d.veggie.map(x => r2(x.anteil_pct, 1));

  // ── Kanäle ──────────────────────────────────────────────────────────────
  const kanalFolge = ['Counter', 'Drive-Through', 'App Order', 'Kiosk'];
  const k2025 = (name) => d.kanaeleJahr.find(x => x.jahr === 2025 && x.kanal === name) || {};
  R.channelLabels        = kanalFolge.map(n => KANAL_KURZ[n]);
  R.channelOrders2025    = kanalFolge.map(n => k2025(n).bestellungen ?? 0);
  R.channelRevenue2025   = kanalFolge.map(n => Math.round(k2025(n).umsatz ?? 0));
  R.channelAOV2025       = kanalFolge.map(n => r2(k2025(n).aov));
  const anteilJahr = (name) => R.paymentYears.map(j => {
    const t = d.kanaeleJahr.find(x => x.jahr === Number(j) && x.kanal === name);
    return t ? r2(t.anteil_pct, 1) : 0;
  });
  R.counterData = anteilJahr('Counter');
  R.driveData   = anteilJahr('Drive-Through');
  R.appData     = anteilJahr('App Order');
  R.kioskData   = anteilJahr('Kiosk');

  // Kanäle im Tagesverlauf
  R.channelTodHours = [...new Set(d.kanaeleStunde.map(x => x.stunde))].sort((a, b) => a - b);
  const todAnteil = (name) => R.channelTodHours.map(s => {
    const t = d.kanaeleStunde.find(x => x.stunde === s && x.kanal === name);
    return t ? Math.round(t.anteil_pct) : 0;
  });
  R.channelTodCounter = todAnteil('Counter');
  R.channelTodDrive   = todAnteil('Drive-Through');
  R.channelTodApp     = todAnteil('App Order');
  R.channelTodKiosk   = todAnteil('Kiosk');

  // ── Zahlarten ───────────────────────────────────────────────────────────
  const zahlartJahr = (name) => R.paymentYears.map(j => {
    const t = d.zahlartenJahr.find(x => x.jahr === Number(j) && x.zahlart === name);
    return t ? r2(t.anteil_pct, 1) : 0;
  });
  R.cashData   = zahlartJahr('Cash');
  R.ecData     = zahlartJahr('EC Card');
  R.ccData     = zahlartJahr('Credit Card');
  R.mobileData = zahlartJahr('Mobile Payment');

  // ── Zeitachsen ──────────────────────────────────────────────────────────
  R.dowLabels  = d.wochentage.map(x => WOCHENTAG_KURZ[x.wochentag] || x.wochentag);
  R.dowOrders  = d.wochentage.map(x => x.bestellungen);
  R.dowRevenue = d.wochentage.map(x => Math.round(x.umsatz));
  R.hourLabels = d.stunden.map(x => String(x.stunde).padStart(2, '0'));
  R.hourOrders = d.stunden.map(x => x.bestellungen);
  R.satHours   = d.stunden.map(x => x.stunde);
  R.satHourVal = d.stunden.map(x => r2(x.zufriedenheit, 3));

  // Heatmap: Wochentag × Stunde, in der Reihenfolge der beiden Achsen
  const stundenFolge = R.satHours;
  R.heatmapData = d.wochentage.map(w => stundenFolge.map(s => {
    const t = d.heatmap.find(x => x.wochentag === w.wochentag && x.stunde === s);
    return t ? t.bestellungen : 0;
  }));

  // ── Kunden ──────────────────────────────────────────────────────────────
  R.ageGroups    = ALTERSFOLGE.map(a => a === '18-24' ? '18–24' : a === '25-34' ? '25–34'
                    : a === '35-44' ? '35–44' : a === '45-54' ? '45–54' : a === '55-64' ? '55–64' : a);
  R.ageCount     = ALTERSFOLGE.map(a => (d.kundenAlter.find(x => x.altersgruppe === a) || {}).kunden ?? 0);
  const loyFolge = ['None', 'Bronze', 'Silver', 'Gold'];
  R.loyaltyTiers = loyFolge.map(s => LOYALTY_TEXT[s]);
  R.loyaltyCount = loyFolge.map(s => (d.kundenLoyalty.find(x => x.stufe === s) || {}).kunden ?? 0);
  R.districtLabels = d.kundenBezirke.map(x => x.bezirk);
  R.districtCounts = d.kundenBezirke.map(x => x.kunden);

  // ── Personal ────────────────────────────────────────────────────────────
  R.empBranches    = d.personalFilialen.map(x => x.branch_name);
  R.empTypes       = d.personalFilialen.map(x => x.branch_type);
  R.empCount       = d.personalFilialen.map(x => x.mitarbeiter);
  R.empRevPerEmp   = d.personalFilialen.map(x => Math.round(x.umsatz_je_ma));
  R.empOrdPerEmp   = d.personalFilialen.map(x => Math.round(x.bestellungen_je_ma));
  R.empAvgSat      = d.personalFilialen.map(x => r2(x.zufriedenheit));
  R.empAvgDuration = d.personalFilialen.map(x => r2(x.dauer, 1));
  R.empRoles       = d.personalRollen.map(x => x.bezeichnung ?? x.rolle);
  R.empRoleCount   = d.personalRollen.map(x => x.anzahl);
  R.empRoleWage    = d.personalRollen.map(x => r2(x.stundenlohn, 1));

  // ── Zufriedenheit ───────────────────────────────────────────────────────
  R.satChannels   = d.zufriedenheitKanal.map(x => x.kanal);
  R.satChannelVal = d.zufriedenheitKanal.map(x => r2(x.zufriedenheit, 3));
  R.satChannelN   = d.zufriedenheitKanal.map(x => x.bestellungen);
  R.satDurBins    = d.zufriedenheitDauer.map(x => x.dauer_klasse);
  R.satDurVal     = d.zufriedenheitDauer.map(x => r2(x.zufriedenheit, 3));

  // ── Aktionen ────────────────────────────────────────────────────────────
  const promo = [...d.promotionen].sort((a, b) => b.zufriedenheit - a.zufriedenheit);
  R.promoNames       = promo.map(x => x.aktion);
  R.promoOrders      = promo.map(x => x.bestellungen);
  R.promoTotalRev    = promo.map(x => Math.round(x.umsatz));
  R.promoROI         = promo.map(x => r2(x.roi, 1));
  R.promoAvgSat      = promo.map(x => r2(x.zufriedenheit));
  R.promoBaselineNet = r2(d.promotionen[0]?.baseline_aov);

  // ── Wetter ──────────────────────────────────────────────────────────────
  R.weatherConds = d.wetterLagen.map(x => x.wetterlage);
  R.weatherRev   = d.wetterLagen.map(x => Math.round(x.umsatz_je_tag));
  R.weatherOrd   = d.wetterLagen.map(x => Math.round(x.bestellungen_je_tag));
  const temp = d.wetterTemperatur.filter(x => x.tage > 0);
  R.tempBins     = temp.map(x => `${Math.round(x.von)}–${Math.round(x.bis)}`);
  R.tempRevAvg   = temp.map(x => Math.round(x.umsatz_je_tag));
  R.tempOrdAvg   = temp.map(x => Math.round(x.bestellungen_je_tag));
  R.tempDays     = temp.map(x => x.tage);
  R.rainBins     = d.wetterRegen.map(x => x.klasse);
  R.rainRev      = d.wetterRegen.map(x => Math.round(x.umsatz_je_tag));
  // Die Achse ist mit "Tagesumsatz" beschriftet und die drei Nachbar-
  // diagramme zeigen Umsatz; gezeichnet wurden bisher Bestellungen.
  R.weatherScatter = d.wetterTage.map(x => ({ x: x.temperatur, y: Math.round(x.umsatz) }));

  // ── Kohorten ────────────────────────────────────────────────────────────
  R.cohortLabels = [...new Set(d.kohorten.map(x => x.kohorte))].sort();
  R.cohortSizes  = R.cohortLabels.map(k =>
    (d.kohorten.find(x => x.kohorte === k) || {}).kohortengroesse ?? 0);
  R.cohortMatrix = R.cohortLabels.map(k => R.cohortLabels.map(j => {
    if (j < k) return null;                       // vor der Kohorte: kein Wert
    const t = d.kohorten.find(x => x.kohorte === k && x.jahr === j);
    return t ? r2(100 * t.aktive / t.kohortengroesse, 1) : null;
  }));

  // ── Warenkorbanalyse ────────────────────────────────────────────────────
  R.assocLabels = d.warenkorb.map(x => x.regel);
  R.assocLift   = d.warenkorb.map(x => r2(x.lift));

  // ── RFM ─────────────────────────────────────────────────────────────────
  // Die Farbe folgt der Recency, nicht der Position in der Liste: gruen, wo die
  // letzte Bestellung nah liegt, rot, wo sie lange her ist. Eine feste
  // Farbliste nach Position faerbte die Neukunden rot, sobald sich die
  // Sortierung aendert — genau das war passiert.
  const rfmFarbe = (tage) => tage <= 30 ? '#16a34a' : tage >= 180 ? '#dc2626' : '#5b7a9d';
  R.rfmSegments = d.rfm.map(x => ({
    seg: x.segment, count: x.kunden, pct: r2(x.anteil_pct, 1),
    avgR: Math.round(x.recency_tage), avgF: r2(x.frequenz, 1),
    avgM: Math.round(x.lebenswert), totalM: Math.round(x.umsatz_gesamt),
    farbe: rfmFarbe(x.recency_tage),
  }));

  // ── Preissimulation ─────────────────────────────────────────────────────
  R.simProducts = d.simulation.map(x => ({
    name: x.produkt, price: r2(x.preis), cost: r2(x.kosten),
    vol: x.menge, rev: Math.round(x.umsatz),
  }));

  // ── Markierungen und Vergleichslinien in Diagrammen ─────────────────────
  // Vier Werte standen bis August 2026 als Zahl im Skript des Dashboards.
  // Sie gehoeren nicht zu einer Reihe, sondern markieren einzelne Punkte —
  // und altern deshalb besonders unauffaellig. Die Beschriftung des
  // Pandemie-Punktes lautete "−62 %", der tatsaechliche Rueckgang betraegt
  // 54,8 Prozent.
  const netzAov = R.yearRevenue.reduce((a, b) => a + b, 0)
                / R.yearOrders.reduce((a, b) => a + b, 0);
  R.aovNetz = r2(netzAov);

  // Der Einbruch wird nicht ueber den Monat gesucht, sondern ueber die
  // Eigenschaft: der groesste Rueckgang gegenueber dem Vormonat.
  let tief = { i: 1, mom: 0 };
  for (let i = 1; i < R.mRevenue.length; i++) {
    const mom = (R.mRevenue[i] / R.mRevenue[i - 1] - 1) * 100;
    if (mom < tief.mom) tief = { i, mom };
  }
  R.monatTief = { index: tief.i, wert: R.mRevenue[tief.i],
                  label: R.mLabels[tief.i], mom: r2(tief.mom, 1) };
  const hoch = R.mRevenue.indexOf(Math.max(...R.mRevenue));
  R.monatHoch = { index: hoch, wert: R.mRevenue[hoch], label: R.mLabels[hoch] };

  // Basislinie der Zufriedenheit: der Mittelwert ohne Aktion, gemessen, nicht
  // gesetzt — siehe db/aufbau/0012_diagrammwerte.sql.
  const ohneAktion = d.einzelwerteZusatz.find(x => x.kennung === 'zufriedenheit_ohne_aktion');
  R.satBasis = ohneAktion ? Number(ohneAktion.wert) : null;

  // Achsengrenzen und Farbschwellen der Zufriedenheitsdiagramme folgen den
  // Daten. Fest gesetzte Grenzen schneiden Werte ab, sobald sich der Bestand
  // aendert — und niemand sieht es.
  const spanne = (werte, luft = 0.05) => {
    const gueltig = werte.filter(v => v !== null && isFinite(v));
    const lo = Math.min(...gueltig), hi = Math.max(...gueltig);
    return { min: r2(lo - luft, 2), max: r2(hi + luft, 2),
             mitte: r2((lo + hi) / 2, 2) };
  };
  R.satStunde = spanne(R.satHourVal);
  R.satKanal  = spanne(R.satChannelVal);
  R.satPromo  = spanne(R.promoAvgSat);

  // ── Prognoseszenarien ───────────────────────────────────────────────────
  // Wachstumsraten und Investitionsbetraege sind ANNAHMEN, keine Messwerte.
  // Sie stehen hier an einer Stelle, damit Diagramm und Tabelle nicht
  // auseinanderlaufen. Basis ist das letzte vollstaendige Jahr.
  // Der Ruecklauf ist bewusst schlicht definiert: Mehrumsatz ueber drei Jahre
  // gegenueber dem konservativen Fall, geteilt durch die Investition. Er sagt
  // nichts ueber Marge oder Kapitalbindung, sondern nur, wie oft sich der
  // eingesetzte Betrag im Zusatzumsatz wiederfindet.
  const iBasis = R.yearLabels.findIndex(x => parseInt(x) === 2025);
  const basis = R.yearRevenue[iBasis];
  const reihe = (rate) => [1, 2, 3].map(k => basis * Math.pow(1 + rate, k));
  const kons = reihe(0.03);
  R.prognoseBasis = basis;
  R.szenarien = [
    { name: 'Konservativ',  rate: 0.03, investition: 0,       jahre: kons },
    { name: 'Optimistisch', rate: 0.08, investition: 350000,  jahre: reihe(0.08) },
    { name: 'Expansiv',     rate: 0.15, investition: 1200000, jahre: reihe(0.15) },
  ].map(s => {
    const mehr = s.jahre.reduce((a, v, i) => a + (v - kons[i]), 0);
    return { ...s, mehrumsatz: mehr,
             ruecklauf: s.investition ? mehr / s.investition : null };
  });

  return R;
}
