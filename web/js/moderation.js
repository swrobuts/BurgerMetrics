/*
 * moderation.js — die Logik hinter dem Bereich „Rezensionen“ der Kasse, ohne DOM.
 * So lässt sie sich mit `node --test` prüfen, und pos.html kümmert sich nur um
 * die Darstellung.
 */

/** Die sechs Fragen an Jev: Spalte in v_moderation und Name für die Balken. */
export const FRAGEN = [
  ['p_gesundheitsrisiko', 'Gesundheitsrisiko'],
  ['p_beleidigung', 'Beleidigung'],
  ['p_personenbezug', 'Personenbezug'],
  ['p_werbung', 'Werbung'],
  ['p_anweisung', 'Anweisung'],
  ['p_themenbezug', 'Themenbezug'],
];

/** Was ein Grund bedeutet, in einem Satz für die Moderation. */
export const GRUND_ERKLAERUNG = {
  'Kontaktdaten oder Link': 'Der Text enthält eine E-Mail-Adresse, Telefonnummer oder einen Link.',
  'Gesundheitsrisiko': 'Der Text beschreibt eine mögliche Gefahr durch Essen oder Getränke; ein QS-Fall ist angelegt.',
  'Beleidigung': 'Jev hält eine Beleidigung oder Drohung für wahrscheinlich.',
  'Personenbezug': 'Jev hält es für wahrscheinlich, dass eine Person erkennbar ist.',
  'Werbung': 'Jev hält Werbung oder eine Aufforderung zur Kontaktaufnahme für wahrscheinlich.',
  'Anweisung': 'Der Text versucht wahrscheinlich, die Prüfung zu steuern.',
  'unsicher': 'Jev ist sich nicht sicher, oder der Text passt nicht zu BurgerMetrics.',
  'Prüfung nicht möglich': 'Jev war dreimal nicht erreichbar.',
  'Tageslimit erreicht': 'Das Tageslimit für Anfragen an Jev war erreicht.',
};

/** Ein Grund mit seiner Erklärung; unbekannte Gründe bleiben, wie sie sind. */
export function grundText(grund) {
  return GRUND_ERKLAERUNG[grund] ? `${grund}: ${GRUND_ERKLAERUNG[grund]}` : String(grund);
}

/** Das höchste Risiko einer Zeile: Gesundheit, Verstöße und fehlender Themenbezug; ohne Prüfung 0. */
export function risikoWert(zeile) {
  if (zeile.p_themenbezug === null || zeile.p_themenbezug === undefined) return 0;
  const werte = [zeile.p_gesundheitsrisiko, zeile.p_beleidigung, zeile.p_personenbezug,
                 zeile.p_werbung, zeile.p_anweisung].map(w => Number(w) || 0);
  werte.push(1 - Number(zeile.p_themenbezug));
  return Math.max(...werte);
}

/** QS-Fälle zuerst, dann höchstes Risiko, bei gleichem Risiko die ältere Rezension zuerst. */
export function nachRisiko(zeilen) {
  return [...zeilen].sort((a, b) => {
    if (Boolean(a.qs_fall) !== Boolean(b.qs_fall)) return a.qs_fall ? -1 : 1;
    if (risikoWert(a) !== risikoWert(b)) return risikoWert(b) - risikoWert(a);
    return Date.parse(a.erstellt_am) - Date.parse(b.erstellt_am);
  });
}

/** Die sechs Wahrscheinlichkeiten in ganzen Prozent; ohne Prüfung keine. */
export function balken(zeile) {
  if (zeile.p_themenbezug === null || zeile.p_themenbezug === undefined) return [];
  return FRAGEN.map(([feld, name]) => ({ name, prozent: Math.round((Number(zeile[feld]) || 0) * 100) }));
}

/** Die Statuszeile aus v_pruefdienst_stand; warnt, wenn eine Rezension fünf Minuten oder länger wartet. */
export function standText(stand) {
  if (!stand) return { text: 'Stand des Prüfdienstes unbekannt.', warnung: true };
  const text = `${stand.offen} offen · ${stand.zurueckgehalten} zurückgehalten · ${stand.qs_offen} QS-Fälle`;
  const minuten = Number(stand.aelteste_offene_min) || 0;
  if (stand.offen > 0 && minuten >= 5) {
    return { text: `${text} · Die älteste offene Rezension wartet seit ${minuten} Minuten; läuft der Prüfdienst?`,
             warnung: true };
  }
  return { text, warnung: false };
}

/** Zahl am Knopf: zurückgehaltene Rezensionen plus offene QS-Fälle. */
export function zahlAmKnopf(stand) {
  if (!stand) return 0;
  return (Number(stand.zurueckgehalten) || 0) + (Number(stand.qs_offen) || 0);
}

/** Gilt eine gespeicherte Anmeldung noch? */
export function sitzungGueltig(sitzung, jetzt = Date.now()) {
  return Boolean(sitzung && sitzung.token && jetzt < Number(sitzung.gueltigBis));
}

/** Tag, Monat und Uhrzeit in Berlin: „01.10., 14:05“. */
export function zeitText(iso) {
  if (!iso) return '';
  return new Date(iso).toLocaleString('de-DE', { timeZone: 'Europe/Berlin', day: '2-digit',
                                                 month: '2-digit', hour: '2-digit', minute: '2-digit' });
}
