// tabellen.js — die sieben Datentabellen des Dashboards fuellen.
//
// Die Tabellen standen als 265 fest getippte Zellen im HTML. Sie sind der
// unangenehmste Fall von einkodierten Daten: Eine Tabelle sieht aus wie ein
// Auszug aus der Datenbank, auch wenn sie einer ist, den jemand vor zwei
// Jahren abgetippt hat. Beim Abgleich fiel entsprechend auf, dass die Spalte
// "Mietquote" eine Jahresmiete gegen neun Jahre kumulierten Umsatz rechnete
// (2,4 Prozent statt 15,2) — ein Fehler, den man einer Zahl nicht ansieht.
//
// Gefuellt wird ueber die id der Tabelle. Die Kopfzeilen bleiben im HTML; sie
// beschreiben die Spalten und sind keine Daten. Sortier- und Filterfunktionen
// des Dashboards lesen den tbody bei jedem Aufruf neu und funktionieren
// deshalb unveraendert weiter.

const zahl = (v, n = 0) => Number(v).toLocaleString('de-DE',
  { minimumFractionDigits: n, maximumFractionDigits: n }).replace('-', '−');
const euro = (v, n = 2) => '€' + zahl(v, n);
const proz = (v, n = 1) => zahl(v, n) + '%';
const mio  = (v) => '€' + zahl(v / 1e6, 2) + 'M';

// Wachstum gegenueber dem Vorwert, eingefaerbt. Fehlt der Vorwert, steht ein
// Gedankenstrich — nicht "0 %", was eine Messung vortaeuschen wuerde.
function wachstum(jetzt, vorher) {
  if (vorher === undefined || vorher === null || !isFinite(vorher) || vorher === 0) {
    return ['—', 'text-muted'];
  }
  const p = (jetzt / vorher - 1) * 100;
  return [(p >= 0 ? '+' : '') + zahl(p, 1) + '%', p >= 0 ? 'text-pos' : 'text-neg'];
}

const gruen = 'color:var(--green)';
const grau  = 'color:var(--muted)';

// Baut eine Zeile aus Zellbeschreibungen: String, oder [Text, Klasse], oder
// {t, k, s} fuer Text, Klasse und Inline-Stil.
function zeile(zellen) {
  const tr = document.createElement('tr');
  zellen.forEach(z => {
    const td = document.createElement('td');
    if (Array.isArray(z)) { td.textContent = z[0]; if (z[1]) td.className = z[1]; }
    else if (z && typeof z === 'object') {
      td.textContent = z.t;
      if (z.k) td.className = z.k;
      if (z.s) td.setAttribute('style', z.s);
    } else td.textContent = z;
    tr.appendChild(td);
  });
  return tr;
}

function fuellen(id, zeilen) {
  const t = document.getElementById(id);
  if (!t) return 0;
  const tb = t.querySelector('tbody');
  if (!tb) return 0;
  tb.replaceChildren(...zeilen);
  return zeilen.length;
}

