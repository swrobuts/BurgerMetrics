/**
 * BM-Lab · SQL ohne Browser ausprobieren
 *
 *   node tools/sql.mjs "SELECT count(*) FROM fact_orders"
 *   node tools/sql.mjs --datei abfrage.sql
 *
 * Lädt dieselbe Saat wie die Seite (Schema wawi aus wawi_mini.sql, Schema
 * burgermetrics aus burgermetrics_mini.sql, dazu bm_sichten.sql, Suchpfad
 * wawi, burgermetrics) in PGlite und druckt das letzte Ergebnis mit Spalten.
 * Gedacht, um Musterlösungen zu prüfen, bevor sie in eine Übung wandern.
 */
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const WURZEL = join(dirname(fileURLToPath(import.meta.url)), '..')
const lies = (p) => readFileSync(join(WURZEL, p), 'utf8')

/** Saatfolge — identisch mit saeen() in assets/bm.js. */
export const SAAT = [
  ['CREATE SCHEMA wawi; SET search_path TO wawi;', 'data/wawi_mini.sql'],
  ['CREATE SCHEMA burgermetrics; SET search_path TO burgermetrics;', 'data/burgermetrics_mini.sql'],
  ['SET search_path TO wawi, burgermetrics;', 'data/bm_sichten.sql']
]

export async function neueDatenbank () {
  const { PGlite } = await import(new URL('../assets/pglite/index.js', import.meta.url))
  const db = await PGlite.create()
  for (const [vorspann, datei] of SAAT) {
    await db.exec(vorspann)
    await db.exec(lies(datei))
  }
  await db.exec('SET search_path TO wawi, burgermetrics')
  return db
}

export async function fuehreAus (db, sql) {
  const teile = await db.exec(sql, { rowMode: 'array' })
  const letzte = [...teile].reverse().find(t => t.fields && t.fields.length) || { fields: [], rows: [] }
  return { spalten: letzte.fields.map(f => f.name), zeilen: letzte.rows }
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  const rest = process.argv.slice(2)
  if (!rest.length) { console.error('Aufruf: node tools/sql.mjs "SQL" | --datei pfad'); process.exit(2) }
  const sql = rest[0] === '--datei' ? readFileSync(rest[1], 'utf8') : rest.join(' ')
  const db = await neueDatenbank()
  try {
    const r = await fuehreAus(db, sql)
    if (!r.spalten.length) console.log('(keine Tabelle)')
    else {
      console.log(r.spalten.join(' | '))
      for (const z of r.zeilen.slice(0, 50)) console.log(z.map(v => v instanceof Date ? v.toISOString().slice(0, 10) : String(v)).join(' | '))
      console.log(`-- ${r.zeilen.length} Zeilen`)
    }
  } catch (e) {
    console.log('FEHLER: ' + e.message)
    process.exitCode = 1
  } finally { await db.close() }
}
