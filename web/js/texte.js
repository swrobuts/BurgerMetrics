// texte.js — die Fliesstexte des Dashboards aus den Daten erzeugen.
//
// Kacheln und Diagramme holen ihre Zahlen seit dem Umbau aus der Datenquelle.
// Die Deutungs- und Empfehlungstexte taten das nicht: dort standen Zahlen als
// Buchstaben im HTML. Ein Text, der "5.484 abwanderungsgefaehrdete Kunden"
// behauptet, waehrend das Diagramm daneben 4.998 zeichnet, ist schlimmer als
// gar kein Text — er sieht aus wie eine Quelle.
//
// Deshalb wird hier jeder Satz gebaut, der eine Zahl enthaelt. Rein
// methodische Saetze ("Nullpunkt auf der Achse, weil ...") bleiben im HTML,
// wo sie hingehoeren: sie sind keine Daten.
//
// Der Schluessel ist das data-txt-Attribut am jeweiligen Textfeld, in der Form
// <canvas-id>.<feld> — zum Beispiel data-txt="revenueChart.deutung".

const zahl = (v, n = 0) => Number(v).toLocaleString('de-DE',
  { minimumFractionDigits: n, maximumFractionDigits: n }).replace('-', '−');
const euro = (v, n = 2) => '€' + zahl(v, n);
const proz = (v, n = 1) => zahl(v, n) + ' %';
const mio  = (v) => euro(v / 1e6, 2) + ' Mio.';
const tsd  = (v) => '€' + zahl(v / 1000, 0) + 'k';
// Vorzeichen mitschreiben, damit ein Rueckgang als solcher lesbar ist.
const vz   = (v, n = 1) => (v >= 0 ? '+' : '') + zahl(v, n) + ' %';

