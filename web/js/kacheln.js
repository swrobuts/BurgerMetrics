/*
 * kacheln.js — füllt die 72 Kennzahlkacheln aus den geladenen Reihen.
 *
 * Jede Kachel trägt im HTML ein data-kpi-Merkmal (Reiter + laufende Nummer).
 * Hier steht zu jeder Kennung, wie ihr Wert, ihre Veränderung und ihr
 * Zusatztext zu rechnen sind. Im HTML selbst steht nur noch die Beschriftung.
 */

const zahl = (v, n = 0) => Number(v).toLocaleString('de-DE',
  { minimumFractionDigits: n, maximumFractionDigits: n }).replace('-', '−');
const euro = (v, n = 2) => '€' + zahl(v, n);
const mio  = (v) => '€' + zahl(v / 1e6, 2) + 'M';
const proz = (v, n = 1) => zahl(v, n) + '%';
const pp   = (v) => (v >= 0 ? '+' : '−') + zahl(Math.abs(v), 1) + 'pp';

/** Veränderung als Text mit Pfeil, für die kpi-delta-Zeile. */
function delta(neu, alt, form = proz) {
  const v = (neu / alt - 1) * 100;
  return { text: (v >= 0 ? '↑ ' : '↓ ') + form(Math.abs(v)), gut: v >= 0 };
}

