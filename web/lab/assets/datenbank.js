/** Gemeinsame PGlite-Helfer für Browser und lokale Lab-Prüfung. */

/** Ganze Aufträge serialisieren, nicht nur die einzelnen SQL-Anweisungen. */
export function warteschlange () {
  let ende = Promise.resolve()
  return (auftrag) => {
    const lauf = ende.then(auftrag)
    // Ein fehlerhafter Auftrag darf spätere Abfragen nicht blockieren.
    ende = lauf.catch(() => {})
    return lauf
  }
}

/** Auch selbst angelegte Schemata mit Sonderzeichen sicher entfernen. */
export async function neuSaeen (db, saat, lies) {
  const schemata = await db.query(
    "SELECT nspname FROM pg_namespace WHERE nspname NOT LIKE 'pg\\_%' AND nspname <> 'information_schema'")
  for (const z of schemata.rows) {
    await db.exec(`DROP SCHEMA IF EXISTS "${z.nspname.replaceAll('"', '""')}" CASCADE`)
  }
  await db.exec('CREATE SCHEMA public;')
  for (const [vorspann, datei] of saat) {
    await db.exec(vorspann)
    await db.exec(await lies(datei))
  }
  await db.exec('SET search_path TO wawi, burgermetrics')
}