export function baueTexte(B, roh) {
  const T = {};
  const j = B.yearLabels.map(x => parseInt(x));
  const iL = (jahr) => j.indexOf(jahr);
  const letztesVoll = 2025;
  const iV = iL(letztesVoll);
  const kum = B.yearRevenue.reduce((a, b) => a + b, 0);
  const kumBest = B.yearOrders.reduce((a, b) => a + b, 0);
  const f = roh.filialen;
  const fUmsatz = [...f].sort((a, b) => b.umsatz - a.umsatz);
  const aovNetz = kum / kumBest;

  // ── Umsatz ───────────────────────────────────────────────────────────────
  // Monatsreihe: Tiefpunkt, Hochpunkt und der Einbruch im April 2020.
  const mx = B.mRevenue.indexOf(Math.max(...B.mRevenue));
  // Der niedrigste Monat der Reihe ist der Gruendungsmonat, nicht die Pandemie
  // — deshalb wird April 2020 ausdruecklich gesucht statt das Minimum genommen.
  const iApr20 = B.mLabels.findIndex(x => /2020.0?4/.test(x));
  const momApr = iApr20 > 0
    ? (B.mRevenue[iApr20] / B.mRevenue[iApr20 - 1] - 1) * 100 : null;

  T['revenueChart.deutung'] =
    (iApr20 > 0
      ? `Der tiefste Einschnitt der Reihe ist ${B.mLabels[iApr20]} mit `
        + `${tsd(B.mRevenue[iApr20])}, ${vz(momApr)} gegenüber dem Vormonat — die `
        + `Schließungen der Pandemie. `
      : '')
    + `Der stärkste Monat ist ${B.mLabels[mx]} mit ${tsd(B.mRevenue[mx])}. `
    + `Dazwischen liegt eine Erholung, die sich verlangsamt: Der Jahresumsatz wuchs `
    + `${letztesVoll} noch um ${vz(B.revYoY[B.revYoY.length - 1])}, in der Frühphase `
    + `um ${vz(B.revYoY[0])}. Die Expansion erreicht ein Plateau.`;
  T['revenueChart.empfehlung'] =
    `Mit ${f.length} Standorten in Würzburg ist das Wachstum durch Neueröffnungen `
    + `weitgehend ausgereizt. Bleiben zwei Hebel: der Bestellwert — ein Euro mehr je `
    + `Bestellung entspräche bei ${zahl(B.yearOrders[iV])} Bestellungen im Jahr `
    + `${letztesVoll} rund ${tsd(B.yearOrders[iV])} zusätzlichem Umsatz — oder `
    + `Standorte außerhalb der Stadt.`;

  // ── Bestellwert ──────────────────────────────────────────────────────────
  const aovErst = B.yearAOV[0], aovLetzt = B.yearAOV[B.yearAOV.length - 1];
  // Fuer die Ueberschrift das letzte vollstaendige Jahr, damit ein angebrochenes
  // Jahr die Aussage nicht verzerrt.
  const aovVoll = B.yearAOV[iV];
  const aovMaxJahr = B.aovYoY.indexOf(Math.max(...B.aovYoY));
  const combo = roh.warenkorb.find(r => /Medium Fries/.test(r.produkt_a)) || {};

  T['aovChart.titel'] =
    `Ø Bestellwert stieg um ${zahl((aovVoll / aovErst - 1) * 100, 0)} % seit Gründung`;
  // Dasselbe Bezugsjahr wie in der Ueberschrift. Vorher stand hier das
  // angebrochene Jahr: 14,50 auf 22,48 sind +55 %, waehrend die Ueberschrift
  // mit dem letzten vollen Jahr +51 % auswies — zwei Zahlen zu einem Diagramm,
  // die sich widersprachen.
  T['aovChart.deutung'] =
    `Der Bestellwert stieg von ${euro(aovErst)} (${j[0]}) auf ${euro(aovVoll)} `
    + `(${letztesVoll}); im angebrochenen Jahr ${j[j.length - 1]} liegt er bei `
    + `${euro(aovLetzt)}. Den größten Sprung brachte ${j[aovMaxJahr + 1]} mit `
    + `${vz(B.aovYoY[aovMaxJahr])}. Seither flacht die Kurve ab `
    + `(${letztesVoll}: ${vz(B.aovYoY[B.aovYoY.length - 1])}) — ein Hinweis darauf, `
    + `dass die Zahlungsbereitschaft in dieser Preislage begrenzt ist.`;
  T['aovChart.empfehlung'] =
    `Statt am Preis am Warenkorb ansetzen: ${zahl(combo.konfidenz_pct, 1)} % derer, die `
    + `${combo.produkt_a} kaufen, nehmen ${combo.produkt_b} dazu (Lift `
    + `${zahl(combo.lift, 2)}). Ein Kombiangebot bündelt einen Kauf, der ohnehin `
    + `stattfindet, und hebt den Bestellwert, ohne die Preiswahrnehmung zu belasten.`;

  // ── Bestellungen ─────────────────────────────────────────────────────────
  const ordLetzt = B.ordYoY[B.ordYoY.length - 1];
  const ordMax = Math.max(...B.ordYoY);
  const loyal = roh.kundenLoyalty.reduce((a, x) => a + x.kunden, 0);
  const ohneStufe = roh.kundenLoyalty.find(x => /kein|ohne|none/i.test(x.stufe));
  const imProgramm = loyal - (ohneStufe ? ohneStufe.kunden : 0);

  T['ordersChart.titel'] = `Bestellwachstum verlangsamt sich auf ${vz(ordLetzt)}`;
  T['ordersChart.deutung'] =
    `${letztesVoll} wurden ${zahl(B.yearOrders[iV])} Bestellungen verarbeitet — ein `
    + `Höchststand, aber nur ${vz(ordLetzt)} gegenüber dem Vorjahr. In der Frühphase `
    + `lag das Wachstum bei ${vz(ordMax)}. Der Markt in Würzburg nähert sich der `
    + `Sättigung. Für ${j[j.length - 1]} sind bislang ${zahl(B.yearOrders[j.length - 1])} `
    + `Bestellungen verbucht; das Jahr ist noch nicht vollständig.`;
  T['ordersChart.empfehlung'] =
    `Frequenz statt Neukunden: ${proz(100 * imProgramm / loyal)} der ${zahl(loyal)} `
    + `angelegten Kundenkonten haben eine Treuestufe. Eine Punkteaktion im ersten `
    + `Quartal träfe genau die schwächste Jahreszeit.`;

  // ── Wachstum synchron ────────────────────────────────────────────────────
  T['yoyChart.deutung'] =
    `Alle drei Kurven zeigen dasselbe Muster: eine explosive Frühphase `
    + `(${vz(B.revYoY[0])} Umsatz), den Einbruch ${j[iL(2020)]} `
    + `(${vz(B.revYoY[iL(2020) - 1])}), die Erholung ${j[iL(2021)]} `
    + `(${vz(B.revYoY[iL(2021) - 1])}) und seither eine stetige Verlangsamung. `
    + `${letztesVoll} wächst der Umsatz um ${vz(B.revYoY[B.revYoY.length - 1])} — `
    + `davon ${vz(B.aovYoY[B.aovYoY.length - 1])} aus dem Bestellwert und `
    + `${vz(B.ordYoY[B.ordYoY.length - 1])} aus der Menge. Das Wachstum ist `
    + `preisgetrieben, nicht mengengetrieben.`;
  T['yoyChart.empfehlung'] = (() => {
    const kj = roh.kanaeleJahr.filter(x => x.jahr === letztesVoll);
    const kv = roh.kanaeleJahr.filter(x => x.jahr === letztesVoll - 1);
    const wachstum = kj.map(x => {
      const v = kv.find(y => y.kanal === x.kanal);
      return { kanal: x.kanal, pct: v ? (x.bestellungen / v.bestellungen - 1) * 100 : 0 };
    }).sort((a, b) => b.pct - a.pct);
    return `Um die Menge wiederzubeleben, bieten sich zwei Hebel an: der `
      + `${wachstum[0].kanal}-Kanal, der ${letztesVoll} um ${vz(wachstum[0].pct)} zulegte `
      + `und damit am schnellsten wächst, und Standorte außerhalb Würzburgs.`;
  })();

  // ── Umsatz je Filiale ────────────────────────────────────────────────────
  const fMin = fUmsatz[fUmsatz.length - 1], fMax = fUmsatz[0];
  const fJung = [...f].sort((a, b) => a.betriebsjahre - b.betriebsjahre)[0];

  T['yoyBranchChart.titel'] =
    `Umsatz pro Filiale — Spreizung von ${tsd(fMin.umsatz)} bis ${mio(fMax.umsatz)}, `
    + `geprägt von der Betriebsdauer`;
  T['yoyBranchChart.deutung'] =
    `${fMax.branch_name} führt mit ${mio(fMax.umsatz)} (${proz(100 * fMax.umsatz / kum)} `
    + `Anteil) vor ${fUmsatz[1].branch_name} (${mio(fUmsatz[1].umsatz)}) und `
    + `${fUmsatz[2].branch_name} (${mio(fUmsatz[2].umsatz)}). Der Vorsprung ist `
    + `allerdings zur Hälfte Vorsprung an Zeit: ${fMax.branch_name} läuft seit `
    + `${zahl(fMax.betriebsjahre)} Jahren und hat dabei einen Bestellwert von `
    + `${euro(fMax.aov)}. ${fJung.branch_name}, erst ${zahl(fJung.betriebsjahre)} Jahre `
    + `offen, kommt auf ${mio(fJung.umsatz)} bei ${euro(fJung.aov)} je Bestellung — `
    + `das wirtschaftlichere Profil.`;
  T['yoyBranchChart.empfehlung'] = (() => {
    // Umsatz je Betriebsjahr statt Gesamtumsatz oder Bestellwert: Der
    // Gesamtumsatz belohnt Alter, der Bestellwert allein die kleinste Filiale.
    const vorbild = [...f].sort((a, b) => b.umsatz / b.betriebsjahre
                                        - a.umsatz / a.betriebsjahre)[0];
    const luecke = (aovNetz - fMax.aov) * fMax.bestellungen;
    return `${vorbild.branch_name} setzt je Betriebsjahr `
      + `${tsd(vorbild.umsatz / vorbild.betriebsjahre)} um, mehr als jede andere `
      + `Filiale, bei ${euro(vorbild.aov)} je Bestellung — die ${vorbild.branch_type}-Lage `
      + `taugt als Vorlage für neue Standorte. ${fMax.branch_name} liegt mit `
      + `${euro(fMax.aov)} unter dem Netzdurchschnitt von ${euro(aovNetz)}; auf `
      + `Durchschnitt gehoben wären das bei ${zahl(fMax.bestellungen)} Bestellungen `
      + `rund ${tsd(Math.abs(luecke))} ${luecke > 0 ? 'mehr' : 'weniger'} Umsatz.`;
  })();

  // Die Ueberschrift der Stundenkurve behauptete einen Faktor 3. Er stimmt —
  // aber nur fuer den Blockvergleich Mittag gegen Frueh, nicht fuer einzelne
  // Stunden (dort waeren es 6,4). Deshalb nennt der Titel jetzt die Fenster.
  const stdMittag = roh.stunden.filter(x => x.stunde >= 11 && x.stunde <= 14)
    .reduce((a, x) => a + x.umsatz, 0);
  const stdFrueh = roh.stunden.filter(x => x.stunde < 11)
    .reduce((a, x) => a + x.umsatz, 0);
  T['hourChart.titel'] =
    `Das Mittagsfenster 11–14 Uhr setzt ${zahl(stdMittag / stdFrueh, 1)}× so viel `
    + 'um wie der gesamte Vormittag';

  // ═══ Reiter, aus Fragmenten zusammengesetzt ═══

  // ── Reiter filialen ────────────────────────────────────────────────
  // ── Filialen ─────────────────────────────────────────────────────────────
    // Bezugsgroesse fuer jeden Filialvergleich ist der Umsatz je Betriebsjahr.
    // Der kumulierte Umsatz misst vor allem, wie lange ein Standort schon
    // geoeffnet ist; eine Rangfolge daraus ist eine Rangfolge des Alters.
    const flF = roh.filialen;
    const flKum = flF.reduce((a, x) => a + x.umsatz, 0);
    const flBestGes = flF.reduce((a, x) => a + x.bestellungen, 0);
    const flAovNetz = flBestGes > 0 ? flKum / flBestGes : 0;
    const flJeJahr = (x) => x.betriebsjahre > 0 ? x.umsatz / x.betriebsjahre : 0;
    const flMitteJeJahr = flF.length > 0
      ? flF.reduce((a, x) => a + flJeJahr(x), 0) / flF.length : 0;
    const flNachUmsatz = [...flF].sort((a, b) => b.umsatz - a.umsatz);
    const flNachJahr = [...flF].sort((a, b) => flJeJahr(b) - flJeJahr(a));
    const flNachAov = [...flF].sort((a, b) => a.aov - b.aov);
    const flNachDatum = [...flF].sort((a, b) =>
      String(a.opening_date) < String(b.opening_date) ? -1 : 1);
    const flUeberMitte = flF.filter(x => flJeJahr(x) > flMitteJeJahr);
    const flSpitze = flNachJahr[0];
    const flZweit = flNachJahr[1] ?? flNachJahr[0];
    const flSchluss = flNachJahr[flNachJahr.length - 1];
    const flErsterUnterMitte = flNachJahr[flUeberMitte.length] ?? flSchluss;
    const flAovMin = flNachAov[0];
    const flAovMax = flNachAov[flNachAov.length - 1];
    const flAovZweit = flNachAov[flNachAov.length - 2] ?? flAovMax;
    const flAelteste = flNachDatum[0];
    const flJuengste = flNachDatum[flNachDatum.length - 1];
    const flTypen = [...new Set(flF.map(x => x.branch_type))];
    const flJahrVon = (x) => String(x.opening_date).slice(0, 4);
    const flAlt = flF.filter(x => parseInt(String(x.opening_date).slice(0, 4)) < 2020);
    const flAltUmsatz = flAlt.reduce((a, x) => a + x.umsatz, 0);
    const flTop3 = flNachUmsatz.slice(0, 3).reduce((a, x) => a + x.umsatz, 0);
    const flRangSpitze = flNachUmsatz.indexOf(flSpitze) + 1;
    const flAovRangJuengste = flNachAov.length - flNachAov.indexOf(flJuengste);

    T['branchChart.deutung'] =
      `Die Rangfolge im kumulierten Umsatz bildet vor allem die Betriebsdauer ab: `
      + `Die ${zahl(flAlt.length)} vor 2020 eröffneten Standorte tragen `
      + `${proz(100 * flAltUmsatz / flKum)} der ${mio(flKum)} Gesamtumsatz, die drei `
      + `umsatzstärksten ${proz(100 * flTop3 / flKum)}. Je Betriebsjahr gerechnet führt `
      + `dagegen ${flSpitze.branch_name} mit ${tsd(flJeJahr(flSpitze))} nach `
      + `${zahl(flSpitze.betriebsjahre)} Jahren; im kumulierten Umsatz steht der `
      + `Standort auf Rang ${zahl(flRangSpitze)}. ${flJuengste.branch_name}, seit `
      + `${flJahrVon(flJuengste)} geöffnet, liegt im Gesamtumsatz hinten, erreicht beim `
      + `Bestellwert mit ${euro(flJuengste.aov)} aber Rang ${zahl(flAovRangJuengste)} `
      + `von ${zahl(flF.length)} und damit einen Wert `
      + `${flJuengste.aov >= flAovNetz ? 'über' : 'unter'} dem Netzmittel von `
      + `${euro(flAovNetz)}.`;

    T['branchChart.empfehlung'] =
      `Filialziele auf den Umsatz je Betriebsjahr umstellen statt auf den kumulierten `
      + `Umsatz, der das Alter des Standorts belohnt. Gemessen daran liegen `
      + `${zahl(flUeberMitte.length)} der ${zahl(flF.length)} Filialen über dem `
      + `Netzmittel von ${tsd(flMitteJeJahr)}, angeführt von ${flSpitze.branch_name} mit `
      + `${tsd(flJeJahr(flSpitze))}; ${flSchluss.branch_name} kommt auf `
      + `${tsd(flJeJahr(flSchluss))}. Als Erfolgsmaß dient, ob eine Filiale nach jedem `
      + `abgeschlossenen Geschäftsjahr über diesem Mittelwert liegt.`;

    // Kanal-AOV netzweit ueber alle Jahre, weil die Sicht nur je Jahr vorliegt.
    const flKanalSumme = roh.kanaeleJahr.reduce((m, x) => {
      const e = m[x.kanal] || (m[x.kanal] = { best: 0, ums: 0 });
      e.best += x.bestellungen; e.ums += x.umsatz; return m;
    }, {});
    const flKanalAov = (n) => {
      const e = flKanalSumme[n];
      return e && e.best > 0 ? e.ums / e.best : 0;
    };

    T['filialen_tabelle1.deutung'] =
      `Farbcodierung AOV: Grün = über dem Netzmittel von ${euro(flAovNetz)}, Rot = `
      + `darunter. Die Spanne reicht von ${euro(flAovMin.aov)} `
      + `(${flAovMin.branch_name}) bis ${euro(flAovMax.aov)} (${flAovMax.branch_name}), `
      + `ein Abstand von ${proz(100 * (flAovMax.aov / flAovMin.aov - 1))}. Der `
      + `Filialtyp erklärt diese Spanne nicht: Die ${zahl(flF.length)} Standorte `
      + `verteilen sich auf ${zahl(flTypen.length)} verschiedene Typen, jeder Typ tritt `
      + `also ${flTypen.length === flF.length ? 'genau einmal' : 'nur vereinzelt'} auf.`
      + (flKanalAov('Drive-Through') > 0 && flKanalAov('Counter') > 0
        ? ` Auch der Bestellkanal trägt wenig bei: Drive-Through liegt netzweit bei `
          + `${euro(flKanalAov('Drive-Through'))} je Bestellung, Counter bei `
          + `${euro(flKanalAov('Counter'))}.`
        : '');

    // Groesster Rueckschritt im Bestellwert zwischen zwei nacheinander eroeffneten
    // Filialen — belegt, dass das Eroeffnungsjahr keine Reihenfolge erzwingt.
    const flBruch = (() => {
      let beste = null;
      for (let i = 1; i < flNachDatum.length; i++) {
        const d = flNachDatum[i - 1].aov - flNachDatum[i].aov;
        if (d > 0 && (beste === null || d > beste.d)) {
          beste = { d, vor: flNachDatum[i - 1], nach: flNachDatum[i] };
        }
      }
      return beste;
    })();

    T['branchAovChart.deutung'] =
      `Der Bestellwert steigt im Trend mit dem Eröffnungsjahr, aber nicht Schritt für `
      + `Schritt. Oben liegen ${flAovMax.branch_name} (${flJahrVon(flAovMax)}, `
      + `${euro(flAovMax.aov)}) und ${flAovZweit.branch_name} `
      + `(${flJahrVon(flAovZweit)}, ${euro(flAovZweit.aov)}); den niedrigsten Wert hat `
      + `mit ${euro(flAovMin.aov)} ${flAovMin.branch_name} `
      + `(${flJahrVon(flAovMin)})${flAovMin === flAelteste ? '' : `, nicht die `
        + `Gründungsfiliale ${flAelteste.branch_name}, die auf `
        + `${euro(flAelteste.aov)} kommt`}.`
      + (flBruch ? ` Die Reihenfolge bricht bei ${flBruch.nach.branch_name} `
          + `(${flJahrVon(flBruch.nach)}), das trotz späterer Eröffnung `
          + `${euro(flBruch.d)} unter ${flBruch.vor.branch_name} liegt.` : '')
      + ` Das Eröffnungsjahr allein erklärt den Bestellwert also nicht.`;

    // Bestellungen je Betriebsjahr als Basis: Die Spalte bestellungen ist ueber
    // die gesamte Laufzeit kumuliert, ein Jahreswert waere sonst zu hoch.
    const flUnter = flF.filter(x => x.aov < flAovNetz)
      .map(x => ({
        f: x,
        luecke: (flAovNetz - x.aov)
          * (x.betriebsjahre > 0 ? x.bestellungen / x.betriebsjahre : 0),
      }))
      .sort((a, b) => b.luecke - a.luecke);
    const flLueckeGes = flUnter.reduce((a, x) => a + x.luecke, 0);

    T['branchAovChart.empfehlung'] =
      `Menü und Preisstruktur der bestellwertstärksten Standorte in den `
      + `${zahl(flUnter.length)} Filialen unter dem Netzmittel erproben, zuerst in `
      + `${flUnter.slice(0, 2).map(x => x.f.branch_name).join(' und ')}. Auf das `
      + `Netzmittel von ${euro(flAovNetz)} gehoben entspräche das zusammen rund `
      + `${tsd(flLueckeGes)} je Betriebsjahr, davon ${tsd(flUnter[0].luecke)} allein `
      + `auf ${flUnter[0].f.branch_name}. Erfolgsmaß ist der monatliche Bestellwert `
      + `der Testfilialen gegenüber dem Netzmittel.`;

    T['branchEfficiencyChart.deutung'] =
      `Auf die Betriebsdauer normiert führt ${flSpitze.branch_name} mit `
      + `${tsd(flJeJahr(flSpitze))} je Betriebsjahr vor ${flZweit.branch_name} `
      + `(${tsd(flJeJahr(flZweit))}); der Vorsprung beträgt `
      + `${vz(100 * (flJeJahr(flSpitze) / flJeJahr(flZweit) - 1))}, nicht das Doppelte. `
      + `Über dem Netzmittel von ${tsd(flMitteJeJahr)} liegen nur `
      + `${zahl(flUeberMitte.length)} der ${zahl(flF.length)} Standorte; die übrigen `
      + `${zahl(flF.length - flUeberMitte.length)} bewegen sich eng beieinander `
      + `zwischen ${tsd(flJeJahr(flSchluss))} und `
      + `${tsd(flJeJahr(flErsterUnterMitte))}. Zwischen erstem und letztem Platz liegen `
      + `${vz(100 * (flJeJahr(flSpitze) / flJeJahr(flSchluss) - 1))}.`;

    // Heutige Monatsmiete gegen den mittleren Umsatz je Betriebsjahr. Die Miete
    // ist nicht historisiert, die Quote beschreibt also die Gegenwart, nicht die
    // Vergangenheit — deshalb steht das im Satz.
    const flMieteJahr = (x) => (x.monthly_rent_eur ?? 0) * 12;
    const flMietQuote = (x) => flJeJahr(x) > 0 ? 100 * flMieteJahr(x) / flJeJahr(x) : 0;
    const flMietSumme = flF.reduce((a, x) => a + flMieteJahr(x), 0);
    const flJeJahrSumme = flF.reduce((a, x) => a + flJeJahr(x), 0);
    const flMietQuoteNetz = flJeJahrSumme > 0 ? 100 * flMietSumme / flJeJahrSumme : 0;
    const flNachMiete = [...flF].sort((a, b) => flMietQuote(b) - flMietQuote(a));
    const flMietHoch = flNachMiete[0];
    const flMietTief = flNachMiete[flNachMiete.length - 1];

    T['branchEfficiencyChart.empfehlung'] =
      `Den Umsatz je Betriebsjahr gegen die Miete stellen: ${flMietHoch.branch_name} `
      + `bindet davon ${proz(flMietQuote(flMietHoch))} in der Miete `
      + `(${tsd(flMieteJahr(flMietHoch))} im Jahr für ${zahl(flMietHoch.size_sqm)} m²), `
      + `gegenüber ${proz(flMietQuote(flMietTief))} bei ${flMietTief.branch_name} und `
      + `${proz(flMietQuoteNetz)} im Netzschnitt. Für ${flMietHoch.branch_name} `
      + `Mietkonditionen oder Flächenzuschnitt neu verhandeln; für neue Standorte das `
      + `Profil von ${flSpitze.branch_name} (${flSpitze.branch_type}, `
      + `${proz(flMietQuote(flSpitze))} Mietquote) als Vorlage nehmen. Erfolgsmaß ist `
      + `die Mietquote am Umsatz je Betriebsjahr, gerechnet mit der heutigen Miete.`;

  // ── Reiter produkte ────────────────────────────────────────────────
  // ---------------------------------------------------------------------------
  // Reiter "produkte" — Produktrangliste, Kategorien, Veggie-Anteil, Warenkorb
  //
  // Bezugsgroesse dieses Reiters ist durchgaengig der Positionsumsatz
  // (line_total je Bestellposition, also brutto vor Rabatt). Er ist eine andere
  // Groesse als der Umsatz der Bestellungen (net_total, nach Rabatt), der auf
  // den Reitern Uebersicht und Filialen steht. Anteile werden deshalb nur
  // innerhalb der Positionsebene gebildet und im Text auch so benannt.
  // ---------------------------------------------------------------------------

  const prProd = [...(roh.produkte ?? [])].sort(
    (a, b) => b.positionsumsatz - a.positionsumsatz);
  const prKat = [...(roh.kategorien ?? [])].sort(
    (a, b) => b.positionsumsatz - a.positionsumsatz);

  const prPosGesamt = prProd.reduce((s, x) => s + (x.positionsumsatz ?? 0), 0);
  const prMengeGesamt = prProd.reduce((s, x) => s + (x.menge ?? 0), 0);
  const prAnteil = v => 100 * v / (prPosGesamt || 1);
  const prJeStueck = x => (x.positionsumsatz ?? 0) / (x.menge || 1);

  const prLeer = { product_name: '', category: '', subcategory: '',
                   menge: 0, positionsumsatz: 0 };
  const prP = i => prProd[i] ?? prLeer;
  const prTop = prProd.slice(0, 15);
  const prTop3Anteil = prAnteil(prProd.slice(0, 3)
    .reduce((s, x) => s + x.positionsumsatz, 0));
  const prTop2Anteil = prAnteil(prProd.slice(0, 2)
    .reduce((s, x) => s + x.positionsumsatz, 0));

  const prUnd = a => a.length > 1
    ? a.slice(0, -1).join(', ') + ' und ' + a[a.length - 1]
    : (a[0] ?? '');

  // Der Rang, an dem die Top-15-Liste des Diagramms endet — als Bezugspunkt fuer
  // das untere Ende der Rangliste.
  const prLetzterTop = prTop[prTop.length - 1] ?? prLeer;
  const prVegTop = prTop.filter(x => x.is_vegetarian || x.is_vegan);
  const prVegTopAnteil = 100 * prVegTop.reduce((s, x) => s + x.positionsumsatz, 0)
    / (prTop.reduce((s, x) => s + x.positionsumsatz, 0) || 1);

  // Mengenstaerkstes Produkt: eine andere Rangfolge als die nach Umsatz, weil
  // Getraenke und Beilagen viele Einheiten zu kleinen Betraegen verkaufen.
  const prMengeErst = [...prProd].sort((a, b) => b.menge - a.menge)[0] ?? prLeer;

  // Die Unterkategorie des Spitzenreiters (im Datenbestand "Vegan") — sie traegt
  // die Aussage ueber das pflanzliche Segment, nicht das Kennzeichen
  // is_vegetarian, das auch Getraenke und Pommes umfasst.
  const prSubTop = prP(0).subcategory;
  const prSubProd = prProd.filter(x => x.subcategory === prSubTop);
  const prSubAnteil = prAnteil(prSubProd.reduce((s, x) => s + x.positionsumsatz, 0));

  // Produkte je Jahr: die Sicht liefert genau ein Jahr; das Jahr wird aus den
  // Daten gelesen, nicht gesetzt.
  const prPJ = roh.produkteJahr ?? [];
  const prPJJahr = prPJ[0]?.jahr;
  const prPJSort = [...prPJ].sort((a, b) => b.positionsumsatz - a.positionsumsatz);
  const prPJErst = prPJSort[0] ?? prLeer;
  const prPJZwei = prPJSort[1] ?? prLeer;
  const prPJSub = prPJ.filter(x => x.subcategory === prSubTop)
    .reduce((s, x) => s + (x.anteil_pct ?? 0), 0);

  T['topProductsChart.titel'] =
    `${prP(0).product_name} und ${prP(1).product_name} stehen für `
    + `${proz(prTop2Anteil)} des Positionsumsatzes`;

  T['topProductsChart.deutung'] =
    `Interpretation: Die drei umsatzstärksten Produkte — ${prP(0).product_name} `
    + `(${mio(prP(0).positionsumsatz)}), ${prP(1).product_name} `
    + `(${mio(prP(1).positionsumsatz)}) und ${prP(2).product_name} `
    + `(${tsd(prP(2).positionsumsatz)}) — tragen ${proz(prTop3Anteil)} des `
    + `Positionsumsatzes. Die beiden ersten Plätze gehören zur Unterkategorie `
    + `„${prSubTop}", die insgesamt ${proz(prSubAnteil)} erreicht. In der Top-15-Liste `
    + `sind ${zahl(prVegTop.length)} von ${zahl(prTop.length)} Produkten als `
    + `vegetarisch oder vegan gekennzeichnet — das Kennzeichen tragen auch Getränke `
    + `und Beilagen — und stehen für ${proz(prVegTopAnteil)} des Umsatzes dieser `
    + `${zahl(prTop.length)} Produkte. `
    + (prPJJahr
        ? `Im Jahr ${prPJJahr} führt allerdings ${prPJErst.product_name} `
          + `(${tsd(prPJErst.positionsumsatz)}) vor ${prPJZwei.product_name} `
          + `(${tsd(prPJZwei.positionsumsatz)}) — die kumulierte Rangfolge bildet den `
          + `Vorsprung aus früheren Jahren ab, nicht den heutigen Stand. `
        : '')
    + `Am unteren Ende der Liste steht ${prLetzterTop.product_name} mit `
    + `${tsd(prLetzterTop.positionsumsatz)}: ${zahl(prLetzterTop.menge)} verkaufte `
    + `Einheiten zu ${euro(prJeStueck(prLetzterTop))} je Einheit — ein Volumen-, `
    + `kein Preiseffekt.`;

  T['topProductsChart.empfehlung'] =
    `Handlungsempfehlung: Ein drittes Produkt der Unterkategorie „${prSubTop}" `
    + `aufnehmen und preislich an den beiden bestehenden ausrichten, die je `
    + `verkaufter Einheit ${euro(prJeStueck(prP(0)))} und ${euro(prJeStueck(prP(1)))} `
    + `erlösen — gegenüber ${euro(prPosGesamt / (prMengeGesamt || 1))} im Mittel über `
    + `alle Produkte. Erfolgsmaß ist der Anteil dieser Unterkategorie am `
    + `Positionsumsatz: kumuliert ${proz(prSubAnteil)}`
    + (prPJJahr ? `, im Jahr ${prPJJahr} bereits ${proz(prPJSub)}` : '')
    + `; ein drittes Produkt müsste diesen Anteil weiter heben, ohne die Menge der `
    + `beiden bestehenden zu verringern.`;

  // ---------------------------------------------------------------------------

  const prKatLeer = { category: '', menge: 0, positionsumsatz: 0 };
  const prK = i => prKat[i] ?? prKatLeer;
  const prKatMenge = prKat.reduce((s, x) => s + (x.menge ?? 0), 0);
  const prKatAnteil = x => prAnteil(x.positionsumsatz ?? 0);
  const prMengeAnteil = x => 100 * (x.menge ?? 0) / (prKatMenge || 1);
  const prZweiAnteil = prKatAnteil(prK(0)) + prKatAnteil(prK(1));
  const prNischen = prKat.slice(3);

  // Mengenstaerkste Kategorie: Sie ist nicht die umsatzstaerkste, und genau
  // dieser Unterschied ist die Aussage.
  const prKatMengeErst = [...prKat].sort((a, b) => b.menge - a.menge)[0] ?? prKatLeer;
  // Kleinste Kategorie nach Menge — das Fruehstueckssegment ist ein Mengen-,
  // kein Preisproblem, deshalb ist die Menge die Bezugsgroesse.
  const prKatMengeLetzt = [...prKat].sort((a, b) => a.menge - b.menge)[0] ?? prKatLeer;
  const prKatJeStueckRang = [...prKat]
    .sort((a, b) => prJeStueck(b) - prJeStueck(a))
    .findIndex(x => x.category === prKatMengeLetzt.category) + 1;

  T['categoryChart.titel'] =
    `Positionsumsatz nach Kategorie — ${prK(0).category} ${proz(prKatAnteil(prK(0)))}, `
    + `${prK(1).category} ${proz(prKatAnteil(prK(1)))}`;

  T['categoryChart.deutung'] =
    `Interpretation: ${prK(0).category} (${mio(prK(0).positionsumsatz)}, `
    + `${proz(prKatAnteil(prK(0)))}) und ${prK(1).category} `
    + `(${mio(prK(1).positionsumsatz)}, ${proz(prKatAnteil(prK(1)))}) machen zusammen `
    + `${proz(prZweiAnteil)} des Positionsumsatzes aus, ${prK(2).category} folgt mit `
    + `${mio(prK(2).positionsumsatz)} (${proz(prKatAnteil(prK(2)))}). Nach Menge sieht `
    + `die Rangfolge anders aus: ${prKatMengeErst.category} führt mit `
    + `${zahl(prKatMengeErst.menge)} Einheiten (${proz(prMengeAnteil(prKatMengeErst))} `
    + `aller Positionen) bei ${euro(prJeStueck(prKatMengeErst))} je Einheit, während `
    + `${prK(0).category} mit ${euro(prJeStueck(prK(0)))} je Einheit den höchsten Wert `
    + `je Position erzielt. `
    + `${prUnd(prNischen.map(x => `${x.category} (${proz(prKatAnteil(x))})`))} bleiben `
    + `Nischen.`;

  T['categoryChart.empfehlung'] =
    `Handlungsempfehlung: ${prKatMengeLetzt.category} ist kein Preis-, sondern ein `
    + `Mengenproblem: Je verkaufter Einheit erlöst die Kategorie `
    + `${euro(prJeStueck(prKatMengeLetzt))} und liegt damit auf Rang `
    + `${zahl(prKatJeStueckRang)} von ${zahl(prKat.length)}, stellt aber mit `
    + `${zahl(prKatMengeLetzt.menge)} Einheiten nur `
    + `${proz(prMengeAnteil(prKatMengeLetzt))} aller verkauften Positionen und `
    + `${proz(prKatAnteil(prKatMengeLetzt))} des Positionsumsatzes. Ein eigenständiges `
    + `Frühstücksmenü sollte deshalb auf Frequenz zielen, nicht auf den Preis. `
    + `Erfolgsmaß ist der Mengenanteil dieser Kategorie, heute `
    + `${proz(prMengeAnteil(prKatMengeLetzt))}, bei unverändertem Erlös je Einheit.`;

  // ---------------------------------------------------------------------------

  const prVeg = [...(roh.veggie ?? [])].sort((a, b) => a.jahr - b.jahr);
  const prVegErst = prVeg[0] ?? { jahr: '', anteil_pct: 0 };
  const prVegLetzt = prVeg[prVeg.length - 1] ?? prVegErst;
  const prVegFaktor = (prVegLetzt.anteil_pct ?? 0) / (prVegErst.anteil_pct || 1);
  // Das letzte Jahr der Reihe ist angebrochen (Stand Maerz 2026); als letztes
  // vollstaendiges Jahr wird deshalb 2025 gesondert ausgewiesen.
  const prVegVoll = prVeg.find(x => x.jahr === 2025) ?? prVegLetzt;
  const prVegHalb = prVeg.find(x => x.anteil_pct >= 50);
  // Spruenge in Prozentpunkten gegenueber dem Vorjahr, absteigend sortiert.
  const prVegSpruenge = prVeg.slice(1)
    .map((x, i) => ({ jahr: x.jahr, wert: x.anteil_pct,
                      dpp: x.anteil_pct - prVeg[i].anteil_pct }))
    .sort((a, b) => b.dpp - a.dpp);
  const prSprung1 = prVegSpruenge[0] ?? { jahr: '', wert: 0, dpp: 0 };
  const prSprung2 = prVegSpruenge[1] ?? prSprung1;
  const prPP = v => (v >= 0 ? '+' : '') + zahl(v, 1) + ' Prozentpunkte';

  T['veggieChart.titel'] = prVegHalb
    ? `Vegetarische und vegane Burger überschreiten ${prVegHalb.jahr} erstmals die `
      + `Hälfte der verkauften Burger-Menge — ${proz(prVegHalb.anteil_pct)}`
    : `Vegetarische und vegane Burger erreichen ${prVegLetzt.jahr} `
      + `${proz(prVegLetzt.anteil_pct)} der verkauften Burger-Menge`;

  T['veggieChart.deutung'] =
    `Interpretation: Die Reihe zeigt den Mengenanteil vegetarischer und veganer `
    + `Produkte innerhalb der Kategorie Burger, nicht den Anteil der Kunden oder der `
    + `Bestellungen. Er stieg von ${proz(prVegErst.anteil_pct)} (${prVegErst.jahr}) auf `
    + `${proz(prVegVoll.anteil_pct)} (${prVegVoll.jahr}) und liegt im angebrochenen `
    + `Jahr ${prVegLetzt.jahr} bei ${proz(prVegLetzt.anteil_pct)} — das `
    + `${zahl(prVegFaktor, 1)}-Fache des Ausgangswerts. Der Anstieg verlief nicht `
    + `gleichmäßig: Die größten Sprünge fallen auf ${prSprung1.jahr} `
    + `(${prPP(prSprung1.dpp)} auf ${proz(prSprung1.wert)}) und ${prSprung2.jahr} `
    + `(${prPP(prSprung2.dpp)} auf ${proz(prSprung2.wert)}); seither wächst der `
    + `Anteil nur noch um wenige Punkte im Jahr. Da ${prVegLetzt.jahr} erst begonnen `
    + `hat, ist die Überschreitung der Hälfte noch nicht durch ein volles Jahr belegt.`;

  // ---------------------------------------------------------------------------

  const prWk = [...(roh.warenkorb ?? [])];
  const prWkLeer = { regel: '', produkt_a: '', produkt_b: '', gemeinsam: 0,
                     support_pct: 0, konfidenz_pct: 0, lift: 0 };
  // Konfidenz ist gerichtet: Sie misst den Anteil der Warenkoerbe mit produkt_a,
  // in denen auch produkt_b liegt. Der umgekehrte Satz waere eine andere Zahl.
  const prWkKonf = [...prWk].sort((a, b) => b.konfidenz_pct - a.konfidenz_pct)[0]
    ?? prWkLeer;
  const prWkLift = [...prWk].sort((a, b) => b.lift - a.lift)[0] ?? prWkLeer;
  const prWkHaeufig = [...prWk].sort((a, b) => b.gemeinsam - a.gemeinsam)[0] ?? prWkLeer;

  // Die Regeln zum umsatzstaerksten Produkt: Sie tragen die Aussage ueber dessen
  // Cross-Sell-Umfeld.
  const prWkErstProd = prWk.filter(x => x.produkt_a === prP(0).product_name)
    .sort((a, b) => b.konfidenz_pct - a.konfidenz_pct);
  const prWkErstLift = [...prWkErstProd].sort((a, b) => b.lift - a.lift)[0] ?? prWkLeer;

  // Lift 1 bedeutet Unabhaengigkeit; als "ueberzufaellig" gelten hier Regeln, die
  // deutlich darueber liegen. Die Schwelle ist gesetzt, nicht gerechnet.
  const prLiftSchwelle = 2;
  const prLiftNeutral = 1;
  const prWkStark = prWk.filter(x => x.lift > prLiftSchwelle)
    .sort((a, b) => b.lift - a.lift);

  T['produkte_tabelle3.deutung'] =
    `Interpretation: Die höchste Konfidenz erreicht ${prWkKonf.produkt_a} → `
    + `${prWkKonf.produkt_b}: In ${proz(prWkKonf.konfidenz_pct)} der Warenkörbe, die `
    + `${prWkKonf.produkt_a} enthalten, liegt auch ${prWkKonf.produkt_b} — das sind `
    + `${zahl(prWkKonf.gemeinsam)} Bestellungen oder ${proz(prWkKonf.support_pct)} `
    + `aller Warenkörbe. Die Richtung ist dabei nicht umkehrbar: Die Konfidenz bezieht `
    + `sich auf die Käufe von ${prWkKonf.produkt_a}, nicht auf die von `
    + `${prWkKonf.produkt_b}. Für ${prP(0).product_name} liegen die Konfidenzen bei `
    + `${prUnd(prWkErstProd.map(r => `${r.produkt_b} ${proz(r.konfidenz_pct)}`))}; `
    + `überzufällig ist davon vor allem ${prWkErstLift.produkt_b} mit einem Lift von `
    + `${zahl(prWkErstLift.lift, 2)}, während die übrigen Paare nahe am `
    + `Unabhängigkeitswert ${zahl(prLiftNeutral)} liegen.`;

  T['produkte_tabelle3.empfehlung'] =
    `Handlungsempfehlung: Als Bündel eignen sich die ${zahl(prWkStark.length)} der `
    + `${zahl(roh.warenkorb.length)} gezeigten Warenkörbe mit einem Lift über `
    + `${zahl(prLiftSchwelle)}, weil nur sie deutlich über den Zufall hinausgehen — `
    + `die Tabelle zeigt eine kuratierte Auswahl, nicht alle Paare des Bestands: `
    + `${prUnd(prWkStark.map(r => `${r.produkt_a} mit ${r.produkt_b} (Lift `
        + `${zahl(r.lift, 2)}, Konfidenz ${proz(r.konfidenz_pct)})`))}. `
    + `${prWkHaeufig.produkt_a} und ${prWkHaeufig.produkt_b} sind mit `
    + `${zahl(prWkHaeufig.gemeinsam)} gemeinsamen Bestellungen bereits etabliert; `
    + `Spielraum bietet ${prWkErstLift.produkt_a} mit ${prWkErstLift.produkt_b}, das `
    + `bislang in ${zahl(prWkErstLift.gemeinsam)} Warenkörben zusammentrifft. `
    + `Erfolgsmaß ist die Konfidenz dieser Regel, heute `
    + `${proz(prWkErstLift.konfidenz_pct)}, und ihr Support von `
    + `${proz(prWkErstLift.support_pct)}. Ein konkreter Bündelpreis lässt sich hier `
    + `nicht ableiten: Einzelpreise und Kosten liegen im Datensatz nur für Burger vor.`;

  // ── Reiter kunden ──────────────────────────────────────────────────
  // ── Reiter "kunden" ───────────────────────────────────────────────────────
  // Quellen: roh.kundenAlter (Kopfzahlen je Altersgruppe, 25.000 Kunden),
  // roh.alterUmsatz (nur Kunden mit mindestens einer Bestellung, 24.992),
  // roh.kundenLoyalty, roh.kundenBezirke.

  const kdLeer = { altersgruppe: '–', bezirk: '–', stufe: '–',
                   kunden: 0, bestellungen: 0, umsatz: 0 };
  // Die Achsen der Diagramme schreiben Altersgruppen mit Halbgeviertstrich.
  const kdBez = s => String(s ?? '–').replace('-', '–');
  // Groesste im Etikett vorkommende Zahl: "<18" -> 18, "25-34" -> 34, "65+" -> 65.
  // Damit lassen sich Gruppen ohne feste Reihenfolge nach Alter buendeln.
  const kdObergrenze = s => Math.max(...(String(s).match(/\d+/g) || ['0']).map(Number));

  // ── Altersstruktur (Kopfzahlen) ───────────────────────────────────────────
  const kdAlter    = roh.kundenAlter ?? [];
  const kdAlterGes = kdAlter.reduce((s, x) => s + (x.kunden ?? 0), 0);
  const kdAnt      = n => kdAlterGes ? n / kdAlterGes * 100 : 0;
  const kdAlterAbs = [...kdAlter].sort((a, b) => (b.kunden ?? 0) - (a.kunden ?? 0));
  const kdA1       = kdAlterAbs[0] ?? kdLeer;
  const kdA2       = kdAlterAbs[1] ?? kdLeer;
  const kdAKlein   = kdAlterAbs[kdAlterAbs.length - 1] ?? kdLeer;
  const kdSumme    = f => kdAlter.filter(f).reduce((s, x) => s + (x.kunden ?? 0), 0);
  const kdUnter35  = kdSumme(x => kdObergrenze(x.altersgruppe) <= 34);
  const kdAb45     = kdSumme(x => kdObergrenze(x.altersgruppe) >= 45);

  // ── Altersgruppen mit Umsatz ──────────────────────────────────────────────
  const kdAU     = roh.alterUmsatz ?? [];
  const kdAUums  = kdAU.reduce((s, x) => s + (x.umsatz ?? 0), 0);
  const kdAUbest = kdAU.reduce((s, x) => s + (x.bestellungen ?? 0), 0);
  const kdAUkund = kdAU.reduce((s, x) => s + (x.kunden ?? 0), 0);
  const kdAov    = x => (x.bestellungen ? x.umsatz / x.bestellungen : 0);
  const kdFreq   = x => (x.kunden ? x.bestellungen / x.kunden : 0);
  const kdAovGes = kdAUbest ? kdAUums / kdAUbest : 0;
  const kdUAnt   = u => kdAUums ? u / kdAUums * 100 : 0;
  const kdKAnt   = k => kdAUkund ? k / kdAUkund * 100 : 0;
  const kdNachUmsatz = [...kdAU].sort((a, b) => (b.umsatz ?? 0) - (a.umsatz ?? 0));
  const kdNachAov    = [...kdAU].sort((a, b) => kdAov(b) - kdAov(a));
  const kdNachFreq   = [...kdAU].sort((a, b) => kdFreq(a) - kdFreq(b));
  const kdUTop   = kdNachUmsatz[0] ?? kdLeer;
  const kdUKlein = kdNachUmsatz[kdNachUmsatz.length - 1] ?? kdLeer;
  const kdAovTop = kdNachAov[0] ?? kdLeer;
  const kdAov2   = kdNachAov[1] ?? kdLeer;
  const kdAovRest = kdNachAov.slice(2);
  const kdFreqMin = kdNachFreq[0] ?? kdLeer;
  const kdFreqMax = kdNachFreq[kdNachFreq.length - 1] ?? kdLeer;
  // Aggregat der beiden Gruppen mit dem hoechsten Bestellwert gegen alle
  // Gruppen unter 35: das ist der eigentliche Unterschied zwischen den Kohorten.
  const kdBuendel = f => kdAU.filter(f).reduce((s, x) => ({
    kunden: s.kunden + (x.kunden ?? 0),
    bestellungen: s.bestellungen + (x.bestellungen ?? 0),
    umsatz: s.umsatz + (x.umsatz ?? 0),
  }), { kunden: 0, bestellungen: 0, umsatz: 0 });
  const kdJung   = kdBuendel(x => kdObergrenze(x.altersgruppe) <= 34);
  const kdReif   = kdBuendel(x => [kdAovTop.altersgruppe, kdAov2.altersgruppe]
                                    .includes(x.altersgruppe));
  const kdAU45   = kdBuendel(x => kdObergrenze(x.altersgruppe) >= 45);
  // Auf Cent gerundet subtrahieren, damit die Luecke zu den beiden im selben
  // Satz genannten Bestellwerten passt und der Leser nachrechnen kann.
  const kdCent   = v => Math.round(v * 100) / 100;
  const kdLuecke = kdCent(kdAov(kdReif)) - kdCent(kdAov(kdJung));

  // ── Loyalty ───────────────────────────────────────────────────────────────
  const kdLoyText = { None: 'Kein Programm', Bronze: 'Bronze', Silver: 'Silber', Gold: 'Gold' };
  const kdLoy     = roh.kundenLoyalty ?? [];
  const kdLoyGes  = kdLoy.reduce((s, x) => s + (x.kunden ?? 0), 0);
  const kdStufe   = n => (kdLoy.find(x => x.stufe === n) || {}).kunden ?? 0;
  const kdOhne    = kdStufe('None');
  const kdMit     = kdLoyGes - kdOhne;
  const kdBasisAnt = n => kdLoyGes ? n / kdLoyGes * 100 : 0;
  const kdMitAnt   = n => kdMit ? n / kdMit * 100 : 0;
  const kdBronze  = kdStufe('Bronze');
  const kdSilber  = kdStufe('Silver');
  const kdGold    = kdStufe('Gold');
  const kdStufen  = [...kdLoy].filter(x => x.stufe !== 'None')
                              .sort((a, b) => (b.kunden ?? 0) - (a.kunden ?? 0));
  const kdStufeGross = kdStufen[0] ?? kdLeer;
  // Angenommene Werbewirkung; wird im Text ausdruecklich als Annahme benannt.
  const kdConv    = 0.2;
  const kdNeuMit  = kdOhne * kdConv;
  const kdQuoteZiel = kdBasisAnt(kdMit + kdNeuMit);
  const kdPunkteHub = 10;              // Prozentpunkte, angenommener Effekt
  const kdNeuGold = kdSilber * kdPunkteHub / 100;

  // ── Bezirke ───────────────────────────────────────────────────────────────
  const kdBezirke = [...(roh.kundenBezirke ?? [])].sort((a, b) => (b.kunden ?? 0) - (a.kunden ?? 0));
  const kdBezGes  = kdBezirke.reduce((s, x) => s + (x.kunden ?? 0), 0);
  const kdB1 = kdBezirke[0] ?? kdLeer;
  const kdB2 = kdBezirke[1] ?? kdLeer;
  const kdB3 = kdBezirke[2] ?? kdLeer;
  const kdBLetzt = kdBezirke[kdBezirke.length - 1] ?? kdLeer;
  const kdBSpanne = kdBLetzt.kunden ? (kdB1.kunden / kdBLetzt.kunden - 1) * 100 : 0;
  const kdBSchnitt = kdBezirke.length ? kdBezGes / kdBezirke.length : 0;

  // ── ageChart ──────────────────────────────────────────────────────────────
  T['ageChart.titel'] =
    `${proz(kdAnt(kdUnter35))} der Kunden sind unter 35 — Kernzielgruppe ist jung-urban`;

  T['ageChart.sub'] =
    `Kundenverteilung nach Altersgruppe · ${zahl(kdAlterGes)} Kunden · `
    + `${zahl(kdAlter.length)} Altersgruppen`;

  T['ageChart.deutung'] =
    `Interpretation: Die Altersstruktur ist jung. Die beiden stärksten Gruppen `
    + `${kdBez(kdA1.altersgruppe)} (${zahl(kdA1.kunden)} Kunden, ${proz(kdAnt(kdA1.kunden))}) `
    + `und ${kdBez(kdA2.altersgruppe)} (${zahl(kdA2.kunden)}, ${proz(kdAnt(kdA2.kunden))}) `
    + `stellen zusammen ${proz(kdAnt(kdA1.kunden + kdA2.kunden))} der ${zahl(kdAlterGes)} Kunden, `
    + `unter 35 Jahren sind ${proz(kdAnt(kdUnter35))}. Am dünnsten besetzt ist `
    + `${kdBez(kdAKlein.altersgruppe)} mit ${zahl(kdAKlein.kunden)} Kunden `
    + `(${proz(kdAnt(kdAKlein.kunden))}). Alle Gruppen ab 45 zusammen kommen auf `
    + `${zahl(kdAb45)} Kunden oder ${proz(kdAnt(kdAb45))} der Basis.`;

  T['ageChart.empfehlung'] =
    `Handlungsempfehlung: Ein familienfreundliches Angebot (Kinder-Menü, Familiensonntag) `
    + `adressiert die Gruppen ab 45 mit heute ${zahl(kdAb45)} Kunden. Das Segment ist klein, `
    + `aber nicht schwach: sein Umsatzanteil liegt mit ${proz(kdUAnt(kdAU45.umsatz))} praktisch `
    + `auf seinem Kundenanteil von ${proz(kdKAnt(kdAU45.kunden))}, wie in allen Altersgruppen. `
    + `Zusätzlicher Umsatz aus diesem Segment kommt deshalb aus mehr Köpfen, nicht aus mehr `
    + `Ausgaben je Kopf — Erfolgsmaß ist der Anteil der Gruppen ab 45 an der Kundenbasis, `
    + `heute ${proz(kdAnt(kdAb45))}.`;

  // ── loyaltyChart ──────────────────────────────────────────────────────────
  T['loyaltyChart.titel'] =
    `${proz(kdBasisAnt(kdOhne))} der Kunden sind nicht im Loyalty-Programm — `
    + `${zahl(kdOhne)} Personen ohne Programmbindung`;

  T['loyaltyChart.sub'] =
    `Verteilung nach Loyalty-Tier · ${zahl(kdLoy.length)} Stufen · ${zahl(kdLoyGes)} Kunden`;

  T['loyaltyChart.deutung'] =
    `Interpretation: Nur ${proz(kdBasisAnt(kdMit))} der Kunden nehmen am Loyalty-Programm teil. `
    + `Von den ${zahl(kdMit)} Mitgliedern entfallen ${proz(kdMitAnt(kdBronze))} auf Bronze, `
    + `${proz(kdMitAnt(kdSilber))} auf Silber und ${proz(kdMitAnt(kdGold))} auf Gold. `
    + `Die ${zahl(kdOhne)} Kunden ohne Programm sind die mit Abstand größte Gruppe der `
    + `Datenbasis — zahlreicher als alle drei Stufen zusammen.`;

  T['loyaltyChart.empfehlung'] =
    `Handlungsempfehlung: Ein Welcome-Bonus bei der Anmeldung (etwa eine Portion Pommes) `
    + `richtet sich an die ${zahl(kdOhne)} Nicht-Mitglieder. Bei einer angenommenen Conversion `
    + `von ${proz(kdConv * 100, 0)} wären das ${zahl(kdNeuMit)} neue Mitglieder und eine `
    + `Programmquote von ${proz(kdQuoteZiel)} statt heute ${proz(kdBasisAnt(kdMit))}. `
    + `Erfolgsmaß ist diese Quote, fortgeschrieben je Anmeldemonat.`;

  // ── loyaltyBarChart ───────────────────────────────────────────────────────
  T['loyaltyBarChart.titel'] =
    `Nur ${proz(kdBasisAnt(kdGold))} der Kunden erreichen Gold — `
    + `${kdLoyText[kdStufeGross.stufe] ?? kdStufeGross.stufe} ist mit `
    + `${zahl(kdStufeGross.kunden)} Kunden die größte Stufe`;

  T['loyaltyBarChart.deutung'] =
    `Interpretation: ${zahl(kdGold)} Kunden stehen auf Gold, ${proz(kdBasisAnt(kdGold))} der `
    + `Gesamtbasis und ${proz(kdMitAnt(kdGold))} der Mitglieder. Bronze bildet mit `
    + `${zahl(kdBronze)} Kunden die Eingangsebene. Die Stufen verjüngen sich ungleichmäßig: `
    + `Silber erreicht ${proz(kdBronze ? kdSilber / kdBronze * 100 : 0)} des Bronze-Bestands, `
    + `Gold nur ${proz(kdSilber ? kdGold / kdSilber * 100 : 0)} des Silber-Bestands. `
    + `Ob dahinter Aufstiege oder unterschiedlich große Eintrittsjahrgänge stehen, lässt sich `
    + `aus der Stufenverteilung allein nicht ablesen.`;

  T['loyaltyBarChart.empfehlung'] =
    `Handlungsempfehlung: Eine befristete Punkteaktion für die ${zahl(kdSilber)} Silber-Kunden `
    + `(doppelte Punkte auf jede Bestellung) zielt auf den schwächsten Übergang der Leiter. `
    + `Hebt sie die Aufstiegsquote um ${zahl(kdPunkteHub)} Prozentpunkte, sind das `
    + `${zahl(kdNeuGold)} zusätzliche Gold-Kunden. Erfolgsmaß ist der Gold-Anteil an allen `
    + `Mitgliedern, heute ${proz(kdMitAnt(kdGold))}.`;

  // ── districtChart ─────────────────────────────────────────────────────────
  T['districtChart.sub'] =
    `Kundenherkunft nach Würzburger Stadtbezirk · ${zahl(kdBezGes)} Kunden · `
    + `${zahl(kdBezirke.length)} Bezirke · dim_customer.csv (home_district)`;

  T['districtChart.deutung'] =
    `Interpretation: Die Kunden verteilen sich auffallend gleichmäßig auf die `
    + `${zahl(kdBezirke.length)} erfassten Stadtbezirke. ${kdB1.bezirk} (${zahl(kdB1.kunden)}), `
    + `${kdB2.bezirk} (${zahl(kdB2.kunden)}) und ${kdB3.bezirk} (${zahl(kdB3.kunden)}) führen `
    + `knapp, der letzte Bezirk ${kdBLetzt.bezirk} kommt auf ${zahl(kdBLetzt.kunden)} Kunden. `
    + `Zwischen größtem und kleinstem Bezirk liegen damit nur ${proz(kdBSpanne)}, bei einem `
    + `Mittelwert von ${zahl(kdBSchnitt)} Kunden je Bezirk. Weitere Bezirke gibt es nicht: `
    + `die ${zahl(kdBezirke.length)} Einträge decken alle ${zahl(kdBezGes)} Kunden ab.`;

  // ── ageRevenueChart ───────────────────────────────────────────────────────
  T['ageRevenueChart.deutung'] =
    `Interpretation: ${kdBez(kdUTop.altersgruppe)} trägt mit ${proz(kdUAnt(kdUTop.umsatz))} den `
    + `größten Umsatzanteil, dicht bei ihrem Kundenanteil von ${proz(kdKAnt(kdUTop.kunden))}. `
    + `Die Bestellhäufigkeit trennt die Gruppen kaum: sie liegt in allen `
    + `${zahl(kdAU.length)} Gruppen zwischen ${zahl(kdFreq(kdFreqMin), 1)} und `
    + `${zahl(kdFreq(kdFreqMax), 1)} Bestellungen je Kunde. Der Unterschied steckt im `
    + `Bestellwert: ${kdBez(kdAovTop.altersgruppe)} (${euro(kdAov(kdAovTop))}) und `
    + `${kdBez(kdAov2.altersgruppe)} (${euro(kdAov(kdAov2))}) liegen klar über dem Schnitt von `
    + `${euro(kdAovGes)}, die übrigen ${zahl(kdAovRest.length)} Gruppen zwischen `
    + `${euro(kdAov(kdAovRest[kdAovRest.length - 1] ?? kdLeer))} und `
    + `${euro(kdAov(kdAovRest[0] ?? kdLeer))}. ${kdBez(kdUKlein.altersgruppe)} ist mit `
    + `${zahl(kdUKlein.kunden)} Kunden die kleinste Gruppe und trägt `
    + `${proz(kdUAnt(kdUKlein.umsatz))} bei.`;

  T['ageRevenueChart.empfehlung'] =
    `Handlungsempfehlung: Ein Familien-Bundle (zwei Burger, zwei Kinder-Menüs, Getränke) baut `
    + `auf dem Bestellmuster von ${kdBez(kdAov2.altersgruppe)} und `
    + `${kdBez(kdAovTop.altersgruppe)} auf, die zusammen ${euro(kdAov(kdReif))} je Bestellung `
    + `erreichen. Übertragen werden soll es auf die Gruppen unter 35, die mit `
    + `${proz(kdUAnt(kdJung.umsatz))} des Umsatzes den größten Block stellen, dabei aber nur `
    + `${euro(kdAov(kdJung))} je Bestellung erreichen. Erfolgsmaß ist genau dieser Bestellwert: `
    + `die Lücke von ${euro(kdLuecke)} je Bestellung ist der Spielraum, den das Bundle `
    + `schließen soll.`;

  // ── Reiter kanaele ─────────────────────────────────────────────────
  // ── Kanaele ───────────────────────────────────────────────────────────────
    // Bezugsjahr ist 2025, das letzte vollstaendige Jahr. 2026 ist erst
    // angebrochen und wuerde jeden Vergleich mit vollen Jahren verzerren.
    const knJahr = 2025;
    const knPP = (v, n = 1) => (v >= 0 ? '+' : '') + zahl(v, n) + ' Prozentpunkte';
    const knK = roh.kanaeleJahr.filter(x => x.jahr === knJahr);
    const knUms = knK.reduce((a, x) => a + x.umsatz, 0);
    const knBest = knK.reduce((a, x) => a + x.bestellungen, 0);
    // Netzdurchschnitt aus Summe Umsatz je Summe Bestellungen, nicht als Mittel
    // der Kanal-AOV: sonst zaehlt der kleinste Kanal so viel wie der groesste.
    const knAov = knBest ? knUms / knBest : 0;
    const knNachAov = [...knK].sort((a, b) => b.aov - a.aov);
    const knOben = knNachAov[0] ?? {};
    const knUnten = knNachAov[knNachAov.length - 1] ?? {};
    const knSpreiz = (knOben.aov ?? 0) - (knUnten.aov ?? 0);

    T['channelAOVChart.deutung'] =
      `Die Rangfolge der Bestellwerte lautet ${knJahr}: `
      + knNachAov.map(x => `${x.kanal} ${euro(x.aov)}`).join(', ')
      + `. Alle ${zahl(knK.length)} Kanäle liegen dicht am Netzdurchschnitt von `
      + `${euro(knAov)}: Zwischen ${knOben.kanal} und ${knUnten.kanal} liegen `
      + `${euro(knSpreiz)}, also ${proz(knAov ? 100 * knSpreiz / knAov : 0)} des `
      + `Durchschnittswerts. Der gewählte Kanal erklärt den Bestellwert damit nur `
      + `zu einem kleinen Teil.`;

    // ── Umsatzanteil je Kanal ────────────────────────────────────────────────
    const knNachUms = [...knK].sort((a, b) => b.umsatz - a.umsatz);
    // anteil_pct der Sicht ist der Bestellanteil. Die Differenz zum Umsatzanteil
    // zeigt, welcher Kanal ueber seinem Mengengewicht verkauft.
    const knDiff = x => (knUms ? 100 * x.umsatz / knUms : 0) - x.anteil_pct;
    const knHebel = [...knK].sort((a, b) => knDiff(b) - knDiff(a))[0] ?? {};
    const knGross = knNachUms[0] ?? {};
    const knKlein = knNachUms[knNachUms.length - 1] ?? {};

    T['channelRevenueChart.sub'] =
      `Umsatzanteil in % · ${knJahr} · ${zahl(knK.length)} Kanäle · `
      + `${mio(knUms)} Gesamtumsatz`;

    T['channelRevenueChart.deutung'] =
      `Der Umsatz ${knJahr} verteilt sich auf `
      + knNachUms.map(x => `${x.kanal} ${proz(knUms ? 100 * x.umsatz / knUms : 0)}`)
          .join(', ')
      + `. Die Bestellanteile liegen jeweils dicht daneben — ${knGross.kanal} `
      + `${proz(knGross.anteil_pct)}, ${knKlein.kanal} ${proz(knKlein.anteil_pct)} —, `
      + `weil sich die Bestellwerte der Kanäle kaum unterscheiden. Nur `
      + `${knHebel.kanal} setzt anteilig mehr um, als er an Bestellungen auf sich `
      + `zieht (${knPP(knDiff(knHebel))}).`;

    const knApp = knK.find(x => /App/i.test(x.kanal)) ?? {};
    // Was ein Anheben des App-Bestellwerts auf den Netzschnitt einbraechte —
    // nicht, was eine Verlagerung von Bestellungen einbraechte: die App hat den
    // niedrigsten AOV, verlagerte Bestellungen wuerden den Umsatz senken.
    const knAppLuecke = (knAov - (knApp.aov ?? knAov)) * (knApp.bestellungen ?? 0);

    T['channelRevenueChart.empfehlung'] =
      `Die App ist nicht der Kanal mit dem höchsten, sondern mit dem niedrigsten `
      + `Bestellwert (${euro(knApp.aov ?? 0)} gegenüber ${euro(knAov)} im Netz); `
      + `Bestellungen aus anderen Kanälen in die App zu verlagern, hebt den Umsatz `
      + `deshalb nicht. Der Hebel liegt im Bestellwert selbst: Läge die App auf dem `
      + `Netzdurchschnitt, wären das bei ${zahl(knApp.bestellungen ?? 0)} `
      + `App-Bestellungen des Jahres ${knJahr} rund ${euro(knAppLuecke, 0)} mehr `
      + `Umsatz. Angezeigt ist daher ein Kombivorschlag im Bestellablauf der App; `
      + `messen ließe sich der Erfolg am Abstand des App-Bestellwerts zum `
      + `Netzdurchschnitt.`;

    // ── Kanal nach Tageszeit ─────────────────────────────────────────────────
    const knStd = roh.kanaeleStunde;
    const knStunden = [...new Set(knStd.map(x => x.stunde))].sort((a, b) => a - b);
    const knStdGes = knStd.reduce((a, x) => a + x.bestellungen, 0);
    const knProfil = [...new Set(knStd.map(x => x.kanal))].map(n => {
      const r = knStd.filter(x => x.kanal === n);
      const mn = r.reduce((a, b) => (b.anteil_pct < a.anteil_pct ? b : a));
      const mx = r.reduce((a, b) => (b.anteil_pct > a.anteil_pct ? b : a));
      return {
        kanal: n, mn, mx,
        spanne: mx.anteil_pct - mn.anteil_pct,
        mittel: knStdGes ? 100 * r.reduce((a, b) => a + b.bestellungen, 0) / knStdGes : 0
      };
    }).sort((a, b) => b.mittel - a.mittel);
    const knSchwank = [...knProfil].sort((a, b) => b.spanne - a.spanne)[0] ?? {};

    T['channelTodChart.deutung'] =
      `Der Kanalmix ist über den Tag hinweg nahezu konstant. In jeder der `
      + `${zahl(knStunden.length)} erfassten Stunden bleibt `
      + knProfil.map(p => `${p.kanal} zwischen ${proz(p.mn.anteil_pct)} `
          + `(${zahl(p.mn.stunde)} Uhr) und ${proz(p.mx.anteil_pct)} `
          + `(${zahl(p.mx.stunde)} Uhr)`).join(', ')
      + `. Die größte Schwankung zeigt ${knSchwank.kanal} mit `
      + `${zahl(knSchwank.spanne, 1)} Prozentpunkten zwischen schwächster und `
      + `stärkster Stunde, gemessen an einem Tagesmittel von `
      + `${proz(knSchwank.mittel)}. Ein ausgeprägtes Pendler- oder Abendprofil `
      + `einzelner Kanäle ist in diesen Daten nicht zu erkennen.`;

    const knProStunde = knStunden.map(h => ({
      stunde: h,
      bestellungen: knStd.filter(x => x.stunde === h)
        .reduce((a, b) => a + b.bestellungen, 0)
    }));
    const knSpitze = knProStunde.reduce((a, b) =>
      (b.bestellungen > a.bestellungen ? b : a), knProStunde[0] ?? { bestellungen: 0 });
    // Kiosk und App zusammen als "Selbstbedienung": beide binden kein Personal
    // an der Kasse. Der Vergleich Spitzenstunde gegen Tagesmittel zeigt, ob die
    // Selbstbedienung die Spitze heute schon ueberdurchschnittlich traegt.
    const knSelbstRegex = /Kiosk|App/i;
    const knSelbstSpitze = knStd
      .filter(x => x.stunde === knSpitze.stunde && knSelbstRegex.test(x.kanal))
      .reduce((a, b) => a + b.anteil_pct, 0);
    const knSelbstTag = knProfil
      .filter(p => knSelbstRegex.test(p.kanal))
      .reduce((a, b) => a + b.mittel, 0);

    T['channelTodChart.empfehlung'] =
      `Weil sich der Kanalmix über den Tag kaum verschiebt, sind kanalspezifische `
      + `Tageszeit-Aktionen durch diese Daten nicht gedeckt. Der Engpass ist die `
      + `Menge: In der Spitzenstunde um ${zahl(knSpitze.stunde)} Uhr fallen `
      + `${zahl(knSpitze.bestellungen)} Bestellungen an, `
      + `${proz(knStdGes ? 100 * knSpitze.bestellungen / knStdGes : 0)} des `
      + `Tagesvolumens. Naheliegend ist, dort Selbstbedienung gezielt zu bewerben: `
      + `Kiosk und App tragen in dieser Stunde ${proz(knSelbstSpitze)} der `
      + `Bestellungen und damit praktisch genauso viel wie im Tagesmittel `
      + `(${proz(knSelbstTag)}). Der Erfolg wäre daran abzulesen, dass dieser `
      + `Anteil in der Spitzenstunde über den Tageswert steigt.`;

    // ── Produkte je Kanal ────────────────────────────────────────────────────
    // Staerkste Regel nach Lift, nicht nach Haeufigkeit: Lift misst, wie weit
    // der gemeinsame Kauf ueber dem Zufall liegt, und traegt damit ein Bundle.
    const knRegel = [...roh.warenkorb].sort((a, b) => b.lift - a.lift)[0] ?? {};

    T['kanaele_tabelle3.empfehlung'] =
      `Da alle ${zahl(knK.length)} Kanäle dieselben Spitzenprodukte führen, trägt `
      + `ein kanalspezifisches Sortiment nicht; ein einheitliches Kombiangebot `
      + `trifft in jedem Kanal dieselbe Nachfrage. Die stärkste Regel im Warenkorb `
      + `ist ${knRegel.produkt_a} → ${knRegel.produkt_b}: In `
      + `${proz(knRegel.konfidenz_pct)} der Bestellungen mit ${knRegel.produkt_a} `
      + `liegt auch ${knRegel.produkt_b}, bei einem Lift von `
      + `${zahl(knRegel.lift, 2)}. Als Erfolgsmaß `
      + `taugt der Bestellwert je Kanal, der ${knJahr} zwischen `
      + `${euro(knUnten.aov ?? 0)} und ${euro(knOben.aov ?? 0)} liegt — ein `
      + `Kombiangebot müsste diese Spanne anheben, nicht nur verschieben.`;

  // ── Reiter zeitanalyse ─────────────────────────────────────────────
  // ── Zeitanalyse: Wochentag, Stunde, Heatmap ──────────────────────────────
    const zaTagDE = { Monday: 'Montag', Tuesday: 'Dienstag', Wednesday: 'Mittwoch',
                      Thursday: 'Donnerstag', Friday: 'Freitag', Saturday: 'Samstag',
                      Sunday: 'Sonntag' };
    const zaLeerTag = { wochentag: '', nr: 0, bestellungen: 0, umsatz: 0 };
    const zaTage = [...roh.wochentage].sort((a, b) => a.nr - b.nr);
    const zaName = (t) => zaTagDE[t && t.wochentag] ?? ((t && t.wochentag) || '');
    const zaTag = (n) => zaTage.find(x => x.nr === n) ?? zaLeerTag;
    const zaBest = zaTage.reduce((a, x) => a + x.bestellungen, 0);
    const zaUms = zaTage.reduce((a, x) => a + x.umsatz, 0);
    const zaAnteil = (t) => 100 * t.bestellungen / (zaBest || 1);
    const zaAov = (t) => t.bestellungen ? t.umsatz / t.bestellungen : 0;
    const zaSpanne = (a) => a.length ? [Math.min(...a), Math.max(...a)] : [0, 0];

    const zaNachBest = [...zaTage].sort((a, b) => b.bestellungen - a.bestellungen);
    const zaStark = zaNachBest[0] ?? zaLeerTag;
    const zaSchwach = zaNachBest[zaNachBest.length - 1] ?? zaLeerTag;
    const zaAovHoch = [...zaTage].sort((a, b) => zaAov(b) - zaAov(a))[0] ?? zaLeerTag;
    const zaAovTief = [...zaTage].sort((a, b) => zaAov(a) - zaAov(b))[0] ?? zaLeerTag;
    // Wochenende hier Fr-So (nr 5-7), Werktage Mo-Do: der Freitag folgt in der
    // Reihe dem Wochenendmuster, nicht dem der ersten Wochenhaelfte.
    const zaWE = zaTage.filter(x => x.nr >= 5);
    const zaWoche = zaTage.filter(x => x.nr <= 4);
    const zaWEUms = zaWE.reduce((a, x) => a + x.umsatz, 0);
    const zaWochenUms = zaWoche.reduce((a, x) => a + x.umsatz, 0);
    const zaWETag = zaWEUms / (zaWE.length || 1);
    const zaWochenTag = zaWochenUms / (zaWoche.length || 1);
    const zaWEAnteil = 100 * zaWEUms / (zaUms || 1);
    const zaWochenAov = zaWochenUms
      / (zaWoche.reduce((a, x) => a + x.bestellungen, 0) || 1);
    // Mo-Mi als Band, weil die drei Tage so dicht beieinander liegen, dass eine
    // Einzelnennung mehr Genauigkeit vortaeuschen wuerde, als in den Daten steckt.
    const [zaBandMin, zaBandMax] = zaSpanne(zaTage.filter(x => x.nr <= 3).map(zaAnteil));
    // Messlatte fuer den schwaechsten Tag ist der staerkste Werktag Mo-Do; das
    // Wochenende ist als Ziel fuer einen Montag bis Donnerstag nicht erreichbar.
    const zaZiel = [...zaWoche].sort((a, b) => b.bestellungen - a.bestellungen)[0] ?? zaLeerTag;
    const zaLuecke = Math.max(0, zaZiel.bestellungen - zaSchwach.bestellungen);
    const zaQ = (roh.einzelwerteZusatz ?? []).find(x => x.kennung === 'spitzenquartal') ?? {};
    // 'Q3 Peak' -> 'Q3'; das Wort "Peak" stuende im Satz sonst doppelt.
    const zaQName = String(zaQ.text ?? '').split(' ')[0];
    const zaQSatz = (zaQ.anzahl && zaQ.vergleich && zaQName)
      ? `: Das Geschäft schwankt saisonal, ${zaQName} ist in ${zahl(zaQ.anzahl)} von `
        + `${zahl(zaQ.vergleich)} vollen Jahren das stärkste Quartal`
      : '';

    T['dowChart.titel'] =
      `${zaName(zaStark)} zählt `
      + `${proz(100 * (zaStark.bestellungen / (zaSchwach.bestellungen || 1) - 1), 0)} `
      + `mehr Bestellungen als ${zaName(zaSchwach)}`;
    T['dowChart.deutung'] =
      `Die Wochenverteilung folgt einem festen Muster: ${zaName(zaTag(1))} bis `
      + `${zaName(zaTag(3))} tragen je ${proz(zaBandMin)} bis ${proz(zaBandMax)} der `
      + `${zahl(zaBest)} Bestellungen, ${zaName(zaTag(4))} leitet mit `
      + `${proz(zaAnteil(zaTag(4)))} den Anstieg ein, ${zaName(zaTag(5))} `
      + `(${proz(zaAnteil(zaTag(5)))}) und ${zaName(zaTag(6))} `
      + `(${proz(zaAnteil(zaTag(6)))}) sind die Spitzentage, ${zaName(zaTag(7))} fällt auf `
      + `${proz(zaAnteil(zaTag(7)))} zurück. Der Bestellwert unterscheidet sich dabei `
      + `kaum: Er liegt zwischen ${euro(zaAov(zaAovTief))} (${zaName(zaAovTief)}) und `
      + `${euro(zaAov(zaAovHoch))} (${zaName(zaAovHoch)}), eine Spanne von `
      + `${proz(100 * (zaAov(zaAovHoch) / (zaAov(zaAovTief) || 1) - 1))}. Die Unterschiede `
      + `zwischen den Tagen entstehen also über die Zahl der Bestellungen, nicht über `
      + `den einzelnen Bon.`;
    T['dowChart.empfehlung'] =
      `Den größten Spielraum hat der ${zaName(zaSchwach)}: Mit `
      + `${zahl(zaSchwach.bestellungen)} Bestellungen liegt er ${zahl(zaLuecke)} unter dem `
      + `${zaName(zaZiel)}, dem stärksten Tag der ersten Wochenhälfte. Eine allein auf `
      + `diesen Tag begrenzte Aktion, die den Abstand schließt, entspräche über den `
      + `gesamten Zeitraum rund ${tsd(zaLuecke * zaAov(zaSchwach))} Umsatz — aber nur, `
      + `solange der Rabatt nicht den Bestellwert aufzehrt, der am ${zaName(zaSchwach)} `
      + `heute bei ${euro(zaAov(zaSchwach))} liegt. Gemessen wird deshalb am Anteil des `
      + `${zaName(zaSchwach)}s an den Wochenbestellungen (heute `
      + `${proz(zaAnteil(zaSchwach))}) und am Bestellwert des Tages, nicht an absoluten `
      + `Bestellzahlen${zaQSatz}.`;

    // ── Tagesverlauf ─────────────────────────────────────────────────────────
    const zaLeerStd = { stunde: -1, bestellungen: 0, umsatz: 0, zufriedenheit: 0 };
    const zaStd = [...roh.stunden].sort((a, b) => a.stunde - b.stunde);
    const zaS = (h) => zaStd.find(x => x.stunde === h) ?? zaLeerStd;
    const zaUhr = (h) => String(h).padStart(2, '0');
    const zaStdBest = zaStd.reduce((a, x) => a + x.bestellungen, 0);
    const zaStdAnteil = (n) => 100 * n / (zaStdBest || 1);
    const zaSAov = (x) => x.bestellungen ? x.umsatz / x.bestellungen : 0;
    const zaSumme = (a) => a.reduce((s, x) => s + x.bestellungen, 0);

    // Mittagsspitze: staerkste Stunde des Tages plus die staerkere Nachbarstunde.
    const zaMit1 = [...zaStd].sort((a, b) => b.bestellungen - a.bestellungen)[0] ?? zaLeerStd;
    const zaMit2 = [zaS(zaMit1.stunde - 1), zaS(zaMit1.stunde + 1)]
      .sort((a, b) => b.bestellungen - a.bestellungen)[0] ?? zaLeerStd;
    const zaMitVon = Math.min(zaMit1.stunde, zaMit2.stunde);
    const zaMitBis = Math.max(zaMit1.stunde, zaMit2.stunde);
    // Abendspitze: staerkste Stunde mit mindestens einer Stunde Abstand zum
    // Mittagsblock, sonst waere es dieselbe Spitze ein zweites Mal.
    const zaAb1 = zaStd.filter(x => x.stunde > zaMitBis + 1)
      .sort((a, b) => b.bestellungen - a.bestellungen)[0] ?? zaLeerStd;
    const zaAb2 = [zaS(zaAb1.stunde - 1), zaS(zaAb1.stunde + 1)]
      .filter(x => x.stunde > zaMitBis)
      .sort((a, b) => b.bestellungen - a.bestellungen)[0] ?? zaLeerStd;
    const zaAbVon = Math.min(zaAb1.stunde, zaAb2.stunde);
    const zaAbBis = Math.max(zaAb1.stunde, zaAb2.stunde);
    const zaMittagAnteil = zaStdAnteil(zaMit1.bestellungen + zaMit2.bestellungen);
    const zaAbendAnteil = zaStdAnteil(zaAb1.bestellungen + zaAb2.bestellungen);
    // Nachmittagstal: schwaechste Stunde zwischen den beiden Spitzen.
    const zaTal = zaStd.filter(x => x.stunde > zaMitBis && x.stunde < zaAbVon)
      .sort((a, b) => a.bestellungen - b.bestellungen)[0] ?? zaLeerStd;
    const zaTalNachbar = zaS(zaTal.stunde + 1);
    // Schulterstunde: staerkste Stunde zwischen Tal und Abendspitze. Sie ist die
    // Messlatte, die im Tagesverlauf tatsaechlich erreichbar ist - die
    // Nachbarstunde des Tals liegt dafuer viel zu dicht daran.
    const zaSchulter = zaStd.filter(x => x.stunde > zaTal.stunde && x.stunde < zaAbVon)
      .sort((a, b) => b.bestellungen - a.bestellungen)[0] ?? zaTal;
    const zaTalLuecke = Math.max(0, zaSchulter.bestellungen - zaTal.bestellungen);
    const zaNachmittagAnteil = zaStdAnteil(zaSumme(
      zaStd.filter(x => x.stunde >= zaTal.stunde && x.stunde <= zaSchulter.stunde)));
    // Fruehgeschaeft: die Stunden vor 10 Uhr, also vor dem Anlauf zum Mittag.
    const zaMorgen = zaStd.filter(x => x.stunde < 10);
    const zaMorgenAnteil = zaStdAnteil(zaSumme(zaMorgen));
    const zaMorgenVon = zaMorgen.length ? zaMorgen[0].stunde : 0;
    const zaMorgenBis = zaMorgen.length ? zaMorgen[zaMorgen.length - 1].stunde : 0;
    const zaZufMin = [...zaStd].sort((a, b) => a.zufriedenheit - b.zufriedenheit)[0] ?? zaLeerStd;
    const zaZufMax = [...zaStd].sort((a, b) => b.zufriedenheit - a.zufriedenheit)[0] ?? zaLeerStd;

    T['hourChart.deutung'] =
      `Der Tag hat zwei Spitzen: ${zaUhr(zaMitVon)}–${zaUhr(zaMitBis + 1)} Uhr mit `
      + `${zahl(zaMit1.bestellungen)} und ${zahl(zaMit2.bestellungen)} Bestellungen, `
      + `zusammen ${proz(zaMittagAnteil)} des Tagesgeschäfts, und `
      + `${zaUhr(zaAbVon)}–${zaUhr(zaAbBis + 1)} Uhr mit ${zahl(zaAb1.bestellungen)} und `
      + `${zahl(zaAb2.bestellungen)} Bestellungen (${proz(zaAbendAnteil)}). Dazwischen `
      + `liegt das Tal um ${zaUhr(zaTal.stunde)} Uhr mit ${zahl(zaTal.bestellungen)} `
      + `Bestellungen, ${proz(100 * zaTal.bestellungen / (zaMit1.bestellungen || 1))} der `
      + `Mittagsspitze. Zwischen ${zaUhr(zaMorgenVon)} und ${zaUhr(zaMorgenBis + 1)} Uhr `
      + `fallen nur ${proz(zaMorgenAnteil)} aller Bestellungen an — das Frühgeschäft ist `
      + `der am schwächsten entwickelte Teil des Tages.`;
    T['hourChart.empfehlung'] =
      `Ein Angebot für den frühen Nachmittag setzt am Tal an. Als Ziel taugt dabei `
      + `nicht die Folgestunde — ${zaUhr(zaTalNachbar.stunde)} Uhr liegt nur `
      + `${zahl(zaTalNachbar.bestellungen - zaTal.bestellungen)} Bestellungen über `
      + `${zaUhr(zaTal.stunde)} Uhr —, sondern die Schulterstunde `
      + `${zaUhr(zaSchulter.stunde)} Uhr mit ${zahl(zaSchulter.bestellungen)} `
      + `Bestellungen: Das wären ${zahl(zaTalLuecke)} zusätzliche Bestellungen und beim `
      + `Bestellwert dieser Tageszeit (${euro(zaSAov(zaTal))}) rund `
      + `${tsd(zaTalLuecke * zaSAov(zaTal))} über den gesamten Zeitraum. Erfolgskriterium `
      + `ist der Anteil der Stunden ${zaUhr(zaTal.stunde)}–${zaUhr(zaSchulter.stunde + 1)} `
      + `Uhr am Tagesvolumen, heute ${proz(zaNachmittagAnteil)}, bei unveränderter `
      + `Mittagsspitze — sonst wird nur verschoben.`;

    // ── Heatmap ──────────────────────────────────────────────────────────────
    const zaLeerZelle = { wochentag: '', stunde: 0, bestellungen: 0 };
    const zaHm = roh.heatmap ?? [];
    const zaHmSort = [...zaHm].sort((a, b) => b.bestellungen - a.bestellungen);
    const zaHmMax = zaHmSort[0] ?? zaLeerZelle;
    const zaHm2 = zaHmSort[1] ?? zaLeerZelle;
    const zaHmMin = zaHmSort[zaHmSort.length - 1] ?? zaLeerZelle;
    const zaZelle = (tag, std) =>
      (zaHm.find(x => x.wochentag === tag && x.stunde === std) ?? zaLeerZelle).bestellungen ?? 0;
    const zaStunden = [...new Set(zaHm.map(x => x.stunde))].sort((a, b) => a - b);
    // Behauptung "an jedem Wochentag dasselbe Muster" wird geprueft statt
    // uebernommen: die beiden Mittagsstunden muessen in jeder Zeile vorn liegen.
    const zaMuster = zaTage.length > 0 && zaTage.every(t =>
      [...zaStunden]
        .sort((a, b) => zaZelle(t.wochentag, b) - zaZelle(t.wochentag, a))
        .slice(0, 2)
        .every(s => s >= zaMitVon && s <= zaMitBis));
    const zaAbendMuster = zaTage.length > 0 && zaTage.every(t =>
      [...zaStunden].filter(s => s > zaMitBis)
        .sort((a, b) => zaZelle(t.wochentag, b) - zaZelle(t.wochentag, a))[0] === zaAb1.stunde);
    // Stunde fuer Stunde geprueft, ob die schwaechste Wochenendstunde noch ueber
    // der staerksten Stunde von Mo-Mi liegt; sonst waere die Aussage zu stark.
    const zaWEImmer = zaStunden.length > 0 && zaStunden.every(s =>
      Math.min(...zaWE.map(t => zaZelle(t.wochentag, s)))
      > Math.max(...zaTage.filter(x => x.nr <= 3).map(t => zaZelle(t.wochentag, s))));
    // Staerkstes Drei-Stunden-Fenster der Woche: Schichten werden in Bloecken
    // geplant, nicht in einzelnen Stunden.
    let zaFenster = { name: '', von: 0, wert: 0 };
    zaTage.forEach(t => zaStunden.forEach(s => {
      const v = zaZelle(t.wochentag, s) + zaZelle(t.wochentag, s + 1)
              + zaZelle(t.wochentag, s + 2);
      if (v > zaFenster.wert) zaFenster = { name: zaName(t), von: s, wert: v };
    }));
    // Ruhigste Tage in den drei letzten Betriebsstunden der Reihe.
    const zaSpaet = zaStunden.slice(-3);
    const zaRuhig = zaTage
      .map(t => ({ name: zaName(t),
                   wert: zaSpaet.reduce((a, s) => a + zaZelle(t.wochentag, s), 0) }))
      .sort((a, b) => a.wert - b.wert);
    const zaRuhig1 = zaRuhig[0] ?? { name: '', wert: 0 };
    const zaRuhig2 = zaRuhig[1] ?? zaRuhig1;
    const zaFaktor = zaHmMin.bestellungen ? zaHmMax.bestellungen / zaHmMin.bestellungen : 0;
    // Mittagsfenster: die beiden Spitzenstunden plus die Anlaufstunde davor.
    const zaMittagsStd = zaStunden.filter(s => s >= zaMitVon - 1 && s <= zaMitBis);
    const zaWerktagMittag = zaWoche.reduce((a, t) =>
      a + zaMittagsStd.reduce((b, s) => b + zaZelle(t.wochentag, s), 0), 0);
    const zaMittagsVon = zaMittagsStd.length ? zaMittagsStd[0] : zaMitVon;
    const zaMittagsBis = zaMittagsStd.length
      ? zaMittagsStd[zaMittagsStd.length - 1] + 1 : zaMitBis + 1;

    T['zeitanalyse_tabelle2.titel'] =
      `${zaTagDE[zaHmMax.wochentag] ?? zaHmMax.wochentag} ${zaUhr(zaHmMax.stunde)} Uhr ist `
      + `der Hotspot der Woche mit ${zahl(zaHmMax.bestellungen)} Bestellungen`;
    T['zeitanalyse_tabelle2.deutung'] =
      (zaMuster
        ? `Das Doppelmuster des Tages wiederholt sich in jeder Zeile: `
          + `${zaUhr(zaMitVon)} und ${zaUhr(zaMitBis)} Uhr sind an jedem Wochentag die `
          + `beiden stärksten Stunden`
        : `Die Mittagsstunden ${zaUhr(zaMitVon)} und ${zaUhr(zaMitBis)} Uhr prägen die `
          + `Heatmap`)
      + (zaAbendMuster ? `, ${zaUhr(zaAb1.stunde)} Uhr folgt überall als Abendspitze` : '')
      + `. Die höchsten Zellen sind ${zaTagDE[zaHmMax.wochentag] ?? zaHmMax.wochentag} `
      + `${zaUhr(zaHmMax.stunde)} Uhr mit ${zahl(zaHmMax.bestellungen)} und `
      + `${zaTagDE[zaHm2.wochentag] ?? zaHm2.wochentag} ${zaUhr(zaHm2.stunde)} Uhr mit `
      + `${zahl(zaHm2.bestellungen)} Bestellungen; den Tiefpunkt bildet `
      + `${zaTagDE[zaHmMin.wochentag] ?? zaHmMin.wochentag} ${zaUhr(zaHmMin.stunde)} Uhr `
      + `mit ${zahl(zaHmMin.bestellungen)}. `
      + (zaWEImmer
        ? `${zaName(zaTag(5))} bis ${zaName(zaTag(7))} liegen dabei in jeder einzelnen `
          + `Stunde über ${zaName(zaTag(1))} bis ${zaName(zaTag(3))}.`
        : `${zaName(zaTag(5))} bis ${zaName(zaTag(7))} liegen in der Summe über `
          + `${zaName(zaTag(1))} bis ${zaName(zaTag(3))}, aber nicht in jeder Stunde.`);
    T['zeitanalyse_tabelle2.empfehlung'] =
      `Die Schichtplanung sollte dem Raster folgen: Das stärkste Drei-Stunden-Fenster `
      + `der Woche ist ${zaFenster.name} ${zaUhr(zaFenster.von)}–`
      + `${zaUhr(zaFenster.von + 3)} Uhr mit ${zahl(zaFenster.wert)} Bestellungen, während `
      + `${zaRuhig1.name} und ${zaRuhig2.name} in den letzten drei Öffnungsstunden nur auf `
      + `${zahl(zaRuhig1.wert)} und ${zahl(zaRuhig2.wert)} kommen. Zwischen der stärksten `
      + `und der schwächsten Zelle der Heatmap liegt der Faktor `
      + `${zahl(zaFaktor, 0)} — eine über die Woche konstante Besetzung ist an beiden `
      + `Enden falsch. Ob die Umstellung trägt, zeigt die Zufriedenheit in den `
      + `Spitzenstunden: Sie ist um ${zaUhr(zaZufMin.stunde)} Uhr mit `
      + `${zahl(zaZufMin.zufriedenheit, 2)} am niedrigsten, gegenüber `
      + `${zahl(zaZufMax.zufriedenheit, 2)} um ${zaUhr(zaZufMax.stunde)} Uhr.`;

    // ── Umsatz je Wochentag ──────────────────────────────────────────────────
    T['dowRevenueChart.titel'] =
      `${zaName(zaTag(5))} bis ${zaName(zaTag(7))} bringen ${proz(zaWEAnteil)} des `
      + `Umsatzes an drei von sieben Tagen`;
    T['dowRevenueChart.deutung'] =
      `${zaName(zaTag(5))} (${mio(zaTag(5).umsatz)}), ${zaName(zaTag(6))} `
      + `(${mio(zaTag(6).umsatz)}) und ${zaName(zaTag(7))} (${mio(zaTag(7).umsatz)}) `
      + `ergeben zusammen ${mio(zaWEUms)} und damit ${proz(zaWEAnteil)} des `
      + `Gesamtumsatzes von ${mio(zaUms)}; die übrigen ${proz(100 - zaWEAnteil)} `
      + `verteilen sich auf vier Tage. Je Tag gerechnet steht ein Wochenendtag mit `
      + `${mio(zaWETag)} gegen ${mio(zaWochenTag)} an einem Tag von ${zaName(zaTag(1))} `
      + `bis ${zaName(zaTag(4))} — ein Unterschied von `
      + `${proz(100 * (zaWETag / (zaWochenTag || 1) - 1))}. Der Bestellwert erklärt davon `
      + `nichts: Zwischen dem höchsten Tageswert (${zaName(zaAovHoch)}, `
      + `${euro(zaAov(zaAovHoch))}) und dem niedrigsten (${zaName(zaAovTief)}, `
      + `${euro(zaAov(zaAovTief))}) liegen ${euro(zaAov(zaAovHoch) - zaAov(zaAovTief))}.`;
    T['dowRevenueChart.empfehlung'] =
      `Ein Mittagsangebot von ${zaName(zaTag(1))} bis ${zaName(zaTag(4))} setzt dort an, `
      + `wo diese Tage bereits Volumen haben: Auf das Fenster ${zaUhr(zaMittagsVon)}–`
      + `${zaUhr(zaMittagsBis)} Uhr entfallen an den vier Tagen `
      + `${zahl(zaWerktagMittag)} Bestellungen, ${proz(zaStdAnteil(zaWerktagMittag))} des `
      + `Wochengeschäfts. Ein Zehntel mehr in diesem Fenster wären `
      + `${zahl(zaWerktagMittag * 0.1)} Bestellungen und beim Bestellwert dieser Tage `
      + `(${euro(zaWochenAov)}) rund ${tsd(zaWerktagMittag * 0.1 * zaWochenAov)} über den `
      + `gesamten Zeitraum. Ob das Angebot wirkt, zeigt der durchschnittliche Umsatz je `
      + `Tag von ${zaName(zaTag(1))} bis ${zaName(zaTag(4))} gegenüber heute `
      + `${mio(zaWochenTag)}; der Bestellwert taugt als Kennzahl nicht, weil er über alle `
      + `Wochentage praktisch konstant ist.`;

  // ── Reiter trends ──────────────────────────────────────────────────
  // ── Zahlarten ────────────────────────────────────────────────────────────
    // Bezugsjahr ist 2025, das letzte vollstaendige Jahr. 2026 ist erst
    // angebrochen; sein Anteilswert taugt nicht fuer Jahresvergleiche.
    const trJahr = 2025;
    const trZ = roh.zahlartenJahr;
    const trZJahre = [...new Set(trZ.map(x => x.jahr))].sort((a, b) => a - b);
    const trStart = trZJahre[0];
    const trArt = (jahr, muster) => trZ.find(x => x.jahr === jahr && muster.test(x.zahlart)) ?? {};
    const trBar = j => trArt(j, /^Cash$|Bar/i);
    const trEc = j => trArt(j, /^EC/i);
    const trMob = j => trArt(j, /Mobile/i);
    const trBarStart = trBar(trStart), trBarVoll = trBar(trJahr);

    T['paymentChart.titel'] =
      `Bargeldanteil sinkt von ${proz(trBarStart.anteil_pct ?? 0)} (${trStart}) auf `
      + `${proz(trBarVoll.anteil_pct ?? 0)} (${trJahr})`;

    // Wendejahr nicht gesetzt, sondern gesucht: das Jahr mit dem staerksten
    // Rueckgang des Bargeldanteils gegenueber dem Vorjahr.
    const trBarSchritte = trZJahre.slice(1).map(y => ({
      jahr: y,
      delta: (trBar(y).anteil_pct ?? 0) - (trBar(y - 1).anteil_pct ?? 0)
    }));
    const trBruch = trBarSchritte.reduce((a, b) => (b.delta < a.delta ? b : a),
      trBarSchritte[0] ?? { jahr: trStart, delta: 0 });
    const trPhase = trBruch.jahr;
    const trBarPhase = Math.abs((trBar(trPhase).anteil_pct ?? 0) - (trBarStart.anteil_pct ?? 0));
    const trEcPhase = Math.abs((trEc(trPhase).anteil_pct ?? 0) - (trEc(trStart).anteil_pct ?? 0));

    T['paymentChart.deutung'] =
      `Die Umstellung verlief in zwei Phasen. Von ${trStart} bis ${trPhase} verlor `
      + `Bargeld ${zahl(trBarPhase, 1)} Prozentpunkte Anteil, während die `
      + `EC-Karte ${zahl(trEcPhase, 1)} Prozentpunkte gewann; der stärkste `
      + `Einzelschritt entfällt mit ${zahl(Math.abs(trBruch.delta), 1)} `
      + `Prozentpunkten auf ${trPhase}, das erste Pandemiejahr. Danach trug vor `
      + `allem Mobile Payment den Wandel: von ${proz(trMob(trPhase).anteil_pct ?? 0)} `
      + `(${zahl(trMob(trPhase).bestellungen ?? 0)} Bestellungen) auf `
      + `${proz(trMob(trJahr).anteil_pct ?? 0)} `
      + `(${zahl(trMob(trJahr).bestellungen ?? 0)}) im Jahr ${trJahr}, während `
      + `sich die EC-Karte bei ${proz(trEc(trJahr).anteil_pct ?? 0)} einpendelte.`;

    // Fortschreibung des mittleren jaehrlichen Rueckgangs der letzten fuenf
    // vollstaendigen Jahre. Bewusst linear und als Rechnung ausgewiesen — sie
    // dient nur dazu, das Zieljahr einer Umstellung realistisch einzuordnen.
    const trBarBasis = trBar(trJahr - 5);
    const trBarRate = ((trBarBasis.anteil_pct ?? 0) - (trBarVoll.anteil_pct ?? 0)) / 5;
    const trBarNull = trBarRate > 0
      ? trJahr + Math.round((trBarVoll.anteil_pct ?? 0) / trBarRate) : null;

    T['paymentChart.empfehlung'] =
      `Bargeld ist ${trJahr} noch bei ${zahl(trBarVoll.bestellungen ?? 0)} `
      + `Bestellungen die Zahlart, ${proz(trBarVoll.anteil_pct ?? 0)} aller `
      + `Bestellungen — eine flächendeckende Umstellung auf bargeldlos wäre `
      + `verfrüht. Der Anteil sinkt seit ${trJahr - 5} im Mittel um `
      + `${zahl(trBarRate, 1)} Prozentpunkte je Jahr; linear fortgeschrieben wäre `
      + (trBarNull ? `er erst um ${trBarNull} bei null. ` : `kein Zieljahr ableitbar. `)
      + `Angezeigt ist deshalb ein Test an einzelnen Standorten mit je einer rein `
      + `digitalen Kasse, gemessen daran, ob der Bargeldanteil dort schneller fällt `
      + `als im Netz und die Bestellzahl der Filiale dabei stabil bleibt.`;

    // ── Kanaele im Zeitverlauf ────────────────────────────────────────────────
    const trK = roh.kanaeleJahr;
    const trKJahre = [...new Set(trK.map(x => x.jahr))].sort((a, b) => a - b);
    const trKStart = trKJahre[0];
    const trKLetzt = trKJahre[trKJahre.length - 1];
    const trKanal = (jahr, muster) => trK.find(x => x.jahr === jahr && muster.test(x.kanal)) ?? {};
    const trAnfang = [...trK].filter(x => x.jahr === trKStart)
      .sort((a, b) => b.anteil_pct - a.anteil_pct);
    const trKAlle = roh.kennzahlenJahr;
    const trKz = jahr => trKAlle.find(x => x.jahr === jahr) ?? {};
    // Erstes Jahr, in dem der Kanal ueberhaupt vorkommt — nicht fest verdrahtet,
    // damit sich die Aussage mit der Datenbasis mitbewegt.
    const trErstesJahr = muster => {
      const r = trK.filter(x => muster.test(x.kanal)).sort((a, b) => a.jahr - b.jahr)[0];
      return r ?? {};
    };
    const trKioskStart = trErstesJahr(/Kiosk/i);
    const trAppStart = trErstesJahr(/App/i);
    const trAppVoll = trKanal(trJahr, /App/i);

    T['channelChart.deutung'] =
      `Im Jahr ${trKStart} gab es nur ${zahl(trAnfang.length)} Kanäle: Von den `
      + `damals ${zahl(trKz(trKStart).bestellungen ?? 0)} Bestellungen entfielen `
      + trAnfang.map(x => `${proz(x.anteil_pct)} auf ${x.kanal}`).join(' und ')
      + `. Der ${trKioskStart.kanal} kam ${trKioskStart.jahr} hinzu und erreichte im `
      + `ersten Jahr ${proz(trKioskStart.anteil_pct ?? 0)}; Drive-Through fiel im `
      + `selben Jahr von ${proz(trKanal(trKioskStart.jahr - 1, /Drive/i).anteil_pct ?? 0)} `
      + `auf ${proz(trKanal(trKioskStart.jahr, /Drive/i).anteil_pct ?? 0)}, stieg `
      + `${trKioskStart.jahr + 1} noch einmal auf `
      + `${proz(trKanal(trKioskStart.jahr + 1, /Drive/i).anteil_pct ?? 0)} und liegt `
      + `${trJahr} bei ${proz(trKanal(trJahr, /Drive/i).anteil_pct ?? 0)}. Die App `
      + `startete ${trAppStart.jahr} mit ${zahl(trAppStart.bestellungen ?? 0)} `
      + `Bestellungen (${proz(trAppStart.anteil_pct ?? 0)}) und kam ${trJahr} auf `
      + `${zahl(trAppVoll.bestellungen ?? 0)} (${proz(trAppVoll.anteil_pct ?? 0)}); `
      + `seit ${trJahr - 4} hat sich ihr Anteil etwa alle zwei Jahre verdoppelt `
      + `(${proz(trKanal(trJahr - 4, /App/i).anteil_pct ?? 0)}, `
      + `${proz(trKanal(trJahr - 2, /App/i).anteil_pct ?? 0)}, `
      + `${proz(trAppVoll.anteil_pct ?? 0)}). Der Counter hält ${trJahr} noch `
      + `${proz(trKanal(trJahr, /Counter/i).anteil_pct ?? 0)}; für ${trKLetzt} sind `
      + `bislang erst ${zahl(trKz(trKLetzt).bestellungen ?? 0)} von zuletzt `
      + `${zahl(trKz(trJahr).bestellungen ?? 0)} Jahresbestellungen verbucht, das `
      + `Jahr ist also nicht vergleichbar.`;

    const trKVoll = trK.filter(x => x.jahr === trJahr);
    const trNetzAov = trKVoll.reduce((a, x) => a + x.umsatz, 0)
      / (trKVoll.reduce((a, x) => a + x.bestellungen, 0) || 1);
    const trZufr = [...roh.zufriedenheitKanal].sort((a, b) => b.zufriedenheit - a.zufriedenheit);
    const trZufrApp = trZufr.find(x => /App/i.test(x.kanal)) ?? {};
    const trZufrUnten = trZufr[trZufr.length - 1] ?? {};

    T['channelChart.empfehlung'] =
      `Der Ausbau der App lässt sich nicht mit dem Bestellwert begründen: Er liegt `
      + `${trJahr} mit ${euro(trAppVoll.aov ?? 0)} unter dem jedes anderen Kanals `
      + `und unter dem Netzdurchschnitt von ${euro(trNetzAov)}. Belegt ist dagegen `
      + `die Zufriedenheit — App-Bestellungen werden mit `
      + `${zahl(trZufrApp.zufriedenheit ?? 0, 2)} von 5 bewertet gegenüber `
      + `${zahl(trZufrUnten.zufriedenheit ?? 0, 2)} beim Schlusslicht `
      + `${trZufrUnten.kanal}, bei ${zahl(trZufrApp.bewertungen ?? 0)} abgegebenen `
      + `Bewertungen. Die Maßnahme wäre, den Bestellablauf in der App um `
      + `Kombivorschläge zu ergänzen, und zu messen wären zwei Größen: der Abstand `
      + `des App-Bestellwerts zum Netzdurchschnitt und der App-Anteil an den `
      + `Bestellungen, der ${trJahr} bei ${proz(trAppVoll.anteil_pct ?? 0)} liegt.`;

  // ── Reiter datamining ──────────────────────────────────────────────
  // ---------------------------------------------------------------------------
  // Reiter "datamining" — RFM-Segmente und Assoziationsregeln
  // ---------------------------------------------------------------------------

  const dmRfm = roh.rfm ?? [];
  const dmLeer = { segment: '', kunden: 0, anteil_pct: 0, recency_tage: 0,
                   frequenz: 0, lebenswert: 0, umsatz_gesamt: 0 };
  const dmSeg = n => dmRfm.find(x => x.segment === n) ?? dmLeer;

  const dmKunden = dmRfm.reduce((s, x) => s + (x.kunden ?? 0), 0);
  const dmGross  = [...dmRfm].sort((a, b) => b.kunden - a.kunden)[0] ?? dmLeer;

  const dmChamp = dmSeg('Champions');
  const dmLoyal = dmSeg('Loyal');
  const dmRisk  = dmSeg('Abwanderungsgefahr');
  const dmVerl  = dmSeg('Verloren');
  const dmPot   = dmSeg('Potenzial');
  const dmNeu   = dmSeg('Neukunden');

  // Lebenswert-Verhaeltnis gegen die Neukunden, weil das die einzige Gruppe ist,
  // deren Kaufhistorie noch nicht durch Alter verzerrt wird.
  const dmClvFaktor = dmChamp.lebenswert / (dmNeu.lebenswert || 1);

  // Ein Prozentpunkt Reaktivierung im Risikosegment, als Bezugsgroesse fuer die
  // Erfolgsmessung der Kampagne.
  const dmRiskProPunkt = dmRisk.kunden / 100;

  // Abstand Potenzial -> Loyal: die naechsthoehere Stufe mit gleicher Recency-Lage,
  // nicht die Champions, deren Abstand ueber eine Kampagne nicht erreichbar ist.
  const dmPotFreqLuecke = dmLoyal.frequenz - dmPot.frequenz;
  const dmPotClvLuecke  = dmLoyal.lebenswert - dmPot.lebenswert;
  const dmPotPotenzial  = dmPot.kunden * dmPotClvLuecke;

  T['rfmSegmentChart.titel'] =
    `RFM-Segmente — ${proz(dmRisk.anteil_pct)} der Kunden sind abwanderungsgefährdet, `
    + `${proz(dmVerl.anteil_pct)} bereits verloren`;

  T['rfmSegmentChart.sub'] =
    `RFM-Segmentierung · ${zahl(dmKunden)} Kunden · ${zahl(dmRfm.length)} Cluster`;

  T['rfmSegmentChart.deutung'] =
    `Interpretation: Die RFM-Analyse (Recency × Frequency × Monetary) teilt `
    + `${zahl(dmKunden)} Kunden in ${zahl(dmRfm.length)} Segmente. Das größte Segment `
    + `ist „${dmGross.segment}" mit ${zahl(dmGross.kunden)} Kunden `
    + `(${proz(dmGross.anteil_pct)}). „Abwanderungsgefahr" umfasst `
    + `${zahl(dmRisk.kunden)} Kunden (${proz(dmRisk.anteil_pct)}): Sie haben im Mittel `
    + `${zahl(dmRisk.frequenz, 1)} Bestellungen aufgegeben, die letzte liegt aber `
    + `${zahl(dmRisk.recency_tage)} Tage zurück; auf sie entfallen bisher `
    + `${mio(dmRisk.umsatz_gesamt)} Umsatz. Die „Champions" (${zahl(dmChamp.kunden)}, `
    + `${proz(dmChamp.anteil_pct)}) kommen auf ${zahl(dmChamp.frequenz, 1)} Bestellungen `
    + `bei ${zahl(dmChamp.recency_tage)} Tagen Recency und ${euro(dmChamp.lebenswert, 0)} `
    + `Lebenswert je Kopf.`;

  T['rfmSegmentChart.empfehlung'] =
    `Handlungsempfehlung: Die ${zahl(dmRisk.kunden)} abwanderungsgefährdeten Kunden `
    + `gezielt ansprechen, bevor sie in das Segment „Verloren" rutschen, dessen letzte `
    + `Bestellung im Mittel ${zahl(dmVerl.recency_tage)} Tage zurückliegt und dessen `
    + `Lebenswert mit ${euro(dmVerl.lebenswert, 0)} unter den `
    + `${euro(dmRisk.lebenswert, 0)} des Risikosegments liegt. Erfolg misst sich an der `
    + `mittleren Recency dieses Segments, heute ${zahl(dmRisk.recency_tage)} Tage, und am `
    + `Anteil der Kunden, die binnen eines Quartals erneut bestellen — jeder `
    + `Prozentpunkt entspricht rund ${zahl(dmRiskProPunkt)} Kunden.`;

  T['rfmValueChart.titel'] =
    `Champions erreichen ${euro(dmChamp.lebenswert, 0)} Lebenswert je Kopf — `
    + `${zahl(dmClvFaktor, 1)}× so viel wie Neukunden`;

  T['rfmValueChart.deutung'] =
    `Interpretation: Der Lebenswert folgt in erster Linie der Kaufhäufigkeit: `
    + `Champions (${euro(dmChamp.lebenswert, 0)} bei Ø ${zahl(dmChamp.frequenz, 1)} `
    + `Bestellungen) und Loyale (${euro(dmLoyal.lebenswert, 0)} bei Ø `
    + `${zahl(dmLoyal.frequenz, 1)}) liegen vorn, Neukunden mit `
    + `${euro(dmNeu.lebenswert, 0)} und Ø ${zahl(dmNeu.frequenz, 1)} Bestellungen am Ende. `
    + `Die Recency trennt davon unabhängig: „Abwanderungsgefahr" kommt trotz Ø `
    + `${zahl(dmRisk.frequenz, 1)} Bestellungen nur auf ${euro(dmRisk.lebenswert, 0)}, weil `
    + `die letzte Bestellung Ø ${zahl(dmRisk.recency_tage)} Tage zurückliegt. Die Gruppe `
    + `„Potenzial" (${zahl(dmPot.kunden)} Kunden) ist mit Ø ${zahl(dmPot.recency_tage)} `
    + `Tagen Recency aktiv, hat aber erst Ø ${zahl(dmPot.frequenz, 1)} Bestellungen — hier `
    + `fehlt Frequenz, nicht Rückgewinnung.`;

  T['rfmValueChart.empfehlung'] =
    `Handlungsempfehlung: Die ${zahl(dmPot.kunden)} „Potenzial"-Kunden über ein `
    + `Treueprogramm auf höhere Bestellfrequenz führen; bis zum Segment „Loyal" fehlen `
    + `ihnen Ø ${zahl(dmPotFreqLuecke, 1)} Bestellungen und `
    + `${euro(dmPotClvLuecke, 0)} Lebenswert je Kunde. Erfolgsmaß ist der Anteil dieser `
    + `Gruppe, der binnen zwölf Monaten die Frequenz des Segments „Loyal" (Ø `
    + `${zahl(dmLoyal.frequenz, 1)} Bestellungen) erreicht; der vollständige Aufstieg der `
    + `Gruppe entspräche ${tsd(dmPotPotenzial)} zusätzlichem Lebenswert.`;

  // ---------------------------------------------------------------------------

  const dmWk = roh.warenkorb ?? [];

  // Schwellen der Lift-Skala als Konstanten, damit Legende und Zaehlung
  // nicht auseinanderlaufen koennen.
  const dmLiftStark   = 2;
  const dmLiftModerat = 1.3;

  const dmUnd = a => a.length > 1
    ? a.slice(0, -1).join(', ') + ' und ' + a[a.length - 1]
    : (a[0] ?? '');

  const dmStark = dmWk.filter(x => x.lift > dmLiftStark).sort((a, b) => b.lift - a.lift);
  const dmModer = dmWk.filter(x => x.lift > dmLiftModerat && x.lift <= dmLiftStark);
  const dmSchwach = dmWk.filter(x => x.lift <= dmLiftModerat);
  const dmRest = dmWk.filter(x => x.lift <= dmLiftStark);
  const dmRestMin = dmRest.length ? Math.min(...dmRest.map(x => x.lift)) : 0;
  const dmRestMax = dmRest.length ? Math.max(...dmRest.map(x => x.lift)) : 0;

  const dmTopLift = dmStark[0] ?? dmWk[0] ?? {};
  const dmTopHaeufig = [...dmWk].sort((a, b) => b.gemeinsam - a.gemeinsam)[0] ?? {};
  const dmSchwaechsteKonf = [...dmStark].sort((a, b) => a.konfidenz_pct - b.konfidenz_pct)[0]
    ?? dmTopLift;
  const dmStaerksteKonf = [...dmStark].sort((a, b) => b.konfidenz_pct - a.konfidenz_pct)[0]
    ?? dmTopLift;

  // Bezugsmenge der Support-Werte ist die Gesamtzahl aller Bestellungen, also die
  // Summe ueber alle Jahre einschliesslich des angebrochenen letzten Jahres.
  const dmBest = (B.yearOrders ?? []).reduce((s, x) => s + x, 0);

  T['liftChart.sub'] =
    `${zahl(dmWk.length)} ausgewählte Assoziationsregeln · Support, Konfidenz und `
    + `Lift · ${zahl(dmBest)} Bestellungen`;

  T['liftChart.deutung'] =
    `Interpretation: Nur ${zahl(dmStark.length)} der ${zahl(dmWk.length)} Regeln erreichen `
    + `einen Lift über ${zahl(dmLiftStark)} und damit eine starke Assoziation: `
    + `${dmUnd(dmStark.map(r => `${r.produkt_a} → ${r.produkt_b} (Lift `
        + `${zahl(r.lift, 2)}, Konfidenz ${proz(r.konfidenz_pct)})`))}. Die übrigen `
    + `${zahl(dmRest.length)} Regeln liegen zwischen ${zahl(dmRestMin, 2)} und `
    + `${zahl(dmRestMax, 2)}; sie beschreiben häufige, aber nur schwach überzufällige `
    + `Kombinationen. Die stärkste Regel ist dabei nicht die häufigste: `
    + `${dmTopLift.produkt_a} → ${dmTopLift.produkt_b} tritt in `
    + `${zahl(dmTopLift.gemeinsam)} Bestellungen auf (${proz(dmTopLift.support_pct)} `
    + `Support), ${dmTopHaeufig.produkt_a} → ${dmTopHaeufig.produkt_b} dagegen in `
    + `${zahl(dmTopHaeufig.gemeinsam)} (${proz(dmTopHaeufig.support_pct)}).`;

  T['liftChart.empfehlung'] =
    `Handlungsempfehlung: Die ${zahl(dmStark.length)} Regeln mit Lift über `
    + `${zahl(dmLiftStark)} als feste Bundles führen — `
    + `${dmUnd(dmStark.map(r => `${r.produkt_a} mit ${r.produkt_b}`))} — und dieselben `
    + `Paare in Kiosk und App als Vorschlag einblenden. Erfolgsmaß ist die Konfidenz der `
    + `jeweiligen Regel: ${dmStaerksteKonf.produkt_a} → ${dmStaerksteKonf.produkt_b} liegt `
    + `bereits bei ${proz(dmStaerksteKonf.konfidenz_pct)}, `
    + `${dmSchwaechsteKonf.produkt_a} → ${dmSchwaechsteKonf.produkt_b} erst bei `
    + `${proz(dmSchwaechsteKonf.konfidenz_pct)} — dort ist der Spielraum am größten.`;

  T['datamining_tabelle4.deutung'] =
    `Lift-Bewertung: ★★★ = Lift über ${zahl(dmLiftStark)} (stark, `
    + `${zahl(dmStark.length)} Regeln), ★★ = Lift ${zahl(dmLiftModerat, 1)} bis `
    + `${zahl(dmLiftStark)} (moderat, ${zahl(dmModer.length)} Regeln), ★ = Lift bis `
    + `${zahl(dmLiftModerat, 1)} (schwach, ${zahl(dmSchwach.length)} Regeln).`;

  // ── Reiter simulation ──────────────────────────────────────────────
  // ---------------------------------------------------------------------------
  // Reiter "simulation" — Preissimulation und Umsatzprognose
  // ---------------------------------------------------------------------------

  const simBasis = roh.simulation ?? [];
  const simLeerP = { produkt: '', preis: 0, kosten: 0, menge: 0, umsatz: 0 };

  // Bezugsgroesse der Marge ist der gebuchte Positionsumsatz (Feld umsatz), nicht
  // Preis mal Menge: preis ist der Listenpreis, umsatz der tatsaechlich
  // fakturierte Zeilenwert. Die Kosten kommen ueber Menge mal Stueckkosten.
  const simUmsatz   = simBasis.reduce((s, x) => s + (x.umsatz ?? 0), 0);
  const simKosten   = simBasis.reduce((s, x) => s + (x.kosten ?? 0) * (x.menge ?? 0), 0);
  const simMenge    = simBasis.reduce((s, x) => s + (x.menge ?? 0), 0);
  const simDb       = simUmsatz - simKosten;
  const simDbQuote  = simUmsatz ? simDb / simUmsatz * 100 : 0;
  const simDbStueck = simMenge ? simDb / simMenge : 0;

  const simQuote = x => (x.umsatz ? (x.umsatz - x.kosten * x.menge) / x.umsatz * 100 : 0);
  const simSchwaechste = [...simBasis].sort((a, b) => simQuote(a) - simQuote(b))[0] ?? simLeerP;
  const simStaerkste   = [...simBasis].sort((a, b) => simQuote(b) - simQuote(a))[0] ?? simLeerP;

  // Elastizitaet und Reglerspanne sind Vorgaben des Diagramms, keine Groessen aus
  // den Daten. Sie stehen hier, damit Text und Regler nicht auseinanderlaufen.
  const simEps    = -1.2;
  const simProbe  = 10;
  const simSpanne = Array.from({ length: 41 }, (_, i) => i - 20);

  // Modell des Diagramms: der Preis aendert sich um p Prozent, die Menge um
  // p mal Elastizitaet.
  const simVolF  = p => 1 + p * simEps / 100;
  const simUmsF  = p => ((1 + p / 100) * simVolF(p) - 1) * 100;
  const simDbBei = p => simUmsatz * (1 + p / 100) * simVolF(p) - simKosten * simVolF(p);

  const simOpt   = simSpanne.reduce((a, b) => (simDbBei(b) > simDbBei(a) ? b : a), 0);
  const simOptDb = simDb ? (simDbBei(simOpt) / simDb - 1) * 100 : 0;

  const simJahre = (B.yearLabels ?? []).map(x => parseInt(x, 10)).filter(x => !isNaN(x));
  const simVon   = simJahre[0] ?? '';
  const simBis   = simJahre[simJahre.length - 1] ?? '';

  T['simChart.sub'] =
    `${zahl(simBasis.length)} Burger-Produkte · Elastizität `
    + `ε = −${zahl(Math.abs(simEps), 1)} (Annahme, Voreinstellung des Reglers) · `
    + `Basis: alle Burger-Positionen ${simVon}–${simBis}`;

  T['simChart.deutung'] =
    `Interpretation: Grundlage sind die ${zahl(simBasis.length)} Burger-Produkte mit `
    + `${mio(simUmsatz)} Positionsumsatz und ${zahl(simMenge)} verkauften Stück über den `
    + `gesamten Bestand ${simVon}–${simBis}, nicht über ein einzelnes Jahr. Zieht man `
    + `Menge × Stückkosten ab, bleibt ein Deckungsbeitrag von ${mio(simDb)}; auf diesen `
    + `Positionsumsatz bezogen sind das ${proz(simDbQuote)}. Die Elastizität ist eine `
    + `Annahme des Modells und keine Messung: Mit ε = −${zahl(Math.abs(simEps), 1)} folgt `
    + `aus einer Preiserhöhung um ${proz(simProbe, 0)} rechnerisch `
    + `${vz(simProbe * simEps, 0)} Menge und ${vz(simUmsF(simProbe))} Umsatz. Den höchsten `
    + `Deckungsbeitrag erreicht das Modell in der Reglerspanne bei ${vz(simOpt, 0)} Preis, `
    + `und zwar mit ${vz(simOptDb)} — erkauft mit ${vz(simOpt * simEps)} Menge und `
    + `${vz(simUmsF(simOpt))} Umsatz.`;

  const simFilialen = (roh.filialen ?? []).length;

  T['simChart.empfehlung'] =
    `Handlungsempfehlung: Die Elastizität sollte gemessen statt angenommen werden — eine `
    + `Preiserhöhung um ${proz(simOpt, 0)} zunächst in einer der ${zahl(simFilialen)} `
    + `Filialen und nur für ein Quartal, die übrigen als Vergleichsgruppe. Erfolgsmaß ist `
    + `der Deckungsbeitrag je verkauftem Stück, heute ${euro(simDbStueck)} über alle `
    + `${zahl(simBasis.length)} Burger, zusammen mit der abgesetzten Menge; der Umsatz `
    + `allein taugt nicht, weil er im Modell auch dann sinkt, wenn der Deckungsbeitrag `
    + `steigt. Den größten Spielraum trägt ${simSchwaechste.produkt} mit der niedrigsten `
    + `Deckungsbeitragsquote (${proz(simQuote(simSchwaechste))} bei `
    + `${mio(simSchwaechste.umsatz)} Positionsumsatz), den kleinsten `
    + `${simStaerkste.produkt} mit ${proz(simQuote(simStaerkste))}.`;

  // ---------------------------------------------------------------------------

  // Die drei Wachstumsraten und der Prognosehorizont sind feste Parameter der
  // Prognosekurven, keine Groessen aus den Daten.
  const simRaten     = { konservativ: 3, optimistisch: 8, expansiv: 15 };
  const simHorizont  = 3;

  // Basis der Fortschreibung ist das letzte vollstaendige Jahr, nicht das
  // angebrochene letzte Jahr des Bestands.
  const simVollJahre = (B.yearLabels ?? []).filter(l => !String(l).includes('*'))
                                           .map(x => parseInt(x, 10))
                                           .filter(x => !isNaN(x));
  const simBasisJahr = simVollJahre[simVollJahre.length - 1] ?? simBis;
  const simBasisIdx  = simJahre.indexOf(simBasisJahr);
  const simBasisUms  = simBasisIdx >= 0 ? ((B.yearRevenue ?? [])[simBasisIdx] ?? 0) : 0;
  const simZielJahr  = simBasisJahr + simHorizont;
  const simFort      = r => simBasisUms * Math.pow(1 + r / 100, simHorizont);
  const simLuecke    = simFort(simRaten.optimistisch) - simFort(simRaten.konservativ);

  const simWachstum = j => {
    const i = simJahre.indexOf(j);
    const v = (B.yearRevenue ?? [])[i];
    const p = (B.yearRevenue ?? [])[i - 1];
    return (i > 0 && p) ? (v / p - 1) * 100 : 0;
  };
  const simRaum   = [simBasisJahr - 2, simBasisJahr - 1, simBasisJahr];
  const simMittel = simRaum.reduce((s, j) => s + simWachstum(j), 0) / simRaum.length;

  // Das angebrochene Jahr laesst sich nur gegen dieselben Monate des Vorjahres
  // halten; ein Vergleich ganzer Jahre wuerde die fehlenden Monate als Rueckgang
  // ausweisen.
  const simML      = B.mLabels ?? [];
  const simMR      = B.mRevenue ?? [];
  const simMonate  = simML.filter(m => String(m).slice(0, 4) === String(simBis));
  const simMSumme  = liste => liste.reduce((s, m) => {
    const i = simML.indexOf(m);
    return s + (i >= 0 ? (simMR[i] ?? 0) : 0);
  }, 0);
  const simIstNeu  = simMSumme(simMonate);
  const simIstAlt  = simMSumme(simMonate.map(m => `${simBis - 1}-${String(m).slice(5)}`));
  const simLauf    = simIstAlt ? (simIstNeu / simIstAlt - 1) * 100 : 0;

  const simPfad = simLauf < simRaten.konservativ
    ? 'unterhalb des konservativen Pfades'
    : simLauf < simRaten.optimistisch
      ? 'zwischen dem konservativen und dem optimistischen Pfad'
      : simLauf < simRaten.expansiv
        ? 'zwischen dem optimistischen und dem expansiven Pfad'
        : 'oberhalb des expansiven Pfades';

  T['forecastChart.sub'] =
    `Basis: Umsatz ${simBasisJahr} (${mio(simBasisUms)}) · Konservativ `
    + `${proz(simRaten.konservativ, 0)} · Optimistisch ${proz(simRaten.optimistisch, 0)} · `
    + `Expansiv ${proz(simRaten.expansiv, 0)} je Jahr`;

  T['forecastChart.deutung'] =
    `Interpretation: Alle drei Szenarien setzen beim Umsatz ${simBasisJahr} `
    + `(${mio(simBasisUms)}) an und schreiben ihn mit fester Rate fort: `
    + `${proz(simRaten.konservativ, 0)} führen auf `
    + `${mio(simFort(simRaten.konservativ))}, ${proz(simRaten.optimistisch, 0)} auf `
    + `${mio(simFort(simRaten.optimistisch))} und ${proz(simRaten.expansiv, 0)} auf `
    + `${mio(simFort(simRaten.expansiv))} im Jahr ${simZielJahr}. Der beobachtete Verlauf zeigt dagegen `
    + `nachlassendes Wachstum — `
    + `${simRaum.map(j => `${proz(simWachstum(j))} (${j})`).join(', ')} —, und der `
    + `Mittelwert von ${proz(simMittel)} wird allein vom Sprung des Jahres `
    + `${simRaum[0]} getragen. Das Jahr ${simBis} ist erst mit ${zahl(simMonate.length)} `
    + `Monaten erfasst und deshalb nicht in der Grafik; in diesen Monaten liegt der Umsatz `
    + `${vz(simLauf)} über den gleichen Monaten des Vorjahres und damit ${simPfad}.`;

  const simKanal2025 = (roh.kanaeleJahr ?? []).filter(x => x.jahr === simBasisJahr);
  const simKleinst   = [...simKanal2025].sort((a, b) => a.anteil_pct - b.anteil_pct)[0]
    ?? { kanal: '', anteil_pct: 0 };
  const simRisiko    = (roh.rfm ?? []).find(x => x.segment === 'Abwanderungsgefahr')
    ?? { kunden: 0, recency_tage: 0 };

  T['forecastChart.empfehlung'] =
    `Handlungsempfehlung: Zwischen dem konservativen und dem optimistischen Pfad liegen `
    + `im Jahr ${simZielJahr} ${tsd(simLuecke)} Jahresumsatz; dafür sind zwei Hebel `
    + `bezifferbar. Der schwächste der ${zahl(simKanal2025.length)} Kanäle ist `
    + `${simKleinst.kanal} mit ${proz(simKleinst.anteil_pct)} der Bestellungen `
    + `${simBasisJahr}, und im Segment „Abwanderungsgefahr" stehen `
    + `${zahl(simRisiko.kunden)} Kunden, deren letzte Bestellung im Mittel `
    + `${zahl(simRisiko.recency_tage)} Tage zurückliegt. Erfolg misst sich am Kanalanteil `
    + `von ${simKleinst.kanal} und an der mittleren Recency dieses Segments; über einen `
    + `weiteren Standort neben den ${zahl(simFilialen)} bestehenden sollte erst entschieden `
    + `werden, wenn vom laufenden Jahr mehr als ${zahl(simMonate.length)} Monate vorliegen.`;

  // ── Reiter wetter ──────────────────────────────────────────────────
  // ---------------------------------------------------------------------------
  // Reiter "wetter" — Temperatur, Wetterlage und Niederschlag
  // ---------------------------------------------------------------------------

  const wtKlassen = roh.wetterTemperatur ?? [];
  const wtTage    = roh.wetterTage ?? [];
  const wtLeerK   = { klasse: 0, von: 0, bis: 0, tage: 0,
                      umsatz_je_tag: 0, bestellungen_je_tag: 0 };

  const wtTagWort  = n => (n === 1 ? 'Tag' : 'Tage');
  const wtTagenWrt = n => (n === 1 ? 'Tag' : 'Tagen');

  const wtTageZahl = wtKlassen.reduce((s, x) => s + (x.tage ?? 0), 0);
  const wtMittel   = wtTage.length
    ? wtTage.reduce((s, x) => s + (x.umsatz ?? 0), 0) / wtTage.length : 0;

  const wtJahre = wtTage.map(x => String(x.tag).slice(0, 4)).filter(Boolean);
  const wtVon   = wtJahre.length ? wtJahre.reduce((a, b) => (b < a ? b : a)) : '';
  const wtBis   = wtJahre.length ? wtJahre.reduce((a, b) => (b > a ? b : a)) : '';

  const wtKorr = paare => {
    const n = paare.length;
    if (n < 2) return 0;
    const mx = paare.reduce((s, p) => s + p[0], 0) / n;
    const my = paare.reduce((s, p) => s + p[1], 0) / n;
    let sxy = 0, sxx = 0, syy = 0;
    for (const [a, b] of paare) {
      sxy += (a - mx) * (b - my); sxx += (a - mx) ** 2; syy += (b - my) ** 2;
    }
    return (sxx && syy) ? sxy / Math.sqrt(sxx * syy) : 0;
  };

  // Der Vergleich innerhalb eines Jahres braucht ein vollstaendiges Jahr; das
  // letzte Jahr des Bestands ist angebrochen und traegt im Label einen Stern.
  const wtVollJahre = (B.yearLabels ?? []).filter(l => !String(l).includes('*'));
  const wtRefJahr   = wtVollJahre.length ? String(wtVollJahre[wtVollJahre.length - 1]) : wtBis;

  const wtRAlle = wtKorr(wtTage.map(x => [x.temperatur, x.umsatz]));
  const wtRRef  = wtKorr(wtTage.filter(x => String(x.tag).slice(0, 4) === wtRefJahr)
                               .map(x => [x.temperatur, x.umsatz]));

  const wtSort  = [...wtKlassen].sort((a, b) => a.von - b.von);
  const wtKalt  = wtSort[0] ?? wtLeerK;
  const wtKalt2 = wtSort[1] ?? wtLeerK;
  const wtWarm  = wtSort[wtSort.length - 1] ?? wtLeerK;

  // Nur Klassen mit mindestens 100 Tagen werden verglichen: die beiden
  // Randklassen beruhen auf so wenigen Tagen, dass ihr Mittelwert vom Zufall des
  // einzelnen Tages getrieben wird.
  const wtSchwelle = 100;
  const wtBesetzt  = wtKlassen.filter(x => (x.tage ?? 0) >= wtSchwelle);
  const wtBest     = [...wtBesetzt].sort((a, b) => b.umsatz_je_tag - a.umsatz_je_tag)[0] ?? wtLeerK;
  const wtSchwach  = [...wtBesetzt].sort((a, b) => a.umsatz_je_tag - b.umsatz_je_tag)[0] ?? wtLeerK;
  const wtAbstand  = wtSchwach.umsatz_je_tag
    ? (wtBest.umsatz_je_tag / wtSchwach.umsatz_je_tag - 1) * 100 : 0;

  const wtFrost     = wtKlassen.filter(x => x.bis < 0);
  const wtFrostTage = wtFrost.reduce((s, x) => s + (x.tage ?? 0), 0);
  const wtFrostUms  = wtFrostTage
    ? wtFrost.reduce((s, x) => s + x.tage * x.umsatz_je_tag, 0) / wtFrostTage : 0;

  // Schwelle fuer "Hitzetag" wie in der bisherigen Empfehlung: ab 25 Grad.
  const wtHitze     = 25;
  const wtHeiss     = wtKlassen.filter(x => x.von >= wtHitze);
  const wtHeissTage = wtHeiss.reduce((s, x) => s + (x.tage ?? 0), 0);
  const wtHeissAnt  = wtTageZahl ? wtHeissTage / wtTageZahl * 100 : 0;

  // tempBinChart.sub wird weiter unten gesetzt, wo die Klassen mit mindestens
  // 100 Tagen bereits ausgewertet sind. Die fruehere Zuweisung stand hier
  // doppelt und wurde stillschweigend ueberschrieben.

  T['tempBinChart.deutung'] =
    `Interpretation: Über alle ${zahl(wtTageZahl)} Betriebstage erklärt die Temperatur den `
    + `Tagesumsatz kaum — die Korrelation beträgt ${zahl(wtRAlle, 2)}, weil der `
    + `Wachstumstrend der Jahre den Wettereffekt überlagert; innerhalb des Jahres `
    + `${wtRefJahr} allein steigt sie auf ${zahl(wtRRef, 2)}. Ein U-förmiger Verlauf lässt `
    + `sich nicht belegen: Die kälteste Klasse zeigt mit `
    + `${euro(wtKalt.umsatz_je_tag, 0)} zwar den höchsten Wert der Grafik, umfasst aber nur `
    + `${zahl(wtKalt.tage)} ${wtTagWort(wtKalt.tage)}, und die nächste Klasse liegt mit `
    + `${euro(wtKalt2.umsatz_je_tag, 0)} an ${zahl(wtKalt2.tage)} `
    + `${wtTagenWrt(wtKalt2.tage)} unter dem Mittel aller Tage von `
    + `${euro(wtMittel, 0)}. Belastbar ist die Mitte: `
    + `${zahl(wtBest.von, 1)}–${zahl(wtBest.bis, 1)} °C bringt an ${zahl(wtBest.tage)} `
    + `${wtTagenWrt(wtBest.tage)} im Mittel ${euro(wtBest.umsatz_je_tag, 0)} je Tag. Auch die `
    + `wärmste Klasse kommt mit ${euro(wtWarm.umsatz_je_tag, 0)} auf nur `
    + `${zahl(wtWarm.tage)} ${wtTagWort(wtWarm.tage)}.`;

  T['tempBinChart.empfehlung'] =
    `Handlungsempfehlung: Eine eigene Schichtplanung für Hitzetage trägt sich nicht — Tage `
    + `ab ${zahl(wtHitze)} °C machen ${zahl(wtHeissTage)} von ${zahl(wtTageZahl)} `
    + `Betriebstagen aus, ${proz(wtHeissAnt)} des Bestands. Auch Winteraktionen setzen am `
    + `falschen Punkt an: An den ${zahl(wtFrostTage)} Frosttagen liegt der Tagesumsatz mit `
    + `${euro(wtFrostUms, 0)} praktisch auf dem Mittel aller Tage von `
    + `${euro(wtMittel, 0)}. Lohnender ist eine Planung entlang der gut besetzten Klassen, `
    + `zwischen denen ${proz(wtAbstand)} Unterschied im Tagesumsatz liegen: `
    + `${zahl(wtBest.von, 1)}–${zahl(wtBest.bis, 1)} °C mit `
    + `${euro(wtBest.umsatz_je_tag, 0)} gegen ${zahl(wtSchwach.von, 1)}–`
    + `${zahl(wtSchwach.bis, 1)} °C mit ${euro(wtSchwach.umsatz_je_tag, 0)}. Erfolgsmaß `
    + `wäre der Umsatz je geplanter Personalstunde, getrennt nach Temperaturklasse.`;

  T['weatherScatterChart.sub'] =
    `Ein Punkt je Betriebstag · ${zahl(wtTage.length)} Tage · ${wtVon}–${wtBis}`;

  // ── Reiter personal ────────────────────────────────────────────────
  // ── Personal ─────────────────────────────────────────────────────────────
    // umsatz_je_ma und bestellungen_je_ma sind ueber die gesamte Laufzeit
    // kumuliert und belohnen damit die Betriebsdauer. Fuer jeden Vergleich
    // zwischen Filialen wird deshalb zusaetzlich auf ein Betriebsjahr normiert.
    const psP = roh.personalFilialen;
    const psR = roh.personalRollen;
    const psJahre = (name) =>
      (roh.filialen.find(x => x.branch_name === name) || {}).betriebsjahre ?? 0;
    const psUmsJeJahr = (x) => {
      const j = psJahre(x.branch_name);
      return j > 0 ? x.umsatz_je_ma / j : 0;
    };
    const psBestJeJahr = (x) => {
      const j = psJahre(x.branch_name);
      return j > 0 ? x.bestellungen_je_ma / j : 0;
    };
    const psNachKum = [...psP].sort((a, b) => b.umsatz_je_ma - a.umsatz_je_ma);
    const psNachNorm = [...psP].sort((a, b) => psUmsJeJahr(b) - psUmsJeJahr(a));
    const psNachBest = [...psP].sort((a, b) => psBestJeJahr(b) - psBestJeJahr(a));
    const psNachDauer = [...psP].sort((a, b) => a.dauer - b.dauer);
    const psKumHoch = psNachKum[0];
    const psKumTief = psNachKum[psNachKum.length - 1];
    const psNormHoch = psNachNorm[0];
    const psNormTief = psNachNorm[psNachNorm.length - 1];
    const psSpanneKum = psKumTief.umsatz_je_ma > 0
      ? psKumHoch.umsatz_je_ma / psKumTief.umsatz_je_ma : 0;
    const psSpanneNorm = psUmsJeJahr(psNormTief) > 0
      ? psUmsJeJahr(psNormHoch) / psUmsJeJahr(psNormTief) : 0;
    const psDauerKurz = psNachDauer[0];
    const psDauerLang = psNachDauer[psNachDauer.length - 1];
    const psDauerMittel = psP.length > 0
      ? psP.reduce((a, x) => a + x.dauer, 0) / psP.length : 0;
    const psZuf = psP.map(x => x.zufriedenheit);
    const psRollenMA = psR.reduce((a, x) => a + x.anzahl, 0);
    const psLohnMittel = psRollenMA > 0
      ? psR.reduce((a, x) => a + x.anzahl * x.stundenlohn, 0) / psRollenMA : 0;
    const psNachLohn = [...psR].sort((a, b) => a.stundenlohn - b.stundenlohn);
    const psLohnTief = psNachLohn[0];
    const psLohnHoch = psNachLohn[psNachLohn.length - 1];
    const psName = (r) => r.bezeichnung ?? r.rolle;

    T['empProdChart.deutung'] =
      `Der Umsatz je Mitarbeiter ist über die gesamte Laufzeit kumuliert und spreizt `
      + `sich deshalb von ${tsd(psKumTief.umsatz_je_ma)} (${psKumTief.branch_name}) bis `
      + `${tsd(psKumHoch.umsatz_je_ma)} (${psKumHoch.branch_name}), das `
      + `${zahl(psSpanneKum, 1)}-Fache. Auf ein Betriebsjahr heruntergerechnet schrumpft `
      + `der Abstand auf das ${zahl(psSpanneNorm, 1)}-Fache, und an der Spitze steht `
      + `dann ${psNormHoch.branch_name} mit ${tsd(psUmsJeJahr(psNormHoch))} je `
      + `Mitarbeiter und Jahr. Was übrig bleibt, folgt dem Standorttyp und der `
      + `Kundenfrequenz, nicht der Leistung der Teams: Die Bearbeitungsdauer liegt `
      + `netzweit zwischen ${zahl(psDauerKurz.dauer, 1)} `
      + `(${psDauerKurz.branch_name}) und ${zahl(psDauerLang.dauer, 1)} Minuten `
      + `(${psDauerLang.branch_name}), die `
      + `Zufriedenheit zwischen ${zahl(Math.min(...psZuf), 2)} und `
      + `${zahl(Math.max(...psZuf), 2)} Punkten. Auch die Löhne erklären die Spreizung `
      + `nicht: Sie reichen von ${euro(psLohnTief.stundenlohn)} `
      + `(${psName(psLohnTief)}) bis ${euro(psLohnHoch.stundenlohn)} `
      + `(${psName(psLohnHoch)}) je Stunde, im Mittel über alle `
      + `${zahl(psRollenMA)} Beschäftigten ${euro(psLohnMittel)}.`;

    T['empProdChart.empfehlung'] =
      `Die Besetzung an der Bestellmenge messen statt am Umsatz je Kopf: Je `
      + `Mitarbeiter und Betriebsjahr verarbeitet ${psNachBest[0].branch_name} `
      + `${zahl(psBestJeJahr(psNachBest[0]))} Bestellungen, `
      + `${psNachBest[psNachBest.length - 1].branch_name} `
      + `${zahl(psBestJeJahr(psNachBest[psNachBest.length - 1]))}. Für `
      + `${psNachBest.slice(-2).map(x => x.branch_name).join(' und ')} die `
      + `Schichtbesetzung gegen die Öffnungszeiten prüfen, bevor Stellen verschoben `
      + `werden. Erfolgsmaß sind die Bestellungen je Mitarbeiter und Betriebsjahr `
      + `zusammen mit der Bearbeitungsdauer, die dabei nicht über die heutigen `
      + `${zahl(psDauerMittel, 1)} Minuten im Filialmittel steigen darf.`;

    const psK = roh.zufriedenheitKanal;
    const psKBest = psK.reduce((a, x) => a + x.bestellungen, 0);
    const psKBew = psK.reduce((a, x) => a + x.bewertungen, 0);
    const psKHoch = [...psK].sort((a, b) => b.zufriedenheit - a.zufriedenheit)[0];

    // satChannelChart.sub wird weiter unten gesetzt und hat diese Zuweisung
    // ueberschrieben; die dortige Fassung nennt zusaetzlich die Spanne.

    const psD = roh.zufriedenheitDauer;
    const psDSort = [...psD].sort((a, b) => a.nr - b.nr);
    const psDGes = psD.reduce((a, x) => a + x.bestellungen, 0);
    const psDHoch = [...psD].sort((a, b) => b.zufriedenheit - a.zufriedenheit)[0];
    const psDTief = [...psD].sort((a, b) => a.zufriedenheit - b.zufriedenheit)[0];
    const psDLetzte = psDSort[psDSort.length - 1];
    // Groesster Einzelschritt zwischen zwei benachbarten Dauerklassen: zeigt, ob
    // der Rueckgang gleichmaessig verlaeuft oder an einer Stelle springt.
    const psSprung = (() => {
      let beste = null;
      for (let i = 1; i < psDSort.length; i++) {
        const d = psDSort[i - 1].zufriedenheit - psDSort[i].zufriedenheit;
        if (d > 0 && (beste === null || d > beste.d)) {
          beste = { d, vor: psDSort[i - 1], nach: psDSort[i] };
        }
      }
      return beste;
    })();
    const psSchnell = psDSort.slice(0, 2).reduce((a, x) => a + x.bestellungen, 0);

    const psStd = roh.stunden;
    const psStdGes = psStd.reduce((a, x) => a + x.bestellungen, 0);
    const psStdTief = [...psStd].sort((a, b) => a.zufriedenheit - b.zufriedenheit)[0];
    const psStdVoll = [...psStd].sort((a, b) => b.bestellungen - a.bestellungen)[0];

    T['satDurationChart.deutung'] =
      `Über die ${zahl(psD.length)} Dauerklassen fällt die Zufriedenheit von `
      + `${zahl(psDHoch.zufriedenheit, 2)} in der Klasse ${psDHoch.dauer_klasse} Minuten `
      + `auf ${zahl(psDTief.zufriedenheit, 2)} in der Klasse ${psDTief.dauer_klasse} `
      + `Minuten, also um ${zahl(psDHoch.zufriedenheit - psDTief.zufriedenheit, 2)} `
      + `Punkte.`
      + (psSprung ? ` Der Rückgang verläuft ungleichmäßig: Der größte Einzelschritt `
          + `liegt zwischen den Klassen ${psSprung.vor.dauer_klasse} und `
          + `${psSprung.nach.dauer_klasse} Minuten mit ${zahl(psSprung.d, 2)} Punkten.`
        : '')
      + ` Die langsamste Klasse ist zugleich die dünnste: `
      + `${zahl(psDLetzte.bestellungen)} von ${zahl(psDGes)} Bestellungen oder `
      + `${proz(100 * psDLetzte.bestellungen / psDGes)}, ihr Wert steht also auf `
      + `schmaler Grundlage. Nach Tageszeit liegt das Minimum bei `
      + `${zahl(psStdTief.stunde)} Uhr mit ${zahl(psStdTief.zufriedenheit, 2)}`
      + (psStdVoll.stunde === psStdTief.stunde
        ? ` — der Stunde mit den meisten Bestellungen `
          + `(${zahl(psStdTief.bestellungen)}).`
        : `, während die Stunde mit den meisten Bestellungen `
          + `(${zahl(psStdVoll.stunde)} Uhr) auf `
          + `${zahl(psStdVoll.zufriedenheit, 2)} kommt.`);

    T['satDurationChart.empfehlung'] =
      `Die Bearbeitungsdauer in der stärksten Stunde begrenzen, etwa über eine `
      + `Express-Spur oder Vorbestellung: ${zahl(psStdVoll.stunde)} Uhr trägt `
      + `${zahl(psStdVoll.bestellungen)} Bestellungen und damit `
      + `${proz(100 * psStdVoll.bestellungen / psStdGes)} des Tagesgeschäfts. `
      + `Erfolgsmaß sind zwei Größen: der Anteil der Bestellungen in den beiden `
      + `schnellsten Dauerklassen, heute ${proz(100 * psSchnell / psDGes)}, und die `
      + `Zufriedenheit in dieser Stunde, heute ${zahl(psStdVoll.zufriedenheit, 2)} `
      + `gegenüber ${zahl(psKHoch.zufriedenheit, 2)} im Kanal ${psKHoch.kanal} als `
      + `bestem Wert im Netz.`;

  // ── Reiter promotions ──────────────────────────────────────────────
  // ── Reiter "promotions" ──────────────────────────────────────────────────

  const pmAkt = roh.promotionen ?? [];
  const pmN   = pmAkt.length;

  // Bezugsgroesse fuer den Aktionsanteil ist die Summe aller Bestellungen ueber
  // alle Jahre, weil auch die Aktionszeilen ueber die gesamte Reihe kumuliert
  // sind — ein einzelnes Jahr waere die falsche Vergleichsmenge.
  const pmBestGes    = (roh.kennzahlenJahr ?? []).reduce((s, x) => s + (x.bestellungen ?? 0), 0);
  const pmBest       = pmAkt.reduce((s, x) => s + (x.bestellungen ?? 0), 0);
  const pmRabattGes  = pmAkt.reduce((s, x) => s + (x.rabattsumme ?? 0), 0);
  const pmAnteilBest = pmBestGes ? 100 * pmBest / pmBestGes : 0;
  const pmBasis      = pmAkt.find(x => x.baseline_aov != null)?.baseline_aov ?? 0;

  // Bestellwert vor Rabatt: (Umsatz + Rabattsumme) je Bestellung. Nur diese
  // Groesse ist mit baseline_aov vergleichbar — die Baseline stammt aus
  // Bestellungen ohne Aktion und enthaelt daher keinen Rabatt, das Feld aov
  // dagegen ist der Wert nach Abzug.
  const pmVor        = (x) => x.bestellungen ? (x.umsatz + x.rabattsumme) / x.bestellungen : 0;
  const pmUeberBasis = pmAkt.filter(x => pmVor(x) > pmBasis);
  const pmVorTop     = [...pmAkt].sort((a, b) => pmVor(b) - pmVor(a))[0] ?? {};
  const pmVorFlop    = [...pmAkt].sort((a, b) => pmVor(a) - pmVor(b))[0] ?? {};

  // Groesste Gruppe von Aktionen mit gleichem Rabattsatz. Sie belegt, dass der
  // ROI nichts als den Rabattsatz spiegelt: gleicher ROI trotz weit
  // auseinanderliegender Bestellwerte.
  const pmGruppe  = [...new Set(pmAkt.map(x => x.rabatt_pct))]
    .map(p => pmAkt.filter(x => x.rabatt_pct === p))
    .sort((a, b) => b.length - a.length)[0] ?? [];
  const pmGrpRoi  = pmGruppe[0]?.roi ?? 0;
  const pmGrpSatz = pmGruppe[0]?.rabatt_pct ?? 0;
  const pmGrpAov  = pmGruppe.map(x => x.aov);
  const pmGrpMin  = pmGrpAov.length ? Math.min(...pmGrpAov) : 0;
  const pmGrpMax  = pmGrpAov.length ? Math.max(...pmGrpAov) : 0;

  // Empfehlungskandidat: unter den Aktionen mit Bestellwert ueber der Baseline
  // die mit den meisten Bestellungen — groesste Reichweite bei belegtem
  // Korbeffekt, statt der hoechste Wert bei einer sehr kleinen Fallzahl.
  const pmEmpf         = [...pmUeberBasis].sort((a, b) => b.bestellungen - a.bestellungen)[0] ?? {};
  const pmEmpfRabattJe = pmEmpf.bestellungen ? pmEmpf.rabattsumme / pmEmpf.bestellungen : 0;

  const pmSatSort   = [...pmAkt].sort((a, b) => a.zufriedenheit - b.zufriedenheit);
  const pmSatMin    = pmSatSort[0] ?? {};
  const pmSatMax    = pmSatSort[pmSatSort.length - 1] ?? {};
  const pmSatSpanne = (pmSatMax.zufriedenheit ?? 0) - (pmSatMin.zufriedenheit ?? 0);

  T['promoROIChart.titel'] =
    `Nur ${proz(pmAnteilBest)} der Bestellungen laufen über eine Aktion — `
    + `der ROI folgt allein dem Rabattsatz`;

  T['promoROIChart.sub'] =
    `${zahl(pmN)} Aktionen · Umsatz je Rabatt-Euro · Baseline ${euro(pmBasis)} `
    + `Bestellwert ohne Aktion · Rabatteinsatz ${tsd(pmRabattGes)}`;

  T['promoROIChart.deutung'] =
    `Der ROI ist Umsatz je eingesetztem Rabatt-Euro und damit rechnerisch an den `
    + `Rabattsatz gekoppelt: Die ${zahl(pmGruppe.length)} Aktionen mit `
    + `${proz(pmGrpSatz, 0)} Rabatt kommen alle auf ${zahl(pmGrpRoi, 1)}x, obwohl `
    + `ihr Bestellwert zwischen ${euro(pmGrpMin)} und ${euro(pmGrpMax)} liegt. Ein `
    + `hoher Wert zeigt deshalb einen niedrigen Rabatt an, nicht Zusatzumsatz. `
    + `Nach Rabatt liegt der Bestellwert jeder Aktion unter der Baseline von `
    + `${euro(pmBasis)}; rechnet man den Rabatt heraus, liegen `
    + `${zahl(pmUeberBasis.length)} von ${zahl(pmN)} Aktionen darüber, am weitesten `
    + `${pmVorTop.aktion} mit ${euro(pmVor(pmVorTop))}. ${pmVorFlop.aktion} bleibt `
    + `mit ${euro(pmVor(pmVorFlop))} auch vor Rabatt unter der Baseline.`;

  T['promoROIChart.empfehlung'] =
    `Die Aktionen nach dem Bestellwert vor Rabatt gegen die Baseline bewerten `
    + `statt nach ROI. Unter den ${zahl(pmUeberBasis.length)} Aktionen über der `
    + `Baseline hat ${pmEmpf.aktion} mit ${zahl(pmEmpf.bestellungen)} Bestellungen `
    + `die größte Reichweite: ${euro(pmVor(pmEmpf))} vor Rabatt gegenüber `
    + `${euro(pmBasis)} Baseline, bei ${euro(pmEmpfRabattJe)} Rabatt je Bestellung. `
    + `${pmVorFlop.aktion} liegt mit ${euro(pmVor(pmVorFlop))} am weitesten `
    + `darunter und gehört zuerst auf den Prüfstand. Messgröße für den Erfolg ist `
    + `der Abstand des Vor-Rabatt-Bestellwerts zur Baseline je Aktion, zusammen `
    + `mit der Bestellzahl, damit ein höherer Bestellwert nicht durch weniger `
    + `Aktionsbestellungen erkauft wird.`;

  // Ohne Aktion ist keine Zufriedenheit ausgewiesen; statt eines Baseline-Werts
  // wird deshalb die Spanne zwischen den Aktionen benannt.
  T['promoSatChart.sub'] =
    `Ø Zufriedenheit je Aktion · ${zahl(pmN)} Aktionen mit ${zahl(pmBest)} `
    + `Bestellungen · Spanne ${zahl(pmSatMin.zufriedenheit, 2)} `
    + `(${pmSatMin.aktion}) bis ${zahl(pmSatMax.zufriedenheit, 2)} `
    + `(${pmSatMax.aktion}), also ${zahl(pmSatSpanne, 2)} Punkte`;

  // ── Kohorten ─────────────────────────────────────────────────────────────

  const pmKoh      = roh.kohorten ?? [];
  const pmKohJahre = [...new Set(pmKoh.map(x => x.kohorte))].sort((a, b) => a - b);
  const pmErstJahr = pmKohJahre[0] ?? 0;
  const pmLetztJahr = pmKoh.reduce((m, x) => Math.max(m, x.jahr), pmErstJahr);
  const pmKunden   = pmKohJahre.reduce((s, k) =>
    s + (pmKoh.find(x => x.kohorte === k)?.kohortengroesse ?? 0), 0);
  const pmQuote    = (x) => (x && x.kohortengroesse) ? 100 * x.aktive / x.kohortengroesse : 0;

  // Aussagekraeftig sind nur Zellen ab dem Eintrittsjahr — die Sicht enthaelt
  // auch Zeilen fuer Jahre davor. Das laufende Jahr bleibt aussen vor, weil es
  // angebrochen ist; ebenso das Eintrittsjahr selbst, das bei jedem Jahrgang nur
  // einen Teil des Jahres umfasst.
  const pmVollZellen = pmKoh.filter(x => x.jahr >= x.kohorte && x.jahr < pmLetztJahr);
  const pmFolge      = pmVollZellen.filter(x => x.jahr > x.kohorte);
  const pmFolgeQ     = pmFolge.map(pmQuote);
  const pmFolgeMin   = pmFolgeQ.length ? Math.min(...pmFolgeQ) : 0;
  const pmFolgeMax   = pmFolgeQ.length ? Math.max(...pmFolgeQ) : 0;
  const pmFolgeNenner = pmFolge.reduce((s, x) => s + x.kohortengroesse, 0);
  const pmFolgeMittel = pmFolgeNenner
    ? 100 * pmFolge.reduce((s, x) => s + x.aktive, 0) / pmFolgeNenner : 0;

  const pmErstZelle = pmKoh.find(x => x.kohorte === pmErstJahr && x.jahr === pmErstJahr) ?? {};

  // Anteil der schon bestehenden Kunden, die in einem Kalenderjahr aktiv waren.
  const pmJahrQuote = (y) => {
    const z = pmKoh.filter(x => x.jahr === y && x.kohorte < y);
    const g = z.reduce((s, x) => s + x.kohortengroesse, 0);
    return g ? 100 * z.reduce((s, x) => s + x.aktive, 0) / g : null;
  };
  const pmJahresreihe = [...new Set(pmVollZellen.map(x => x.jahr))]
    .filter(y => y > pmErstJahr).sort((a, b) => a - b)
    .map(y => ({ jahr: y, quote: pmJahrQuote(y) })).filter(x => x.quote != null);
  // Der Einbruch wird ueber den groessten Rueckgang gegenueber dem Vorjahr
  // gesucht, nicht ueber den kleinsten Wert: In den fruehen Jahren zaehlt erst
  // ein einziger, noch junger Jahrgang, deren Niveau ist daher nicht
  // vergleichbar.
  const pmDip = pmJahresreihe.slice(1).reduce((b, x, i) => {
    const d = x.quote - pmJahresreihe[i].quote;
    return (b === null || d < b.diff)
      ? { jahr: x.jahr, quote: x.quote, vorquote: pmJahresreihe[i].quote, diff: d } : b;
  }, null) ?? {};

  const pmAktuellZellen = pmKoh.filter(x => x.jahr === pmLetztJahr && x.kohorte <= pmLetztJahr);
  const pmAktuellNenner = pmAktuellZellen.reduce((s, x) => s + x.kohortengroesse, 0);
  const pmAktuellQuote  = pmAktuellNenner
    ? 100 * pmAktuellZellen.reduce((s, x) => s + x.aktive, 0) / pmAktuellNenner : 0;
  const pmAktuellSchwach = [...pmAktuellZellen].sort((a, b) => pmQuote(a) - pmQuote(b))[0] ?? {};

  // Wie weit das laufende Jahr reicht, steht in der Monatsreihe.
  const pmMonate = (roh.umsatzMonat ?? [])
    .filter(x => String(x.monat).startsWith(`${pmLetztJahr}-`)).length;

  T['cohortChart.titel'] =
    `Kohortenanalyse — in vollen Jahren nach dem Eintritt bleiben `
    + `${proz(pmFolgeMin)} bis ${proz(pmFolgeMax)} eines Jahrgangs aktiv`;

  T['cohortChart.sub'] =
    `Anteil aktiver Kunden je Kohorte (Eintrittsjahr) · `
    + `${zahl(pmKohJahre.length)} Jahrgänge, ${zahl(pmKunden)} erfasste Kunden · `
    + `von ${pmLetztJahr} liegen erst ${zahl(pmMonate)} Monate vor`;

  T['cohortChart.deutung'] =
    `In vollen Jahren nach dem Eintritt bleiben im Mittel ${proz(pmFolgeMittel)} `
    + `eines Jahrgangs aktiv, der niedrigste Wert liegt bei ${proz(pmFolgeMin)}. `
    + `Das Eintrittsjahr ${pmErstJahr} erreicht nur ${proz(pmQuote(pmErstZelle))}, `
    + `weil die Reihe erst im Laufe dieses Jahres beginnt. Der Einbruch gehört `
    + `nicht zu einem Jahrgang, sondern zum Kalenderjahr ${pmDip.jahr}: Dort waren `
    + `${proz(pmDip.quote)} der bereits bestehenden Kunden aktiv gegenüber `
    + `${proz(pmDip.vorquote)} im Vorjahr, und das in allen Jahrgängen `
    + `gleichermaßen. Der Wert von ${proz(pmAktuellQuote)} für ${pmLetztJahr} ist `
    + `kein Abriss, sondern ein Zwischenstand: Von diesem Jahr liegen erst `
    + `${zahl(pmMonate)} von zwölf Monaten vor.`;

  T['cohortChart.empfehlung'] =
    `Den Punkt für ${pmLetztJahr} bis zum Jahresende als Zwischenstand führen und `
    + `die Kurven erst danach bewerten. Als Schwelle taugt der niedrigste bisher `
    + `gemessene Wert eines vollen Jahres, ${proz(pmFolgeMin)}: Bleibt ein `
    + `Jahrgang zum Jahresende darunter, ist er ein Fall für eine Reaktivierung. `
    + `Am unteren Rand des laufenden Jahres steht derzeit der Jahrgang `
    + `${pmAktuellSchwach.kohorte} mit ${proz(pmQuote(pmAktuellSchwach))}; er `
    + `eignet sich als erste Beobachtungsgruppe.`;

  // ── Filial-Scorecard ─────────────────────────────────────────────────────

  const pmFil = roh.filialen ?? [];
  // Umsatz je Quadratmeter und Mietquote der Tabelle summieren alle
  // Betriebsjahre und belohnen damit Alter. Beide werden hier auf ein
  // Betriebsjahr normiert, damit junge und alte Standorte vergleichbar sind.
  const pmQmJahr = (x) => x.betriebsjahre ? x.umsatz_je_qm / x.betriebsjahre : 0;
  const pmMietQ  = (x) => (x.betriebsjahre && x.umsatz)
    ? 100 * x.monthly_rent_eur * 12 / (x.umsatz / x.betriebsjahre) : 0;
  const pmQmRang   = [...pmFil].sort((a, b) => pmQmJahr(b) - pmQmJahr(a));
  const pmQm1      = pmQmRang[0] ?? {};
  const pmQm2      = pmQmRang[1] ?? {};
  const pmMietRang = [...pmFil].sort((a, b) => pmMietQ(a) - pmMietQ(b));
  const pmMietGut  = pmMietRang[0] ?? {};
  const pmMietTeuer = pmMietRang[pmMietRang.length - 1] ?? {};
  const pmHeimat   = (roh.heimatbezirk ?? [])[0] ?? {};

  T['promotions_tabelle3.deutung'] =
    `Umsatz je Quadratmeter und Mietquote der Tabelle summieren alle `
    + `Betriebsjahre und belohnen damit Alter. Je Betriebsjahr gerechnet führt `
    + `${pmQm1.branch_name} mit ${euro(pmQmJahr(pmQm1), 0)} je Quadratmeter, knapp `
    + `vor ${pmQm2.branch_name} mit ${euro(pmQmJahr(pmQm2), 0)}. Ebenso bei der `
    + `Miete: Gemessen am Umsatz eines Betriebsjahres ist ${pmMietGut.branch_name} `
    + `mit ${proz(pmMietQ(pmMietGut))} der günstigste und `
    + `${pmMietTeuer.branch_name} mit ${proz(pmMietQ(pmMietTeuer))} der teuerste `
    + `Standort. Nur ${proz(pmHeimat.anteil_pct)} der Bestellungen stammen aus dem `
    + `Wohnbezirk der Kunden: ${zahl(pmHeimat.filialbezirke)} Filialbezirke `
    + `bedienen Kunden aus ${zahl(pmHeimat.wohnbezirke)} Wohnbezirken.`;
  // ═══ Ende der Reiter-Fragmente ═══

  // =========================================================================
  // Diagrammtitel und Unterzeilen
  //
  // Bis hierher waren 66 Titel- und Unterzeilen als Text im HTML eingetragen.
  // Sie sind der gefaehrlichste Ort fuer eine Zahl: Ein Titel wird gelesen wie
  // ein Befund, steht aber ueber einem Diagramm, das ihn nicht mehr belegen
  // muss. Beim Abgleich gegen die Datenbank fielen sechs falsche Aussagen auf,
  // eine davon widersprach einem anderen Titel derselben Seite.
  //
  // Unterzeilen beschreiben Achse und Bezugsmenge. Auch dort stehen Zahlen —
  // "109 Monate", "8 Standorte", "188 Mitarbeiter" —, und auch die altern.
  // =========================================================================
  const jVon = j[0], jBis = j[j.length - 1];
  const spanne = `${jVon}–${jBis}`;
  const monate = B.mLabels.length;
  const nFil = f.length;
  // Die Monatsschluessel kommen als "2017-03" aus der Sicht. In einer Unterzeile
  // liest sich das wie eine Kennung, nicht wie ein Datum.
  const MON = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli',
               'August', 'September', 'Oktober', 'November', 'Dezember'];
  const monLang = (s) => {
    const m = /^(\d{4})-(\d{2})/.exec(String(s));
    return m ? `${MON[Number(m[2]) - 1]} ${m[1]}` : String(s);
  };

  // ── Umsatz, Wachstum ─────────────────────────────────────────────────────
  // Ab welchem Jahr wuchs der Umsatz ohne Unterbrechung? Rueckwaerts suchen,
  // statt "seit 2021" zu behaupten.
  let seit = j[j.length - 1];
  for (let i = B.revYoY.length - 1; i >= 0; i--) {
    if (B.revYoY[i] <= 0) break;
    seit = j[i + 1];
  }
  T['revenueChart.titel'] =
    `Umsatz wächst seit ${seit} ohne Rückschlag — der Zuwachs wird kleiner`;
  T['revenueChart.sub'] =
    `Monatlicher Umsatz in € · ${zahl(monate)} Monate · ${monLang(B.mLabels[0])} bis `
    + `${monLang(B.mLabels[monate - 1])} · alle ${nFil} Filialen`;

  T['aovChart.sub']    = `Ø Bestellwert in € · Jahresdurchschnitte · ${spanne}`;
  T['ordersChart.sub'] = `Bestellungen pro Jahr · ${spanne}`;

  // Verlangsamen sich wirklich alle drei Kennzahlen? Erste gegen letzte
  // Wachstumsrate vergleichen, je Kennzahl einzeln.
  const yoyEnde = [
    ['Umsatz', B.revYoY], ['Bestellungen', B.ordYoY], ['Bestellwert', B.aovYoY],
  ].map(([n, r]) => ({ n, erst: r[0], letzt: r[r.length - 1] }));
  const langsamer = yoyEnde.filter(x => x.letzt < x.erst);
  T['yoyChart.titel'] = langsamer.length === yoyEnde.length
    ? `Alle ${zahl(yoyEnde.length)} Kennzahlen wachsen langsamer als in der Frühphase`
    : `${zahl(langsamer.length)} von ${zahl(yoyEnde.length)} Kennzahlen wachsen `
      + `langsamer — ${langsamer.map(x => x.n).join(' und ')}`;
  T['yoyChart.sub'] =
    `Wachstum gegenüber dem Vorjahr in % · Umsatz, Bestellungen, Bestellwert · `
    + `${j[1]}–${letztesVoll}`;

  T['yoyBranchChart.sub'] =
    `Kumulierter Umsatz in € · alle ${nFil} Standorte · ${spanne}`;

  // ── Filialen ─────────────────────────────────────────────────────────────
  const fAov  = [...f].sort((a, b) => b.aov - a.aov);
  const fEff  = [...f].map(x => ({ ...x, jeJahr: x.umsatz / x.betriebsjahre }))
                      .sort((a, b) => b.jeJahr - a.jeJahr);
  T['branchChart.titel'] =
    `${fUmsatz[0].branch_name} führt im Umsatz, ${fAov[0].branch_name} im Bestellwert`;
  T['branchChart.sub'] =
    `Kumulierter Umsatz in € · ${nFil} Standorte in Würzburg · ${spanne}`;
  T['tblBranch.titel'] = `Filial-Scorecard — alle ${nFil} Standorte im Vergleich`;
  T['tblBranch.sub']   = `Alle Kennzahlen je Standort · sortiert nach Umsatz`;

  // Steigt der Bestellwert wirklich mit dem Eroeffnungsjahr? Rangkorrelation
  // nach Spearman — und die Ausreisser dazu, damit "systematisch" belegt ist
  // oder eben nicht.
  const nachAlter = [...f].sort((a, b) =>
    String(a.opening_date).localeCompare(String(b.opening_date)));
  const rangAov = [...nachAlter].sort((a, b) => a.aov - b.aov)
                                .map(x => x.branch_id);
  const dQuad = nachAlter.reduce((s, x, i) =>
    s + (i - rangAov.indexOf(x.branch_id)) ** 2, 0);
  const rho = 1 - (6 * dQuad) / (nFil * (nFil ** 2 - 1));
  const bruch = nachAlter.filter((x, i) => i > 0 && x.aov < nachAlter[i - 1].aov);
  T['branchAovChart.titel'] =
    `Jüngere Filialen liegen im Bestellwert vorn — aber nicht ausnahmslos`;
  T['branchAovChart.sub'] =
    `Ø Bestellwert in € · nach Eröffnungsdatum · ${nFil} Standorte · `
    + `Rangkorrelation ϱ = ${zahl(rho, 2)}, ${zahl(bruch.length)} Ausnahmen`;
  const jungJahr = new Date(nachAlter[nFil - 1].opening_date).getFullYear();
  T['branchAovChart.warnung'] =
    `Der Zusammenhang ist kein Beleg für bessere Standorte: Die ${jungJahr} eröffnete `
    + `${nachAlter[nFil - 1].branch_name} hat nur Umsätze aus Jahren, in denen die `
    + `Preise ohnehin höher lagen. `
    + `Der Bestellwert im Netz stieg von ${euro(B.yearAOV[0])} (${jVon}) auf `
    + `${euro(B.yearAOV[iV])} (${letztesVoll}) — ein Basiseffekt, kein Standorteffekt.`;

  T['branchEfficiencyChart.titel'] =
    `${fEff[0].branch_name} erwirtschaftet je Betriebsjahr am meisten`;
  T['branchEfficiencyChart.sub'] =
    `Umsatz geteilt durch Betriebsjahre · ${euro(fEff[fEff.length - 1].jeJahr, 0)} `
    + `bis ${euro(fEff[0].jeJahr, 0)} · ${nFil} Standorte`;

  // ── Produkte ─────────────────────────────────────────────────────────────
  T['topProductsChart.sub'] =
    `Top ${zahl(B.topProducts.length)} Artikel nach kumuliertem Umsatz · ${spanne} · `
    + `alle ${nFil} Filialen`;
  T['categoryChart.sub'] =
    `Umsatzanteil nach Hauptkategorie · ${zahl(B.categories.length)} Kategorien · `
    + `${spanne}`;
  T['veggieChart.sub'] =
    `Anteil vegetarischer und veganer Bestellungen in % · ${spanne}`;

  const wkTop = [...roh.warenkorb].sort((a, b) => b.konfidenz_pct - a.konfidenz_pct)[0];
  T['tblBasket.titel'] =
    `Höchste Konfidenz: ${wkTop.produkt_a} → ${wkTop.produkt_b} bei `
    + `${proz(wkTop.konfidenz_pct)}`;
  T['tblBasket.sub'] =
    `${zahl(roh.warenkorb.length)} ausgewählte Warenkörbe · Support, Konfidenz `
    + `und Lift · ${zahl(kumBest)} Bestellungen`;

  // ── Kunden ───────────────────────────────────────────────────────────────
  const bz = [...roh.kundenBezirke].sort((a, b) => b.kunden - a.kunden);
  const bzSpanne = (bz[0].kunden / bz[bz.length - 1].kunden - 1) * 100;
  T['districtChart.titel'] =
    `Kunden gleichmäßig über die Bezirke verteilt — ${bz[0].bezirk} knapp vorn`;
  T['loyaltyBarChart.sub'] =
    `Kunden je Treuestufe · ${zahl(B.loyaltyCount.reduce((a, b) => a + b, 0))} Kunden`;

  // Die Frequenz je Kunde ist ueber die Altersgruppen nahezu gleich. Was sich
  // unterscheidet, ist die Zahl der Kunden — das gehoert in den Titel, sonst
  // liest man einen Kohorteneffekt in eine Groessenverteilung hinein.
  const alt = roh.alterUmsatz;
  const freq = alt.map(x => ({ g: x.altersgruppe, f: x.bestellungen / x.kunden }));
  const frqMin = Math.min(...freq.map(x => x.f));
  const frqMax = Math.max(...freq.map(x => x.f));
  const altTop = [...alt].sort((a, b) => b.umsatzanteil_pct - a.umsatzanteil_pct)[0];
  T['ageRevenueChart.titel'] =
    `Umsatzanteil folgt der Kundenzahl — die Bestellfrequenz tut es nicht`;
  T['ageRevenueChart.sub'] =
    `Umsatzanteil je Altersgruppe in % · ${altTop.altersgruppe} führt mit `
    + `${proz(altTop.umsatzanteil_pct)} · Frequenz ${zahl(frqMin, 1)} bis `
    + `${zahl(frqMax, 1)} Bestellungen je Kunde in allen ${zahl(alt.length)} Gruppen`;

  // ── Kanäle ───────────────────────────────────────────────────────────────
  const k25 = B.channelLabels.map((n, i) => ({
    n, aov: B.channelAOV2025[i], best: B.channelOrders2025[i],
    ums: B.channelRevenue2025[i],
  }));
  const kAov  = [...k25].sort((a, b) => b.aov - a.aov);
  const kBest = [...k25].sort((a, b) => b.best - a.best);
  const kUms  = [...k25].sort((a, b) => b.ums - a.ums);
  T['channelAOVChart.titel'] =
    `${letztesVoll}: höchster Bestellwert im ${kAov[0].n}, höchstes Volumen am `
    + `${kBest[0].n}`;
  T['channelAOVChart.sub'] =
    `Ø Bestellwert je Kanal in € · ${letztesVoll} · `
    + `${euro(kAov[kAov.length - 1].aov)} bis ${euro(kAov[0].aov)} · `
    + `alle ${nFil} Filialen`;

  const appJetzt = B.appData[B.appData.length - 1];
  const appJahr = j[B.appData.length - 1];
  const appFrueh = B.appData.find(x => x > 0);
  T['channelRevenueChart.titel'] =
    `${kUms[0].n} trägt den größten Umsatzanteil, App Order wächst am schnellsten`;

  // Der Kanalmix ueber den Tag: die groesste Spanne aller vier Kanaele
  // entscheidet, ob es Tageszeitkanaele gibt. Sie liegt im niedrigen
  // einstelligen Prozentpunktbereich — also gibt es sie nicht.
  const tod = B.channelTodSpanne[0];
  T['channelTodChart.titel'] =
    `Der Kanalmix ist über den ganzen Tag praktisch konstant`;
  T['channelTodChart.sub'] =
    `Anteil der Bestellungen in % · ${zahl(B.channelLabels.length)} Kanäle · `
    + `${zahl(B.channelTodHours[0])}–${zahl(B.channelTodHours[B.channelTodHours.length - 1])} Uhr · `
    + `größte Tagesschwankung ${zahl(tod.spanne, 1)} Prozentpunkte (${tod.kanal})`;

  // ── Spitzenartikel je Kanal ──────────────────────────────────────────────
  const kp = B.kanalProdukte;
  const gleich = kp.filter(x =>
    x.artikel.map(a => a.produkt).join('|')
      === kp[0].artikel.map(a => a.produkt).join('|')).length;
  T['kanalProdukte.titel'] = gleich === kp.length
    ? `Alle ${zahl(kp.length)} Kanäle haben dieselben fünf Spitzenartikel`
    : `${zahl(gleich)} der ${zahl(kp.length)} Kanäle haben dieselben fünf Spitzenartikel`;
  T['kanalProdukte.sub'] =
    `Rang nach Stückzahl · Anteil an der Stückzahl des Kanals · ${spanne}`;
  T['kanalProdukte.deutung'] =
    `Interpretation: Die Kanalprofile unterscheiden sich kaum. Alle `
    + `${zahl(kp.length)} Kanäle führen ${kp[0].artikel[0].produkt}, `
    + `${kp[0].artikel[1].produkt} und ${kp[0].artikel[2].produkt} auf den ersten `
    + `drei Rängen; die Anteile liegen zwischen `
    + `${proz(Math.min(...kp.flatMap(x => x.artikel.map(a => a.anteil_pct))))} und `
    + `${proz(Math.max(...kp.flatMap(x => x.artikel.map(a => a.anteil_pct))))} der `
    + `Stückzahl des jeweiligen Kanals. Ein Kanal ist danach kein Geschmacksprofil, `
    + `sondern nur ein Zugangsweg.`;

  // ── Zeit ─────────────────────────────────────────────────────────────────
  T['dowChart.sub'] = `Bestellungen je Wochentag · Mo–So · ${spanne}`;
  T['hourChart.sub'] =
    `Bestellungen je Stunde · ${zahl(B.hourLabels[0])}–`
    + `${zahl(B.hourLabels[B.hourLabels.length - 1])} Uhr · ${spanne}`;
  T['heatmapGrid.sub'] =
    `Bestellungen nach Wochentag × Stunde · Farbintensität = Volumen · ${spanne}`;
  T['dowRevenueChart.sub'] = `Umsatz je Wochentag in € · ${spanne}`;
  T['paymentChart.sub'] =
    `Anteil in % · ${zahl(B.paymentYears ? 4 : 4)} Zahlungsarten · ${spanne} · `
    + `alle ${nFil} Filialen`;

  T['channelChart.titel'] =
    `App Order steigt auf ${proz(appJetzt)} (${appJahr}) — ${kUms[0].n} gibt `
    + `langsam ab`;
  T['channelChart.sub'] =
    `Anteil der Bestellungen in % · ${zahl(B.channelLabels.length)} Kanäle · ${spanne}`;

  // ── RFM und Assoziation ──────────────────────────────────────────────────
  T['rfmValueChart.sub'] =
    `Ø Kundenwert je Segment in € · ${zahl(B.rfmSegments.length)} Segmente`;
  T['tblRFM.titel'] =
    `RFM-Profil der ${zahl(B.rfmSegments.length)} Segmente`;
  T['tblRFM.sub'] =
    `${zahl(B.rfmSegments.length)} Segmente · Recency, Frequency, Monetary · `
    + `${zahl(roh.rfm.reduce((s, x) => s + Number(x.kunden), 0))} Kunden`;

  T['liftChart.titel'] =
    `${zahl(dmStark.length)} der ${zahl(dmWk.length)} Paare erreichen einen Lift `
    + `über ${zahl(dmLiftStark)}`;
  // Nicht "Alle": v_warenkorb_regeln fuehrt weit mehr Paare, die Tabelle
  // zeigt eine kuratierte Auswahl.
  T['tblAssoc.titel'] = `${zahl(dmWk.length)} ausgewählte Regeln mit Lift-Metrik`;
  T['tblAssoc.sub'] =
    `${zahl(dmWk.length)} ausgewählte Regeln · nach Häufigkeit geordnet · Lift `
    + `über ${zahl(dmLiftStark)} gilt als starke Assoziation`;

  // ── Simulation und Prognose ──────────────────────────────────────────────
  T['simChart.titel'] =
    `Preissimulation — wie eine Preisänderung auf Umsatz und Marge wirkt`;
  // Die Prognose setzt auf dem letzten vollstaendigen Jahr auf, nicht auf dem
  // angebrochenen — sonst waere das erste Prognosejahr zur Haelfte gemessen.
  const pJahre = B.szenarien[0].jahre.length;
  const pVon = letztesVoll + 1, pBis = letztesVoll + pJahre;
  T['forecastChart.titel'] =
    `Umsatzprognose ${pVon}–${pBis} in ${zahl(B.szenarien.length)} Szenarien`;
  T['tblForecast.titel'] = `Szenarienvergleich — Umsatz, Bestellungen, Investition`;
  T['tblForecast.sub'] =
    `${zahl(B.szenarien.length)} Szenarien für ${pVon}–${pBis} · fortgeschrieben aus `
    + `${zahl(B.revYoY.length)} Jahren beobachtetem Wachstum`;

  // ── Wetter ───────────────────────────────────────────────────────────────
  // Die Randklassen der Temperatur bestehen aus sehr wenigen Tagen. Ohne diese
  // Zahl liest man aus einem Ausschlag einen Effekt heraus, der auf einem
  // einzigen Tag beruht.
  const tb = roh.wetterTemperatur;
  const tbMin = [...tb].sort((a, b) => a.tage - b.tage)[0];
  const tbGross = tb.filter(x => x.tage >= 100);
  const tbHoch = [...tbGross].sort((a, b) => b.umsatz_je_tag - a.umsatz_je_tag)[0];
  const tbTief = [...tbGross].sort((a, b) => a.umsatz_je_tag - b.umsatz_je_tag)[0];
  T['tempBinChart.titel'] =
    `Wärmere Tage bringen mehr Umsatz — der Abstand ist klein`;
  T['tempBinChart.sub'] =
    `Ø Tagesumsatz je Temperaturklasse · ${euro(tbTief.umsatz_je_tag, 0)} bis `
    + `${euro(tbHoch.umsatz_je_tag, 0)} über Klassen mit mindestens 100 Tagen · `
    + `die kleinste Klasse umfasst ${zahl(tbMin.tage)} `
    + `${Number(tbMin.tage) === 1 ? 'Tag' : 'Tage'}`;

  const wl = [...roh.wetterLagen].sort((a, b) => b.umsatz_je_tag - a.umsatz_je_tag);
  T['weatherCondChart.titel'] =
    `Zwischen bester und schwächster Wetterlage liegen `
    + `${proz((wl[0].umsatz_je_tag / wl[wl.length - 1].umsatz_je_tag - 1) * 100)} `
    + `Tagesumsatz`;
  T['weatherCondChart.sub'] =
    `Ø Tagesumsatz nach Wetterlage · ${zahl(wl.length)} Kategorien · `
    + `${zahl(wl[wl.length - 1].tage)} bis ${zahl(wl[0].tage)} Tage je Kategorie`;

  // Die Klassengrenzen standen als Text in den Kacheln ("25-30 Grad"),
  // waehrend der waermste erfasste Tag 27,7 Grad hat. Jetzt kommen sie
  // aus derselben Quelle wie die Werte darunter.
  const tKl   = roh.wetterTemperatur.filter(x => x.tage > 0);
  const tWarm = tKl[tKl.length - 1], tKalt = tKl[1];
  // "bis" statt Gedankenstrich: Bei negativen Graden entstuende sonst
  // "−8,7–−5,1", was niemand liest.
  T['wetter1.titel'] =
    `WÄRMSTE TAGE (${zahl(tWarm.von, 1)} bis ${zahl(tWarm.bis, 1)} °C)`;
  T['wetter2.titel'] =
    `KÄLTESTE TAGE (${zahl(tKalt.von, 1)} bis ${zahl(tKalt.bis, 1)} °C)`;

  T['weatherScatterChart.titel'] =
    `Temperatur gegen Tagesumsatz — der Wachstumstrend überlagert den Wettereffekt`;

  const rg = roh.wetterRegen;
  const rgGross = rg.filter(x => x.tage >= 100);
  const rgHoch = [...rgGross].sort((a, b) => b.umsatz_je_tag - a.umsatz_je_tag)[0];
  const rgKlein = [...rg].sort((a, b) => a.tage - b.tage)[0];
  T['rainChart.titel'] = `Niederschlag zeigt keinen erkennbaren negativen Effekt`;
  T['rainChart.sub'] =
    `Ø Tagesumsatz je Niederschlagsklasse · ${zahl(rg.length)} Klassen · `
    + `der höchste Wert steht über ${zahl(rgKlein.tage)} `
    + `${Number(rgKlein.tage) === 1 ? 'Tag' : 'Tagen'} und trägt deshalb nicht`;

  // Die Deutung stand bis zuletzt als fester Text im HTML und nannte 7 Tage,
  // waehrend die Daten 8 zeigen — die Untertitelzeile darueber war laengst
  // mitgewandert, weil sie erzeugt wird. Jetzt wird auch die Deutung gebaut.
  const rgSpitze  = [...rg].sort((a, b) => b.umsatz_je_tag - a.umsatz_je_tag)[0];
  const rgTage    = rg.reduce((s, x) => s + Number(x.tage), 0);
  const rgMittel  = rg.reduce((s, x) => s + x.umsatz_je_tag * x.tage, 0) / rgTage;
  const rgNiedrig = [...rgGross].sort((a, b) => a.umsatz_je_tag - b.umsatz_je_tag)[0];
  const rgSpanne  = (rgHoch.umsatz_je_tag / rgNiedrig.umsatz_je_tag - 1) * 100;
  const rgListe   = rgGross
    .map(x => `${x.klasse} ${euro(x.umsatz_je_tag, 0)} an ${zahl(x.tage)} Tagen`)
    .join(', ');
  T['rainChart.deutung'] =
    `Der Umsatz sinkt nicht mit steigendem Niederschlag: Die stärkste Klasse ist `
    + `${rgSpitze.klasse} mit ${euro(rgSpitze.umsatz_je_tag, 0)} je Tag, gegenüber `
    + `${euro(rgMittel, 0)} im Mittel aller ${zahl(rgTage)} Betriebstage. Belastbar `
    + `ist dieser Spitzenwert nicht: Hinter ihm stehen nur ${zahl(rgSpitze.tage)} `
    + `${Number(rgSpitze.tage) === 1 ? 'Tag' : 'Tage'}. Aussagekräftig sind allein `
    + `die Klassen mit mindestens 100 Tagen — ${rgListe} —, zwischen denen `
    + `${proz(rgSpanne)} liegen. Ein Zusammenhang zwischen Regenmenge und Umsatz `
    + `ist darin nicht zu erkennen.`;
  T['rainChart.empfehlung'] =
    `Auf Regen ausgerichtete Aktionen sind durch diese Daten nicht gedeckt. Die `
    + `naheliegende Vermutung, Regen verlagere Bestellungen vom Counter in den `
    + `Drive-Through, lässt sich hier weder belegen noch widerlegen: Dafür wären `
    + `die Kanalanteile je Tag nötig, die diese Sicht nicht führt. Erfolgsmaß einer `
    + `Prüfung wäre der Counter-Anteil an Regentagen gegenüber trockenen Tagen.`;

  // ── Personal ─────────────────────────────────────────────────────────────
  const pf = [...roh.personalFilialen].sort((a, b) => b.umsatz_je_ma - a.umsatz_je_ma);
  const maGes = roh.personalFilialen.reduce((s, x) => s + Number(x.mitarbeiter), 0);
  T['empProdChart.titel'] =
    `${pf[0].branch_name} erwirtschaftet je Mitarbeiter das `
    + `${zahl(pf[0].umsatz_je_ma / pf[pf.length - 1].umsatz_je_ma, 1)}-fache von `
    + `${pf[pf.length - 1].branch_name}`;
  T['empProdChart.sub'] =
    `Kumulierter Umsatz je Mitarbeiter · ${spanne} · ${nFil} Filialen · `
    + `${zahl(maGes)} Mitarbeiter`;

  const pr = [...roh.personalRollen].sort((a, b) => b.anzahl - a.anzahl);
  const prGes = roh.personalRollen.reduce((s, x) => s + Number(x.anzahl), 0);
  T['empRoleChart.titel'] =
    `${pr[0].bezeichnung} und ${pr[1].bezeichnung} stellen `
    + `${proz(100 * (Number(pr[0].anzahl) + Number(pr[1].anzahl)) / prGes)} der Belegschaft`;
  T['empRoleChart.sub'] =
    `${zahl(roh.personalRollen.length)} Rollen · Anzahl und Ø-Stundenlohn · `
    + `${zahl(prGes)} Mitarbeiter`;

  // ── Zufriedenheit ────────────────────────────────────────────────────────
  const zk = [...roh.zufriedenheitKanal].sort((a, b) => b.zufriedenheit - a.zufriedenheit);
  T['satChannelChart.titel'] =
    `${zk[0].kanal} liegt mit ${zahl(zk[0].zufriedenheit, 2)} vorn, `
    + `${zk[zk.length - 1].kanal} mit ${zahl(zk[zk.length - 1].zufriedenheit, 2)} hinten`;
  T['satChannelChart.sub'] =
    `Ø Zufriedenheit je Kanal · Skala 1 bis 5 · Spanne `
    + `${zahl(zk[0].zufriedenheit - zk[zk.length - 1].zufriedenheit, 2)} Punkte über `
    + `${zahl(roh.zufriedenheitKanal.reduce((s, x) => s + Number(x.bewertungen), 0))} `
    + `Bewertungen`;

  // Wo faellt die Zufriedenheit? Die erste Klasse, die deutlich unter der
  // besten liegt — die Klassengrenzen kommen aus der Sicht, nicht aus dem Kopf.
  const zd = roh.zufriedenheitDauer;
  const zdBest = Math.max(...zd.map(x => x.zufriedenheit));
  // Ab welcher Klasse faellt die Zufriedenheit spuerbar? Ein Zehntelpunkt auf
  // einer Skala von 1 bis 5 — darunter ist es Rauschen, nicht Erfahrung.
  const zdFall = zd.find(x => zdBest - x.zufriedenheit > 0.1);
  T['satDurationChart.titel'] = zdFall
    ? `Zufriedenheit bleibt stabil und fällt erst ab ${zdFall.dauer_klasse} Minuten`
    : `Zufriedenheit bleibt über alle Bearbeitungsdauern stabil`;
  T['satDurationChart.sub'] =
    `Ø Zufriedenheit nach Bearbeitungsdauer · ${zahl(zd.length)} Klassen · `
    + `${zahl(Math.min(...zd.map(x => x.zufriedenheit)), 2)} bis `
    + `${zahl(zdBest, 2)} Punkte`;

  const sh = B.satHourVal, shMin = Math.min(...sh), shMax = Math.max(...sh);
  T['satHourChart.titel'] =
    `Zufriedenheit über den Tag: ${zahl(shMax - shMin, 2)} Punkte zwischen bester `
    + `und schwächster Stunde`;
  T['satHourChart.sub'] =
    `Ø Zufriedenheit je Stunde · ${zahl(B.satHours[0])}–`
    + `${zahl(B.satHours[B.satHours.length - 1])} Uhr · Skala 1 bis 5`;

  const psUnter = B.promoNames.filter((n, i) => B.promoAvgSat[i] < B.satBasis);
  T['promoSatChart.titel'] = psUnter.length === 0
    ? `Jede Aktion liegt über der Zufriedenheit ohne Aktion`
    : `Alle Aktionen liegen über der Basislinie — außer ${psUnter.join(' und ')}`;

  // ── Standortvergleich ────────────────────────────────────────────────────
  T['tblGeo.titel'] =
    `${fUmsatz[0].branch_name} mit dem höchsten Umsatz, ${fAov[0].branch_name} mit `
    + `dem höchsten Bestellwert`;
  T['tblGeo.sub'] =
    `${nFil} Standorte · Umsatz, Flächenproduktivität, Mietquote · Würzburg`;


  return T;
}