export function fuelleKacheln(B, roh) {
  const j = B.yearLabels.map(x => parseInt(x));      // Jahre als Zahl
  const i25 = j.indexOf(2025), i24 = j.indexOf(2024), i17 = j.indexOf(2017);
  const i26 = j.indexOf(2026);
  const kanal = (n) => B.channelLabels.indexOf(n);
  const seg   = (n) => B.rfmSegments.find(s => s.seg === n) || {};
  const kum   = B.yearRevenue.reduce((a, b) => a + b, 0);
  const kumBest = B.yearOrders.reduce((a, b) => a + b, 0);
  const kunden = B.rfmSegments.reduce((a, s) => a + s.count, 0);
  const anteilJahr = (reihe, idx) => reihe[idx];

  const K = {};

  // ── Übersicht ───────────────────────────────────────────────────────────
  K.uebersicht1 = { wert: mio(B.yearRevenue[i25]), ...delta(B.yearRevenue[i25], B.yearRevenue[i24]),
    kontext: `vs. ${mio(B.yearRevenue[i24])} in 2024 · ${zahl(B.yearOrders[i25])} Bestellungen` };
  K.uebersicht2 = { wert: zahl(B.yearOrders[i25]), ...delta(B.yearOrders[i25], B.yearOrders[i24]),
    kontext: `vs. ${zahl(B.yearOrders[i24])} in 2024 · Ø ${zahl(B.yearOrders[i25] / 12)}/Monat` };
  K.uebersicht3 = { wert: euro(B.yearAOV[i25]), ...delta(B.yearAOV[i25], B.yearAOV[i24]),
    kontext: `vs. ${euro(B.yearAOV[i24])} in 2024 · +${proz((B.yearAOV[i25] / B.yearAOV[i17] - 1) * 100, 0)} seit 2017` };
  K.uebersicht4 = { wert: mio(kum), ...delta(B.yearRevenue[i25], B.yearRevenue[i17], v => proz(v, 0)),
    // Neben einer Bestellzahl meint "Kunden" die, die bestellt haben (24.992),
    // nicht die 25.000 Saetze in dim_customer. v_alter_umsatz zaehlt ueber
    // fact_orders und trifft damit dieselbe Menge wie die Summary-Kopfzeile.
    kontext: `${zahl(kumBest)} Bestellungen · ${zahl(roh.alterUmsatz.reduce((a, x) => a + x.kunden, 0))} Kunden · ${B.branchLabels.length} Filialen` };
  K.uebersicht5 = { kontext: `App wächst ${pp(B.appData[i25] - B.appData[i24])} YoY · Counter ${pp(B.counterData[i25] - B.counterData[i24])}` };

  const topBurger = roh.produkteJahr.filter(p => p.category === 'Burger')
    .sort((a, b) => b.menge - a.menge)[0] || {};
  const posUmsatz25 = roh.kategorien.reduce((a, x) => a + x.positionsumsatz, 0);
  K.uebersicht6 = { wert: topBurger.product_name, delta: '↑ meistverkauft', gut: true,
    kontext: `${zahl(topBurger.menge)} verkauft · ${proz(topBurger.anteil_pct)} Umsatzanteil` };

  const E = (k) => roh.einzelwerte.find(x => x.kennung === k) || {};
  const wieder = E('wiederkehrend_2025'), zufr = E('zufriedenheit_2025');
  K.uebersicht7 = { wert: proz(wieder.wert), text: pp(wieder.wert - wieder.vergleich), gut: true,
    kontext: `vs. ${proz(wieder.vergleich)} in 2024 · ${zahl(wieder.anzahl)} Stammkunden` };
  K.uebersicht8 = { wert: zahl(zufr.wert, 2) + ' / 5',
    text: (zufr.wert === zufr.vergleich ? '± 0,00'
           : (zufr.wert > zufr.vergleich ? '↑ ' : '↓ ') + zahl(Math.abs(zufr.wert - zufr.vergleich), 2)),
    gut: zufr.wert >= zufr.vergleich,
    kontext: `vs. ${zahl(zufr.vergleich, 2)} in 2024 · ${zahl(zufr.anzahl)} Bewertungen` };

  // ── Filialen ────────────────────────────────────────────────────────────
  const fTop = roh.filialen[0], fAov = [...roh.filialen].sort((a, b) => b.aov - a.aov)[0];
  const fSat = [...roh.filialen].sort((a, b) => b.zufriedenheit - a.zufriedenheit)[0];
  K.filialen1 = { wert: fTop.branch_name.replace('BM ', ''), delta: mio(fTop.umsatz), gut: true,
    kontext: `${proz(100 * fTop.umsatz / kum)} des Gesamtumsatzes · Seit ${new Date(fTop.opening_date).getFullYear()}` };
  K.filialen2 = { wert: fAov.branch_name.replace('BM ', ''), delta: euro(fAov.aov), gut: true,
    kontext: `Höchster Ø Warenkorb · Seit ${new Date(fAov.opening_date).getFullYear()}` };
  K.filialen3 = { wert: fSat.branch_name.replace('BM ', ''), delta: zahl(fSat.zufriedenheit, 2) + ' ★', gut: true,
    kontext: `Bestes Kundenfeedback · ${fSat.branch_type}-Lage` };
  const aovs = roh.filialen.map(x => x.aov);
  K.filialen4 = { wert: euro(kum / kumBest), delta: `${B.branchLabels.length} Filialen`, gut: true,
    kontext: `Ø AOV · Spreizung: ${euro(Math.min(...aovs))}–${euro(Math.max(...aovs))}` };

  // ── Produkte ────────────────────────────────────────────────────────────
  const pTop = roh.produkte[0], kTop = roh.kategorien[0];
  K.produkte1 = { wert: pTop.product_name, delta: mio(pTop.positionsumsatz), gut: true,
    kontext: `${proz(100 * pTop.positionsumsatz / posUmsatz25)} des Gesamtumsatzes · umsatzstärkstes Produkt` };
  K.produkte2 = { wert: kTop.category, delta: mio(kTop.positionsumsatz), gut: true,
    kontext: `${proz(100 * kTop.positionsumsatz / posUmsatz25)} des Gesamtumsatzes` };
  const vg = B.veggiePercent;
  K.produkte3 = { wert: proz(vg[vg.length - 1]), delta: `↑ von ${proz(vg[0])}`, gut: true,
    kontext: 'Mengenanteil veggie/vegan innerhalb der Kategorie Burger' };
  const wkTop = [...roh.warenkorb].sort((a, b) => b.gemeinsam - a.gemeinsam)[0];
  K.produkte4 = { wert: wkTop.regel.split('→')[0] + ' + ' + wkTop.regel.split('→')[1],
    delta: proz(wkTop.konfidenz_pct) + ' Conf.', gut: true,
    kontext: `${zahl(wkTop.gemeinsam)} gemeinsame Bestellungen` };

  // ── Kunden ──────────────────────────────────────────────────────────────
  const kGes = roh.kundenAlter.reduce((a, x) => a + x.kunden, 0);
  const aMax = [...roh.kundenAlter].sort((a, b) => b.kunden - a.kunden)[0];
  const u35 = roh.kundenAlter.filter(x => ['<18', '18-24', '25-34'].includes(x.altersgruppe))
    .reduce((a, x) => a + x.kunden, 0);
  const mitProgramm = roh.kundenLoyalty.filter(x => x.stufe !== 'None').reduce((a, x) => a + x.kunden, 0);
  const gold = (roh.kundenLoyalty.find(x => x.stufe === 'Gold') || {}).kunden ?? 0;
  const bez = roh.kundenBezirke, top10 = bez.slice(0, 10).reduce((a, x) => a + x.kunden, 0);
  K.kunden1 = { wert: zahl(kGes), kontext: 'Registrierte Kunden im System' };
  K.kunden2 = { wert: aMax.altersgruppe.replace('-', '–') + ' J.', delta: proz(100 * aMax.kunden / kGes), gut: true,
    kontext: `${zahl(aMax.kunden)} Kunden · Kernzielgruppe` };
  K.kunden3 = { wert: proz(100 * u35 / kGes, 0), kontext: `${zahl(u35)} von ${zahl(kGes)} · jung-urbanes Profil` };
  K.kunden4 = { wert: proz(100 * mitProgramm / kGes), delta: `${proz(100 * (kGes - mitProgramm) / kGes)} ohne Programm`, gut: true,
    kontext: `${zahl(mitProgramm)} Mitglieder · ${zahl(gold)} Gold` };
  K.kunden5 = { wert: bez[0].bezirk, delta: zahl(bez[0].kunden), gut: true,
    kontext: `${proz(100 * bez[0].kunden / kGes)} aller Kunden · Top-Bezirk` };
  K.kunden6 = { wert: proz(100 * top10 / kGes), kontext: `${zahl(top10)} von ${zahl(kGes)} Kunden in den Top 10 Bezirken` };
  K.kunden7 = { wert: '~' + zahl(Math.round(kGes / bez.length / 100) * 100),
    kontext: `Ø Kunden pro Bezirk · sehr gleichmäßig verteilt` };
  K.kunden8 = { wert: zahl(kGes - top10), delta: proz(100 * (kGes - top10) / kGes), gut: false,
    kontext: 'Kunden außerhalb der Top 10 Bezirke' };

  // ── Kanäle ──────────────────────────────────────────────────────────────
  ['Counter', 'Drive-Through', 'App', 'Kiosk'].forEach((n, idx) => {
    const k = kanal(n);
    const reihe = [B.counterData, B.driveData, B.appData, B.kioskData][idx];
    K['kanaele' + (idx + 1)] = {
      wert: proz(reihe[i25]),
      text: pp(reihe[i25] - reihe[i24]), gut: reihe[i25] >= reihe[i24],
      kontext: `${zahl(B.channelOrders2025[k])} Bestellungen · Ø AOV ${euro(B.channelAOV2025[k])} · `
        + (B.channelRevenue2025[k] >= 1e6 ? '€' + zahl(B.channelRevenue2025[k] / 1e6, 3) + 'M'
           : '€' + zahl(B.channelRevenue2025[k] / 1000, 0) + 'k') + ' Umsatz',
    };
  });

  // ── Zeitanalyse ─────────────────────────────────────────────────────────
  const wtSort = [...roh.wochentage].sort((a, b) => b.umsatz - a.umsatz);
  const stark = wtSort[0], schwach = wtSort[wtSort.length - 1];
  const TAG = { Monday: 'Montag', Tuesday: 'Dienstag', Wednesday: 'Mittwoch', Thursday: 'Donnerstag',
                Friday: 'Freitag', Saturday: 'Samstag', Sunday: 'Sonntag' };
  const stSort = [...roh.stunden].sort((a, b) => b.bestellungen - a.bestellungen)[0];
  K.zeitanalyse1 = { wert: TAG[stark.wochentag], delta: mio(stark.umsatz), gut: true,
    kontext: `${proz(100 * stark.umsatz / kum)} · ${zahl(stark.bestellungen)} Bestellungen` };
  K.zeitanalyse2 = { wert: TAG[schwach.wochentag], delta: mio(schwach.umsatz), gut: false,
    kontext: `${proz(100 * schwach.umsatz / kum)} · ${zahl(schwach.bestellungen)} Bestellungen` };
  K.zeitanalyse3 = { wert: String(stSort.stunde).padStart(2, '0') + ':00 Uhr', delta: zahl(stSort.bestellungen), gut: true,
    kontext: `${proz(100 * stSort.bestellungen / kumBest)} aller Bestellungen` };
  K.zeitanalyse4 = { wert: zahl(stark.umsatz / schwach.umsatz, 2) + '×',
    kontext: `${proz((stark.umsatz / schwach.umsatz - 1) * 100, 0)} mehr Umsatz am ${TAG[stark.wochentag]} vs. ${TAG[schwach.wochentag]}` };

  // ── Trends ──────────────────────────────────────────────────────────────
  const letzt = B.paymentYears.length - 1;
  const digital = 100 - B.cashData[letzt], digital17 = 100 - B.cashData[0];
  K.trends1 = { wert: proz(B.cashData[letzt]), delta: `↓ von ${proz(B.cashData[0])}`, gut: false,
    kontext: `${pp(B.cashData[letzt] - B.cashData[0])} seit 2017 · Cash stirbt` };
  K.trends2 = { wert: proz(B.ecData[letzt]), delta: 'Marktführer', gut: true, kontext: 'Stabiler Marktanteil seit 2021' };
  K.trends3 = { wert: proz(B.mobileData[letzt]), delta: `↑ von ${proz(B.mobileData[0])}`, gut: true,
    kontext: 'Höchster Zuwachs aller Zahlarten' };
  K.trends4 = { wert: proz(digital), kontext: `EC + Kreditkarte + Mobile · vs. ${proz(digital17)} in 2017` };
  K.trends5 = { wert: proz(B.counterData[letzt]), delta: `↓ von ${proz(Math.max(...B.counterData))}`, gut: false,
    kontext: 'Immer noch #1, aber fallend' };
  K.trends6 = { wert: proz(B.driveData[letzt]), delta: `↓ von ${proz(B.driveData[0])}`, gut: false,
    kontext: 'Starker Rückgang seit Kiosk-Einführung' };
  K.trends7 = { wert: proz(B.appData[letzt]), delta: `↑ von ${proz(B.appData[0])}`, gut: true,
    kontext: 'Schnellstwachsender Kanal · seit 2019' };
  K.trends8 = { wert: proz(B.kioskData[letzt]), kontext: 'Stabil seit 2022 · seit Einführung 2019' };

  // ── Data Mining ─────────────────────────────────────────────────────────
  const ch = seg('Champions'), risk = seg('Abwanderungsgefahr'), lost = seg('Verloren');
  const neu = seg('Neukunden');
  K.datamining1 = { wert: zahl(ch.count), delta: proz(ch.pct), gut: true,
    kontext: `Ø ${zahl(ch.avgF, 1)} Bestellungen · Ø ${euro(ch.avgM, 0)} Umsatz` };
  K.datamining2 = { wert: zahl(risk.count), delta: proz(risk.pct), gut: false,
    kontext: `Ø ${zahl(risk.avgR)} Tage inaktiv · ${mio(risk.totalM)} Umsatzrisiko` };
  K.datamining3 = { wert: zahl(lost.count), delta: proz(lost.pct), gut: false,
    kontext: `Ø ${zahl(lost.avgR)} Tage inaktiv · ${mio(lost.totalM)} verloren` };
  K.datamining4 = { wert: zahl(ch.avgM / neu.avgM, 1) + '×',
    kontext: `Champion ${euro(ch.avgM, 0)} vs. Neukunde ${euro(neu.avgM, 0)}` };
  const regeln = [...roh.warenkorb];
  const rLift = [...regeln].sort((a, b) => b.lift - a.lift)[0];
  const rSup  = [...regeln].sort((a, b) => b.gemeinsam - a.gemeinsam)[0];
  const rCross = regeln.filter(r => r.lift > 2 && r !== rLift && r !== rSup)
    .sort((a, b) => b.lift - a.lift)[0] || regeln[8];
  const kurz = (r) => r.regel.replace('→', '+');
  K.datamining5 = { wert: kurz(rLift), delta: `Lift ${zahl(rLift.lift, 2)}`, gut: true,
    kontext: `${proz(rLift.konfidenz_pct)} Confidence · ${zahl(rLift.gemeinsam)} gemeinsam` };
  K.datamining6 = { wert: kurz(rSup), delta: zahl(rSup.gemeinsam) + '×', gut: true,
    kontext: `${proz(rSup.support_pct)} Support · Lift ${zahl(rSup.lift, 2)}` };
  K.datamining7 = { wert: kurz(rCross), delta: `Lift ${zahl(rCross.lift, 2)}`, gut: true,
    kontext: `Gesundheitscluster · ${zahl(rCross.gemeinsam)} Bestellungen` };
  K.datamining8 = { wert: String(regeln.filter(r => r.lift > 2).length),
    kontext: `Von ${regeln.length} analysierten Paaren · signifikant` };

  // ── Simulation ──────────────────────────────────────────────────────────
  // Die Simulation rechnet mit Listenpreis mal Menge. Der tatsaechlich erloeste
  // Positionsumsatz liegt darunter, weil Rabatte und Aktionen abgehen. Beide
  // Groessen stehen nebeneinander, damit der Modellwert nicht fuer eine
  // Messung gehalten wird.
  const burgerMenge  = roh.simulation.reduce((a, x) => a + x.menge, 0);
  const burgerIst    = roh.simulation.reduce((a, x) => a + x.umsatz, 0);
  const burgerListe  = roh.simulation.reduce((a, x) => a + x.preis * x.menge, 0);
  const burgerKosten = roh.simulation.reduce((a, x) => a + x.kosten * x.menge, 0);
  const margeListe   = burgerListe - burgerKosten;
  const margeIst     = burgerIst - burgerKosten;
  K.simulation1 = { wert: mio(burgerListe), delta: '0%', gut: true,
    kontext: `Modell: Listenpreis × Menge · tatsächlich erlöst ${mio(burgerIst)}` };
  K.simulation2 = { wert: zahl(burgerMenge), delta: '0%', gut: true,
    kontext: `Basis: ${zahl(burgerMenge)} Stück (2017–2026)` };
  K.simulation3 = { wert: mio(margeListe), delta: '0%', gut: true,
    kontext: `zu Listenpreisen (${proz(100 * margeListe / burgerListe)}) · `
      + `auf den Ist-Umsatz gerechnet ${mio(margeIst)} (${proz(100 * margeIst / burgerIst)})` };
  K.simulation4 = { wert: euro(margeListe / burgerMenge),
    kontext: `pro Burger zu Listenpreisen · auf Ist-Umsatz ${euro(margeIst / burgerMenge)}` };

  // ── Wetter ──────────────────────────────────────────────────────────────
  const tMax = roh.wetterTemperatur.filter(x => x.tage > 0).slice(-1)[0];
  const tMin = roh.wetterTemperatur.filter(x => x.tage > 0)[1];
  const oMittel = roh.wetterTage.reduce((a, x) => a + x.umsatz, 0) / roh.wetterTage.length;
  const sonnig = roh.wetterLagen.find(x => x.wetterlage === 'Sunny');
  const schnee = roh.wetterLagen.find(x => x.wetterlage === 'Snowy');
  K.wetter1 = { wert: 'Ø ' + euro(tMax.umsatz_je_tag, 0), delta: `+${proz((tMax.umsatz_je_tag / oMittel - 1) * 100, 0)} vs. Ø`, gut: true,
    kontext: `${zahl(tMax.bestellungen_je_tag)} Bestellungen/Tag · ${tMax.tage} Tage` };
  K.wetter2 = { wert: 'Ø ' + euro(tMin.umsatz_je_tag, 0), delta: `${proz((tMin.umsatz_je_tag / oMittel - 1) * 100, 0)} vs. Ø`, gut: false,
    kontext: `${zahl(tMin.bestellungen_je_tag)} Bestellungen/Tag · ${tMin.tage} Tage` };
  K.wetter3 = { wert: '+' + proz((sonnig.umsatz_je_tag / schnee.umsatz_je_tag - 1) * 100),
    kontext: `${euro(sonnig.umsatz_je_tag, 0)} vs. ${euro(schnee.umsatz_je_tag, 0)} Ø Tagesumsatz` };
  K.wetter4 = { wert: 'r = ' + zahl(E('korr_temperatur_umsatz').wert, 3),
    kontext: 'Schwacher linearer Zusammenhang' };

  // ── Personal ────────────────────────────────────────────────────────────
  const pfSort = [...roh.personalFilialen].sort((a, b) => b.umsatz_je_ma - a.umsatz_je_ma);
  const pTopF = pfSort[0], pBotF = pfSort[pfSort.length - 1];
  const rollen = roh.personalRollen;
  const maGes = rollen.reduce((a, x) => a + x.anzahl, 0);
  const rTop3 = rollen.slice(0, 3).map(x => `${x.anzahl} ${x.bezeichnung ?? x.rolle}`).join(' · ');
  const zkSort = [...roh.zufriedenheitKanal].sort((a, b) => b.zufriedenheit - a.zufriedenheit);
  const zBest = zkSort[0], zWorst = zkSort[zkSort.length - 1];
  // Gewichtet mit der Zahl der BEWERTUNGEN, nicht der Bestellungen: nur
  // 142.317 von 754.513 Bestellungen tragen überhaupt eine Bewertung.
  const zMittel = roh.zufriedenheitKanal.reduce((a, x) => a + x.zufriedenheit * x.bewertungen, 0)
                / roh.zufriedenheitKanal.reduce((a, x) => a + x.bewertungen, 0);
  K.personal1 = { wert: euro(pTopF.umsatz_je_ma, 0),
    kontext: `pro MA · ${pTopF.mitarbeiter} Mitarbeiter · ${pTopF.branch_type}` };
  K.personal2 = { wert: euro(pBotF.umsatz_je_ma, 0),
    kontext: `pro MA · ${pBotF.mitarbeiter} Mitarbeiter · ${pBotF.branch_type}` };
  K.personal3 = { wert: 'r = ' + zahl(E('korr_wartezeit_zufriedenheit').wert, 2),
    kontext: 'Mittlere negative Korrelation (Filialmittelwerte)' };
  K.personal4 = { wert: zahl(maGes), kontext: rTop3 };
  K.personal5 = { wert: zahl(zMittel, 2), kontext: `von 5,0 · ${zahl(kumBest)} Bestellungen` };
  K.personal6 = { wert: zahl(zBest.zufriedenheit, 2), delta: `+${proz((zBest.zufriedenheit / zMittel - 1) * 100)} vs. Ø`, gut: true,
    kontext: `${zahl(zBest.bestellungen)} Bestellungen` };
  K.personal7 = { wert: zahl(zWorst.zufriedenheit, 2), delta: `${proz((zWorst.zufriedenheit / zMittel - 1) * 100)} vs. Ø`, gut: false,
    kontext: `${zahl(zWorst.bestellungen)} Bestellungen` };
  K.personal8 = { wert: 'r = ' + zahl(E('korr_dauer_zufriedenheit').wert, 3),
    kontext: 'Schwach negativ je Bestellung (aggregiert stärker)' };

  // ── Promotionen ─────────────────────────────────────────────────────────
  const pm = roh.promotionen;
  const promoBest = pm.reduce((a, x) => a + x.bestellungen, 0);
  const promoRabatt = pm.reduce((a, x) => a + x.rabattsumme, 0);
  const roiTop = [...pm].sort((a, b) => b.roi - a.roi)[0];
  const satTop = [...pm].sort((a, b) => b.zufriedenheit - a.zufriedenheit)[0];
  const kohGross = B.cohortSizes.indexOf(Math.max(...B.cohortSizes));
  K.promotions1 = { wert: zahl(promoBest), delta: `${proz(100 * promoBest / kumBest)} aller Bestellungen`, gut: true,
    kontext: `Baseline Ø ${euro(B.promoBaselineNet)} netto` };
  K.promotions2 = { wert: euro(promoRabatt, 0), kontext: `Ø ${proz(100 * promoRabatt / kum)} Discount-Rate` };
  const kurzAktion = (a) => a.split(' ')[0] + ' ';
  K.promotions3 = { wert: kurzAktion(roiTop.aktion) + roiTop.rabatt_pct + '%',
    delta: `ROI ${zahl(roiTop.roi, 1)}x`, gut: true,
    kontext: `${zahl(roiTop.bestellungen)} Bestellungen · Ø ${euro(roiTop.aov)}` };
  K.promotions4 = { wert: kurzAktion(satTop.aktion) + satTop.rabatt_pct + '%',
    delta: `Sat. ${zahl(satTop.zufriedenheit, 2)}`, gut: true,
    kontext: `${zahl(satTop.bestellungen)} Bestellungen` };
  K.promotions5 = { wert: String(B.cohortLabels[kohGross]), kontext: `${zahl(B.cohortSizes[kohGross])} Neukunden` };
  K.promotions6 = { wert: proz(E('retention_mittel').wert),
    kontext: 'Kohorte im Folgejahr wieder aktiv · exkl. 2026 (unvollständig)' };
  K.promotions7 = { wert: '~' + proz(E('aktiv_2026').wert, 0),
    kontext: 'Jan.–Apr. 2026 (Jahr läuft noch)' };
  K.promotions8 = { wert: zahl(kunden), kontext: `${B.cohortLabels.length} Kohorten · 2017–2026` };

  // ── Eintragen ───────────────────────────────────────────────────────────
  let gesetzt = 0, offen = [];
  document.querySelectorAll('[data-kpi]').forEach(karte => {
    const k = K[karte.dataset.kpi];
    if (!k) { offen.push(karte.dataset.kpi); return; }
    const w = karte.querySelector('.kpi-value');
    const d = karte.querySelector('[class^="kpi-delta"]');
    const c = karte.querySelector('.kpi-context');
    if (w && k.wert !== undefined) w.textContent = k.wert;
    if (d && (k.delta !== undefined || k.text !== undefined)) {
      d.textContent = k.delta ?? k.text;
      if (k.gut !== undefined) d.className = 'kpi-delta ' + (k.gut ? 'pos' : 'neg');
    }
    if (c && k.kontext !== undefined) c.textContent = k.kontext;
    gesetzt++;
  });

  // Die Kanalkachel hat keine einzelne Kennzahl, sondern vier Anteile neben
  // ihren Beschriftungen. Zugeordnet wird ueber die Beschriftung, nicht ueber
  // die Position — sonst verschiebt ein Umsortieren im HTML die Werte still.
  const k25 = roh.kanaeleJahr.filter(x => x.jahr === 2025);
  document.querySelectorAll('[data-kanal]').forEach(el => {
    const name = el.parentElement.querySelector('span:not(.mono)');
    const txt = name ? name.textContent.trim() : '';
    const treffer = k25.find(x => x.kanal.toLowerCase().startsWith(txt.toLowerCase()));
    if (treffer) { el.textContent = proz(treffer.anteil_pct); gesetzt++; }
  });

  // Kopfzeile der Seite.
  const kopf = document.querySelector('[data-kopf]');
  if (kopf) {
    kopf.textContent = `Burger-Filial-Performance · ${zahl(kumBest)} Bestellungen · `
      + `${B.yearLabels[0].replace('*', '')}–${B.yearLabels[B.yearLabels.length - 1].replace('*', '')}`;
    gesetzt++;
  }

  return { gesetzt, offen };
}

