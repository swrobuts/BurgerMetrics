# 4 — Validierung

> Voraussetzung: [ETL-Strecke und Reproduzierbarkeit](03-etl.md)

Der Bericht enthält rund 200 fest eingetragene Zahlen. Keine davon wird zur Laufzeit aus den CSV-Dateien berechnet — sie stehen als Konstanten im JavaScript. Damit stellt sich die Frage, die in jedem Berichtsprojekt gestellt werden muss: **Woher weiß man, dass sie stimmen?**

Der Leitsatz aus BINT E05 gilt hier wörtlich: Selbst eine Differenz von wenigen Cent würde auf ein Problem hindeuten.

---

## 4.1 Zwei getrennte Prüfstrecken

| | Prüfgegenstand | Werkzeug | Umfang | Ergebnis |
|---|---|---|---|---|
| **A** | `dataset/README.md` — die dokumentierten Muster | `dataset/verify_readme.py` | 79 Angaben | automatisiert, Exit-Code |
| **B** | `web/dashboard.html` — die Berichtswerte | Prüfberichte in `docs/` | 185 Werte | manuell, dokumentiert |

Die Trennung hat einen Grund: Strecke A prüft Aussagen, die als Text formuliert sind und sich maschinell gegen eine Berechnung halten lassen. Strecke B prüft Werte, die in einer HTML-Datei verstreut sind und deren fachliche Bedeutung erst aus dem Kontext hervorgeht.

---

## 4.2 Strecke A: automatisierte Prüfung der Dokumentation

```bash
cd dataset
python verify_readme.py     # Exit-Code 0 = alle Angaben bestätigt
```

Das Skript rechnet jede Zahl der Datensatz-Dokumentation neu und vergleicht sie mit der dort behaupteten:

```python
def pruefe(label, berechnet, readme_wert, toleranz=0.005):
    """toleranz ist relativ; 0 erzwingt exakte Gleichheit (für Zählungen)."""
    grenze = toleranz * max(abs(readme_wert), 1e-9)
    bestanden = abs(berechnet - readme_wert) <= grenze
```

Die Toleranz ist je Kennzahl gewählt: `0` für Zählungen (Zeilenzahlen müssen exakt stimmen), `0,005` für gerundete Kennzahlen, größere Werte für Angaben, die im Text ohnehin gerundet stehen.

Aktueller Stand: **79 von 79 Angaben bestätigt.**

Der Nutzen liegt weniger im einmaligen Lauf als in der Wiederholbarkeit. Ändert sich der Datenbestand, meldet das Skript jede Dokumentationsstelle, die dadurch falsch wird — statt dass sie jahrelang unbemerkt stehen bleibt.

---

## 4.3 Strecke B: Prüfung des Berichts

Der Bericht wurde zweimal vollständig geprüft. Beide Berichte sind erhalten, weil ihre Abfolge zeigt, wie Validierung tatsächlich abläuft.

**[10. April 2026](validierung-dashboard-2026-04-10.md)** — 42 geprüfte Werte. Ergebnis: 35 korrekt, 7 fehlerhaft. Die Fehler häuften sich in den Übersichtskacheln, während Jahrestabelle und Filial-Scorecard vollständig stimmten.

**[12. April 2026](validierung-dashboard-2026-04-12.md)** — 185 geprüfte Werte, systematisch je Registerkarte, mit vorangestelltem Schema-Abgleich. Ergebnis: 167 korrekt, 3 Rundungsdifferenzen, rund 15 mit Korrekturbedarf.

Dass die zweite, gründlichere Prüfung **mehr** Fehler fand, ist kein Widerspruch, sondern der Normalfall: Die erste Runde prüfte die auffälligen Werte, die zweite alle.

### Der Schema-Abgleich als erster Schritt

Der zweite Bericht beginnt nicht mit Zahlen, sondern mit einem Abgleich der Wertebereiche. Das erwies sich als die ergiebigste Prüfung überhaupt, weil es Annahmen aufdeckte, die nie explizit gemacht wurden:

| Feld | Tatsächliche Werte | Aufgedeckte Fehlannahme |
|---|---|---|
| `order_channel` | Counter, Drive-Through, Kiosk, App Order | Es gibt **keinen** Kanal „Online" und keinen „Web-Shop". Wer POS gegen Digital vergleichen will, muss die Zuordnung selbst festlegen. |
| `promo_id` | 0 = keine Promotion, 1–12 = Aktionen | `promo_id = 0` ist kein Rabatt. Wer alle Zeilen mit `promo_id IS NOT NULL` zählt, erhält 100 % statt 8,2 %. |
| `home_district` | 12 Würzburger Stadtbezirke | Kein Bezirk heißt „Innenstadt" — ein im Bericht verwendeter Name existiert in den Daten nicht. |
| `loyalty_tier` | `"None"` (15.339), Bronze, Silver, Gold | `"None"` ist eine Zeichenkette, kein fehlender Wert. |
| `gender` | Male 48,5 %, Female 47,8 %, Non-Binary 3,8 % | Der Bericht behauptete 55 % männlich. |

