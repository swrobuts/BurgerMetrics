/**
 * BM-Lab · Laufzeit der Lernumgebung
 *
 * Abgeleitet von der WInf-SP-Laufzeit (winf.js): nur Deutsch, eine
 * Datenbankmaschine (PGlite mit zwei Schemata), ohne Terminal- und
 * Deploy-Simulator. Zuständig für:
 *   - Betriebssystemwahl mac/win/cmd (merkt sich die Wahl, gilt seitenweit)
 *   - Befehlskarten mit Kopierknopf und Erklärung der Bestandteile
 *   - eine echte Datenbank im Browser: PostgreSQL (PGlite) mit den Schemata
 *     wawi und burgermetrics des Miniaturbestands der Fallstudie BurgerMetrics
 *   - Übungsboxen aus data/uebungen/<lab>.json in sieben Bauformen:
 *     quiz, zuordnen, checkliste, sql, json, reihenfolge, regal
 *   - Regal-Simulator (Power BI / Tableau)
 *   - Fortschrittsanzeige je Lab
 *
 * Ohne Framework, ohne Build-Schritt, ohne fremde Server: Die Seite lässt
 * sich unverändert auf GitHub Pages legen.
 */

import { pruefeJson } from './jsonpruefung.js'
import { AGGREGATE, ergebnis as regalErgebnis, darstellung as regalDarstellung, abweichungen as regalAbweichungen } from './regal.js'

/* ------------------------------------------------------------------ Sprache */

/**
 * Das BM-Lab ist einsprachig. Die Sprache bleibt als Attribut und Ereignis
 * erhalten, damit die aus WInf-SP übernommenen Bausteine (txt, zwei) unverändert
 * arbeiten; gesetzt wird immer Deutsch.
 */
const SPRACHSCHLUESSEL = 'bm:sprache'
const OSSCHLUESSEL = 'bm:os'

export function aktuelleSprache () {
  return document.documentElement.getAttribute('data-lang') === 'en' ? 'en' : 'de'
}

function setzeSprache (lang) {
  document.documentElement.setAttribute('data-lang', lang)
  document.documentElement.setAttribute('lang', lang)
  try { localStorage.setItem(SPRACHSCHLUESSEL, lang) } catch { /* Privater Modus */ }
  document.dispatchEvent(new CustomEvent('bm:sprache', { detail: { lang } }))
}

function initSprache () {
  setzeSprache('de')
}

/* -------------------------------------------------------- Betriebssystem */

/**
 * Die Wahl gilt für die ganze Umgebung: Wer sich einmal als Windows-Nutzerin
 * zu erkennen gibt, soll nicht auf jeder Seite erneut umschalten. Beim ersten
 * Besuch rät die Umgebung anhand der Plattform - falsch geraten ist harmlos,
 * der Schalter steht sichtbar über jeder Befehlskarte.
 */
function geratenesOs () {
  const p = (navigator.userAgentData?.platform || navigator.platform || '').toLowerCase()
  if (p.includes('win')) return 'win'
  return 'mac'
}

export function aktuellesOs () {
  return document.documentElement.getAttribute('data-os') || 'mac'
}

function setzeOs (os) {
  document.documentElement.setAttribute('data-os', os)
  try { localStorage.setItem(OSSCHLUESSEL, os) } catch { /* egal */ }
  document.querySelectorAll('[data-os-btn]').forEach(b => {
    const an = b.dataset.osBtn === os
    b.classList.toggle('active', an)
    b.setAttribute('aria-pressed', String(an))
  })
  document.dispatchEvent(new CustomEvent('bm:os', { detail: { os } }))
}

function initOs () {
  let gespeichert = null
  try { gespeichert = localStorage.getItem(OSSCHLUESSEL) } catch { /* egal */ }
  setzeOs(['mac', 'win', 'cmd'].includes(gespeichert) ? gespeichert : geratenesOs())
}

/* ------------------------------------------------------------------ Texte */

const txt = (o) => (o == null ? '' : (typeof o === 'string' ? o : (o[aktuelleSprache()] ?? o.de ?? '')))
const menge = (n, formen) => `${n} ${txt(formen)[n === 1 ? 0 : 1]}`

const M = {
  uebung:  { de: ['Übung', 'Übungen'] },
  zeile:   { de: ['Zeile', 'Zeilen'] }
}

const T = {
  pruefen:      { de: 'Prüfen' },
  ausfuehren:   { de: 'Ausführen' },
  loesung:      { de: 'Musterlösung anzeigen' },
  hinweis:      { de: 'Hinweis' },
  leeren:       { de: 'Eingabe leeren' },
  kopieren:     { de: 'Kopieren' },
  kopiert:      { de: 'kopiert' },
  kopiertNein:  { de: 'Kopieren nicht möglich – bitte von Hand markieren.' },
  uebernehmen:  { de: 'In den Editor übernehmen' },
  richtig:      { de: 'Richtig.' },
  nochNicht:    { de: 'Noch nicht.' },
  ok:           { de: 'Erledigt' },
  fragenOffen:  { de: 'Bitte beantworten Sie alle Fragen.' },
  alleZuordnen: { de: 'Bitte ordnen Sie jeden Eintrag zu.' },
  waehlen:      { de: 'bitte wählen …' },
  leer:         { de: 'Das Feld ist leer.' },
  ergebnis:     { de: 'Ergebnis' },
  ausgefuehrt:  { de: 'Ausgeführt. Diese Anweisung liefert keine Tabelle zurück.' },
  fehlerSql:    { de: 'PostgreSQL meldet einen Fehler' },
  dbLaden:      { de: 'PostgreSQL wird gestartet, der Miniaturbestand von BurgerMetrics wird geladen …' },
  abfrageLaeuft:{ de: 'Die Abfrage läuft …' },
  dbBereit:     { de: 'PostgreSQL im Browser (PGlite) · Schemata wawi und burgermetrics · 19 Bestellungen, 12 Rezensionen' },
  dbFehler:     { de: 'Die Datenbank konnte nicht gestartet werden.' },
  dbZuruck:     { de: 'Datenbank zurücksetzen' },
  angezeigt:    { de: 'angezeigt' },
  spaltenFalsch:{ de: 'Die Spalten stimmen nicht mit der Aufgabe überein.' },
  zeilenFalsch: { de: 'Die Zeilen stimmen nicht mit der Aufgabe überein.' },
  stand:        { de: 'Ihr Stand' },
  loeschen:     { de: 'Fortschritt zurücksetzen' },
  loeschenFrage:{ de: 'Den vermerkten Lernfortschritt aller Labs löschen?' },
  geloescht:    { de: 'Der Lernfortschritt ist gelöscht.' },
  allesGeloest: { de: 'Alle Übungen gelöst.' },
  voraussetzung:{ de: 'Voraussetzung' },
  umfang:       { de: 'Umfang' },
  zeitrahmen:   { de: 'Zeitrahmen' },
  ziel:         { de: 'Kompetenzziel' },
  keine:        { de: 'keine' },
  formatieren:  { de: 'Formatieren' },
  jsonUngueltig:{ de: 'Kein gültiges JSON' },
  jsonGueltig:  { de: 'Gültiges JSON – aber noch nicht das verlangte.' },
  jsonOk:       { de: 'Gültiges JSON.' },
  jsonFormatiert:{ de: 'Formatiert.' },
  hoch:         { de: 'nach oben' },
  runter:       { de: 'nach unten' },
  reihenfolgeFalsch: { de: 'Ab Position {n} stimmt die Reihenfolge nicht.' },
  feldHinzu:    { de: 'Feld hinzufügen …' },
  entfernen:    { de: 'entfernen' },
  filterWerte:  { de: 'Werte' },
  keineDaten:   { de: 'Legen Sie ein Feld auf ein Regal.' },
  typ: {
    quiz:        { de: 'Verständnis' },
    zuordnen:    { de: 'Zuordnen' },
    checkliste:  { de: 'Inbetriebnahme' },
    sql:         { de: 'SQL schreiben' },
    json:        { de: 'JSON schreiben' },
    reihenfolge: { de: 'In Reihenfolge bringen' },
    regal:       { de: 'Am Regal' }
  }
}

/** Hinweise zu den häufigsten JSON-Syntaxfehlern. Die Parsermeldung bleibt daneben stehen. */
const JSON_URSACHEN = {
  bom:            { de: 'Die Datei beginnt mit einer Byte-Order-Markierung (BOM). Windows-Editoren schreiben sie gern; JSON-Parser weisen sie ab. Speichern als „UTF-8 ohne BOM“.' },
  einfacheAnfuehrung: { de: 'JSON kennt nur doppelte Anführungszeichen. Einfache sind in Python und JavaScript erlaubt, in JSON nicht.' },
  nachkomma:      { de: 'Ein Komma vor der schließenden Klammer – JavaScript und Python verzeihen das, JSON nicht.' },
  schluesselOhneAnfuehrung: { de: 'Schlüssel sind Zeichenketten und stehen in doppelten Anführungszeichen – auch dann, wenn sie wie Namen aussehen.' },
  kommentar:      { de: 'JSON hat keine Kommentare. Wo Sie welche brauchen, nehmen Sie ein Feld wie "_hinweis" – oder ein anderes Format (YAML, JSONC).' },
  keinJsonWert:   { de: 'undefined, NaN und Infinity sind JavaScript, nicht JSON. Erlaubt sind Zahl, Zeichenkette, true, false, null, Objekt und Feld.' },
  pythonLiteral:  { de: 'True, False und None sind Python. In JSON heißen sie true, false und null – kleingeschrieben.' },
  kommaFehlt:     { de: 'Zwischen zwei Werten fehlt ein Komma.' },
  unvollstaendig: { de: 'Das Dokument endet, bevor alle Klammern geschlossen sind.' }
}