/*
 * Die Management Summary. Ihre Karten sind Deutungen — ein Satz Prosa je
 * Befund —, aber jede Zahl darin kommt aus der Datenbank. Der Text wird
 * deshalb hier zusammengesetzt und nicht im HTML vorgehalten.
 */
export function fuelleSummary(B, roh) {
  const zahl = (v, n = 0) => Number(v).toLocaleString('de-DE',
    { minimumFractionDigits: n, maximumFractionDigits: n }).replace('-', '−');
  const euro = (v, n = 2) => '€' + zahl(v, n);
  const proz = (v, n = 1) => zahl(v, n) + ' %';
  const E = (k) => roh.einzelwerte.find(x => x.kennung === k)
                || roh.einzelwerteZusatz.find(x => x.kennung === k) || {};
  const j = B.yearLabels.map(x => parseInt(x));
  const i25 = j.indexOf(2025), i19 = j.indexOf(2019);
  const kum = B.yearRevenue.reduce((a, b) => a + b, 0);
  const kumBest = B.yearOrders.reduce((a, b) => a + b, 0);
  const f = roh.filialen, fTop = f[0];
  const qm = [...f].sort((a, b) => b.umsatz / b.size_sqm - a.umsatz / a.size_sqm)[0];
  const pf = [...roh.personalFilialen].sort((a, b) => b.umsatz_je_ma - a.umsatz_je_ma);
  const schwach = [...f].sort((a, b) => a.umsatz - b.umsatz)[0];
  const seg = (n) => B.rfmSegments.find(s => s.seg === n) || {};
  const cagr = (Math.pow(B.yearRevenue[i25] / B.yearRevenue[i19], 1 / (2025 - 2019)) - 1) * 100;
  const kGes = roh.kundenAlter.reduce((a, x) => a + x.kunden, 0);
  const aTop = [...roh.kundenAlter].sort((a, b) => b.kunden - a.kunden)[0];
  const regeln = [...roh.warenkorb].filter(r => r.lift > 2).sort((a, b) => b.lift - a.lift);
  const pTop = [...roh.produkteJahr].sort((a, b) => b.menge - a.menge)[0];
  const zk = [...roh.zufriedenheitKanal].sort((a, b) => b.zufriedenheit - a.zufriedenheit);
  const zMittel = roh.zufriedenheitKanal.reduce((a, x) => a + x.zufriedenheit * x.bewertungen, 0)
                / roh.zufriedenheitKanal.reduce((a, x) => a + x.bewertungen, 0);
  const sats = f.map(x => x.zufriedenheit);
  const pm = roh.promotionen, promoBest = pm.reduce((a, x) => a + x.bestellungen, 0);
  const promoRabatt = pm.reduce((a, x) => a + x.rabattsumme, 0);
  const roiTop = [...pm].sort((a, b) => b.roi - a.roi)[0];
  const roiFlop = [...pm].sort((a, b) => a.roi - b.roi)[0];
  const sonnig = roh.wetterLagen.find(x => x.wetterlage === 'Sunny');
  const schnee = roh.wetterLagen.find(x => x.wetterlage === 'Snowy');
  const tExtrem = [...roh.wetterTemperatur].filter(x => x.tage > 0)
    .sort((a, b) => b.umsatz_je_tag - a.umsatz_je_tag)[0];
  const kanalMin = [...roh.zufriedenheitKanal].sort((a, b) => a.bestellungen - b.bestellungen)[0];
  const posGes = roh.kategorien.reduce((a, x) => a + x.positionsumsatz, 0);

  const items  = roh.produkteJahr.reduce((a, x) => a + x.menge, 0);
  const salat = roh.warenkorb.find(r => /Salad/.test(r.regel)) || {};

  // Fuer die sechs breiten Karten.
  const hb = roh.heimatbezirk[0] ?? {};
  const aU = [...roh.alterUmsatz].sort((a, b) => b.umsatz - a.umsatz);
  const typVon = (name) => (f.find(x => x.branch_name === name) || {}).branch_type ?? '—';
  // Randklassen der Temperatur: die zwei hoechsten Tagesumsaetze. Beide ruhen
  // auf wenigen Tagen — genau das ist die Aussage der Karte.
  const tX = [...roh.wetterTemperatur].sort((a, b) => b.umsatz_je_tag - a.umsatz_je_tag).slice(0, 2);
  // Zahlarten-Trend: erstes gegen letztes Jahr der Reihe. Anteile, keine
  // absoluten Zahlen, damit ein angebrochenes letztes Jahr nicht stoert.
  const zaJahre = [...new Set(roh.zahlartenJahr.map(x => x.jahr))].sort((a, b) => a - b);
  const zaErst = zaJahre[0], zaLetzt = zaJahre[zaJahre.length - 1];
  const zaAnteil = (art, jahr) => (roh.zahlartenJahr
    .find(x => x.zahlart === art && x.jahr === jahr) || {}).anteil_pct ?? 0;
  const zaOben = [...roh.zahlartenJahr].filter(x => x.jahr === zaLetzt)
    .sort((a, b) => b.anteil_pct - a.anteil_pct)[0];

  const S = {
    1: [proz(cagr) + ' p.a.', `CAGR 2019–2025 (ab dem ersten Jahr mit vier Filialen). `
      + `Getrieben von Filialexpansion (1 → ${f.length} Standorte bis 2023) und organischem Wachstum.`],
    2: [euro(kum / kumBest), `Ø Netto-Bestellwert (AOV). Spanne: ${euro(Math.min(...f.map(x => x.aov)))} `
      + `bis ${euro(Math.max(...f.map(x => x.aov)))}.`],
    3: [zahl(E('artikel_je_bestellung').wert, 2) + ' Artikel',
      `Mittlere Zahl verschiedener Artikel je Bestellung `
      + `(Ø ${zahl(E('stueck_je_bestellung').wert, 2)} Stück inkl. Mengen).`],
    4: [E('spitzenquartal').text ?? 'Q3 Peak',
      `Saisonaler Umsatzhöhepunkt — stärkstes Quartal in `
      + `${zahl(E('spitzenquartal').anzahl)} von ${zahl(E('spitzenquartal').vergleich)} vollen Jahren.`],
    5: [proz(100 * fTop.umsatz / kum), `${fTop.branch_name} — ${euro(fTop.umsatz / 1e6, 2)} Mio. `
      + `Umsatzanteil. ${fTop.branch_type}-Lage, ${fTop.size_sqm} m².`],
    6: [euro(qm.umsatz / qm.size_sqm, 0) + '/m²', `${qm.branch_name} — Raumproduktivität `
      + `Spitzenwert auf nur ${qm.size_sqm} m².`],
    7: ['€' + zahl(pf[0].umsatz_je_ma / 1000, 0) + 'k/MA', `${pf[0].branch_name} vs. `
      + `${pf[pf.length - 1].branch_name} — MA-Produktivität ${euro(pf[0].umsatz_je_ma, 0)} vs. `
      + `${euro(pf[pf.length - 1].umsatz_je_ma, 0)}. Faktor `
      + `${zahl(pf[0].umsatz_je_ma / pf[pf.length - 1].umsatz_je_ma, 1)}.`],
    8: [proz(100 * schwach.umsatz / kum), `${schwach.branch_name} — niedrigster Umsatz `
      + `(${euro(schwach.umsatz / 1000, 0)}k) trotz hohem AOV (${euro(schwach.aov)}).`],
    9: [proz(E('retention_mittel').wert), 'Kohorten-Retention im Folgejahr, gemittelt über '
      + 'alle Jahrgänge 2017–2026.'],
    10: [zahl(kumBest / kGes, 1) + ' Best./Kunde', 'Ø Bestellhäufigkeit über den gesamten '
      + 'Beobachtungszeitraum.'],
    11: [proz(seg('Champions').pct) + ' Champions',
      'RFM-Segment mit höchster Kauffrequenz, höchstem Monetary-Wert und jüngstem Kauf.'],
    12: [proz(seg('Abwanderungsgefahr').pct) + ' at Risk',
      `Abwanderungsgefahr — ${zahl(seg('Abwanderungsgefahr').count)} Kunden, `
      + `Ø ${zahl(seg('Abwanderungsgefahr').avgR)} Tage inaktiv. Reaktivierung erforderlich.`],
    13: [pTop.product_name, `Meistverkauftes Produkt nach Absatzmenge `
      + `(${zahl(pTop.menge)} Stk. in 2025).`],
    14: [roh.produkte[0].product_name, `Umsatzstärkstes Produkt mit `
      + `${proz(100 * roh.produkte[0].positionsumsatz / posGes)} des Positionsumsatzes.`
      + (salat.lift ? ` Affinität zu Salat (Lift ${zahl(salat.lift, 2)}).` : '')],
    15: [proz(100 * kanalMin.bestellungen / kumBest) + ' '
      + (kanalMin.kanal === 'App Order' ? 'App' : kanalMin.kanal),
      `Höchste Zufriedenheit (Ø ${zahl(zk[0].zufriedenheit, 1)}/5) — aber am wenigsten genutzter Kanal.`],
    16: [zahl(zk[zk.length - 1].zufriedenheit, 2) + ' ' + zk[zk.length - 1].kanal,
      'Niedrigster Zufriedenheitswert aller Kanäle. Hauptbestellweg.'],
    17: ['+' + proz((sonnig.umsatz_je_tag / schnee.umsatz_je_tag - 1) * 100),
      `Umsatzaufschlag Sunny vs. Snowy (${euro(sonnig.umsatz_je_tag, 0)} vs. `
      + `${euro(schnee.umsatz_je_tag, 0)} Ø Tagesumsatz).`],
    18: ['r = ' + zahl(E('korr_temperatur_umsatz').wert, 3),
      'Korrelation Temperatur ↔ Tagesumsatz nahe null. Wachstumstrend überlagert Wettereffekt.'],
    19: ['r = ' + zahl(E('korr_wartezeit_zufriedenheit').wert, 2),
      'Wartezeit ↔ Zufriedenheit, auf Filialmittelwerten gerechnet.'],
    20: ['Ø ' + zahl(zMittel, 2), `Gesamtzufriedenheit (5er-Skala). Streuung `
      + `${zahl(Math.min(...sats), 2)}–${zahl(Math.max(...sats), 2)} zwischen Standorten.`],
    21: [proz(100 * promoBest / kumBest), `Promo-Quote. Nur jede `
      + `${zahl(kumBest / promoBest, 0)}. Bestellung nutzt eine Aktion.`],
    22: ['Ø ' + euro(B.promoBaselineNet) + ' Baseline',
      `AOV ohne Promotion (${zahl(kumBest - promoBest)} Bestellungen).`],
    23: [zahl(roiTop.roi, 1) + '× ROI', `${roiTop.aktion} — höchster Umsatz je Rabatt-Euro. `
      + `Geringe Rabatthöhe bei hoher Frequenz.`],
    24: [zahl(roiFlop.roi, 1) + '× ROI', `${roiFlop.aktion} — niedrigster Wert. `
      + `Hoher Rabatt ohne nachweislichen Zusatzumsatz.`],

    // 25–30: die sechs breiten Karten am Ende jedes Blocks.
    25: [proz(hb.anteil_pct), `Anteil der Bestellungen, bei denen Wohnbezirk des Kunden und `
      + `Bezirk der Filiale übereinstimmen — ${zahl(hb.aus_heimatbezirk)} von `
      + `${zahl(hb.bestellungen)}. Die ${zahl(hb.filialbezirke)} Standorte bedienen `
      + `${zahl(hb.wohnbezirke)} Wohnbezirke: das Einzugsgebiet ist überregional, `
      + `nicht die Nachbarschaft.`],
    26: [aU[0].altersgruppe + ' Jahre', `Umsatzstärkste Altersgruppe mit `
      + `${proz(aU[0].umsatzanteil_pct)} des Gesamtumsatzes, gefolgt von `
      + `${aU[1].altersgruppe} J. (${proz(aU[1].umsatzanteil_pct)}). Zusammen `
      + `${proz(aU[0].umsatzanteil_pct + aU[1].umsatzanteil_pct)} — die Nachfrage `
      + `verteilt sich breiter, als eine Zielgruppe nahelegt.`],
    27: [`${zahl(regeln.length)} Regeln mit Lift > 2,0`,
      regeln.map(r => `${r.produkt_a} ↔ ${r.produkt_b} (${zahl(r.lift, 2)})`).join(' · ')
      + `. Die übrigen ${zahl(roh.warenkorb.length - regeln.length)} der `
      + `${zahl(roh.warenkorb.length)} geprüften Regeln liegen nahe Lift 1 — `
      + `dort kauft niemand das eine wegen des anderen.`],
    28: [`${zaOben.zahlart === 'Cash' ? 'Bargeld' : 'Kartenzahlung'} ↑`,
      `Anteil an allen Bestellungen von ${zaErst} auf ${zaLetzt}: Bargeld `
      + `${proz(zaAnteil('Cash', zaErst))} → ${proz(zaAnteil('Cash', zaLetzt))}, `
      + `Mobile Payment ${proz(zaAnteil('Mobile Payment', zaErst))} → `
      + `${proz(zaAnteil('Mobile Payment', zaLetzt))}. Der Rückgang ist strukturell, `
      + `nicht saisonal.`],
    29: ['Extremwerte', `Höchste Tagesumsätze in den Randklassen: `
      + `${zahl(tX[0].von, 1)} bis ${zahl(tX[0].bis, 1)} °C (${euro(tX[0].umsatz_je_tag, 0)}) `
      + `und ${zahl(tX[1].von, 1)} bis ${zahl(tX[1].bis, 1)} °C `
      + `(${euro(tX[1].umsatz_je_tag, 0)}). Beide stützen sich auf `
      + `${zahl(tX[0].tage)} bzw. ${zahl(tX[1].tage)} Tage — zu wenig für eine `
      + `Aussage über Temperatur, wahrscheinlich Sondereffekte.`],
    30: [zahl(pf[0].umsatz_je_ma / pf[pf.length - 1].umsatz_je_ma, 1) + '× Spreizung',
      `MA-Produktivität: ${euro(pf[0].umsatz_je_ma / 1000, 0)}k (${pf[0].branch_name}) `
      + `gegen ${euro(pf[pf.length - 1].umsatz_je_ma / 1000, 0)}k `
      + `(${pf[pf.length - 1].branch_name}). Erklärbar durch Standorttyp `
      + `(${typVon(pf[0].branch_name)} gegen ${typVon(pf[pf.length - 1].branch_name)}) `
      + `und Kundenfrequenz, nicht primär durch Personalleistung.`],
  };

  // Kopfzeile der Summary. "Unique Kunden" meint die Kunden MIT Bestellung
  // (24.992), nicht die 25.000 Saetze in dim_customer — acht Kunden haben nie
  // gekauft. Die RFM-Segmente decken genau die kaufenden Kunden ab.
  const kaufende = B.rfmSegments.reduce((a, s) => a + s.count, 0);
  const hero = [
    [zahl(kum / 1e6, 1), 'Mio. €'], [zahl(kumBest), ''], [zahl(kaufende), ''], [String(f.length), ''],
  ];
  // Der Wert steht vor der Einheit (<span class="ms-hero-unit">). Im HTML gibt
  // es dafuer keinen Platzhaltertext mehr, also wird der Textknoten angelegt,
  // wenn er fehlt.
  document.querySelectorAll('#summary .ms-hero-val').forEach((e, k) => {
    if (!hero[k]) return;
    const erst = e.firstChild;
    if (erst && erst.nodeType === Node.TEXT_NODE) erst.nodeValue = hero[k][0];
    else e.insertBefore(document.createTextNode(hero[k][0]), e.firstChild);
  });

  // Spreizungs-Marke auf der Personalkarte und die Fusszeile.
  const spreiz = document.querySelector('[data-tag="spreizung"]');
  if (spreiz) spreiz.textContent =
    zahl(pf[0].umsatz_je_ma / pf[pf.length - 1].umsatz_je_ma, 1) + '× GAP';
  const fuss = document.querySelector('[data-fuss]');
  if (fuss) fuss.textContent = 'Fiktives Unternehmen — BI-Kurs THWS Würzburg · '
    + `Prof. Robert Butscher \u00a0|\u00a0 ${zahl(kumBest)} Bestellungen · `
    + `${B.yearLabels[0].replace('*', '')}–${B.yearLabels[B.yearLabels.length - 1].replace('*', '')}`
    + ' · Erstellt mit Chart.js';

  let gesetzt = 0;
  document.querySelectorAll('[data-ms]').forEach(karte => {
    const e = S[Number(karte.dataset.ms)];
    if (!e) return;
    const v = karte.querySelector('.ms-card-val');
    const t = karte.querySelector('.ms-card-text');
    if (v) v.textContent = e[0];
    if (t) t.textContent = e[1];
    gesetzt++;
  });
  return gesetzt;
}
