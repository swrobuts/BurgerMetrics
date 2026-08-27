/*
 * konfiguration.js — die einzige Stelle mit einer Adresse.
 *
 * Der anon-Schluessel ist bewusst oeffentlich: Er erlaubt ausschliesslich
 * Lesezugriff auf die Sichten der Semantikschicht (Row Level Security,
 * SELECT-Policy). Rohtabellen, Schreibrechte und der service_role-Schluessel
 * sind darueber nicht erreichbar.
 */
export const QUELLE = {
  art: 'postgrest',
  url: 'https://supabase.butscher.cloud',
  schema: 'burgermetrics',
  schluessel: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoiYW5vbiIsImlzcyI6InN1cGFiYXNlIiwiaWF0IjoxNzYyNjc5NTM1LCJleHAiOjIwNzgwMzk1MzV9.Fv3soDCs_GrM9MA-4Goq1ANCoJ7KzVpuJ9l9z7bQEwk',
};