/* --------------------------------------------------------------------- Labs */

/**
 * Reihenfolge, Umfang, Voraussetzung, Kompetenzziel und Zeitrahmen an einer
 * Stelle. Die Lab-Seiten lesen ihre Einordnung hier heraus, die Startseite
 * ihren Fortschritt.
 */
const LABS = [
  { id: 'lab-01', nr: '01', datei: 'lab-01-zugang.html', uebungen: 6,
    titel: { de: 'Zugang und Datenbank' }, voraussetzung: null, zeit: { de: '90 Minuten' },
    ziel: { de: 'Sich mit dem Demo-Konto verbinden, beide Schemata lesen und sagen können, was die Rolle darf und was nicht.' } },
  { id: 'lab-02', nr: '02', datei: 'lab-02-daten.html', uebungen: 5,
    titel: { de: 'Daten beschaffen' }, voraussetzung: { de: 'Lab 01' }, zeit: { de: '75 Minuten' },
    ziel: { de: 'Für jedes Werkzeug den passenden Weg zu den Daten wählen: Datenbank, CSV aus Git LFS oder DuckDB.' } },
  { id: 'lab-03', nr: '03', datei: 'lab-03-datenmodell.html', uebungen: 5,
    titel: { de: 'Analytisches Datenmodell' }, voraussetzung: { de: 'Lab 01' }, zeit: { de: '105 Minuten' },
    ziel: { de: 'Aus dem operativen Modell in vier Schritten ein Auswertungsmodell bauen und die Fan Trap erkennen.' } },
  { id: 'lab-04', nr: '04', datei: 'lab-04-powerbi.html', uebungen: 5,
    titel: { de: 'Power BI' }, voraussetzung: { de: 'Lab 02, Lab 03' }, zeit: { de: '105 Minuten' },
    ziel: { de: 'PostgreSQL anbinden, Beziehungen aus Fremdschlüsseln prüfen, Kennzahlen als Measures definieren und einen Bericht bauen.' } },
  { id: 'lab-05', nr: '05', datei: 'lab-05-tableau.html', uebungen: 5,
    titel: { de: 'Tableau' }, voraussetzung: { de: 'Lab 02, Lab 03' }, zeit: { de: '90 Minuten' },
    ziel: { de: 'Live und Extract unterscheiden, Dimension und Measure richtig legen und ein Dashboard bauen, das eine Frage beantwortet.' } },
  { id: 'lab-06', nr: '06', datei: 'lab-06-python.html', uebungen: 5,
    titel: { de: 'Python und Colab' }, voraussetzung: { de: 'Lab 01' }, zeit: { de: '75 Minuten' },
    ziel: { de: 'Ein Notebook so führen, dass es von oben nach unten gegen die Datenbank durchläuft — ohne Zugangsdaten im Repository.' } },
  { id: 'lab-07', nr: '07', datei: 'lab-07-datamining.html', uebungen: 5,
    titel: { de: 'Data Mining' }, voraussetzung: { de: 'Lab 03, Lab 06' }, zeit: { de: '90 Minuten' },
    ziel: { de: 'Zu einer Frage das passende Verfahren wählen, die Kennzahl lesen und den Fallstrick benennen.' } },
  { id: 'lab-08', nr: '08', datei: 'lab-08-extern.html', uebungen: 5,
    titel: { de: 'Externe Daten und Sentiment' }, voraussetzung: { de: 'Lab 03, Lab 07' }, zeit: { de: '90 Minuten' },
    ziel: { de: 'Externe Quellen über das Datum anbinden, ihre Lizenz nennen und den Weg einer Rezension vom Shop bis zur Sicht verfolgen.' } }
]

const labVon = (id) => LABS.find(l => l.id === id)

/* --------------------------------------------------------------- Fortschritt */

const fortschrittSchluessel = (lab) => `bm:fortschritt:${lab}`

function ladeFortschritt (lab) {
  try { return JSON.parse(localStorage.getItem(fortschrittSchluessel(lab)) || '{}') } catch { return {} }
}
function merkeFortschritt (lab, id) {
  const f = ladeFortschritt(lab)
  f[id] = true
  try { localStorage.setItem(fortschrittSchluessel(lab), JSON.stringify(f)) } catch { /* egal */ }
  document.dispatchEvent(new CustomEvent('bm:fortschritt'))
}
function loescheFortschritt () {
  for (const l of LABS) {
    try { localStorage.removeItem(fortschrittSchluessel(l.id)) } catch { /* egal */ }
  }
  document.dispatchEvent(new CustomEvent('bm:fortschritt'))
}

/* ---------------------------------------------------------------- Werkzeuge */

const el = (tag, klasse, text) => {
  const n = document.createElement(tag)
  if (klasse) n.className = klasse
  if (text != null) n.textContent = text
  return n
}
const html = (tag, klasse, inhalt) => { const n = el(tag, klasse); n.innerHTML = inhalt; return n }
const basisUrl = new URL('..', import.meta.url)
const url = (pfad) => new URL(pfad, basisUrl).href

/** Beschriftet ein Element aus einem { de }-Objekt oder einer Zeichenkette. */
function zwei (knoten, wert, eigenschaft = 'textContent') {
  const setze = () => { knoten[eigenschaft] = txt(wert) }
  setze()
  document.addEventListener('bm:sprache', setze)
  return knoten
}

async function kopiere (text, echo) {
  try {
    await navigator.clipboard.writeText(text)
    if (echo) echo.textContent = txt(T.kopiert)
  } catch {
    if (echo) echo.textContent = txt(T.kopiertNein)
  }
}

/* ============================================================ Befehlskarten */

const OS_NAMEN = { mac: 'macOS · zsh', win: 'PowerShell', cmd: 'cmd.exe' }
const OS_PROMPT = { mac: '%', win: 'PS>', cmd: '>' }

/**
 * Baut eine Befehlskarte: die Zeile auf dunklem Grund, ein Kopierknopf und
 * darunter die Bestandteile einzeln erklärt. Wer einen Befehl abtippt, ohne
 * zu wissen, was die Bindestriche bedeuten, hat ihn nicht gelernt.
 */
function baueBefehl (ziel, def) {
  const karte = el('div', 'befehl')

  const kopf = el('div', 'befehl-kopf')
  kopf.append(zwei(el('span', 'titel'), def.titel))
  kopf.append(el('span', 'spacer'))

  const varianten = def.varianten || { alle: { befehl: def.befehl } }
  const mehrere = !varianten.alle
  if (mehrere) {
    const schalter = el('div', 'os-schalter')
    schalter.setAttribute('role', 'group')
    for (const os of ['mac', 'win', 'cmd']) {
      if (!varianten[os]) continue
      const b = el('button', 'os-btn', OS_NAMEN[os])
      b.type = 'button'
      b.dataset.osBtn = os
      b.addEventListener('click', () => setzeOs(os))
      schalter.append(b)
    }
    kopf.append(schalter)
  }
  karte.append(kopf)

  const zeile = el('div', 'befehl-zeile')
  const promptSpan = el('span', 'prompt', '$')
  const pre = el('pre')
  const knopf = zwei(el('button', 'befehl-kopieren'), T.kopieren)
  knopf.type = 'button'
  zeile.append(promptSpan, pre, knopf)
  karte.append(zeile)

  const teile = el('div', 'befehl-teile')
  const dl = el('dl')
  teile.append(dl)

  let ausgabe = null
  if (def.ausgabe) {
    ausgabe = el('div', 'befehl-ausgabe')
    karte.append(teile, ausgabe)
  } else {
    karte.append(teile)
  }

  const zeichne = () => {
    const os = mehrere ? (varianten[aktuellesOs()] ? aktuellesOs() : Object.keys(varianten)[0]) : 'alle'
    const v = varianten[os]
    karte.querySelectorAll('.os-btn').forEach(b => {
      const an = b.dataset.osBtn === os
      b.classList.toggle('active', an)
      b.setAttribute('aria-pressed', String(an))
    })
    pre.textContent = v.befehl
    promptSpan.textContent = mehrere ? OS_PROMPT[os] : (def.prompt || '$')
    dl.replaceChildren()
    const liste = v.teile || def.teile || []
    for (const t of liste) {
      dl.append(el('dt', null, t.was))
      dl.append(zwei(el('dd'), t.bedeutet))
    }
    teile.hidden = !liste.length
    if (ausgabe) ausgabe.textContent = typeof def.ausgabe === 'string' ? def.ausgabe : (def.ausgabe[os] || def.ausgabe.alle || '')
    knopf.onclick = () => kopiere(v.befehl, null)
  }
  zeichne()
  document.addEventListener('bm:os', zeichne)
  document.addEventListener('bm:sprache', zeichne)

  ziel.replaceChildren(karte)
}

