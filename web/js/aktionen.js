// aktionen.js — der Maßnahmenplan der Management Summary.
//
// Die achtzehn Karten waren die aeltesten Zahlen im Dashboard und die
// folgenreichsten: Sie sagen, was zu tun ist. Mehrere ihrer Aussagen waren
// beim Abgleich mit der Datenbank nicht mehr haltbar — die Empfehlung, den
// Student Discount auszuweiten, stuetzte sich auf einen "ROI", der nichts
// anderes ist als der Rabattsatz von hinten aufgezaeumt.
//
// Deshalb wird hier nicht nur die Zahl ausgetauscht, sondern die Begruendung
// mitgefuehrt: Jede Karte nennt die Groesse, an der sich die Massnahme messen
// laesst. Die Dringlichkeitsstufe bleibt im HTML — sie ist eine Setzung, keine
// Messung.
//
// Format eines Textes: eine Liste aus Zeichenketten und { b: '...' } fuer
// hervorgehobene Werte. So entsteht das Markup ohne innerHTML.

const zahl = (v, n = 0) => Number(v).toLocaleString('de-DE',
  { minimumFractionDigits: n, maximumFractionDigits: n }).replace('-', '−');
const euro = (v, n = 2) => '€' + zahl(v, n);
const proz = (v, n = 1) => zahl(v, n) + ' %';
const tsd  = (v) => '€' + zahl(v / 1000, 0) + 'k';
const mio  = (v) => '€' + zahl(v / 1e6, 2) + ' Mio.';

