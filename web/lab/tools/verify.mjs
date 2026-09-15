/**
 * BM-Lab · Abnahmelauf
 *
 * Prüft ohne Browser, was sich ohne Browser prüfen lässt:
 *
 *   1. Struktur  - Platzhalter und JSON deckungsgleich, Deutsch-Pflicht (jedes
 *                  Textfeld hat `de`, keines hat `en`), Antwortindizes im Bereich,
 *                  Zuordnungsziele vorhanden; JSON-, Reihenfolge- und Regal-Übungen
 *                  sind mit ihrer hinterlegten Lösung lösbar; Seitenbausteine,
 *                  Verweise, Startseite, Stylesheet und Laufzeit ohne Reste der
 *                  Vorlage; die Saatfolge in bm.js stimmt mit tools/sql.mjs überein.
 *   2. SQL       - jede SQL-Lösung läuft in PGlite gegen die frisch gesäte
 *                  Datenbank (Schemata wawi und burgermetrics wie in assets/bm.js):
 *                  Lösung darf nicht scheitern, liefert Zeilen (oder die Kontrolle
 *                  tut es), und der Starttext löst die Aufgabe nicht schon.
 *   3. Befunde   - je Prüfung eine Zusicherung, die ohne die Prüfung scheitern
 *                  würde (ein en-Feld, ein Syntaxfehler, eine abweichende Saat …).
 *
 * Aufruf:  node tools/verify.mjs          (aus web/lab, Exit 1 bei Fehlern)
 */