/* ================================================================ Datenbank

   Eine Maschine: PostgreSQL als PGlite (WebAssembly) im Browser. Die Seite
   trägt data-datenbank="postgres"; gesät werden die beiden Schemata der
   echten Datenbank (wawi, burgermetrics) aus den Mini-Skripten und danach
   die Sichten. Ergebnisse haben immer die Form { fields, rows } mit Zeilen
   als Felder - damit gleichnamige Spalten nicht zusammenfallen.
   =========================================================================== */

/** Saatfolge — identisch mit tools/sql.mjs: zwei Schemata wie in der echten Datenbank, dann die Sichten. */
const SAAT = [
  ['CREATE SCHEMA wawi; SET search_path TO wawi;', 'data/wawi_mini.sql'],
  ['CREATE SCHEMA burgermetrics; SET search_path TO burgermetrics;', 'data/burgermetrics_mini.sql'],
  ['SET search_path TO wawi, burgermetrics;', 'data/bm_sichten.sql']
]
const SUCHPFAD = 'SET search_path TO wawi, burgermetrics'

let dbVersprechen = null
const saatText = {}

async function ladePGlite () {
  try {
    return (await import('./pglite/index.js')).PGlite
  } catch (e) {
    console.warn('Lokale PGlite-Fassung nicht ladbar, weiche auf jsDelivr aus.', e)
    return (await import('https://cdn.jsdelivr.net/npm/@electric-sql/pglite@0.5.5/dist/index.js')).PGlite
  }
}

/** Eine Datenbank je Seite; `gesaet` sagt, ob der Bestand schon geladen ist, `lauf` hält die laufende Saat. */
async function holeDb () {
  if (!dbVersprechen) {
    dbVersprechen = (async () => {
      const PGlite = await ladePGlite()
      return { db: await PGlite.create(), gesaet: false, lauf: null }
    })()
  }
  return dbVersprechen
}

/** Liest ein Saatskript einmal und hält es im Speicher. */
async function holeSaat (datei) {
  if (saatText[datei] == null) {
    const r = await fetch(url(datei))
    if (!r.ok) throw new Error(datei + ': ' + r.status)
    saatText[datei] = await r.text()
  }
  return saatText[datei]
}

/**
 * Sät die Datenbank neu: Alle selbst angelegten Schemata (wawi, burgermetrics,
 * public, …) fallen, damit eine Prüfung immer auf demselben Ausgangsbestand
 * rechnet. Läuft eine Saat schon (etwa die des Datenbankbands), warten alle
 * Aufrufer auf denselben Lauf - zwei verschränkte DROP SCHEMA … CASCADE
 * ließen sonst beide scheitern.
 */
function saeen (h) {
  h.lauf ??= (async () => {
    h.gesaet = false
    try {
      const schemata = await h.db.query(
        "SELECT nspname FROM pg_namespace WHERE nspname NOT LIKE 'pg\\_%' AND nspname <> 'information_schema'")
      for (const z of schemata.rows) await h.db.exec(`DROP SCHEMA IF EXISTS "${z.nspname}" CASCADE`)
      await h.db.exec('CREATE SCHEMA public;')
      for (const [vorspann, datei] of SAAT) {
        await h.db.exec(vorspann)
        await h.db.exec(await holeSaat(datei))
      }
      await h.db.exec(SUCHPFAD)
      h.gesaet = true
    } finally { h.lauf = null }
  })()
  return h.lauf
}

/**
 * Führt SQL aus und liefert das letzte Ergebnis mit Spalten. Bei mehreren
 * Anweisungen zählt die letzte, die eine Tabelle liefert.
 */
async function fuehre (h, sql) {
  if (!/;\s*\S/.test(sql)) return await h.db.query(sql, [], { rowMode: 'array' })
  const teile = await h.db.exec(sql, { rowMode: 'array' })
  return [...teile].reverse().find(t => t.fields && t.fields.length) || teile[teile.length - 1] || { fields: [], rows: [] }
}

/**
 * Die Werte einer Ergebniszeile in Spaltenreihenfolge. Abfragen laufen mit
 * rowMode 'array', also sind Zeilen Felder; ein Objekt kann aber noch von
 * anderswo kommen, dann entscheidet die Spaltenliste.
 */
function werteVon (zeile, fields = []) {
  if (Array.isArray(zeile)) return zeile
  return fields.length ? fields.map(f => zeile[f.name]) : Object.values(zeile)
}

/** Baut eine Ergebnistabelle. Zahlen rechtsbündig, NULL erkennbar. */
function ergebnisTabelle (res, maxZeilen = 200) {
  const wrap = el('div', 'result-table')
  const tab = el('table')
  const thead = el('thead')
  const kopf = el('tr')
  for (const f of res.fields) kopf.append(el('th', null, f.name))
  thead.append(kopf); tab.append(thead)
  const tbody = el('tbody')
  for (const zeile of res.rows.slice(0, maxZeilen)) {
    const tr = el('tr')
    for (const wert of werteVon(zeile, res.fields)) {
      const td = el('td')
      if (wert === null || wert === undefined) { td.className = 'null'; td.textContent = 'NULL' }
      else if (wert instanceof Date) td.textContent = wert.toISOString().slice(0, 10)
      else if (wert instanceof Uint8Array) td.textContent = `<blob ${wert.length} B>`
      else if (typeof wert === 'object') td.textContent = JSON.stringify(wert)
      else {
        const s = String(wert)
        if (typeof wert === 'number' || typeof wert === 'bigint' || /^-?\d+(\.\d+)?$/.test(s)) td.className = 'num'
        td.textContent = s
      }
      tr.append(td)
    }
    tbody.append(tr)
  }
  tab.append(tbody); wrap.append(tab)
  return wrap
}

/** Vergleicht zwei Ergebnisse zeilenweise; Reihenfolge nur, wenn gefordert. */
function gleich (a, b, sortiert) {
  const norm = (r) => r.rows.map(z => werteVon(z, r.fields).map(v =>
    v === null || v === undefined ? '␀'
      : v instanceof Date ? v.toISOString().slice(0, 10)
        : typeof v === 'number' ? Number(v).toFixed(4)
          : /^-?\d+(\.\d+)?$/.test(String(v)) ? Number(v).toFixed(4)
            : String(v).trim()).join(''))
  let x = norm(a); let y = norm(b)
  if (!sortiert) { x = [...x].sort(); y = [...y].sort() }
  return x.length === y.length && x.every((v, i) => v === y[i])
}

function baueDbBand (ziel) {
  const band = el('div', 'db-status busy')
  band.append(el('span', 'dot'))
  const text = el('span', null, txt(T.dbLaden))
  band.append(text, el('span', 'spacer'))
  const btn = zwei(el('button', 'btn-sm'), T.dbZuruck)
  btn.type = 'button'
  btn.disabled = true
  band.append(btn)
  ziel.append(band)

  const setzen = async () => {
    band.className = 'db-status busy'
    text.textContent = txt(T.dbLaden)
    btn.disabled = true
    try {
      const h = await holeDb()
      await saeen(h)
      band.className = 'db-status ready'
      text.textContent = txt(T.dbBereit)
      btn.disabled = false
      document.dispatchEvent(new CustomEvent('bm:datenbank'))
    } catch (e) {
      band.className = 'db-status failed'
      text.textContent = txt(T.dbFehler) + ' ' + e.message
    }
  }
  btn.addEventListener('click', setzen)
  return setzen()
}

/* ============================================================== Übungsboxen */

function status (ziel, art, ueberschrift, detail) {
  ziel.replaceChildren()
  const zeile = el('div', 'line ' + art)
  zeile.append(el('strong', null, ueberschrift))
  if (detail) {
    const p = el('pre'); p.textContent = detail; zeile.append(p)
  }
  ziel.append(zeile)
  return zeile
}

