// screenshots.mjs — nimmt die Bildschirmfotos fuer das BI-Foliendeck auf.
//
// Warum ein Skript und nicht Bilder von Hand: Ein Screenshot altert mit der
// Anwendung. Wer die Aufnahme als Code hat, nimmt sie nach jeder Aenderung neu
// auf, in derselben Groesse, mit demselben Ausschnitt. Die Bilder liegen dann
// reproduzierbar in bilder/ und nicht in einem Downloads-Ordner.
//
// Aufruf (die Anwendung muss unter BASIS erreichbar sein):
//   python3 -m http.server 8899 --directory ../web
//   CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" node screenshots.mjs
//
// Voraussetzungen: playwright, ein Chrome/Chromium. Kein Internet noetig.
import { chromium } from "playwright";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const BASIS = process.env.BASIS || "http://localhost:8899";
const ZIEL = path.join(__dirname, "bilder");
const BREITE = 1440, HOEHE = 900;

// name    Dateiname ohne Endung
// seite   HTML-Datei
// tab     Wert des data-tab-Attributs im Dashboard
// unter   Beschriftung des Unterreiters, per Text angeklickt
// wahl    CSS-Auswahl des aufzunehmenden Bereichs; ohne sie der Sichtbereich
// zu      zusaetzliche Hoehe des Sichtbereichs, falls der Ausschnitt hoeher ist
// vor     JavaScript, das vor der Aufnahme in der Seite laeuft
// warte   zusaetzliche Wartezeit in Millisekunden
const OHNE_LADESCHIRM =
  "const l = document.getElementById('pageLoader'); if (l) l.remove();";
// Die Datensicht der Kasse zeigt erst etwas, wenn etwas gebucht ist: Drei
// Produkte antippen, dann umschalten. Der Wechsel ist animiert — daher die
// zusaetzliche Wartezeit.
const KASSE_DATENSICHT = OHNE_LADESCHIRM + `
  const c = [...document.querySelectorAll('.product-card')];
  [0, 2, 4].forEach(i => c[i] && c[i].click());
  const tg = document.querySelector('.pos-data-toggle'); if (tg) tg.click();`;

// Der Deutungsblock unter jedem Diagramm ist auf einer Folie zu klein zum Lesen
// und wuerde die Aufnahme unnoetig hoch machen. Auf der Folie steht die Deutung
// stattdessen in der Sprechblase daneben.
const OHNE_DEUTUNG =
  "document.querySelectorAll('.interpretation').forEach(e => e.remove());";

// Der Datenmodus des Shops legt ein endlos animiertes Scanline-Overlay ueber
// die Seite (body.data-mode::after). Fuer die Aufnahme wird es stillgelegt —
// bei 1,5 Prozent Deckung ist es im Bild ohnehin unsichtbar, aber die
// Endlosanimation kann den Screenshot-Pfad zum weissen Bild machen.
const OHNE_ANIMATION = `
  const st = document.createElement('style');
  st.textContent = 'body.data-mode::after{display:none!important}'
    + '*{animation:none!important;transition:none!important}';
  document.head.appendChild(st);`;
const SHOP_DATEN = OHNE_LADESCHIRM + OHNE_ANIMATION + "toggleDataMode();";