import { readFileSync, readdirSync, existsSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'
import { pruefeJson } from '../assets/jsonpruefung.js'
import { abweichungen as regalAbweichungen, ergebnis as regalErgebnis } from '../assets/regal.js'
import { SAAT, neueDatenbank, fuehreAus } from './sql.mjs'

const WURZEL = join(dirname(fileURLToPath(import.meta.url)), '..')
const lies = (p) => readFileSync(join(WURZEL, p), 'utf8')
const liesJson = (p) => JSON.parse(lies(p))

let fehler = 0
let geprueft = 0
const gut = (bedingung, was, zusatz = '') => {
  geprueft++
  if (bedingung) return true
  fehler++
  console.log(`  FEHL  ${was}${zusatz ? '  — ' + zusatz : ''}`)
  return false
}
const abschnitt = (titel) => console.log('\n' + titel + '\n' + '-'.repeat(titel.length))

/* ------------------------------------------------------------- Prüfregeln */

const TYPEN = ['quiz', 'zuordnen', 'checkliste', 'sql', 'json', 'reihenfolge', 'regal']
const VORLAGENRESTE = /PITM-Lab|pitm\.css|pitm\.js|pitm:|winf\.css|winf\.js|winf:|WInf-SP|Velo City/
const ENGLISCH_HTML = /lang="en"|data-lang-btn|\?lang=/
const ALTE_FARBEN = /7A1F2E|E0B44C|A0303F|963041/i
const NEUE_FARBEN = ['C2410C', 'ED7004', '9A3412', 'FDF1E7', '7C2D12']

/** Schlüssel, deren Wert ein Textobjekt { de } sein muss. */
const TEXTFELDER = new Set(['titel', 'aufgabe', 'rueckmeldung', 'hinweis', 'frage', 'erklaerung', 'text', 'bedeutet', 'begruessung'])

/**
 * Deutsch-Pflicht: jedes Textfeld hat ein nicht leeres `de` und kein `en`;
 * ein `en` an beliebiger Stelle ist ein Befund. Liefert Befunde mit Pfad.
 */
function deutschBefunde (wert, pfad = '') {
  const befunde = []
  const pruefeText = (o, p) => {
    if (o == null || typeof o !== 'object' || Array.isArray(o)) { befunde.push(`${p}: kein { de }-Objekt`); return }
    if (typeof o.de !== 'string' || !o.de.trim()) befunde.push(`${p}: de fehlt oder ist leer`)
    if ('en' in o) befunde.push(`${p}: en ist nicht erlaubt`)
  }
  const gehe = (o, p) => {
    if (Array.isArray(o)) { o.forEach((x, i) => gehe(x, `${p}[${i}]`)); return }
    if (o == null || typeof o !== 'object') return
    for (const [k, v] of Object.entries(o)) {
      const q = p ? `${p}.${k}` : k
      if (k === 'erwartet') continue // Vergleichsdokument einer JSON-Übung: Inhalt, kein Text
      if (TEXTFELDER.has(k)) pruefeText(v, q)
      else if (k === 'optionen' && Array.isArray(v)) v.forEach((x, i) => pruefeText(x, `${q}[${i}]`))
      else if (k === 'en') befunde.push(`${q}: en ist nicht erlaubt`)
      else gehe(v, q)
    }
  }
  gehe(wert, pfad)
  return befunde
}

/** Die Saatfolge steht zweimal (Browser: bm.js per fetch, Node: sql.mjs per fs). Abweichungen Eintrag für Eintrag. */
function saatAbweichungen (a, b) {
  const befunde = []
  if (a.length !== b.length) befunde.push(`${a.length} gegen ${b.length} Einträge`)
  for (let i = 0; i < Math.max(a.length, b.length); i++) {
    const x = a[i] || [], y = b[i] || []
    if (x[0] !== y[0]) befunde.push(`Eintrag ${i + 1}: Vorspann „${x[0]}“ gegen „${y[0]}“`)
    if (x[1] !== y[1]) befunde.push(`Eintrag ${i + 1}: Datei ${x[1]} gegen ${y[1]}`)
  }
  return befunde
}

/* ========================================================== 1. Struktur */

abschnitt('1. Struktur')

const HTML_ZU_LAB = {}
for (const f of readdirSync(WURZEL).filter(n => /^lab-\d\d-.*\.html$/.test(n))) {
  HTML_ZU_LAB['lab-' + f.slice(4, 6)] = f
}

const laufzeit = lies('assets/bm.js')
const labBlock = (laufzeit.match(/const LABS = \[[\s\S]*?\n\]/) || [''])[0]
const LABS_LAUFZEIT = [...labBlock.matchAll(/id: '(lab-\d\d)', nr: '(\d\d)', datei: '([^']+)', uebungen: (\d+),[\s\S]*?zeit: \{ de: '(\d+) Minuten' \}/g)]
  .map(m => ({ id: m[1], nr: m[2], datei: m[3], uebungen: Number(m[4]), minuten: Number(m[5]) }))
const erwartet = Object.fromEntries(LABS_LAUFZEIT.map(l => [l.id, l.uebungen]))
gut(LABS_LAUFZEIT.length === 8, `bm.js: LABS nennt acht Labs (gefunden ${LABS_LAUFZEIT.length})`)
gut(LABS_LAUFZEIT.reduce((s, l) => s + l.uebungen, 0) === 41, 'bm.js: LABS zählt 41 Übungen',
  String(LABS_LAUFZEIT.reduce((s, l) => s + l.uebungen, 0)))
for (const [lab, datei] of Object.entries(HTML_ZU_LAB)) {
  gut(LABS_LAUFZEIT.some(l => l.id === lab && l.datei === datei), `${lab}: ${datei} steht so in LABS`)
}

const saatBlock = (laufzeit.match(/const SAAT = \[[\s\S]*?\n\]/) || [''])[0]
const SAAT_LAUFZEIT = [...saatBlock.matchAll(/\['([^']*)', '([^']*)'\]/g)].map(m => [m[1], m[2]])
gut(SAAT_LAUFZEIT.length === 3, `bm.js: SAAT ist lesbar und hat drei Einträge (gefunden ${SAAT_LAUFZEIT.length})`)
gut(saatAbweichungen(SAAT_LAUFZEIT, SAAT).length === 0, 'SAAT in bm.js und tools/sql.mjs stimmen überein',
  saatAbweichungen(SAAT_LAUFZEIT, SAAT).join('; '))
for (const [, datei] of SAAT) gut(existsSync(join(WURZEL, datei)), `Saatdatei ${datei} existiert`)

const LABS = {}
for (const [lab, htmlDatei] of Object.entries(HTML_ZU_LAB).sort()) {
  const html = lies(htmlDatei)
  const jsonDatei = `data/uebungen/${lab}.json`
  if (!gut(existsSync(join(WURZEL, jsonDatei)), `${lab}: ${jsonDatei} existiert`)) continue
  let d
  try { d = liesJson(jsonDatei) } catch (e) { gut(false, `${lab}: ${jsonDatei} ist gültiges JSON`, e.message); continue }
  LABS[lab] = d
  const phU = new Set([...html.matchAll(/data-uebung="([^"]+)"/g)].map(m => m[1]))
  const phB = new Set([...html.matchAll(/data-befehl="([^"]+)"/g)].map(m => m[1]))
  const jsU = new Set((d.uebungen || []).map(u => u.id))
  const jsB = new Set(Object.keys(d.befehle || {}))
  const gleichMenge = (a, b) => a.size === b.size && [...a].every(x => b.has(x))

  gut(gleichMenge(phU, jsU), `${lab}: Übungsplatzhalter und JSON deckungsgleich`,
    `nur im HTML ${[...phU].filter(x => !jsU.has(x))}, nur im JSON ${[...jsU].filter(x => !phU.has(x))}`)
  gut(gleichMenge(phB, jsB), `${lab}: Befehlskarten deckungsgleich`,
    `nur im HTML ${[...phB].filter(x => !jsB.has(x))}, nur im JSON ${[...jsB].filter(x => !phB.has(x))}`)
  gut(erwartet[lab] === jsU.size, `${lab}: LABS nennt ${erwartet[lab]}, JSON hat ${jsU.size} Übungen`)
  gut(jsU.size === (d.uebungen || []).length, `${lab}: Übungskennungen sind eindeutig`)
  gut([...jsU].every(id => new RegExp(`^W${lab.slice(4)}-\\d\\d$`).test(id)), `${lab}: Übungskennungen heißen W${lab.slice(4)}-NN`)

  const befundeDe = deutschBefunde(d)
  gut(befundeDe.length === 0, `${lab}: nur Deutsch (jedes Textfeld hat de, keines hat en)`, befundeDe.slice(0, 6).join('; '))

  for (const u of d.uebungen || []) {
    gut(TYPEN.includes(u.typ), `${u.id}: Typ ${u.typ} ist bekannt`)
    gut(!!u.titel && !!u.aufgabe, `${u.id}: hat titel und aufgabe`)
    if (u.typ === 'quiz') {
      gut((u.fragen || []).length > 0, `${u.id}: Quiz hat Fragen`)
      for (const [i, f] of (u.fragen || []).entries()) {
        gut((f.optionen || []).length >= 2, `${u.id} Frage ${i + 1}: mindestens zwei Optionen`)
        gut(Array.isArray(f.richtig) && f.richtig.length > 0 && Math.max(...f.richtig) < (f.optionen || []).length,
          `${u.id} Frage ${i + 1}: Antwortindex im Bereich`)
        gut((f.richtig || []).length === 1 || f.mehrfach === true,
          `${u.id} Frage ${i + 1}: Mehrfachauswahl ist als solche gekennzeichnet`)
      }
    }
    if (u.typ === 'zuordnen') {
      const ziele = new Set((u.ziele || []).map(z => z.id))
      gut(ziele.size >= 2 && (u.paare || []).length >= 2, `${u.id}: Zuordnung hat Ziele und Paare`)
      for (const p of u.paare || []) gut(ziele.has(p.ziel), `${u.id}: Zuordnungsziel ${p.ziel} existiert`)
    }
    if (u.typ === 'checkliste') {
      gut((u.schritte || []).length >= 2, `${u.id}: Checkliste hat Schritte`)
    }
    if (u.typ === 'sql') {
      gut(!!u.loesung, `${u.id}: SQL-Übung hat eine Musterlösung`)
      gut(!!u.hinweis, `${u.id}: SQL-Übung hat einen Hinweis`)
      gut(!u.engine, `${u.id}: kein engine-Feld (es gibt nur PostgreSQL)`)
    }
    if (u.typ === 'json') {
      gut(!!u.loesung, `${u.id}: JSON-Übung hat eine Musterlösung`)
      gut(!!u.hinweis, `${u.id}: JSON-Übung hat einen Hinweis`)
      const r = u.loesung ? pruefeJson(u.loesung, u) : { ok: false, meldung: 'keine Lösung' }
      gut(r.ok, `${u.id}: Musterlösung besteht die eigene Prüfung`, r.meldung || (r.befunde || []).map(b => b.pfad + ': ' + b.text.de).join('; '))
      if (u.start) {
        const s = pruefeJson(u.start, u)
        gut(!s.ok, `${u.id}: der Starttext ist noch nicht die Lösung`)
      }
      gut(u.erwartet !== undefined || (u.regeln || []).length > 0, `${u.id}: hat erwartet oder regeln`)
    }
    if (u.typ === 'reihenfolge') {
      const ids = new Set((u.eintraege || []).map(e => e.id))
      gut(ids.size === (u.eintraege || []).length && ids.size >= 3, `${u.id}: Einträge mit eindeutigen Kennungen`)
      gut((u.richtig || []).length === ids.size && (u.richtig || []).every(x => ids.has(x)), `${u.id}: richtig nennt jede Kennung genau einmal`)
      const start = u.start || [...(u.eintraege || [])].map(e => e.id).reverse()
      gut(start.length === ids.size && start.every(x => ids.has(x)), `${u.id}: Startreihenfolge ist vollständig`)
      gut(JSON.stringify(start) !== JSON.stringify(u.richtig), `${u.id}: Startreihenfolge ist nicht schon die Lösung`)
    }
    if (u.typ === 'regal') {
      const felder = u.felder || d.regal?.felder || []
      gut(felder.length > 0, `${u.id}: Felder vorhanden`)
      gut(felder.every(f => f.id && f.titel?.de && ['dimension', 'kennzahl'].includes(f.typ)), `${u.id}: Felder vollständig (id, titel.de, typ)`)
      const ids = new Set(felder.map(f => f.id))
      const genannt = [...(u.ziel?.spalten || []), ...(u.ziel?.zeilen || [])].map(s => s.includes(':') ? s.split(':')[1] : s)
      if (u.ziel?.farbe) genannt.push(u.ziel.farbe)
      for (const f of Object.keys(u.ziel?.filter || {})) genannt.push(f)
      gut(genannt.length > 0, `${u.id}: Ziel nennt mindestens ein Feld`)
      gut(genannt.every(f => ids.has(f)), `${u.id}: Ziel nennt nur bekannte Felder`, genannt.filter(f => !ids.has(f)).join(', '))
      gut(!!u.loesungBelegung, `${u.id}: Regal-Übung hat eine loesungBelegung`)
      const datenDatei = u.daten || d.regal?.daten || 'data/regal-bestellungen.json'
      if (gut(existsSync(join(WURZEL, datenDatei)), `${u.id}: Regal-Daten ${datenDatei} existieren`) && u.loesungBelegung) {
        const abw = regalAbweichungen(u.loesungBelegung, u.ziel || {})
        gut(abw.length === 0, `${u.id}: loesungBelegung erfüllt das Ziel`, abw.map(a => a.text.de).join('; '))
        const leer = regalAbweichungen({ spalten: [], zeilen: [], farbe: null, filter: {} }, u.ziel || {})
        gut(leer.length > 0, `${u.id}: die leere Belegung erfüllt das Ziel nicht`)
        if (u.startBelegung) {
          const st = regalAbweichungen(u.startBelegung, u.ziel || {})
          gut(st.length > 0, `${u.id}: die Startbelegung erfüllt das Ziel nicht`)
        }
        const daten = liesJson(datenDatei)
        const erg = regalErgebnis(daten, felder, u.loesungBelegung)
        gut(erg.zeilen.length > 0, `${u.id}: die Lösung liefert Zeilen auf den Daten`)
      }
    }
  }
  for (const [id, b] of Object.entries(d.befehle || {})) {
    gut(!!b.titel?.de, `${lab}/${id}: Titel vorhanden`)
    gut(!!(b.befehl || b.varianten), `${lab}/${id}: hat einen Befehl`)
    const teile = b.teile || Object.values(b.varianten || {}).flatMap(v => v.teile || [])
    gut(teile.every(t => t.was && t.bedeutet?.de), `${lab}/${id}: Erläuterungen vollständig (was, bedeutet.de)`)
  }
}

// Jede Seite: Kopf und Bausteine, verlinkte Dateien, Datenbankband, keine Reste der Vorlage.
for (const [lab, htmlDatei] of Object.entries(HTML_ZU_LAB).sort()) {
  const html = lies(htmlDatei)
  const nr = lab.slice(4)
  const d = LABS[lab] || { uebungen: [] }
  for (const m of html.matchAll(/href="((?:vorlagen|data)\/[^"#?]+)"/g)) {
    gut(existsSync(join(WURZEL, m[1])), `${lab}: verlinkte Datei ${m[1]} existiert`)
  }
  gut(!VORLAGENRESTE.test(html), `${lab}: keine Reste der Vorlage (PITM, winf, WInf-SP, Velo City)`)
  gut(!ENGLISCH_HTML.test(html), `${lab}: nur Deutsch (kein lang="en", kein data-lang-btn, kein ?lang=)`)
  gut(/assets\/bm\.css/.test(html) && /<script type="module" src="assets\/bm\.js"><\/script>/.test(html), `${lab}: bindet bm.css und bm.js ein`)
  gut(new RegExp(`<body class="lab-page" data-lab="${lab}"`).test(html), `${lab}: body trägt lab-page und data-lab`)
  gut(new RegExp(`<title>Lab ${nr} · `).test(html), `${lab}: Seitentitel beginnt mit „Lab ${nr} ·“`)
  gut(new RegExp(`lab-num-big">${nr}<`).test(html), `${lab}: die große Lab-Nummer im Kopf stimmt`)
  gut(/<div data-einordnung><\/div>/.test(html) && /data-lab-nav/.test(html) && /data-fortschritt/.test(html),
    `${lab}: Einordnung, Fortschritt und Navigation vorhanden`)
  gut(/id="uebungen"/.test(html) && /id="zusammenfassung"/.test(html), `${lab}: Abschnitte uebungen und zusammenfassung vorhanden`)
  const sidebarLinks = [...html.matchAll(/class="sidebar-link" href="#([^"]+)"/g)].map(m => m[1])
  const abschnitte = [...html.matchAll(/<section class="section-block" id="([^"]+)"/g)].map(m => m[1])
  for (const ziel of sidebarLinks) gut(abschnitte.includes(ziel), `${lab}: Seitennavigation zeigt auf Abschnitt #${ziel}`)
  for (const id of abschnitte) gut(sidebarLinks.includes(id), `${lab}: Abschnitt #${id} steht in der Seitennavigation`)
  gut(!/data-terminal|data-deploy|data-datenbank="sqlite"|data-engine/.test(html), `${lab}: kein Terminal, kein Deploy, kein SQLite`)
  const baender = (html.match(/data-datenbank="postgres"/g) || []).length
  const sqlUebungen = (d.uebungen || []).filter(u => u.typ === 'sql')
  if (sqlUebungen.length) {
    gut(baender === 1, `${lab}: genau ein data-datenbank="postgres" (gefunden ${baender})`)
    const bandPos = html.indexOf('data-datenbank="postgres"')
    const positionen = sqlUebungen.map(u => html.indexOf(`data-uebung="${u.id}"`)).filter(i => i >= 0)
    gut(bandPos >= 0 && positionen.length > 0 && bandPos < Math.min(...positionen), `${lab}: das Datenbankband steht oberhalb der ersten SQL-Übung`)
  } else {
    gut(baender <= 1, `${lab}: höchstens ein Datenbankband (gefunden ${baender})`)
  }
}

// Startseite: nur Deutsch, ohne Reste, acht Karten aus LABS mit passenden Angaben.
{
  const html = lies('index.html')
  gut(!ENGLISCH_HTML.test(html), 'index.html: nur Deutsch (kein lang="en", kein data-lang-btn, kein ?lang=)')
  gut(!VORLAGENRESTE.test(html), 'index.html: keine Reste der Vorlage')
  gut(/assets\/bm\.css/.test(html) && /src="assets\/bm\.js"/.test(html), 'index.html: bindet bm.css und bm.js ein')
  gut(/<div data-fortschritt><\/div>/.test(html), 'index.html: Fortschrittskarte vorhanden')
  const karten = (html.match(/class="lab-card"/g) || []).length
  gut(karten === LABS_LAUFZEIT.length, `index.html: ${LABS_LAUFZEIT.length} Lab-Karten (gefunden ${karten})`)
  for (const l of LABS_LAUFZEIT) {
    const m = html.match(new RegExp(`<a class="lab-card" href="${l.datei}">[\\s\\S]*?<div class="lab-num">(\\d\\d)</div>[\\s\\S]*?<div class="meta">(\\d+) Übungen · (\\d+) Min</div>`))
    gut(!!m, `index.html: Karte für ${l.id} (${l.datei}) mit Nummer und Angaben`)
    if (m) {
      gut(m[1] === l.nr, `index.html: Kartennummer ${m[1]} von ${l.id} stimmt mit LABS überein`)
      gut(Number(m[2]) === l.uebungen && Number(m[3]) === l.minuten,
        `index.html: ${l.id} nennt ${m[2]} Übungen · ${m[3]} Min, LABS ${l.uebungen} Übungen · ${l.minuten} Minuten`)
    }
  }
}

// Stylesheet: hidden-Regel, Palette der Spec (§2.3), keine Farben der Vorlage.
{
  const css = lies('assets/bm.css')
  gut(/\[hidden\]\s*\{[^}]*display:\s*none\s*!important/.test(css), 'bm.css: [hidden] überstimmt eigene display-Regeln')
  gut(css.indexOf('[hidden]') < css.indexOf('.badge {'), 'bm.css: die hidden-Regel steht vor den Komponenten')
  for (const farbe of NEUE_FARBEN) gut(new RegExp(farbe, 'i').test(css), `bm.css: Farbe #${farbe} der Spec kommt vor`)
  gut(!ALTE_FARBEN.test(css), 'bm.css: keine Farben der Vorlage (Bordeaux, Gold, Weinrot)')
}

// Laufzeit: keine entfernten Pfade, keine Sprachreste, die Ereignisse und Schlüssel heißen bm:*.
gut(!/terminal\.js|deploy\.js|sqljs|data-terminal|data-deploy|sqlite/i.test(laufzeit), 'bm.js: kein Terminal, kein Deploy, kein SQLite')
gut(!/winf:|lang=en|\ben:/.test(laufzeit), 'bm.js: keine winf:-Schlüssel, keine ?lang=en-Verweise, keine en-Texte')
gut(/bm:fortschritt/.test(laufzeit) && /bm:sprache/.test(laufzeit) && /bm:os/.test(laufzeit), 'bm.js: Schlüssel und Ereignisse heißen bm:*')
gut(/setzeSprache\('de'\)/.test(laufzeit), 'bm.js: die Sprache ist fest Deutsch')
gut(existsSync(join(WURZEL, 'README.md')), 'README.md vorhanden')

/* ======================================================= 2. SQL-Lösungen */

abschnitt('2. SQL-Lösungen in PGlite')

const saatTexte = {}
const saatText = (datei) => (saatTexte[datei] ??= lies(datei))
const saatVollstaendig = SAAT.every(([, datei]) => existsSync(join(WURZEL, datei)))

/** Neu säen wie saeen() in bm.js: alle eigenen Schemata fallen, dann die Saatfolge. */
async function neuSaeen (db) {
  const schemata = await db.query(
    "SELECT nspname FROM pg_namespace WHERE nspname NOT LIKE 'pg\\_%' AND nspname <> 'information_schema'")
  for (const z of schemata.rows) await db.exec(`DROP SCHEMA IF EXISTS "${z.nspname}" CASCADE`)
  await db.exec('CREATE SCHEMA public;')
  for (const [vorspann, datei] of SAAT) {
    await db.exec(vorspann)
    await db.exec(saatText(datei))
  }
  await db.exec('SET search_path TO wawi, burgermetrics')
}

/** Ergebnisse vergleichen wie gleich() der Laufzeit: Werte normiert; die Zeilenreihenfolge zählt nur bei `sortiert`. */
const normiert = (r, sortiert) => {
  const zeilen = r.zeilen.map(z => z.map(v =>
    v == null ? '\u2400'
      : v instanceof Date ? v.toISOString().slice(0, 10)
        : /^-?\d+(\.\d+)?$/.test(String(v)) ? Number(v).toFixed(4)
          : String(v).trim()).join(''))
  return sortiert ? zeilen : zeilen.sort()
}
const gleichesErgebnis = (a, b, sortiert = false) =>
  a.spalten.length === b.spalten.length && JSON.stringify(normiert(a, sortiert)) === JSON.stringify(normiert(b, sortiert))

/** Prüft eine SQL-Übung auf der frisch gesäten Datenbank. Liefert Befunde (leer = in Ordnung). */
async function pruefeSqlUebung (db, u) {
  const befunde = []
  const lauf = async (sql) => {
    try { return { erg: await fuehreAus(db, sql) } } catch (e) { return { fehler: e.message } }
  }
  const vorbereiten = async () => {
    await neuSaeen(db)
    if (u.vorher) { const v = await lauf(u.vorher); if (v.fehler) befunde.push(`vorher scheitert: ${v.fehler}`) }
  }
  await vorbereiten()
  const l = await lauf(u.loesung || '')
  if (l.fehler) { befunde.push(`loesung scheitert: ${l.fehler}`); return befunde }
  let soll = l.erg
  if (u.kontrolle) {
    const k = await lauf(u.kontrolle)
    if (k.fehler) { befunde.push(`kontrolle scheitert: ${k.fehler}`); return befunde }
    if (!k.erg.zeilen.length) befunde.push('kontrolle liefert nach der Lösung keine Zeile')
    soll = k.erg
  } else if (!l.erg.zeilen.length) {
    befunde.push('loesung liefert keine Zeile (Kontrollabfrage nötig?)')
  }
  // Der Starttext darf die Aufgabe nicht schon lösen.
  if (u.start && u.start.trim()) {
    await vorbereiten()
    const s = await lauf(u.start)
    if (!s.fehler) {
      const ist = u.kontrolle ? await lauf(u.kontrolle) : s
      if (!ist.fehler && gleichesErgebnis(ist.erg, soll, !!u.sortiert)) befunde.push('start liefert schon das Ergebnis der Lösung')
    }
  }
  return befunde
}

/** Startet PGlite mit der Saat; scheitert das, ist es ein Befund und kein Absturz. */
async function datenbankOder (was) {
  try { return await neueDatenbank() } catch (e) { gut(false, `${was}: PGlite startet mit der Saat`, e.message); return null }
}

if (!saatVollstaendig) console.log('  übersprungen: Saatdateien fehlen (Befund in Abschnitt 1)')
for (const [lab, d] of Object.entries(LABS).sort()) {
  const sqlUebungen = (d.uebungen || []).filter(u => u.typ === 'sql')
  if (!sqlUebungen.length || !saatVollstaendig) continue
  const db = await datenbankOder(lab)
  if (!db) continue
  try {
    for (const u of sqlUebungen) {
      const befunde = await pruefeSqlUebung(db, u)
      gut(befunde.length === 0, `${u.id}: Lösung läuft in PGlite und die Aufgabe ist nicht schon gelöst`, befunde.join('; '))
    }
  } finally { await db.close() }
  console.log(`  ${lab}: ${sqlUebungen.length} SQL-Übungen geprüft`)
}

/* =========================================================== 3. Befunde */

abschnitt('3. Zusicherungen der Prüfungen')

// Deutsch-Pflicht: en wird gemeldet, leeres de wird gemeldet, ein sauberes Objekt nicht.
gut(deutschBefunde({ titel: { de: 'Zugang', en: 'Access' } }).length === 1, 'Deutsch-Pflicht: ein en-Feld in einem Textfeld wird gemeldet')
gut(deutschBefunde({ uebungen: [{ hinweis: { de: '' } }] }).length === 1, 'Deutsch-Pflicht: ein leeres de wird gemeldet')
gut(deutschBefunde({ uebungen: [{ titel: 'nur Text' }] }).length === 1, 'Deutsch-Pflicht: eine nackte Zeichenkette statt { de } wird gemeldet')
gut(deutschBefunde({ regal: { felder: [{ id: 'x', titel: { de: 'X' }, erklaerung: { de: 'E', en: 'E' } }] } }).length === 1, 'Deutsch-Pflicht: en tief in regal.felder wird gemeldet')
gut(deutschBefunde({ befehle: { B01: { teile: [{ was: '-p', bedeutet: { en: 'port' } }] } } }).length === 2, 'Deutsch-Pflicht: bedeutet ohne de und mit en ergibt zwei Befunde')
gut(deutschBefunde({ irgendwo: { en: 'tief' } }).length === 1, 'Deutsch-Pflicht: en an beliebiger Stelle wird gemeldet')
gut(deutschBefunde({ uebungen: [{ id: 'W01-01', typ: 'quiz', titel: { de: 'T' }, aufgabe: { de: '<p>A</p>' },
  fragen: [{ frage: { de: 'F' }, optionen: [{ de: 'a' }, { de: 'b' }], richtig: [0], erklaerung: { de: 'E' } }] }] }).length === 0,
'Deutsch-Pflicht: ein sauberes Quiz ist ohne Befund')
gut(deutschBefunde({ uebungen: [{ typ: 'json', titel: { de: 'T' }, erwartet: { titel: 'Rohwert', en: 'Inhalt', text: 'kein Textfeld' } }] }).length === 0,
  'Deutsch-Pflicht: das Vergleichsdokument erwartet einer JSON-Übung wird nicht als Text geprüft')

// Saatfolge: eine veränderte Kopie wird gemeldet, die eigene Kopie nicht.
{
  const kopie = SAAT.map(e => [...e])
  gut(saatAbweichungen(kopie, SAAT).length === 0, 'Saat: die unveränderte Kopie ist ohne Befund')
  kopie[1][1] = 'data/burgermetrics_mini_alt.sql'
  gut(saatAbweichungen(kopie, SAAT).length === 1, 'Saat: eine geänderte Datei wird gemeldet')
  kopie[1][1] = SAAT[1][1]; kopie[2][0] = 'SET search_path TO public;'
  gut(saatAbweichungen(kopie, SAAT).length === 1, 'Saat: ein geänderter Vorspann wird gemeldet')
  gut(saatAbweichungen(SAAT.slice(0, 2), SAAT).length >= 1, 'Saat: ein fehlender Eintrag wird gemeldet')
}

// Regex-Regeln der Seitenprüfung.
gut(ENGLISCH_HTML.test('<span lang="en">x</span>') && ENGLISCH_HTML.test('href="lab-01.html?lang=en"') && !ENGLISCH_HTML.test('<html lang="de" data-lang="de">'),
  'Seiten: lang="en" und ?lang= werden erkannt, lang="de" nicht')
gut(VORLAGENRESTE.test('<link rel="stylesheet" href="assets/winf.css">') && VORLAGENRESTE.test('Velo City') && !VORLAGENRESTE.test('BurgerMetrics'),
  'Seiten: Reste der Vorlage werden erkannt')

// SQL-Prüfung auf einer eigenen Datenbank.
const dbProbe = saatVollstaendig ? await datenbankOder('Zusicherungen') : null
if (!saatVollstaendig) console.log('  übersprungen: Saatdateien fehlen (Befund in Abschnitt 1)')
if (dbProbe) {
  const db = dbProbe
  try {
    const zaehle = async (sql) => Number((await fuehreAus(db, sql)).zeilen[0][0])
    gut(await zaehle('SELECT count(*) FROM fact_orders') === 19 && await zaehle('SELECT count(*) FROM fact_order_items') === 55 &&
        await zaehle('SELECT count(*) FROM fact_reviews') === 12 && await zaehle('SELECT count(*) FROM wawi.rezension') === 12,
    'Saat: 19 Bestellungen, 55 Positionen, 12 Rezensionen in beiden Schemata')
    gut((await fuehreAus(db, 'SELECT round(sum(net_total), 2) FROM fact_orders')).zeilen[0][0] === '200.85', 'Saat: Umsatz 200,85 €')
    gut((await fuehreAus(db, "SELECT nspname FROM pg_namespace WHERE nspname IN ('wawi','burgermetrics') ORDER BY 1")).zeilen.length === 2, 'Saat: beide Schemata vorhanden')
    gut((await fuehreAus(db, 'SHOW search_path')).zeilen[0][0] === 'wawi, burgermetrics', 'Saat: Suchpfad wawi, burgermetrics')

    let b = await pruefeSqlUebung(db, { id: 'T', typ: 'sql', start: 'SELECT 1', loesung: 'SELEKT 1' })
    gut(b.length === 1 && /loesung scheitert/.test(b[0]), 'SQL: eine Lösung mit Syntaxfehler wird gemeldet', b.join('; '))
    b = await pruefeSqlUebung(db, { id: 'T', typ: 'sql', start: 'SELECT count(*) AS n FROM fact_orders', loesung: 'SELECT count(*) AS n FROM fact_orders' })
    gut(b.length === 1 && /start liefert schon/.test(b[0]), 'SQL: ein Starttext, der die Aufgabe schon löst, wird gemeldet', b.join('; '))
    b = await pruefeSqlUebung(db, { id: 'T', typ: 'sql', start: '', loesung: 'SELECT * FROM fact_orders WHERE 1 = 0' })
    gut(b.length === 1 && /keine Zeile/.test(b[0]), 'SQL: eine Lösung ohne Zeilen wird gemeldet', b.join('; '))
    b = await pruefeSqlUebung(db, { id: 'T', typ: 'sql', start: '', loesung: 'CREATE TABLE t AS SELECT 1 AS x', kontrolle: 'SELECT * FROM t WHERE 1 = 0' })
    gut(b.length === 1 && /kontrolle liefert/.test(b[0]), 'SQL: eine Kontrolle ohne Zeilen wird gemeldet', b.join('; '))
    b = await pruefeSqlUebung(db, { id: 'T', typ: 'sql', start: 'SELECT 1', loesung: 'SELECT count(*) AS n FROM fact_orders' })
    gut(b.length === 0, 'SQL: eine saubere Abfrageübung ist ohne Befund', b.join('; '))
    b = await pruefeSqlUebung(db, { id: 'T', typ: 'sql', start: '', loesung: 'CREATE TABLE t AS SELECT order_id FROM fact_orders', kontrolle: 'SELECT count(*) FROM t' })
    gut(b.length === 0, 'SQL: eine saubere CREATE-TABLE-Übung mit Kontrolle ist ohne Befund', b.join('; '))
    b = await pruefeSqlUebung(db, { id: 'T', typ: 'sql', vorher: 'CREATE TABLE t (x int)', start: 'SELECT * FROM t', loesung: 'INSERT INTO t VALUES (1)', kontrolle: 'SELECT * FROM t' })
    gut(b.length === 0, 'SQL: vorher läuft vor Lösung und Start', b.join('; '))
    b = await pruefeSqlUebung(db, { id: 'T', typ: 'sql', start: 'SELECT product_name FROM dim_product', loesung: 'SELECT product_name FROM dim_product ORDER BY product_name DESC' })
    gut(b.length === 1 && /start liefert schon/.test(b[0]), 'SQL: ohne sortiert spielt die Zeilenreihenfolge beim Vergleich keine Rolle', b.join('; '))
    b = await pruefeSqlUebung(db, { id: 'T', typ: 'sql', sortiert: true, start: 'SELECT product_name FROM dim_product ORDER BY product_name', loesung: 'SELECT product_name FROM dim_product ORDER BY product_name DESC' })
    gut(b.length === 0, 'SQL: mit sortiert gilt ein Start, der sich nur in der Reihenfolge unterscheidet, als ungelöst', b.join('; '))
    b = await pruefeSqlUebung(db, { id: 'T', typ: 'sql', sortiert: true, start: 'SELECT product_name FROM dim_product ORDER BY product_name DESC', loesung: 'SELECT product_name FROM dim_product ORDER BY product_name DESC' })
    gut(b.length === 1 && /start liefert schon/.test(b[0]), 'SQL: mit sortiert wird ein Start in derselben Reihenfolge gemeldet', b.join('; '))
    gut((await fuehreAus(db, "SELECT to_regclass('t')")).zeilen[0][0] === null, 'SQL: das Neusäen räumt selbst angelegte Tabellen weg')
    gut(await zaehle('SELECT count(*) FROM fact_orders') === 19, 'SQL: nach dem Neusäen steht der Bestand wieder')
  } finally { await db.close() }
}

/* ================================================================ Ende */

console.log('\n' + '='.repeat(60))
console.log(`${geprueft} Zusicherungen, ${fehler} Fehler.`)
process.exit(fehler ? 1 : 0)