/** Fragenblock für den Typ `quiz`. */
function baueFragen (fragen, ziel, uebungId) {
  const zustand = []
  fragen.forEach((f, i) => {
    const block = el('div', 'frage')
    block.append(html('p', null, txt(f.frage)))
    const mehrfach = !!f.mehrfach
    const eintraege = []
    f.optionen.forEach((o, j) => {
      const lab = el('label')
      const inp = document.createElement('input')
      inp.type = mehrfach ? 'checkbox' : 'radio'
      inp.name = `${uebungId}-f${i}`
      inp.value = String(j)
      const span = zwei(el('span'), o)
      lab.append(inp, span)
      block.append(lab)
      eintraege.push({ lab, inp, j })
    })
    const erk = el('div', 'erklaerung')
    erk.hidden = true
    block.append(erk)
    ziel.append(block)
    zustand.push({ f, eintraege, erk, mehrfach })
  })

  return {
    beantwortet: () => zustand.every(z => z.eintraege.some(e => e.inp.checked)),
    pruefe: () => {
      let alleRichtig = true
      for (const z of zustand) {
        const gewaehlt = z.eintraege.filter(e => e.inp.checked).map(e => e.j).sort()
        const richtig = [...z.f.richtig].sort()
        const passt = gewaehlt.length === richtig.length && gewaehlt.every((v, i) => v === richtig[i])
        if (!passt) alleRichtig = false
        for (const e of z.eintraege) {
          e.lab.classList.remove('richtig', 'falsch')
          if (richtig.includes(e.j)) e.lab.classList.add('richtig')
          else if (e.inp.checked) e.lab.classList.add('falsch')
        }
        if (z.f.erklaerung) { z.erk.hidden = false; z.erk.innerHTML = txt(z.f.erklaerung) }
      }
      return alleRichtig
    }
  }
}

/** Klappbare Hinweis- und Musterlösungsblöcke unter einer Eingabe. */
function hinweisUndLoesung (koerper, uebung, eingabe) {
  if (uebung.hinweis) {
    const d = el('details')
    d.append(zwei(el('summary'), T.hinweis))
    const inh = el('div', 'tip-box')
    const zeichne = () => { inh.innerHTML = txt(uebung.hinweis) }
    zeichne(); document.addEventListener('bm:sprache', zeichne)
    d.append(inh)
    koerper.append(d)
  }
  if (uebung.loesung) {
    const d = el('details')
    d.append(zwei(el('summary'), T.loesung))
    d.append(el('pre', 'code-block', uebung.loesung))
    const akt = el('div', 'uebung-aktionen')
    const bk = zwei(el('button', 'btn-sm'), T.kopieren)
    const bu = zwei(el('button', 'btn-sm'), T.uebernehmen)
    bk.type = bu.type = 'button'
    const echo = el('span', 'hinweis-klein')
    akt.append(bk, bu, echo)
    bk.addEventListener('click', () => kopiere(uebung.loesung, echo))
    bu.addEventListener('click', () => { eingabe.value = uebung.loesung; eingabe.focus() })
    d.append(akt)
    koerper.append(d)
  }
}

/* ======================================================== Regal-Simulator

   Ein Feld liegt auf einem Regal, und aus der Belegung entsteht ein Diagramm -
   das ist der Kern von Tableau (Columns/Rows/Marks) wie von Power BI
   (X-axis/Y-axis/Legend). Der Simulator bildet genau diesen Mechanismus nach,
   nicht die Oberfläche: Felder werden per Auswahlliste auf Regale gelegt,
   Kennzahlen bekommen eine Aggregation, und das Diagramm rechnet live.
   =========================================================================== */

const REGAL_TEXTE = {
  tableau: {
    spalten: 'Columns', zeilen: 'Rows', farbe: 'Color', filter: 'Filters',
    felder: 'Data', dimension: { de: 'Dimension (diskret)' }, kennzahl: { de: 'Kennzahl (stetig)' }
  },
  powerbi: {
    spalten: 'X-axis', zeilen: 'Y-axis', farbe: 'Legend', filter: 'Filters',
    felder: 'Data', dimension: { de: 'Spalte (Text/Datum)' }, kennzahl: { de: 'Σ Kennzahl' }
  }
}

const regalDaten = {}
async function holeRegalDaten (quelle) {
  if (Array.isArray(quelle)) return quelle
  if (!regalDaten[quelle]) {
    regalDaten[quelle] = fetch(url(quelle)).then(r => { if (!r.ok) throw new Error(quelle + ': ' + r.status); return r.json() })
  }
  return regalDaten[quelle]
}

const FARBEN = ['#C2410C', '#ED7004', '#4F6D7A', '#9A3412', '#8C9A5B', '#C98B6A', '#57534E']