export function fuelleTabellen(B, roh) {
  let n = 0;

  // ── Jahresvergleich ──────────────────────────────────────────────────────
  // Nur volle Jahre: Das laufende Jahr in einer Wachstumsspalte zu zeigen,
  // vergliche acht Monate mit zwoelf.
  const jahre = roh.kennzahlenJahr.filter(x => x.jahr <= 2025);
  n += fuellen('tblYears', jahre.map((x, i) => {
    const v = jahre[i - 1];
    return zeile([
      String(x.jahr),
      [euro(x.umsatz, 0), 'mono'],
      wachstum(x.umsatz, v && v.umsatz),
      [zahl(x.bestellungen), 'mono'],
      wachstum(x.bestellungen, v && v.bestellungen),
      [euro(x.aov), 'mono'],
      wachstum(x.aov, v && v.aov),
    ]);
  }));

  // ── Filial-Scorecard ─────────────────────────────────────────────────────
  const aovSchnitt = roh.filialen.reduce((a, x) => a + x.umsatz, 0)
                   / roh.filialen.reduce((a, x) => a + x.bestellungen, 0);
  const monat = (d) => {
    const t = new Date(d);
    return String(t.getMonth() + 1).padStart(2, '0') + '/' + t.getFullYear();
  };
  n += fuellen('tblBranch', roh.filialen.map(f => zeile([
    f.branch_name,
    f.branch_type,
    f.has_drive_through ? { t: '✓ DT', s: gruen + ';font-weight:700' } : { t: '—', s: grau },
    [monat(f.opening_date), 'mono'],
    [euro(f.umsatz, 0), 'mono'],
    [zahl(f.bestellungen), 'mono'],
    [euro(f.aov), 'mono ' + (f.aov >= aovSchnitt ? 'text-pos' : 'text-neg')],
    zahl(f.zufriedenheit, 2) + ' ★',
  ])));

  // ── Produktkombinationen nach Konfidenz ──────────────────────────────────
  const nachKonf = [...roh.warenkorb].sort((a, b) => b.konfidenz_pct - a.konfidenz_pct);
  n += fuellen('tblBasket', nachKonf.slice(0, 10).map(r => zeile([
    `${r.produkt_a} + ${r.produkt_b}`,
    [zahl(r.gemeinsam), 'mono'],
    [proz(r.support_pct), 'mono'],
    [proz(r.konfidenz_pct), 'mono text-pos'],
  ])));

  // ── RFM-Profiling ────────────────────────────────────────────────────────
  // Farbe nach Lage des Segments, nicht nach Groesse: gruen, wo die letzte
  // Bestellung nah liegt, rot, wo sie lange her ist.
  const rfmFarbe = (s) => s.recency_tage <= 30 ? gruen
                        : s.recency_tage >= 180 ? 'color:var(--red)' : '';
  n += fuellen('tblRFM', [...roh.rfm]
    .sort((a, b) => b.umsatz_gesamt - a.umsatz_gesamt)
    .map(s => zeile([
      { t: s.segment, s: rfmFarbe(s) },
      [zahl(s.kunden), 'mono'],
      [proz(s.anteil_pct), 'mono'],
      [zahl(s.recency_tage) + ' Tage',
        'mono ' + (s.recency_tage <= 30 ? 'text-pos' : s.recency_tage >= 180 ? 'text-neg' : '')],
      [zahl(s.frequenz, 1), 'mono'],
      [euro(s.lebenswert, 0), 'mono'],
      [euro(s.umsatz_gesamt, 0), 'mono'],
    ])));

  // ── Assoziationsregeln ───────────────────────────────────────────────────
  // Die Sterne sind eine Lesehilfe fuer den Lift, keine eigene Kennzahl. Die
  // Schwellen stehen hier einmal und werden im Text daneben genannt.
  const STARK = 2, MODERAT = 1.3;
  const sterne = (l) => l > STARK ? { t: '★★★', s: gruen }
                      : l > MODERAT ? { t: '★★', s: 'color:var(--orange)' }
                      : { t: '★', s: grau };
  n += fuellen('tblAssoc', [...roh.warenkorb]
    .sort((a, b) => b.gemeinsam - a.gemeinsam)
    .map(r => zeile([
      `${r.produkt_a} → ${r.produkt_b}`,
      [zahl(r.gemeinsam), 'mono'],
      [proz(r.support_pct), 'mono'],
      [proz(r.konfidenz_pct), 'mono'],
      [zahl(r.lift, 2), 'mono ' + (r.lift > STARK ? 'text-pos' : '')],
      sterne(r.lift),
    ])));

  // ── Szenarien ────────────────────────────────────────────────────────────
  n += fuellen('tblForecast', B.szenarien.map(s => zeile([
    s.name === 'Optimistisch' ? { t: s.name, s: gruen } : s.name,
    ['+' + zahl(s.rate * 100, 0) + '% p.a.', 'mono'],
    [mio(s.jahre[0]), 'mono'],
    [mio(s.jahre[1]), 'mono'],
    [mio(s.jahre[2]), 'mono'],
    [s.investition ? '€' + zahl(s.investition / 1000, 0) + 'k' : '€0', 'mono'],
    s.ruecklauf === null ? ['—', 'mono text-muted']
                         : [zahl(s.ruecklauf, 1) + '×', 'mono text-pos'],
  ])));

  // ── Standortvergleich ────────────────────────────────────────────────────
  n += fuellen('tblGeo', roh.filialen.map(f => zeile([
    f.branch_name,
    f.branch_type,
    [euro(f.umsatz, 0), 'mono'],
    [zahl(f.umsatz_je_qm, 0), 'mono'],
    [proz(f.mietquote_pct), 'mono'],
    [euro(f.aov), 'mono'],
    [zahl(f.zufriedenheit, 2), 'mono'],
    [zahl(f.sitzplaetze), 'mono'],
    f.has_drive_through ? 'Ja' : 'Nein',
  ])));

  n += fuelleKanalProdukte(B);
  return n;
}


// ---------------------------------------------------------------------------
// Spitzenartikel je Kanal. Frueher zwanzig Produktnamen im HTML, deklariert
// als "Musterdaten". Sie waren sogar richtig — falsch war die Ueberschrift
// darueber: Drei der vier Kanaele haben dieselben fuenf Artikel in derselben
// Reihenfolge. Der Rang bekommt hier den Mengenanteil an die Seite, damit
// sichtbar wird, wie klein die Unterschiede sind.
// ---------------------------------------------------------------------------
const RAND = { 'Counter': 'var(--bar)', 'Drive-Through': 'var(--bar-light)',
               'App': 'var(--green)', 'Kiosk': 'var(--orange)' };

function fuelleKanalProdukte(B) {
  const wurzel = document.getElementById('kanalProdukte');
  if (!wurzel || !B.kanalProdukte) return 0;
  wurzel.textContent = '';
  B.kanalProdukte.forEach(k => {
    const sp = document.createElement('div');
    const kopf = document.createElement('div');
    kopf.style.cssText = 'font-size:10px;font-weight:700;color:var(--muted);'
      + 'text-transform:uppercase;letter-spacing:0.5px;margin-bottom:8px;'
      + 'padding-bottom:6px;border-bottom:2px solid ' + (RAND[k.kanal] ?? 'var(--bar)');
    kopf.textContent = k.kanal;
    sp.appendChild(kopf);
    const liste = document.createElement('div');
    liste.style.cssText = 'font-size:11px;line-height:2;color:var(--ink-light)';
    k.artikel.forEach(a => {
      const z = document.createElement('div');
      z.textContent = `${a.rang}. ${a.produkt} · ${proz(a.anteil_pct)}`;
      liste.appendChild(z);
    });
    sp.appendChild(liste);
    wurzel.appendChild(sp);
  });
  return B.kanalProdukte.reduce((s, k) => s + k.artikel.length, 0);
}