export function baueAktionen(B, roh) {
  const f = roh.filialen;
  const jeJahr = (x) => x.umsatz / x.betriebsjahre;
  const nachJahr = [...f].sort((a, b) => jeJahr(b) - jeJahr(a));
  const schwach = [...f].sort((a, b) => jeJahr(a) - jeJahr(b))[0];
  const teuerste = [...f].sort((a, b) => b.mietquote_pct - a.mietquote_pct)[0];
  const qmBest = [...f].sort((a, b) => b.umsatz_je_qm / b.betriebsjahre
                                     - a.umsatz_je_qm / a.betriebsjahre)[0];
  const kleinste = [...f].sort((a, b) => a.size_sqm - b.size_sqm)[0];
  const pf = [...roh.personalFilialen].sort((a, b) => b.umsatz_je_ma - a.umsatz_je_ma);
  const pfMax = pf[0], pfMin = pf[pf.length - 1];
  const hb = roh.heimatbezirk[0] ?? {};

  const zk = [...roh.zufriedenheitKanal].sort((a, b) => b.zufriedenheit - a.zufriedenheit);
  const zBest = zk[0], zSchlecht = zk[zk.length - 1];
  const k25 = roh.kanaeleJahr.filter(x => x.jahr === 2025)
    .sort((a, b) => b.anteil_pct - a.anteil_pct);
  const app = k25.find(x => /App/i.test(x.kanal)) ?? {};
  const kiosk = zk.find(x => /Kiosk/i.test(x.kanal)) ?? {};
  const counter = zk.find(x => /Counter/i.test(x.kanal)) ?? {};
  const ohneDT = f.filter(x => !x.has_drive_through);

  const seg = (n) => roh.rfm.find(x => x.segment === n) ?? {};
  const risk = seg('Abwanderungsgefahr'), champ = seg('Champions');

  // Retention nur ueber volle Jahre: das laufende Jahr ist erst zu einem
  // Viertel gelaufen und wuerde als Einbruch erscheinen, der keiner ist.
  const retention = roh.kohorten
    .filter(x => x.jahr > x.kohorte && x.jahr <= 2025 && x.kohortengroesse)
    .map(x => 100 * x.aktive / x.kohortengroesse);
  const rMin = Math.min(...retention), rMax = Math.max(...retention);

  const stark = [...roh.warenkorb].filter(r => r.lift > 2).sort((a, b) => b.lift - a.lift);
  const salat = stark.find(r => /Salad/i.test(r.produkt_b)) ?? stark[stark.length - 1] ?? {};

  const pm = roh.promotionen;
  const nachUplift = [...pm].sort((a, b) => b.uplift_pct - a.uplift_pct);
  const bestNetto = [...pm].sort((a, b) => b.netto_pct - a.netto_pct)[0];
  const schlechtNetto = [...pm].sort((a, b) => a.netto_pct - b.netto_pct)[0];
  const promoBest = pm.reduce((a, x) => a + x.bestellungen, 0);
  const kumBest = B.yearOrders.reduce((a, b) => a + b, 0);
  const promoQuote = 100 * promoBest / kumBest;

  const zd = [...roh.zufriedenheitDauer].sort((a, b) => a.nr - b.nr);
  // Groesster Sprung zwischen zwei benachbarten Dauerklassen: das ist die
  // Stelle, an der eine Grenze ueberhaupt sinnvoll liegen kann.
  let sprung = { i: 1, delta: 0 };
  for (let i = 1; i < zd.length; i++) {
    const d = zd[i - 1].zufriedenheit - zd[i].zufriedenheit;
    if (d > sprung.delta) sprung = { i, delta: d };
  }
  const vorSprung = zd[sprung.i - 1], nachSprung = zd[sprung.i];

  const A = {};

  // ── Filialen ─────────────────────────────────────────────────────────────
  // Die Leistung je Mitarbeiter derselben Filiale, nicht die schwaechste im
  // Netz — sonst steht in einem Satz die Zahl einer anderen Filiale.
  const schwachPf = roh.personalFilialen
    .find(x => x.branch_name === schwach.branch_name) ?? {};
  const aovNetz = f.reduce((a, x) => a + x.umsatz, 0)
                / f.reduce((a, x) => a + x.bestellungen, 0);
  A[0] = {
    titel: `${schwach.branch_name}: Standort-Review einleiten`,
    text: ['Schwächster Standort je Betriebsjahr (', { b: tsd(jeJahr(schwach)) },
      ` gegen ${tsd(jeJahr(nachJahr[0]))} an der Spitze), bei `,
      { b: tsd(schwachPf.umsatz_je_ma) }, ' je Mitarbeiter gegen '
      + `${tsd(pfMax.umsatz_je_ma)} an der Spitze. Der Bestellwert liegt mit `
      + `${euro(schwach.aov)} `,
      schwach.aov >= aovNetz ? 'über' : 'unter',
      ` dem Netzmittel von ${euro(aovNetz)} — an der Frequenz ändert das nichts. `
      + 'Die Mietquote ist mit ',
      { b: proz(schwach.mietquote_pct) },
      ` nicht der Grund; die höchste trägt ${teuerste.branch_name} `,
      `mit ${proz(teuerste.mietquote_pct)}.`],
    impl: 'Vergleichsrechnung Schließung gegen Relaunch (kleinere Fläche, '
      + 'Mietverhandlung, Konzeptanpassung) im laufenden Quartal. Messgröße ist '
      + 'der Umsatz je Betriebsjahr im Vergleich zum Netzmittel von '
      + `${tsd(f.reduce((a, x) => a + jeJahr(x), 0) / f.length)}.`,
  };
  A[1] = {
    titel: `${qmBest.branch_name}-Format als Vorlage prüfen`,
    text: ['Höchste Flächenleistung je Betriebsjahr (',
      { b: euro(qmBest.umsatz_je_qm / qmBest.betriebsjahre, 0) + '/m²' },
      `) auf ${zahl(qmBest.size_sqm)} m². Die kleinste Fläche im Netz hat `,
      `${kleinste.branch_name} mit ${zahl(kleinste.size_sqm)} m² — Fläche allein `,
      'erklärt die Leistung also nicht.'],
    impl: 'Standort-Screening für ein zweites Kompaktformat in Mainfranken. '
      + 'Messgröße ist der Umsatz je Quadratmeter und Betriebsjahr.',
  };
  A[2] = {
    titel: 'Einzugsgebiet ist überregional',
    text: ['Nur ', { b: proz(hb.anteil_pct) }, ' der Bestellungen stammen von Kunden '
      + `aus dem Bezirk ihrer Filiale (${zahl(hb.aus_heimatbezirk)} von `
      + `${zahl(hb.bestellungen)}). Die ${zahl(hb.filialbezirke)} Standorte bedienen `
      + `${zahl(hb.wohnbezirke)} Wohnbezirke: Standortwahl folgt Verkehr und `
      + 'Lauffrequenz, nicht der Wohnortdichte.'],
    impl: null,
  };

  // ── Kanäle ───────────────────────────────────────────────────────────────
  A[3] = {
    titel: `${zBest.kanal}-Anteil ausbauen — heute ${proz(app.anteil_pct)} der Bestellungen`,
    text: [`Die höchste Zufriedenheit aller Kanäle hat ${zBest.kanal} mit `,
      { b: zahl(zBest.zufriedenheit, 2) },
      ` (aus ${zahl(zBest.bewertungen)} Bewertungen), bei nur `,
      { b: proz(app.anteil_pct) }, ' Anteil im Jahr 2025. Jede verlagerte Bestellung '
      + `entlastet ${zSchlecht.kanal}, den Kanal mit der niedrigsten Zufriedenheit `
      + `(${zahl(zSchlecht.zufriedenheit, 2)}). Der Bestellwert spricht nicht dafür: `
      + `${zBest.kanal} liegt 2025 bei ${euro(app.aov)} und damit am unteren Ende — `
      + 'die Verlagerung zahlt auf Zufriedenheit und Kosten ein, nicht auf den Umsatz.'],
    impl: 'Exklusive Vorbestellung und Treuepunkte in der App. Messgröße ist der '
      + 'Kanalanteil, nicht der Umsatz je Bestellung.',
  };
  A[4] = {
    titel: `Kiosk-Ausbau in ${ohneDT.slice(0, 2).map(x => x.branch_name.replace('BM ', '')).join(' und ')}`,
    text: ['Kiosk erreicht ', { b: zahl(kiosk.zufriedenheit, 2) },
      ` gegen ${zahl(counter.zufriedenheit, 2)} am Counter — ein kleiner, aber `
      + 'durchgängiger Abstand, der zugleich Personal entlastet. '
      + `${zahl(ohneDT.length)} der ${zahl(f.length)} Standorte haben keinen `
      + 'Drive-Through; dort ist der Kiosk die einzige Alternative zur Theke.'],
    impl: 'Zwei Terminals je Standort, Messgröße ist der Kioskanteil an den '
      + 'Bestellungen dieser Filialen.',
  };
  A[5] = {
    titel: 'Mobile-Payment-Infrastruktur vorziehen',
    text: null,
    impl: null,
  };

  // ── Kunden ───────────────────────────────────────────────────────────────
  A[6] = {
    titel: `Reaktivierung für das Segment „Abwanderungsgefahr" (${proz(risk.anteil_pct)})`,
    text: [{ b: zahl(risk.kunden) }, ' Kunden mit belegter Kaufbereitschaft — im Mittel ',
      { b: zahl(risk.frequenz, 1) }, ' Bestellungen — deren letzte Bestellung ',
      { b: zahl(risk.recency_tage) + ' Tage' }, ' zurückliegt. Bisher haben sie ',
      { b: mio(risk.umsatz_gesamt) }, ' gebracht. Das ist kein Risikobetrag, sondern '
      + 'die Größenordnung, um die es geht, wenn die Gruppe in „Verloren" abrutscht.'],
    impl: 'Gestaffelte Ansprache über App und E-Mail. Messgröße ist die mittlere '
      + `Recency dieses Segments, heute ${zahl(risk.recency_tage)} Tage.`,
  };
  A[7] = {
    titel: `Champions-Programm aufbauen (${proz(champ.anteil_pct)} = ${zahl(champ.kunden)} Kunden)`,
    text: ['Diese Gruppe bringt ', { b: euro(champ.lebenswert, 0) },
      ' je Kopf bei ', { b: zahl(champ.frequenz, 1) },
      ' Bestellungen — mehr als jedes andere Segment. Ein Rabatt an sie kostet '
      + 'Marge ohne Verhaltensänderung; das Ziel ist Weiterempfehlung.'],
    impl: 'Eigene Treuestufe mit Vorabzugang statt Rabatt. Messgröße ist der '
      + 'Anteil der Champions, der über zwölf Monate im Segment bleibt.',
  };
  A[8] = {
    titel: `Kohorten-Retention zwischen ${proz(rMin)} und ${proz(rMax)}`,
    text: ['Über alle vollen Jahre bleibt jede Kohorte nahezu vollständig aktiv '
      + `(${proz(rMin)} bis ${proz(rMax)}). Ein strukturelles Abwanderungsproblem `
      + 'gibt es nicht. Der Hebel liegt bei der Frequenz der vorhandenen Kunden, '
      + 'nicht bei der Neukundengewinnung.'],
    impl: null,
  };

  // ── Produkte ─────────────────────────────────────────────────────────────
  A[9] = {
    titel: 'Bundles auf die belastbaren Regeln beschränken',
    text: [`Von ${zahl(roh.warenkorb.length)} geprüften Regeln erreichen nur `,
      { b: zahl(stark.length) }, ' einen Lift über 2: ',
      stark.map(r => `${r.produkt_a} → ${r.produkt_b} (${zahl(r.lift, 2)})`).join(', '),
      '. Alle übrigen liegen nahe 1 — dort kauft niemand das eine wegen des anderen.'],
    impl: 'Kombiangebote nur für diese Paare. Messgröße ist die Konfidenz der '
      + 'jeweiligen Regel.',
  };
  A[10] = {
    titel: 'Pflanzliche Linie ausbauen',
    text: [`${salat.produkt_a} und ${salat.produkt_b} treten mit einem Lift von `,
      { b: zahl(salat.lift, 2) }, ' zusammen auf — überzufällig, aber bei einer '
      + `Konfidenz von ${proz(salat.konfidenz_pct)} kein zwingendes Muster. `
      + 'Der Befund trägt eine Sortimentsprüfung, keine Kampagne.'],
    impl: 'Erweiterung der pflanzlichen Auswahl prüfen. Messgröße ist der '
      + 'Mengenanteil pflanzlicher Burger, der zuletzt bei '
      + `${proz(roh.veggie[roh.veggie.length - 1].anteil_pct)} lag.`,
  };

  // ── Preise und Aktionen ──────────────────────────────────────────────────
  A[11] = {
    titel: 'Preisanpassung mit Augenmaß möglich',
    text: ['Nur ', { b: proz(promoQuote) }, ' aller Bestellungen laufen über eine '
      + 'Aktion. Das spricht gegen ausgeprägte Preissensitivität, ersetzt aber '
      + 'keinen Test — die Preissimulation zeigt Annahmen, keine gemessene '
      + 'Elastizität.'],
    impl: null,
  };
  A[12] = {
    titel: `${schlechtNetto.aktion} reformieren oder einstellen`,
    text: ['Der Warenkorb vor Rabatt liegt mit ',
      { b: euro(schlechtNetto.aov_vor_rabatt) }, ' zwar ',
      schlechtNetto.uplift_pct >= 0 ? 'über' : 'unter',
      ` dem Bestellwert ohne Aktion (${euro(schlechtNetto.baseline_aov)}), nach `,
      `${proz(schlechtNetto.rabatt_pct, 0)} Rabatt bleiben davon aber `,
      { b: proz(schlechtNetto.netto_pct) }, ' — der schlechteste Wert aller Aktionen.'],
    impl: 'Umstellen auf eine Zugabe statt eines Rabatts. Messgröße ist der '
      + 'Bestellwert nach Rabatt gegen den Bestellwert ohne Aktion.',
  };
  A[13] = {
    titel: `${bestNetto.aktion} ausweiten — beste Bilanz nach Rabatt`,
    text: ['Der Warenkorb vor Rabatt liegt bei ', { b: euro(bestNetto.aov_vor_rabatt) },
      `, um ${proz(bestNetto.uplift_pct)} über dem Bestellwert ohne Aktion; nach `,
      `${proz(bestNetto.rabatt_pct, 0)} Rabatt bleiben `, { b: proz(bestNetto.netto_pct) },
      '. Nicht zu verwechseln mit dem ausgewiesenen ROI: Der ist rechnerisch '
      + '(100 − Rabattsatz) / Rabattsatz und sagt über die Wirkung einer Aktion '
      + 'nichts aus.'],
    impl: 'Ausweitung auf weitere Standorte. Messgröße ist der Warenkorb vor '
      + 'Rabatt gegen die Vergleichsgröße ohne Aktion.',
  };
  A[14] = {
    titel: `Aktionsquote bei ${proz(promoQuote)} halten`,
    text: [`${zahl(promoBest)} von ${zahl(kumBest)} Bestellungen laufen über eine `
      + 'Aktion. Von den ', { b: zahl(pm.length) }, ' Aktionen heben ',
      { b: zahl(nachUplift.filter(x => x.uplift_pct > 0).length) },
      ' den Warenkorb vor Rabatt über die Vergleichsgröße; nach Rabatt bleibt '
      + 'keine im Plus. Aktionen sind hier Frequenzmittel, kein Umsatzhebel.'],
    impl: null,
  };

  // ── Betrieb ──────────────────────────────────────────────────────────────
  A[15] = {
    titel: `Bearbeitungsdauer unter ${vorSprung.dauer_klasse.split('-').pop()} Minuten halten`,
    text: ['Die Zufriedenheit sinkt über die Dauerklassen langsam und gleichmäßig, '
      + `von ${zahl(zd[0].zufriedenheit, 2)} in der Klasse ${zd[0].dauer_klasse} `
      + `auf ${zahl(zd[zd.length - 1].zufriedenheit, 2)} in der Klasse `
      + `${zd[zd.length - 1].dauer_klasse} Minuten. Der einzige deutliche Absatz `
      + `liegt zwischen ${vorSprung.dauer_klasse} und ${nachSprung.dauer_klasse} `
      + 'Minuten mit ', { b: zahl(sprung.delta, 2) + ' Punkten' },
      `. Betroffen sind ${zahl(nachSprung.bestellungen)} Bestellungen `
      + `(${proz(100 * nachSprung.bestellungen / kumBest, 1)}) — eine harte Grenze `
      + 'wäre teurer als der Schaden, den sie verhindert.'],
    impl: 'Die langsamsten Fälle beobachten statt eine Zusage über alle Bestellungen '
      + 'zu geben. Messgröße ist der Anteil der Klasse '
      + `${nachSprung.dauer_klasse} Minuten.`,
  };
  A[16] = {
    titel: 'Besetzung an den Spitzenstunden ausrichten',
    text: null,
    impl: null,
  };
  A[17] = {
    titel: 'Produktivitätsgefälle ist standortbedingt',
    text: [{ b: zahl(pfMax.umsatz_je_ma / pfMin.umsatz_je_ma, 1) + '× Spreizung' },
      ` zwischen ${pfMax.branch_name} (${tsd(pfMax.umsatz_je_ma)} je Mitarbeiter) und `
      + `${pfMin.branch_name} (${tsd(pfMin.umsatz_je_ma)}). Sie folgt dem Standorttyp `
      + `(${pfMax.branch_type} gegen ${pfMin.branch_type}) und der Kundenfrequenz. `
      + 'Filialvergleiche zur Personalbewertung müssen danach normalisiert werden.'],
    impl: null,
  };

  return A;
}

function setzen(el, teile) {
  el.replaceChildren();
  teile.forEach(t => {
    if (typeof t === 'string') el.appendChild(document.createTextNode(t));
    else if (t && t.b) {
      const b = document.createElement('strong');
      b.textContent = t.b;
      el.appendChild(b);
    }
  });
}

export function fuelleAktionen(B, roh) {
  const A = baueAktionen(B, roh);
  let n = 0;
  document.querySelectorAll('[data-akt]').forEach(karte => {
    const e = A[Number(karte.dataset.akt)];
    if (!e) return;
    const t = karte.querySelector('.ms-action-title');
    const tx = karte.querySelector('.ms-action-text');
    const im = karte.querySelector('.ms-action-impl');
    if (t && e.titel) { t.textContent = e.titel; }
    if (tx && e.text) { setzen(tx, e.text); }
    if (im && e.impl) { im.textContent = e.impl; }
    n++;
  });
  return n;
}