function baueRegal (ziel, opt) {
  const V = REGAL_TEXTE[opt.variante] || REGAL_TEXTE.tableau
  const felder = opt.felder || []
  const belegung = { spalten: [], zeilen: [], farbe: null, filter: {}, ...(opt.start ? JSON.parse(JSON.stringify(opt.start)) : {}) }
  let daten = []

  const kasten = el('div', 'regal ' + (opt.variante || 'tableau'))
  const feldPane = el('div', 'regal-felder')
  const arbeit = el('div', 'regal-arbeit')
  kasten.append(feldPane, arbeit)
  ziel.replaceChildren(kasten)

  const feldName = (id) => txt(felder.find(f => f.id === id)?.titel || id)
  const istKennzahl = (id) => felder.find(f => f.id === id)?.typ === 'kennzahl'

  /* -- Feldliste links --------------------------------------------------- */
  const zeichneFelder = () => {
    feldPane.replaceChildren()
    feldPane.append(el('div', 'regal-titel', V.felder))
    for (const art of ['dimension', 'kennzahl']) {
      feldPane.append(el('div', 'regal-untertitel', txt(V[art])))
      for (const f of felder.filter(x => (x.typ === 'kennzahl') === (art === 'kennzahl'))) {
        const pill = el('span', 'pille ' + (f.typ === 'kennzahl' ? 'kennzahl' : 'dimension'))
        const symbol = f.typ === 'kennzahl' ? (opt.variante === 'powerbi' ? 'Σ' : '#') : (f.geordnet ? '📅' : 'Abc')
        pill.append(el('i', null, symbol), document.createTextNode(txt(f.titel)))
        pill.title = txt(f.erklaerung || '')
        feldPane.append(pill)
      }
    }
  }

  /* -- Regale ------------------------------------------------------------ */
  const regale = el('div', 'regale')
  const diagramm = el('div', 'regal-diagramm')
  arbeit.append(regale, diagramm)

  const chip = (regal, eintrag, i) => {
    const feld = typeof eintrag === 'string' ? eintrag : eintrag.feld
    const c = el('span', 'chip ' + (istKennzahl(feld) ? 'kennzahl' : 'dimension'))
    if (istKennzahl(feld)) {
      const sel = document.createElement('select')
      sel.className = 'agg'
      sel.setAttribute('aria-label', 'Aggregation')
      for (const a of AGGREGATE) { const o = el('option', null, a); o.value = a; sel.append(o) }
      sel.value = (typeof eintrag === 'object' && eintrag.agg) || 'SUM'
      sel.addEventListener('change', () => { belegung[regal][i] = { feld, agg: sel.value }; zeichneAlles() })
      c.append(sel, document.createTextNode('(' + feldName(feld) + ')'))
    } else {
      c.append(document.createTextNode(feldName(feld)))
    }
    const x = el('button', 'weg', '×'); x.type = 'button'; x.title = txt(T.entfernen); x.setAttribute('aria-label', txt(T.entfernen) + ' ' + feldName(feld))
    x.addEventListener('click', () => {
      if (regal === 'farbe') belegung.farbe = null
      else belegung[regal].splice(i, 1)
      zeichneAlles()
    })
    c.append(x)
    return c
  }

  const auswahl = (regal, nurDimension) => {
    const sel = document.createElement('select')
    sel.className = 'regal-auswahl'
    sel.setAttribute('aria-label', V[regal])
    const leer = el('option', null, txt(T.feldHinzu)); leer.value = ''
    sel.append(leer)
    for (const f of felder) {
      if (nurDimension && f.typ === 'kennzahl') continue
      const o = el('option', null, txt(f.titel)); o.value = f.id; sel.append(o)
    }
    sel.addEventListener('change', () => {
      if (!sel.value) return
      if (regal === 'farbe') belegung.farbe = sel.value
      else belegung[regal].push(istKennzahl(sel.value) ? { feld: sel.value, agg: 'SUM' } : sel.value)
      zeichneAlles()
    })
    return sel
  }

  const zeichneRegale = () => {
    regale.replaceChildren()
    for (const regal of ['spalten', 'zeilen']) {
      const z = el('div', 'regal-zeile')
      z.append(el('span', 'regal-name', V[regal]))
      const inhalt = el('span', 'regal-inhalt')
      belegung[regal].forEach((e, i) => inhalt.append(chip(regal, e, i)))
      inhalt.append(auswahl(regal, false))
      z.append(inhalt)
      regale.append(z)
    }
    const zf = el('div', 'regal-zeile')
    zf.append(el('span', 'regal-name', V.farbe))
    const inhaltF = el('span', 'regal-inhalt')
    if (belegung.farbe) inhaltF.append(chip('farbe', belegung.farbe, 0))
    else inhaltF.append(auswahl('farbe', true))
    zf.append(inhaltF)
    regale.append(zf)

    // Filter: ein Feld wählen, dann Werte ankreuzen.
    const zfi = el('div', 'regal-zeile filter')
    zfi.append(el('span', 'regal-name', V.filter))
    const inhaltFi = el('span', 'regal-inhalt')
    for (const [feld, werte] of Object.entries(belegung.filter)) {
      if (!werte || !werte.length) continue
      const c = el('span', 'chip filter')
      c.append(document.createTextNode(`${feldName(feld)}: ${werte.join(', ')}`))
      const x = el('button', 'weg', '×'); x.type = 'button'; x.title = txt(T.entfernen)
      x.addEventListener('click', () => { delete belegung.filter[feld]; zeichneAlles() })
      c.append(x)
      inhaltFi.append(c)
    }
    const selF = document.createElement('select')
    selF.className = 'regal-auswahl'
    selF.setAttribute('aria-label', V.filter)
    const leerF = el('option', null, txt(T.feldHinzu)); leerF.value = ''
    selF.append(leerF)
    for (const f of felder.filter(x => x.typ !== 'kennzahl')) { const o = el('option', null, txt(f.titel)); o.value = f.id; selF.append(o) }
    inhaltFi.append(selF)
    const werteBox = el('div', 'filter-werte')
    inhaltFi.append(werteBox)
    selF.addEventListener('change', () => {
      werteBox.replaceChildren()
      if (!selF.value) return
      const feld = selF.value
      const werte = [...new Set(daten.map(z => z[feld]))]
      const ordnung = felder.find(f => f.id === feld)?.reihenfolge
      werte.sort((a, b) => ordnung ? ordnung.indexOf(a) - ordnung.indexOf(b) : String(a).localeCompare(String(b), 'de'))
      werteBox.append(el('span', 'hinweis-klein', txt(T.filterWerte) + ': '))
      for (const w of werte) {
        const lab = el('label', 'filter-wert')
        const cb = document.createElement('input'); cb.type = 'checkbox'; cb.value = String(w)
        cb.checked = (belegung.filter[feld] || []).map(String).includes(String(w))
        cb.addEventListener('change', () => {
          const aktuell = new Set((belegung.filter[feld] || []).map(String))
          if (cb.checked) aktuell.add(String(w)); else aktuell.delete(String(w))
          belegung.filter[feld] = [...aktuell]
          zeichneDiagramm()
          // Chips oben nachziehen, Auswahl aber offen lassen.
          zeichneRegale(); regale.querySelector('.filter select').value = feld; regale.querySelector('.filter select').dispatchEvent(new Event('change'))
        })
        lab.append(cb, document.createTextNode(String(w)))
        werteBox.append(lab)
      }
    })
    zfi.append(inhaltFi)
    regale.append(zfi)
  }

  /* -- Diagramm ---------------------------------------------------------- */
  const fmt = (v) => v == null ? '–' : (Math.abs(v) >= 100 ? Math.round(v).toLocaleString('de-DE') : Number(v).toLocaleString('de-DE', { maximumFractionDigits: 2 }))

  const zeichneDiagramm = () => {
    diagramm.replaceChildren()
    const art = regalDarstellung(felder, belegung)
    if (art === 'leer' || !daten.length) { diagramm.append(el('p', 'hinweis-klein', txt(T.keineDaten))); return }
    const erg = regalErgebnis(daten, felder, belegung)

    if (art === 'tabelle') {
      const res = {
        fields: [...erg.dimensionen.map(d => ({ name: feldName(d.feld) })), ...erg.kennzahlen.map(k => ({ name: k.titel }))],
        rows: erg.zeilen.map(z => [...erg.dimensionen.map(d => z.schluessel[d.feld]), ...erg.kennzahlen.map(k => z.werte[k.titel] == null ? null : Math.round(z.werte[k.titel] * 100) / 100)])
      }
      diagramm.append(ergebnisTabelle(res, 50))
      return
    }

    // Achsen: die Dimension auf Spalten bildet die x-Achse (senkrechte Balken);
    // liegt sie auf Zeilen, werden die Balken waagerecht - wie im Werkzeug.
    const dimSp = erg.dimensionen.find(d => d.regal === 'spalten')
    const dimZe = erg.dimensionen.find(d => d.regal === 'zeilen')
    const waagerecht = !dimSp && !!dimZe
    const achse = (dimSp || dimZe).feld
    const kenn = erg.kennzahlen[0]
    const farbe = erg.dimensionen.find(d => d.regal === 'farbe')?.feld || null

    const kategorien = [...new Set(erg.zeilen.map(z => z.schluessel[achse]))]
    const reihen = farbe ? [...new Set(erg.zeilen.map(z => z.schluessel[farbe]))] : [null]
    const wert = (k, r) => erg.zeilen.find(z => z.schluessel[achse] === k && (!farbe || z.schluessel[farbe] === r))?.werte[kenn.titel] ?? 0
    const maxWert = Math.max(1, ...kategorien.map(k => art === 'linie' || !farbe ? Math.max(...reihen.map(r => wert(k, r))) : reihen.reduce((s, r) => s + wert(k, r), 0)))

    const B = 620; const H = waagerecht ? Math.max(180, 26 * kategorien.length + 60) : 300
    const rand = { l: waagerecht ? 130 : 60, r: 16, o: 16, u: waagerecht ? 30 : 60 }
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg')
    svg.setAttribute('viewBox', `0 0 ${B} ${H}`)
    svg.setAttribute('role', 'img')
    svg.setAttribute('aria-label', `${kenn.titel} nach ${feldName(achse)}`)
    const ns = (tag, attrs, text) => {
      const n = document.createElementNS('http://www.w3.org/2000/svg', tag)
      for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v)
      if (text != null) n.textContent = text
      return n
    }
    const innenB = B - rand.l - rand.r; const innenH = H - rand.o - rand.u
    // Achsen und Raster
    for (let i = 0; i <= 4; i++) {
      const v = maxWert * i / 4
      if (waagerecht) {
        const x = rand.l + innenB * i / 4
        svg.append(ns('line', { x1: x, y1: rand.o, x2: x, y2: rand.o + innenH, class: 'raster' }))
        svg.append(ns('text', { x, y: H - 8, class: 'achse', 'text-anchor': 'middle' }, fmt(v)))
      } else {
        const y = rand.o + innenH - innenH * i / 4
        svg.append(ns('line', { x1: rand.l, y1: y, x2: B - rand.r, y2: y, class: 'raster' }))
        svg.append(ns('text', { x: rand.l - 6, y: y + 4, class: 'achse', 'text-anchor': 'end' }, fmt(v)))
      }
    }
    const farbeVon = (r) => FARBEN[reihen.indexOf(r) % FARBEN.length]
    if (art === 'linie') {
      const xVon = (i) => rand.l + (kategorien.length === 1 ? innenB / 2 : innenB * i / (kategorien.length - 1))
      for (const r of reihen) {
        const punkte = kategorien.map((k, i) => `${xVon(i)},${rand.o + innenH - innenH * wert(k, r) / maxWert}`).join(' ')
        svg.append(ns('polyline', { points: punkte, fill: 'none', stroke: farbeVon(r), 'stroke-width': 2.5 }))
        kategorien.forEach((k, i) => {
          const c = ns('circle', { cx: xVon(i), cy: rand.o + innenH - innenH * wert(k, r) / maxWert, r: 3.5, fill: farbeVon(r) })
          c.append(ns('title', {}, `${k}${r != null ? ' · ' + r : ''}: ${fmt(wert(k, r))}`))
          svg.append(c)
        })
      }
      kategorien.forEach((k, i) => svg.append(ns('text', { x: xVon(i), y: H - rand.u + 16, class: 'achse', 'text-anchor': 'middle' }, String(k))))
    } else {
      const schritt = (waagerecht ? innenH : innenB) / kategorien.length
      const breite = schritt * 0.7
      kategorien.forEach((k, i) => {
        let stapel = 0
        for (const r of reihen) {
          const v = wert(k, r)
          if (waagerecht) {
            const y = rand.o + schritt * i + (schritt - breite) / 2
            const x0 = rand.l + innenB * stapel / maxWert
            const rect = ns('rect', { x: x0, y, width: innenB * v / maxWert, height: breite, fill: farbeVon(r) })
            rect.append(ns('title', {}, `${k}${r != null ? ' · ' + r : ''}: ${fmt(v)}`))
            svg.append(rect)
          } else {
            const x = rand.l + schritt * i + (schritt - breite) / 2
            const h = innenH * v / maxWert
            const y = rand.o + innenH - innenH * stapel / maxWert - h
            const rect = ns('rect', { x, y, width: breite, height: h, fill: farbeVon(r) })
            rect.append(ns('title', {}, `${k}${r != null ? ' · ' + r : ''}: ${fmt(v)}`))
            svg.append(rect)
          }
          stapel += v
        }
        if (waagerecht) svg.append(ns('text', { x: rand.l - 6, y: rand.o + schritt * i + schritt / 2 + 4, class: 'achse', 'text-anchor': 'end' }, String(k)))
        else {
          const t = ns('text', { x: rand.l + schritt * i + schritt / 2, y: H - rand.u + 16, class: 'achse', 'text-anchor': 'middle' }, String(k))
          if (kategorien.length > 8) { t.setAttribute('transform', `rotate(-35 ${rand.l + schritt * i + schritt / 2} ${H - rand.u + 16})`); t.setAttribute('text-anchor', 'end') }
          svg.append(t)
        }
      })
    }
    svg.append(ns('text', { x: waagerecht ? B / 2 : 14, y: waagerecht ? H - 8 : H / 2, class: 'achse titel', 'text-anchor': 'middle', transform: waagerecht ? '' : `rotate(-90 14 ${H / 2})` }, kenn.titel))
    diagramm.append(svg)
    if (farbe) {
      const legende = el('div', 'legende')
      for (const r of reihen) { const s = el('span'); s.append(el('i')); s.querySelector('i').style.background = farbeVon(r); s.append(document.createTextNode(String(r))); legende.append(s) }
      diagramm.append(legende)
    }
  }

  const zeichneAlles = () => { zeichneRegale(); zeichneDiagramm() }

  if (opt.ziel) {
    const aktionen = el('div', 'uebung-aktionen')
    const btn = zwei(el('button', 'btn-sm primary'), T.pruefen)
    btn.type = 'button'
    const btnLeer = zwei(el('button', 'btn-sm'), T.leeren)
    btnLeer.type = 'button'
    aktionen.append(btn, btnLeer)
    arbeit.append(aktionen)
    btn.addEventListener('click', () => {
      // Die Abweichungen nennen das Regal mit dem Namen, den das Werkzeug verwendet.
      const fehler = regalAbweichungen(belegung, opt.ziel).map(f => ({
        ...f,
        text: f.regal === 'spalten' || f.regal === 'zeilen' || f.regal === 'farbe'
          ? { de: `Regal „${V[f.regal]}“ stimmt nicht.` }
          : f.text
      }))
      opt.beiPruefung(fehler)
    })
    btnLeer.addEventListener('click', () => { belegung.spalten = []; belegung.zeilen = []; belegung.farbe = null; belegung.filter = {}; zeichneAlles() })
  }

  zeichneFelder()
  zeichneAlles()
  holeRegalDaten(opt.datenQuelle).then(d => { daten = d; zeichneAlles() }).catch(e => {
    diagramm.append(el('p', 'hinweis-klein', 'Daten nicht ladbar: ' + e.message))
  })
  document.addEventListener('bm:sprache', () => { zeichneFelder(); zeichneAlles() })
  return { belegung }
}