Die Lehre daraus: **Wertebereiche prüfen, bevor man Kennzahlen prüft.** Ein Wert kann rechnerisch korrekt aus einer falschen Grundgesamtheit stammen.

---

## 4.4 Der zweite Rechenweg

Die wirksamste Einzelmaßnahme gegen falsche Kennzahlen ist, sie auf einem unabhängigen Weg zu wiederholen. BINT E05 und die Prüfungsordnung der Fallstudie verlangen das ausdrücklich für mindestens drei zentrale Kennzahlen.

Am Beispiel des Gesamtumsatzes, drei Wege:

```sql
-- Weg 1: SQL auf der Faktentabelle
SELECT ROUND(SUM(net_total), 2) FROM fact_orders;
```

```sql
-- Weg 2: SQL auf der One Big Table (andere Datei, andere Struktur)
SELECT ROUND(SUM(net_total), 2) FROM obt_orders;
```

```python
# Weg 3: pandas, gegenprüfend über gross_total minus discount_amount
fo = pd.read_csv("fact_orders.csv", encoding="utf-8-sig")
round((fo.gross_total - fo.discount_amount).sum(), 2)
```

Alle drei ergeben **14.522.378,70 €**. Der dritte Weg ist der wertvollste, weil er nicht dieselbe Spalte noch einmal summiert, sondern sie aus ihren Bestandteilen rekonstruiert. Er würde auch dann anschlagen, wenn `net_total` selbst fehlerhaft befüllt wäre.

---

## 4.5 Wo Prüfung selbst fehlschlägt

Bei der Überarbeitung im August 2026 unterliefen der Prüfung zwei Fehler, die typisch genug sind, um sie festzuhalten.

**Ein Textmuster traf zu viel.** Die Warenkorbanalyse wählte Produkte über Namensmuster aus. `LIKE '%Cola%'` trifft auch *Milkshake **Chocolate***, *Hot **Chocolate*** und *Cookie **Chocolate***; `LIKE '%BBQ%'` trifft neben der *BBQ Sauce* auch den Burger *BBQ Smokehouse*. Die daraus berechnete Konfidenz war um mehrere Prozentpunkte verschoben — plausibel genug, um nicht aufzufallen.

**Eine Kategorie war falsch abgegrenzt.** Für die Saisonalität der Heißgetränke griff ein Muster auf `Tea` und `Chocolate` zu und sammelte damit *Ice Tea* (ein Kaltgetränk) sowie sämtliche Schokoladen-Desserts ein. Das Ergebnis kehrte den Befund um: Der Winterpeak bei Heißgetränken schien widerlegt, obwohl er mit 114,1 gegenüber 74,5 Stück pro Tag deutlich vorhanden ist.

Beide Fehler verschwanden, sobald statt Namensmustern **explizite Produktlisten und die Spalte `subcategory`** verwendet wurden. Die Regel dahinter: Ein Filter über Textmuster ist eine Annahme über die Benennung, keine Auswahl über die Fachlogik. Wo eine Kategoriespalte existiert, ist sie vorzuziehen.

Der Fallstrick ist in [`dataset/README.md`](../dataset/README.md) dokumentiert, weil Studierende bei derselben Aufgabe darauf stoßen werden.

---

## 4.6 Was nicht geprüft ist

Ehrlichkeitshalber gehört dazu, was außerhalb der Prüfstrecken liegt:

- **Die Interpretationstexte im Bericht.** Geprüft sind die Zahlen, nicht die Sätze, die sie deuten. Eine korrekte Zahl kann falsch interpretiert sein.
- **Die Diagramm-Datenreihen.** Geprüft wurden Kennzahlen und Tabellenwerte. Ob jede einzelne Stützstelle einer Zeitreihe stimmt, ist nicht durchgängig belegt.
- **Die Anwendungen POS und Shop.** Sie erzeugen Beispieldaten zur Veranschaulichung; diese sind nicht gegen den CSV-Bestand abgeglichen.

---

**Weiter:** [Anwendungsarchitektur](05-anwendungen.md)
