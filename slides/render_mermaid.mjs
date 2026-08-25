// render_mermaid.mjs — rendert die Mermaid-Quellen aus diagramme/ als PNG.
//
// Warum ueber einen Browser und nicht ueber einen SVG-Rasterer:
// Mermaid setzt Beschriftungen in <foreignObject>, also HTML innerhalb von SVG.
// Das ist kein wohlgeformtes XML; cairosvg und verwandte Werkzeuge brechen daran
// ab ("mismatched tag"). Die Mermaid-Option flowchart.htmlLabels=false greift in
// Version 11 nicht mehr. Ein Browser rendert foreignObject nativ — deshalb Chrome.
//
// Aufruf:
//   node render_mermaid.mjs                    # diagramme/*.mmd -> diagramme/*.png
//   CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" node render_mermaid.mjs
//
// Voraussetzungen: playwright (npm i playwright), ein Chrome/Chromium, Internet
// fuer mermaid.js vom CDN.
import { chromium } from "playwright";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DIR = process.argv[2] || path.join(__dirname, "diagramme");

// THWS-Farben aus assets/tokens.json des Skills thws-slides.
// Grau als Normalfall, Blau nur als Akzent — siehe references/diagramme.md.
const THEME = `%%{init: {'theme':'base','themeVariables':{
'primaryColor':'#FFFFFF','primaryBorderColor':'#9DA8AE','primaryTextColor':'#404040',
'lineColor':'#9DA8AE','secondaryColor':'#F7F5EF','tertiaryColor':'#FFFFFF',
'fontFamily':'Segoe UI, Helvetica, Arial','fontSize':'15px',
'clusterBkg':'#FCFBF8','clusterBorder':'#C9C3B4',
'edgeLabelBackground':'#FFFFFF'}}}%%
`;

const dateien = fs.readdirSync(DIR).filter(f => f.endsWith(".mmd")).sort();
if (!dateien.length) { console.error(`Keine .mmd-Dateien in ${DIR}`); process.exit(1); }

const browser = await chromium.launch({ executablePath: process.env.CHROME_PATH });
const ctx = await browser.newContext({ deviceScaleFactor: 3 });   // scharf genug fuer die Projektion
const page = await ctx.newPage();

await page.setContent(`<!doctype html><html><head><meta charset="utf-8">
<script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
<style>body{margin:0;background:#FFFFFF;font-family:'Segoe UI',Helvetica,Arial}
#ziel{display:inline-block;padding:6px;background:#FFFFFF}</style>
</head><body><div id="ziel"></div></body></html>`, { waitUntil: "networkidle" });

if (!await page.evaluate(() => typeof window.mermaid !== "undefined")) {
  console.error("FEHLER: mermaid.js nicht geladen — Internetverbindung pruefen.");
  await browser.close(); process.exit(1);
}
await page.evaluate(() => window.mermaid.initialize({ startOnLoad: false, securityLevel: "loose" }));

let ok = 0, fehler = 0;
for (const f of dateien) {
  const name = path.basename(f, ".mmd");
  const code = THEME + fs.readFileSync(path.join(DIR, f), "utf-8");
  try {
    await page.evaluate(async (src) => {
      const { svg } = await window.mermaid.render("g" + Math.floor(performance.now() * 1000), src);
      document.getElementById("ziel").innerHTML = svg;
      const s = document.querySelector("#ziel svg");
      // Mermaid setzt width:100%; fuer den Screenshot die echte Groesse aus der viewBox
      s.removeAttribute("width"); s.removeAttribute("style");
      const vb = s.getAttribute("viewBox").split(/\s+/).map(Number);
      s.setAttribute("width", vb[2]); s.setAttribute("height", vb[3]);
    }, code);
    await page.waitForTimeout(140);
    const el = await page.$("#ziel");
    await el.screenshot({ path: path.join(DIR, name + ".png") });
    const box = await el.boundingBox();
    console.log(`  OK      ${name.padEnd(28)} ${Math.round(box.width)} x ${Math.round(box.height)} pt`);
    ok++;
  } catch (e) {
    console.log(`  FEHLER  ${name.padEnd(28)} ${String(e).split("\n")[0].slice(0, 90)}`);
    fehler++;
  }
}
await browser.close();
console.log(`\n==> ${ok} gerendert, ${fehler} fehlgeschlagen`);
process.exit(fehler === 0 ? 0 : 1);