function baueBox (uebung, ctx) {
  const box = el('section', 'uebung')
  box.id = 'uebung-' + uebung.id

  const kopf = el('div', 'uebung-kopf')
  kopf.append(el('span', 'uebung-id', uebung.id))
  kopf.append(zwei(el('span', 'uebung-typ'), T.typ[uebung.typ] || ''))
  kopf.append(zwei(el('span', 'uebung-titel'), uebung.titel))
  kopf.append(el('span', 'spacer'))
  const haken = zwei(el('span', 'badge'), T.ok)
  haken.hidden = !ctx.fortschritt[uebung.id]
  kopf.append(haken)
  box.append(kopf)

  const koerper = el('div', 'uebung-koerper')
  const aufgabe = el('div', 'uebung-aufgabe')
  const zeichneAufgabe = () => { aufgabe.innerHTML = txt(uebung.aufgabe) }
  zeichneAufgabe()
  document.addEventListener('bm:sprache', zeichneAufgabe)
  koerper.append(aufgabe)
  box.append(koerper)

  const erledigt = () => {
    haken.hidden = false
    if (!ctx.frei) merkeFortschritt(ctx.lab, uebung.id)
  }

  const meldung = el('div', 'uebung-status')

  /* ---------------------------------------------------------------- quiz */
  if (uebung.typ === 'quiz') {
    const fragenZiel = el('div')
    koerper.append(fragenZiel)
    const fragen = baueFragen(uebung.fragen, fragenZiel, uebung.id)
    const aktionen = el('div', 'uebung-aktionen')
    const btn = zwei(el('button', 'btn-sm primary'), T.pruefen)
    btn.type = 'button'
    aktionen.append(btn)
    koerper.append(aktionen, meldung)
    btn.addEventListener('click', () => {
      if (!fragen.beantwortet()) { status(meldung, 'note', txt(T.fragenOffen)); return }
      if (fragen.pruefe()) {
        status(meldung, 'ok', txt(T.richtig), uebung.rueckmeldung ? txt(uebung.rueckmeldung) : null)
        erledigt()
      } else {
        status(meldung, 'fail', txt(T.nochNicht))
      }
    })
  }

  /* ------------------------------------------------------------ zuordnen */
  if (uebung.typ === 'zuordnen') {
    const gitter = el('div', 'zuordnen')
    const felder = []
    for (const p of uebung.paare) {
      const zeile = el('div', 'paar')
      zeile.append(zwei(el('span', 'begriff'), p.begriff))
      const sel = document.createElement('select')
      const leer = el('option', null, txt(T.waehlen))
      leer.value = ''
      sel.append(leer)
      for (const z of uebung.ziele) {
        const o = el('option', null, txt(z.text))
        o.value = z.id
        sel.append(o)
      }
      sel.setAttribute('aria-label', txt(p.begriff))
      zeile.append(sel)
      gitter.append(zeile)
      felder.push({ p, sel, zeile })
    }
    koerper.append(gitter)
    const aktionen = el('div', 'uebung-aktionen')
    const btn = zwei(el('button', 'btn-sm primary'), T.pruefen)
    btn.type = 'button'
    aktionen.append(btn)
    koerper.append(aktionen, meldung)

    document.addEventListener('bm:sprache', () => {
      for (const f of felder) {
        f.sel.options[0].textContent = txt(T.waehlen)
        uebung.ziele.forEach((z, i) => { f.sel.options[i + 1].textContent = txt(z.text) })
      }
    })

    btn.addEventListener('click', () => {
      if (felder.some(f => !f.sel.value)) { status(meldung, 'note', txt(T.alleZuordnen)); return }
      let alle = true
      for (const f of felder) {
        const passt = f.sel.value === f.p.ziel
        f.zeile.classList.toggle('richtig', passt)
        f.zeile.classList.toggle('falsch', !passt)
        if (!passt) alle = false
      }
      if (alle) {
        status(meldung, 'ok', txt(T.richtig), uebung.rueckmeldung ? txt(uebung.rueckmeldung) : null)
        erledigt()
      } else status(meldung, 'fail', txt(T.nochNicht))
    })
  }

  /* ---------------------------------------------------------- checkliste */
  if (uebung.typ === 'checkliste') {
    const liste = el('ul', 'checkliste')
    const kaesten = []
    uebung.schritte.forEach((s, i) => {
      const li = el('li')
      const inp = document.createElement('input')
      inp.type = 'checkbox'
      inp.id = `${uebung.id}-s${i}`
      const lab = document.createElement('label')
      lab.className = 'schritt-text'
      lab.htmlFor = inp.id
      const zeichne = () => { lab.innerHTML = txt(s.text) }
      zeichne()
      document.addEventListener('bm:sprache', zeichne)
      li.append(el('span', 'schritt-nr', String(i + 1) + '.'), inp, lab)
      liste.append(li)
      kaesten.push({ inp, li })
    })
    koerper.append(liste, meldung)
    const pruefe = () => {
      for (const k of kaesten) k.li.classList.toggle('ab', k.inp.checked)
      if (kaesten.every(k => k.inp.checked)) {
        status(meldung, 'ok', txt(T.richtig), uebung.rueckmeldung ? txt(uebung.rueckmeldung) : null)
        erledigt()
      }
    }
    for (const k of kaesten) k.inp.addEventListener('change', pruefe)
  }

  /* ----------------------------------------------------------------- sql */
  if (uebung.typ === 'sql') {
    const eingabe = document.createElement('textarea')
    eingabe.spellcheck = false
    eingabe.value = uebung.start || ''
    eingabe.setAttribute('aria-label', txt(uebung.titel))
    koerper.append(eingabe)

    const aktionen = el('div', 'uebung-aktionen')
    const btnRun = zwei(el('button', 'btn-sm'), T.ausfuehren)
    const btnCheck = zwei(el('button', 'btn-sm primary'), T.pruefen)
    btnRun.type = btnCheck.type = 'button'
    btnRun.append(el('kbd', null, navigator.platform.includes('Mac') ? '⌘⏎' : 'Strg+⏎'))
    aktionen.append(btnRun, btnCheck, el('span', 'spacer'))
    const btnLeeren = zwei(el('button', 'btn-sm'), T.leeren)
    btnLeeren.type = 'button'
    aktionen.append(btnLeeren)
    koerper.append(aktionen, meldung)

    hinweisUndLoesung(koerper, uebung, eingabe)

    const zeigeErgebnis = (art, kopfText, res, detail) => {
      const zeile = status(meldung, art, kopfText, detail)
      if (res && res.fields && res.fields.length) {
        meldung.append(el('div', 'result-meta',
          menge(res.rows.length, M.zeile) + (res.rows.length > 200 ? ` (200 ${txt(T.angezeigt)})` : '')))
        if (res.rows.length) meldung.append(ergebnisTabelle(res))
      }
      return zeile
    }

    const sperren = (an) => { btnRun.disabled = btnCheck.disabled = an }

    btnRun.addEventListener('click', async () => {
      const sql = eingabe.value.trim()
      if (!sql) { status(meldung, 'note', txt(T.leer)); return }
      sperren(true); status(meldung, 'note', txt(T.abfrageLaeuft))
      try {
        const h = await holeDb()
        await (h.lauf ?? (h.gesaet ? null : saeen(h)))
        const res = await fuehre(h, sql)
        if (res.fields && res.fields.length) zeigeErgebnis('note', txt(T.ergebnis), res)
        else status(meldung, 'note', txt(T.ausgefuehrt))
      } catch (e) {
        status(meldung, 'fail', txt(T.fehlerSql), e.message)
      } finally { sperren(false) }
    })

    eingabe.addEventListener('keydown', (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') { e.preventDefault(); btnRun.click() }
    })

    btnCheck.addEventListener('click', async () => {
      const sql = eingabe.value.trim()
      if (!sql) { status(meldung, 'note', txt(T.leer)); return }
      sperren(true); status(meldung, 'note', txt(T.abfrageLaeuft))
      try {
        const h = await holeDb()
        await saeen(h)
        if (uebung.vorher) await fuehre(h, uebung.vorher)
        const meins = await fuehre(h, sql)
        // Bei Anweisungen, die den Bestand ändern, wird das Ergebnis über
        // eine Kontrollabfrage verglichen - sonst über die Abfrage selbst.
        const kontrolle = uebung.kontrolle || null
        const meinsK = kontrolle ? await fuehre(h, kontrolle) : meins
        await saeen(h)
        if (uebung.vorher) await fuehre(h, uebung.vorher)
        await fuehre(h, uebung.loesung)
        const soll = kontrolle ? await fuehre(h, kontrolle) : await fuehre(h, uebung.loesung)
        const spaltenGleich = meinsK.fields.length === soll.fields.length
        if (!spaltenGleich) {
          zeigeErgebnis('fail', txt(T.nochNicht), meinsK, txt(T.spaltenFalsch))
        } else if (gleich(meinsK, soll, !!uebung.sortiert)) {
          zeigeErgebnis('ok', txt(T.richtig), meinsK, uebung.rueckmeldung ? txt(uebung.rueckmeldung) : null)
          erledigt()
        } else {
          zeigeErgebnis('fail', txt(T.nochNicht), meinsK, txt(T.zeilenFalsch))
        }
      } catch (e) {
        status(meldung, 'fail', txt(T.fehlerSql), e.message)
      } finally { sperren(false) }
    })

    btnLeeren.addEventListener('click', () => {
      eingabe.value = uebung.start || ''
      meldung.replaceChildren()
      eingabe.focus()
    })
  }

  /* ---------------------------------------------------------------- json */
  if (uebung.typ === 'json') {
    const eingabe = document.createElement('textarea')
    eingabe.spellcheck = false
    eingabe.className = 'json-eingabe'
    eingabe.value = uebung.start || ''
    eingabe.setAttribute('aria-label', txt(uebung.titel))
    koerper.append(eingabe)

    const aktionen = el('div', 'uebung-aktionen')
    const btnCheck = zwei(el('button', 'btn-sm primary'), T.pruefen)
    const btnFormat = zwei(el('button', 'btn-sm'), T.formatieren)
    const btnLeeren = zwei(el('button', 'btn-sm'), T.leeren)
    btnCheck.type = btnFormat.type = btnLeeren.type = 'button'
    aktionen.append(btnCheck, btnFormat, el('span', 'spacer'), btnLeeren)
    koerper.append(aktionen, meldung)
    hinweisUndLoesung(koerper, uebung, eingabe)

    const zeigeSyntaxfehler = (r) => {
      const detail = r.meldung + (r.ursache && JSON_URSACHEN[r.ursache] ? '\n→ ' + txt(JSON_URSACHEN[r.ursache]) : '')
      status(meldung, 'fail', txt(T.jsonUngueltig), detail)
    }

    btnCheck.addEventListener('click', () => {
      const text = eingabe.value
      if (!text.trim()) { status(meldung, 'note', txt(T.leer)); return }
      const r = pruefeJson(text, uebung)
      if (r.meldung) { zeigeSyntaxfehler(r); return }
      if (r.ok) {
        status(meldung, 'ok', txt(ctx.frei ? T.jsonOk : T.richtig), uebung.rueckmeldung ? txt(uebung.rueckmeldung) : null)
        erledigt()
      } else {
        status(meldung, 'fail', txt(T.jsonGueltig), r.befunde.map(b => '• ' + txt(b.text)).join('\n'))
      }
    })
    btnFormat.addEventListener('click', () => {
      const r = pruefeJson(eingabe.value, {})
      if (r.meldung) { zeigeSyntaxfehler(r); return }
      eingabe.value = JSON.stringify(r.geparst, null, 2)
      status(meldung, 'note', txt(T.jsonFormatiert))
    })
    btnLeeren.addEventListener('click', () => { eingabe.value = uebung.start || ''; meldung.replaceChildren(); eingabe.focus() })
  }

  /* --------------------------------------------------------- reihenfolge */
  if (uebung.typ === 'reihenfolge') {
    const eintraege = uebung.eintraege
    const start = uebung.start || [...eintraege].map(e => e.id).reverse()
    let reihenfolge = [...start]
    const liste = el('ol', 'reihenfolge')
    koerper.append(liste)

    const zeichne = () => {
      liste.replaceChildren()
      reihenfolge.forEach((id, i) => {
        const e = eintraege.find(x => x.id === id)
        const li = el('li')
        li.dataset.id = id
        const text = el('span', 'text')
        text.innerHTML = txt(e.text)
        const knoepfe = el('span', 'knoepfe')
        const hoch = el('button', 'btn-mini', '▲'); hoch.type = 'button'; hoch.title = txt(T.hoch); hoch.setAttribute('aria-label', txt(T.hoch))
        const runter = el('button', 'btn-mini', '▼'); runter.type = 'button'; runter.title = txt(T.runter); runter.setAttribute('aria-label', txt(T.runter))
        hoch.disabled = i === 0
        runter.disabled = i === reihenfolge.length - 1
        hoch.addEventListener('click', () => { [reihenfolge[i - 1], reihenfolge[i]] = [reihenfolge[i], reihenfolge[i - 1]]; zeichne(); liste.children[i - 1].querySelector('button').focus() })
        runter.addEventListener('click', () => { [reihenfolge[i + 1], reihenfolge[i]] = [reihenfolge[i], reihenfolge[i + 1]]; zeichne(); liste.children[i + 1].querySelectorAll('button')[1].focus() })
        knoepfe.append(hoch, runter)
        li.append(el('span', 'nr', String(i + 1) + '.'), text, knoepfe)
        liste.append(li)
      })
    }
    zeichne()
    document.addEventListener('bm:sprache', zeichne)

    const aktionen = el('div', 'uebung-aktionen')
    const btn = zwei(el('button', 'btn-sm primary'), T.pruefen)
    btn.type = 'button'
    aktionen.append(btn)
    koerper.append(aktionen, meldung)
    btn.addEventListener('click', () => {
      let erste = -1
      reihenfolge.forEach((id, i) => {
        const passt = uebung.richtig[i] === id
        liste.children[i].classList.toggle('richtig', passt)
        liste.children[i].classList.toggle('falsch', !passt)
        if (!passt && erste < 0) erste = i
      })
      if (erste < 0) {
        status(meldung, 'ok', txt(T.richtig), uebung.rueckmeldung ? txt(uebung.rueckmeldung) : null)
        erledigt()
      } else {
        status(meldung, 'fail', txt(T.nochNicht), txt(T.reihenfolgeFalsch).replace('{n}', String(erste + 1)))
      }
    })
  }

  /* --------------------------------------------------------------- regal */
  if (uebung.typ === 'regal') {
    const halter = el('div')
    koerper.append(halter, meldung)
    baueRegal(halter, {
      variante: uebung.variante || 'tableau',
      felder: uebung.felder || ctx.daten?.regal?.felder,
      datenQuelle: uebung.daten || ctx.daten?.regal?.daten,
      start: uebung.startBelegung,
      ziel: uebung.ziel,
      beiPruefung: (fehler) => {
        if (!fehler.length) {
          status(meldung, 'ok', txt(T.richtig), uebung.rueckmeldung ? txt(uebung.rueckmeldung) : null)
          erledigt()
        } else {
          status(meldung, 'fail', txt(T.nochNicht), fehler.map(f => '• ' + txt(f.text)).join('\n'))
        }
      }
    })
  }

  return box
}