export function fuelleTexte(B, roh) {
  const T = baueTexte(B, roh);
  let gesetzt = 0, fehlend = [];
  document.querySelectorAll('[data-txt]').forEach(el => {
    const s = T[el.dataset.txt];
    if (s === undefined) { fehlend.push(el.dataset.txt); return; }
    // Nur die Textknoten ersetzen. Die Marke ("Interpretation:") steht als
    // <strong> im HTML, und im Deutungsblock steckt die Empfehlung als eigenes
    // Element — beide muessen stehen bleiben, sonst loescht das Fuellen des
    // Deutungstextes die Empfehlung gleich mit.
    [...el.childNodes].filter(k => k.nodeType === Node.TEXT_NODE).forEach(k => k.remove());
    const marke = el.querySelector(':scope > strong');
    // Steht die Marke schon im HTML, darf sie nicht ein zweites Mal aus dem
    // Text kommen — sonst liest man "Interpretation: Interpretation: ...".
    let text = s;
    if (marke) {
      const m = marke.textContent.trim().replace(/:\s*$/, '');
      const doppelt = new RegExp('^\\s*' + m.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
        + '\\s*:\\s*', 'i');
      text = text.replace(doppelt, '');
    }
    const knoten = document.createTextNode(' ' + text + ' ');
    if (marke) marke.after(knoten); else el.prepend(knoten);
    gesetzt++;
  });
  return { gesetzt, fehlend };
}