const AUFNAHMEN = [
  { name: "01_start",          seite: "index.html", jpeg: true },
  { name: "02_shop",           seite: "shop.html", vor: OHNE_LADESCHIRM,
    warte: 1400, jpeg: true },
  { name: "02b_shop_daten",    seite: "shop.html", vor: SHOP_DATEN,
    warte: 2200, jpeg: true },
  { name: "03_pos",            seite: "pos.html", vor: OHNE_LADESCHIRM,
    warte: 900, jpeg: true },
  { name: "03b_pos_daten",     seite: "pos.html", vor: KASSE_DATENSICHT,
    warte: 2400, jpeg: true },
  { name: "04_dash_kpi",       seite: "dashboard.html", tab: "uebersicht",  wahl: ".kpi-row" },
  { name: "05_dash_verlauf",   seite: "dashboard.html", tab: "uebersicht",
    wahl: ".chart-card", vor: OHNE_DEUTUNG },
  { name: "06_dash_regeln",    seite: "dashboard.html", tab: "datamining",
    unter: "Assoziationsregeln", wahl: ".chart-card", vor: OHNE_DEUTUNG },
  { name: "07_dash_rfm",       seite: "dashboard.html", tab: "datamining",
    unter: "RFM-Segmentierung", wahl: ".chart-card", vor: OHNE_DEUTUNG },
  { name: "08_dash_simulation", seite: "dashboard.html", tab: "simulation",
    unter: "Preissimulation", wahl: ".chart-card", vor: OHNE_DEUTUNG },
  { name: "09_dash_summary",   seite: "dashboard.html", tab: "summary", zu: 260 },
  { name: "10_dash_filialen",  seite: "dashboard.html", tab: "filialen",
    wahl: ".chart-card", vor: OHNE_DEUTUNG },
  { name: "11_dash_trends",    seite: "dashboard.html", tab: "trends",
    wahl: ".chart-card", vor: OHNE_DEUTUNG },
];

fs.mkdirSync(ZIEL, { recursive: true });
const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH });
const ctx = await browser.newContext({
  viewport: { width: BREITE, height: HOEHE },
  deviceScaleFactor: 2,                       // scharf genug fuer die Projektion
});
const page = await ctx.newPage();

let ok = 0, fehler = 0;
for (const a of AUFNAHMEN) {
  try {
    if (a.zu) await page.setViewportSize({ width: BREITE, height: HOEHE + a.zu });
    else await page.setViewportSize({ width: BREITE, height: HOEHE });
    await page.goto(`${BASIS}/${a.seite}`, { waitUntil: "networkidle" });
    if (a.tab) {
      await page.click(`[data-tab="${a.tab}"]`);
      await page.waitForTimeout(400);
    }
    if (a.unter) {
      // Unterreiter tragen kein eigenes Attribut — ueber die Beschriftung finden.
      await page.evaluate((t) => {
        const e = [...document.querySelectorAll("*")]
          .find(x => x.children.length === 0 && x.textContent.trim() === t);
        if (e) e.click();
      }, a.unter);
      await page.waitForTimeout(400);
    }
    if (a.vor) await page.evaluate(a.vor);
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(700 + (a.warte || 0));   // Chart.js zeichnet verzoegert
    // Fotolastige Seiten als JPEG: Der Kassenbildschirm kostet als PNG 1,8 MB
    // und als JPEG rund ein Sechstel davon, bei der Projektion ununterscheidbar.
    // Diagramme und Flaechenfarben bleiben PNG — dort erzeugt JPEG Kanten.
    const datei = path.join(ZIEL, a.name + (a.jpeg ? ".jpg" : ".png"));
    const opt = a.jpeg ? { path: datei, type: "jpeg", quality: 88 } : { path: datei };
    if (a.wahl) {
      // Nur der sichtbare Treffer zaehlt: Die Reiter des Dashboards bleiben im
      // DOM und sind nur ausgeblendet — page.$() erwischt sonst den ersten,
      // versteckten, und der Screenshot laeuft in einen Zeitablauf.
      const el = page.locator(`${a.wahl}:visible`).first();
      if (!await el.count()) throw new Error(`Auswahl ${a.wahl} nicht sichtbar`);
      await el.screenshot(opt);
    } else {
      await page.screenshot(opt);
    }
    const kb = Math.round(fs.statSync(datei).size / 1024);
    console.log(`  OK      ${a.name.padEnd(20)} ${path.basename(datei).padEnd(24)} ${kb} KB`);
    ok++;
  } catch (e) {
    console.log(`  FEHLER  ${a.name.padEnd(20)} ${String(e).split("\n")[0].slice(0, 90)}`);
    fehler++;
  }
}
await browser.close();
console.log(`\n==> ${ok} aufgenommen, ${fehler} fehlgeschlagen`);
process.exit(fehler === 0 ? 0 : 1);