/* ========================================================= Seitenbausteine */

/** Einordnung im Lab-Kopf: Voraussetzung, Umfang, Zeit, Kompetenzziel. */
function baueEinordnung (labId) {
  const ziel = document.querySelector('[data-einordnung]')
  if (!ziel) return
  const l = labVon(labId)
  if (!l) return
  const dl = el('dl', 'lab-einordnung')
  const paar = (schluessel, wert) => {
    dl.append(zwei(el('dt'), schluessel))
    dl.append(zwei(el('dd'), wert))
  }
  paar(T.voraussetzung, l.voraussetzung || T.keine)
  paar(T.umfang, { de: `${l.uebungen} Übungen` })
  paar(T.zeitrahmen, l.zeit)
  paar(T.ziel, l.ziel)
  ziel.replaceChildren(dl)
}

/** Hebt den Abschnitt hervor, der gerade gelesen wird. */
function initSeitennavigation () {
  const links = [...document.querySelectorAll('.sidebar-link[href^="#"]')]
  if (!links.length) return
  const abschnitte = links
    .map(a => ({ a, el: document.getElementById(a.getAttribute('href').slice(1)) }))
    .filter(x => x.el)
  const beob = new IntersectionObserver((eintraege) => {
    for (const e of eintraege) {
      if (!e.isIntersecting) continue
      for (const x of abschnitte) x.a.classList.toggle('active', x.el === e.target)
    }
  }, { rootMargin: '-76px 0px -70% 0px' })
  for (const x of abschnitte) beob.observe(x.el)
}

