import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { neueDatenbank, SAAT } from './sql.mjs'
import { neuSaeen, warteschlange } from '../assets/datenbank.js'
import { gleich } from '../assets/sqlpruefung.js'

const lies = p => readFileSync(new URL('../' + p, import.meta.url), 'utf8')
const tabelle = rows => ({ fields: rows[0].map((_, i) => ({ name: 's' + i })), rows })

test('SQL-Vergleich erhält Spaltengrenzen und NULL', () => {
  assert.equal(gleich(tabelle([['ab', 'c']]), tabelle([['a', 'bc']])), false)
  assert.equal(gleich(tabelle([['a\u0001b', 'c']]), tabelle([['a', 'b\u0001c']])), false)
  assert.equal(gleich(tabelle([[null]]), tabelle([['␀']])), false)
  assert.equal(gleich(tabelle([[{ a: 1 }]]), tabelle([[{ a: 2 }]])), false)
  assert.equal(gleich(tabelle([[new Date('2025-01-01T01:00Z')]]), tabelle([[new Date('2025-01-01T02:00Z')]])), false)
})

test('SQL-Vergleich berücksichtigt Sortierung und doppelte Zeilen', () => {
  const a = tabelle([[1], [2], [1]])
  const b = tabelle([['1.0000'], ['1'], [2]])
  assert.equal(gleich(a, b), true)
  assert.equal(gleich(a, b, true), false)
  assert.equal(gleich(a, tabelle([[1], [2], [2]])), false)
})

test('Zurücksetzen entfernt auch Schema-Namen mit Anführungszeichen', async () => {
  const db = await neueDatenbank()
  try {
    await db.exec('CREATE SCHEMA "Probe""Schema"; CREATE TABLE "Probe""Schema".t(x int);')
    await neuSaeen(db, SAAT, lies)
    assert.equal((await db.query('SELECT count(*) AS n FROM fact_orders')).rows[0].n, 19)
    assert.equal((await db.query("SELECT count(*) AS n FROM pg_namespace WHERE nspname=$1", ['Probe"Schema'])).rows[0].n, 0)
  } finally { await db.close() }
})

test('Zwei vollständige Übungsprüfungen und Reset überschneiden sich nicht', async () => {
  const db = await neueDatenbank()
  const auftrag = warteschlange()
  const pruefen = n => auftrag(async () => {
    await neuSaeen(db, SAAT, lies)
    await db.exec(`CREATE TABLE probe AS SELECT ${n} AS x`)
    // Versetzte Fertigstellung provozierte vorher den Verlust der Tabelle.
    await new Promise(resolve => setTimeout(resolve, n === 1 ? 20 : 0))
    const ist = (await db.query('SELECT x FROM probe')).rows[0].x
    await neuSaeen(db, SAAT, lies)
    return ist
  })
  try {
    assert.deepEqual(await Promise.all([pruefen(1), pruefen(2)]), [1, 2])
    await assert.rejects(auftrag(() => db.exec('SELECT * FROM fehlt')), /does not exist/)
    await auftrag(() => neuSaeen(db, SAAT, lies))
    assert.equal((await auftrag(() => db.query('SELECT count(*) AS n FROM fact_orders'))).rows[0].n, 19)
  } finally { await db.close() }
})
