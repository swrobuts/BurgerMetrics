# 8 — Entscheidungsjournal

Die vorangegangenen Kapitel beschreiben, wie das Projekt aufgebaut ist. Dieses Kapitel beschreibt, **warum es so und nicht anders aufgebaut ist**. Jeder Eintrag nennt die Ausgangsfrage, die erwogenen Alternativen, die getroffene Wahl und deren Preis.

Ein solcher Preis ist immer vorhanden. Eine Entscheidung ohne Nachteil war keine Entscheidung, sondern eine Selbstverständlichkeit.

---

## E1 — Synthetische statt realer Daten {#e1}

**Frage:** Woher kommen die Daten?

| Alternative | Bewertung |
|---|---|
| Reale Unternehmensdaten | Nicht veröffentlichbar (Datenschutz, Geschäftsgeheimnis), nicht als Ganzes auslieferbar |
| Öffentlicher Datensatz (Kaggle o. ä.) | Verfügbar, aber ohne Kontrolle über die enthaltenen Muster; oft ohne operatives Gegenstück |
| **Synthetischer Datensatz** | **gewählt** |

**Begründung:** Nur bei synthetischen Daten lässt sich steuern, welche Muster enthalten sind — und das ist für die Lehre die eigentliche Entwurfsarbeit. Es können gezielt Muster angelegt werden, die sich bestätigen lassen, solche, die Sorgfalt verlangen, und Scheinmuster, die einer Prüfung nicht standhalten ([Kapitel 1.4](01-fachkonzept.md#14-anforderungen-an-die-muster-in-den-daten)).

**Preis:** Der Datensatz ist sauberer als die Wirklichkeit. Es fehlen Erfassungsfehler, Dubletten, verspätete Buchungen und Formatbrüche — genau die Probleme, an denen sich Datenqualitätsarbeit zeigen ließe. Wer das üben will, braucht einen zusätzlichen, absichtlich verschmutzten Auszug.

---

## E2 — Galaxy-Schema statt Stern-Schema {#e2}

**Frage:** Eine Faktentabelle oder zwei?

| Alternative | Bewertung |
|---|---|
| Eine Faktentabelle auf Positionsebene | Bestellmerkmale (Rabatt, Dauer, Bewertung) müssten je Position wiederholt werden; jede Summe darüber wäre falsch |
| Eine Faktentabelle auf Bestellebene | Produktanalysen wären unmöglich — genau die Warenkorbanalyse fiele weg |
| **Zwei Faktentabellen, geteilte Dimensionen** | **gewählt** |

**Begründung:** Der Sachverhalt wird tatsächlich auf zwei Ebenen gemessen. Eine Bestellung hat einen Rabatt, eine Wartezeit und eine Bewertung; eine Position hat eine Menge und einen Einzelpreis. Beides in eine Tabelle zu zwingen, würde eine der beiden Ebenen beschädigen.

**Preis:** Das Modell ist kein Stern-Schema mehr, und der Fan Trap wird zur ständigen Fehlerquelle. Wer die Tabellen verbindet und Bestellwerte summiert, erhält das 4,88-fache des richtigen Werts. Dieser Preis wird in Kauf genommen, weil der Fehler selbst Lerngegenstand ist.

---

## E3 — Nur der Verkaufspfad im analytischen Modell {#e3}

**Frage:** Welche der 26 operativen Tabellen wandern ins analytische Modell?

**Gewählt:** Verkauf, Stammdaten und externe Daten. Nicht übernommen: Einkauf, Lieferanten, Lagerverwaltung, Preishistorie, Schichtplan, Rechnungswesen.

**Begründung:** Die Leitfragen aus [Kapitel 1.3](01-fachkonzept.md#13-leitfragen-an-den-datenbestand) betreffen alle den Absatz. Ein vollständiger Nachbau des ERP-Modells hätte den Datenbestand vervielfacht, ohne eine der Fragen zusätzlich zu beantworten.

**Preis, und was daraus wurde:** `dim_supplier` verlor durch diese Auswahl seinen Anschluss und wurde zur Orphan Dimension. Das war zunächst eine Nebenwirkung, keine Absicht. Statt die Tabelle zu entfernen, wurde sie behalten und als Lerngegenstand ausgewiesen — solche Reste finden sich in gewachsenen Auswertungssystemen regelmäßig, und der Weg zurück ins operative Modell ist eine gute Übung.

Diese Umdeutung ist ehrlich zu benennen: Aus einem Nebenprodukt wurde nachträglich ein Merkmal. Das ist vertretbar, solange es dokumentiert ist — und wäre es nicht, wenn man es als ursprüngliche Absicht darstellte.

---

## E4 — Die One Big Table zusätzlich ausliefern {#e4}

**Frage:** Reicht das Galaxy-Schema, oder braucht es eine vorverknüpfte Tabelle?

| Alternative | Bewertung |
|---|---|
| Nur Galaxy-Schema | Sauber, aber Joins sind Voraussetzung für jede erste Auswertung |
| Nur OBT | Einfacher Einstieg, aber das Modellierungsthema entfiele vollständig |
| **Beides** | **gewählt** |

**Begründung:** Die beiden Formen nebeneinander machen den Unterschied erst erfahrbar. Der Laufzeit- und Wartbarkeitsvergleich ist Block E des Übungsblatts; ohne beide Varianten gäbe es nichts zu vergleichen. Zusätzlich senkt die OBT die Einstiegshürde für Werkzeuge, die keine Joins beherrschen.

**Preis:** 176 MB zusätzlich, also mehr als das gesamte Schema. Und eine dauerhafte Konsistenzpflicht: Ändert sich eine Dimension, muss die OBT neu erzeugt werden, sonst driften die beiden Darstellungen auseinander. Genau dieses Risiko hat sich verwirklicht — siehe E8.

---

## E5 — Berichtswerte fest eintragen statt zur Laufzeit berechnen {#e5}

**Frage:** Soll der Bericht die CSV-Dateien lesen?

**Gewählt:** Nein. Alle Werte stehen als Konstanten im JavaScript.

**Begründung:** Ein Browser kann 176 MB CSV nicht sinnvoll verarbeiten; ohne Server scheitert das Laden lokaler Dateien ohnehin an den Sicherheitsregeln. Die Anforderung „läuft per Doppelklick" hätte sich anders nicht halten lassen.

**Preis:** Der Bericht ist eine Momentaufnahme der Daten, kein Fenster auf sie. Er kann von den Daten abweichen, ohne dass es auffällt — und genau das ist eingetreten: Die Prüfung vom 12. April 2026 fand rund 15 korrekturbedürftige Werte. Die gesamte Prüfstrecke aus [Kapitel 4](04-validierung.md) existiert nur, um diesen Preis zu bezahlen.

**Rückblickende Bewertung:** Die Entscheidung war unter der Anforderung „ohne Server lauffähig" richtig. Wäre ein Server zulässig, wäre eine berechnende Variante vorzuziehen — sie würde die Prüfstrecke für die Berichtswerte überflüssig machen.

---

## E6 — Eine Datei je Anwendung {#e6}

**Frage:** Modularisieren oder alles in eine Datei?

**Gewählt:** Je Anwendung eine HTML-Datei mit eingebettetem CSS und JavaScript, bis zu 5.574 Zeilen.

**Begründung:** Lesbarkeit für Studierende. Eine Datei öffnen und alles sehen, ohne Bundler, ohne Modulauflösung. Dasselbe Prinzip verwenden die DABA-Kurseinheiten.

**Preis:** Keine Wiederverwendung. Das Farbschema ist viermal definiert; eine Änderung an den Grundfarben ist an vier Stellen zu machen. Bei einer Anwendung, die weiterentwickelt werden soll, wäre das nicht vertretbar.

---

## E7 — Git LFS für den Datenbestand {#e7}

**Frage:** Wie kommen 311 MB CSV in die Versionsverwaltung?

| Alternative | Bewertung |
|---|---|
| Direkt in Git | Jede Version vollständig gespeichert; das Repository wäre nach wenigen Änderungen unbenutzbar |
| Daten außerhalb, nur Verweis | Datenbestand und Code könnten auseinanderlaufen |
| **Git LFS** | **gewählt** |

**Begründung:** LFS hält die Daten versioniert, ohne die Historie zu belasten. Im Repository liegt je Datei ein Verweis von rund 130 Byte.

**Preis:** Eine zusätzliche Voraussetzung auf jedem Rechner. Fehlt `git-lfs`, erhält man Verweisdateien statt Daten — oder schreibt beim Commit 311 MB Rohdaten in die Historie. Beides fällt nicht sofort auf. Der Einrichtungsschritt steht deshalb in [Kapitel 6.5](06-betrieb.md#65-arbeit-am-repository).

---

## E8 — Nachträgliche Korrekturen (August 2026) {#e8}

Vier Befunde aus der Überarbeitung, die dokumentiert bleiben, weil sie zeigen, wie Projekte auseinanderdriften.

**Die Ladestrecke erzeugte nicht mehr das ausgelieferte Artefakt.** `generate_obt.py` und `obt_orders.csv` waren auseinandergelaufen. Der aufschlussreichste der drei Fehler war eine Bedingung, die nie zutraf: `if "date_id" in dim_weather.columns` — die Tabelle ist über `date` verschlüsselt. Der Wetter-Join wurde stillschweigend übersprungen, ohne Fehlermeldung. **Regel daraus:** Eine Transformation, deren Ergebnis nie gegen ein erwartetes Artefakt geprüft wird, driftet unbemerkt. Seit der Überarbeitung ist die Byte-Identität nachgewiesen.

**Die Datensatz-Dokumentation beschrieb einen älteren Datenstand.** Sie nannte das Kalenderjahr 2024, 106.720 Bestellungen und 12.000 Kunden — tatsächlich sind es 2017–2026, 754.513 Bestellungen und 25.000 Kunden. Zusätzlich enthielt sie drei Muster, die in den Daten nicht nachweisbar sind, darunter „Filialcluster mit unterschiedlichen Kundenprofilen". **Antwort darauf:** `verify_readme.py` prüft seither 79 Angaben maschinell.

**`*.md` stand in der `.gitignore`.** Sämtliche Dokumentation war von der Versionsverwaltung ausgeschlossen. Übungsblatt, ERP-Modell und Datensatz-Dokumentation existierten nur lokal und waren für Studierende unsichtbar.

**Der Auslieferungsablauf lud das gesamte Repository hoch.** 311 MB CSV wurden veröffentlicht, obwohl sie von keiner Seite verlinkt sind — und wären als LFS-Verweisdateien statt als Daten angekommen.

Der gemeinsame Nenner: In allen vier Fällen lief etwas **erfolgreich durch** und lieferte ein falsches Ergebnis. Kein Fehler war als Fehlermeldung sichtbar.

---

## Offene Punkte {#offene-punkte}

Bekannt, nicht behoben, mit Bewertung:

| Punkt | Bewertung |
|---|---|
| `dashboard.html` verlinkt auf keine andere Seite; keine Unterseite führt zurück zum Einstieg | Betrifft die Bedienbarkeit, nicht die Fachlichkeit |
| Keine Subresource Integrity bei den CDN-Einbindungen | Echte Lücke; Risiko begrenzt, da keine Anmeldung und keine personenbezogenen Daten |
| Anwendungen brauchen Internetzugang | Steht im Widerspruch zu „läuft per Doppelklick"; durch lokale Bibliothekskopien auflösbar |
| Keine automatisierte Prüfung der Anwendungen | Vor jedem Bibliothekswechsel manuelle Browser-Prüfung nötig |
| Keine Historisierung (SCD) | Für die Leitfragen ausreichend; als Erweiterungsaufgabe vorgemerkt |
| Interpretationstexte im Bericht ungeprüft | Geprüft sind die Zahlen, nicht ihre Deutung |

---

**Zurück zur** [Übersicht](README.md)