/** Vor- und Zurück-Navigation am Fuß der Lab-Seiten. */
function baueLabNavigation (labId) {
  const ziel = document.querySelector('[data-lab-nav]')
  if (!ziel) return
  const i = LABS.findIndex(l => l.id === labId)
  const zeile = el('div', 'nav-bottom')
  const machen = (l, richtung) => {
    const a = el('a', 'btn')
    a.href = l.datei
    zwei(a, { de: `${richtung === 'vor' ? '→ Weiter mit' : '← Zurück zu'} Lab ${l.nr}: ${l.titel.de}` })
    return a
  }
  if (i > 0) zeile.append(machen(LABS[i - 1], 'zurueck')); else zeile.append(el('span'))
  if (i < LABS.length - 1) zeile.append(machen(LABS[i + 1], 'vor')); else zeile.append(el('span'))
  ziel.replaceChildren(zeile)
}

/** Fortschrittskarte: auf der Startseite über alle Labs, im Lab über eines. */
function karteFortschritt (nurLab = null) {
  const ziel = document.querySelector('[data-fortschritt]')
  if (!ziel) return
  const zeichne = () => {
    const labs = nurLab ? LABS.filter(l => l.id === nurLab) : LABS
    const geloest = labs.reduce((s, l) => s + Math.min(Object.keys(ladeFortschritt(l.id)).length, l.uebungen), 0)
    const gesamt = labs.reduce((s, l) => s + l.uebungen, 0)

    const karte = el('div', 'fortschritt')
    const kopf = el('div', 'fortschritt-kopf')
    kopf.append(zwei(el('span', 'titel'), T.stand))
    kopf.append(el('span', 'zahl', `${geloest} von ${menge(gesamt, M.uebung)}`))
    karte.append(kopf)

    const balken = el('div', 'balken')
    const fuellung = el('i')
    fuellung.style.width = gesamt ? `${Math.round(geloest / gesamt * 100)}%` : '0%'
    balken.append(fuellung)
    balken.setAttribute('role', 'progressbar')
    balken.setAttribute('aria-valuenow', String(geloest))
    balken.setAttribute('aria-valuemin', '0')
    balken.setAttribute('aria-valuemax', String(gesamt))
    karte.append(balken)

    if (!nurLab) {
      const ul = el('ul', 'fortschritt-liste')
      for (const l of LABS) {
        const n = Math.min(Object.keys(ladeFortschritt(l.id)).length, l.uebungen)
        const li = el('li', n === l.uebungen ? 'voll' : null)
        li.append(el('span', 'nr', l.nr))
        const a = el('a', 'name')
        a.href = l.datei
        zwei(a, l.titel)
        li.append(a)
        li.append(el('span', 'stand', `${n} / ${l.uebungen}`))
        ul.append(li)
      }
      karte.append(ul)

      const akt = el('div', 'uebung-aktionen')
      const btn = zwei(el('button', 'btn-sm gefahr'), T.loeschen)
      btn.type = 'button'
      btn.disabled = geloest === 0
      const echo = el('span', 'hinweis-klein')
      akt.append(btn, echo)
      btn.addEventListener('click', () => {
        if (!confirm(txt(T.loeschenFrage))) return
        loescheFortschritt()
        echo.textContent = txt(T.geloescht)
      })
      karte.append(akt)
    } else if (geloest === gesamt && gesamt) {
      karte.append(el('p', 'hinweis-klein', txt(T.allesGeloest)))
    }

    ziel.replaceChildren(karte)
  }
  zeichne()
  document.addEventListener('bm:fortschritt', zeichne)
  document.addEventListener('bm:sprache', zeichne)
}

/* ================================================================= Einstieg */

async function starteLab (labId) {
  const antwort = await fetch(url(`data/uebungen/${labId}.json`))
  if (!antwort.ok) throw new Error(`data/uebungen/${labId}.json: ${antwort.status}`)
  const daten = await antwort.json()

  // Befehlskarten
  for (const halter of document.querySelectorAll('[data-befehl]')) {
    const def = daten.befehle?.[halter.dataset.befehl]
    if (def) baueBefehl(halter, def)
    else halter.append(el('p', 'hinweis-klein', `Befehlskarte ${halter.dataset.befehl} fehlt.`))
  }

  // Datenbankband, falls die Seite SQL enthält (data-datenbank="postgres").
  const dbHalter = document.querySelector('[data-datenbank]')
  if (dbHalter) baueDbBand(dbHalter)

  // Freie SQL-Konsole: dieselbe Bauform, aber ohne Prüfknopf und ohne
  // Fortschrittseintrag - hier gibt es keine richtige Antwort.
  for (const halter of document.querySelectorAll('[data-sql-konsole]')) {
    const box = baueBox({
      id: 'frei', typ: 'sql',
      titel: { de: 'Freie Abfrage' },
      aufgabe: { de: '<p>Schreiben Sie eine beliebige Abfrage gegen den Miniaturbestand im Browser. Nichts hier wirkt über diesen Browser hinaus.</p>' },
      start: halter.dataset.start || 'SELECT * FROM v_kennzahlen_jahr ORDER BY jahr;'
    }, { lab: labId, fortschritt: {}, frei: true })
    box.querySelector('.uebung-kopf').remove()
    box.querySelectorAll('.btn-sm.primary').forEach(b => b.remove())
    box.className = 'sql-konsole'
    halter.replaceChildren(box)
  }

  // Freie JSON-Werkbank: prüfen und formatieren, ohne Auftrag.
  for (const halter of document.querySelectorAll('[data-json-konsole]')) {
    const box = baueBox({
      id: 'frei', typ: 'json',
      titel: { de: 'JSON-Werkbank' },
      aufgabe: { de: '<p>Fügen Sie beliebiges JSON ein. „Prüfen“ sagt, ob es gültig ist, „Formatieren“ rückt es ein. Nichts verlässt den Browser.</p>' },
      start: halter.dataset.start || '{ "filiale": "BM Europastern", "bestellungen": 7, "umsatz": 84.75 }'
    }, { lab: labId, fortschritt: {}, frei: true })
    box.querySelector('.uebung-kopf').remove()
    box.className = 'sql-konsole'
    halter.replaceChildren(box)
  }

  // Freier Regal-Spielplatz (ohne Auftrag, ohne Fortschritt).
  for (const halter of document.querySelectorAll('[data-regal]')) {
    const def = daten.spielplaetze?.[halter.dataset.regal] || {}
    baueRegal(halter, {
      variante: def.variante || halter.dataset.variante || 'tableau',
      felder: def.felder || daten.regal?.felder,
      datenQuelle: def.daten || daten.regal?.daten,
      start: def.startBelegung
    })
  }

  // Übungen
  const fortschritt = ladeFortschritt(labId)
  const ctx = { lab: labId, fortschritt, daten }
  for (const halter of document.querySelectorAll('[data-uebung]')) {
    const u = (daten.uebungen || []).find(x => x.id === halter.dataset.uebung)
    if (!u) { halter.append(el('p', 'hinweis-klein', `Übung ${halter.dataset.uebung} fehlt.`)); continue }
    halter.replaceChildren(baueBox(u, ctx))
  }

  baueEinordnung(labId)
  baueLabNavigation(labId)
  karteFortschritt(labId)
}

function start () {
  initSprache()
  initOs()
  initSeitennavigation()

  const labId = document.body.dataset.lab
  if (labId) {
    starteLab(labId).catch(e => {
      console.error(e)
      for (const h of document.querySelectorAll('[data-uebung], [data-befehl]')) {
        h.append(el('p', 'hinweis-klein', 'Die Übungsdaten konnten nicht geladen werden: ' + e.message))
      }
    })
  } else {
    karteFortschritt(null)
  }
}

if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start)
else start()
