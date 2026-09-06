/*
 * konfiguration.js — die einzige Stelle mit einer Adresse.
 *
 * Zwei Schemata, eine Instanz:
 *   schema      burgermetrics — das Auswertungsmodell (Galaxy-Schema und
 *                Semantikschicht). Das Dashboard liest hier.
 *   schemaWawi  wawi — das operative Warenwirtschaftsmodell (3NF). Kasse und
 *                Shop lesen hier ihren Artikelstamm und schreiben hierher
 *                ihre Bestellungen. Der Weg von wawi nach burgermetrics ist
 *                der ETL-Schritt (db/aufbau/0019).
 *
 * Der anon-Schluessel ist bewusst oeffentlich: Er erlaubt Lesezugriff auf
 * beide Schemata (Row Level Security, SELECT-Policy) und genau einen
 * Schreibweg — die Funktion wawi.bestellung_anlegen(), die ihre Eingaben
 * prueft und die Preise aus dem Stamm nimmt. Rohtabellen sind nicht
 * beschreibbar, der service_role-Schluessel ist darueber nicht erreichbar.
 */
export const QUELLE = {
  art: 'postgrest',
  url: 'https://supabase.butscher.cloud',
  schema: 'burgermetrics',
  schemaWawi: 'wawi',
  schluessel: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlzcyI6InN1cGFiYXNlIiwiaWF0IjoxNzYyNjc5NTM1LCJleHAiOjIwNzgwMzk1MzV9.Fv3soDCs_GrM9MA-4Goq1ANCoJ7KzVpuJ9l9z7bQEwk',
};
