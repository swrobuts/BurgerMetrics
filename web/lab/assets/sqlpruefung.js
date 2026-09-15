/** Derselbe Ergebnisvergleich im Browser und in tools/verify.mjs. */
export function gleich (a, b, sortiert = false) {
  const wert = v => v == null ? null
    : v instanceof Date ? v.toISOString()
      : typeof v === 'number' || /^-?\d+(\.\d+)?$/.test(String(v)) ? Number(v).toFixed(4)
        : typeof v === 'object' ? v : String(v).trim()
  const norm = r => r.rows.map(z => JSON.stringify(
    (Array.isArray(z) ? z : r.fields.map(f => z[f.name])).map(wert)))
  const x = norm(a); const y = norm(b)
  if (!sortiert) { x.sort(); y.sort() }
  return a.fields.length === b.fields.length && x.length === y.length && x.every((v, i) => v === y[i])
}
