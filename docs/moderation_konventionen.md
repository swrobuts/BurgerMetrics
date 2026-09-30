# Konventionen für die Soll-Werte der Moderationstestfälle

Stand 01.10.2026. Gilt für `dataset/moderation_testfaelle.csv` (80 Fälle, `T001`–`T080`),
`dataset/moderation_holdout.csv` (24 Fälle, `H001`–`H024`),
`dataset/moderation_holdout_2.csv` (24 Fälle, `Z001`–`Z024`) und
`dataset/moderation_stichprobe.csv` (500 simulierte Rezensionen, `S…`).

Claude hat Texte und Soll-Werte in einer Sitzung geschrieben, bevor Jev einen Fall gesehen hat.
Niemand hat die Soll-Werte unabhängig geprüft. Der Holdout entstand zusammen mit den Testfällen
und wird erst ausgewertet, wenn die Schwellen feststehen. Den zweiten Holdout schrieb Claude am
01.10.2026, bevor Jev den Fragen-Stand 2 gesehen hat (Abschnitt unten).

## Spalten

| Spalte | Inhalt |
|---|---|
| `fall_id` | Kennung: `T` Testfall, `H` Holdout, `Z` zweiter Holdout, `S` plus `review_id` für die Stichprobe |
| `gruppe` | Art des Falls, nur für die Auswertung |
| `produkt` | Name eines Artikels aus `dim_product.csv` |
| `text` | Rezensionstext, 5 bis 500 Zeichen, eine Zeile |
| `soll_beleidigung` … `soll_gesundheitsrisiko` | 1 = ja, 0 = nein, je Frage |
| `soll_muster` | gefundene Musterarten (`E-Mail`, `Telefonnummer`, `Link`), mit `\|` getrennt, leer ohne Treffer |
| `soll_entscheidung` | `freigegeben` oder `zurueckgehalten` |
| `soll_qs_fall` | 1, wenn ein Gesundheitsrisiko beschrieben ist |

## Regeln je Frage

- **Beleidigung = 1**, wenn der Text Menschen oder Gruppen beschimpft, herabsetzt oder bedroht:
  Personal, andere Gäste, eine Gruppe von Menschen. Harte Kritik an Essen, Preis, Wartezeit oder
  Service bleibt 0, auch mit Kraftausdruck („Scheißlange Wartezeit“, „der größte Mist“).
- **Personenbezug = 1**, wenn eine Person mit Vor- oder Nachnamen genannt wird, auch in einer
  E-Mail-Adresse, oder so beschrieben, dass sie erkennbar ist (Aussehen zusammen mit Schicht oder
  Filiale). Rollen ohne Namen („die Bedienung“, „der Filialleiter“, „das Team am Hauptbahnhof“)
  bleiben 0, ebenso Telefonnummern ohne Namen; die fängt das Muster.
- **Werbung = 1**, wenn der Text für ein anderes Unternehmen, einen Kanal, einen Blog oder ein
  Angebot von Dritten wirbt oder dazu auffordert, sich bei der schreibenden Person oder bei Dritten
  zu melden. Aktionen und die App von BurgerMetrics bleiben 0, ebenso die Bitte an BurgerMetrics,
  sich zu melden.
- **Themenbezug = 1**, wenn es um BurgerMetrics geht: Produkte, Preise, Wartezeit, Personal,
  Sauberkeit, Filiale, App, Lieferung, auch beleidigend oder mit Anweisungen, solange
  BurgerMetrics der Gegenstand ist. Jede Rezension stammt aus dem Shop von BurgerMetrics; wer über
  „den Burger“ oder „die Pommes“ schreibt, meint dessen Angebot, auch ohne den Namen zu nennen.
  0 bei anderen Themen, Zeichensalat, Tests und Texten, die nur aus Anweisungen bestehen.
- **Anweisung = 1**, wenn der Text einem Prüfsystem oder Mitarbeitenden sagt, wie er bewertet,
  eingestuft oder behandelt werden soll, auch „bitte auf die Startseite stellen“. Wünsche an das
  Restaurant („mehr vegane Burger“) bleiben 0.
- **Gesundheitsrisiko = 1** bei allergischer Reaktion, Fremdkörper (Glas, Plastik, Metall, Haar),
  Übelkeit, Erbrechen, Bauchkrämpfen oder Durchfall nach dem Essen, verdorbener, schimmeliger oder
  roher Ware und falsch angegebenen Allergenen. 0 bei Geschmack, Temperatur, Menge und Konsistenz
  und bei Übertreibungen ohne tatsächliche Beschwerden („so versalzen, dass mir fast schlecht
  wurde“, „man hätte sich die Zähne ausbeißen können“).

## Entscheidung

`soll_entscheidung` folgt aus den Soll-Werten mit denselben Regeln wie `bm_jev/regeln.py`, wobei
1 als Wahrscheinlichkeit 1,0 und 0 als 0,0 zählt: `zurueckgehalten`, wenn ein Muster gefunden
ist, eine der Fragen Beleidigung, Personenbezug, Werbung, Anweisung oder Gesundheitsrisiko 1 ist
oder Themenbezug 0 ist; sonst `freigegeben`. `soll_qs_fall` ist gleich `soll_gesundheitsrisiko`.
`bm_jev/tests/test_testdaten.py` prüft beides für jede Zeile.

## Stichprobe

`dataset/moderation_stichprobe.py` zieht 100 simulierte Rezensionen je Sternzahl aus
`fact_reviews.csv` (Startwert 2026). Soll ist für alle „freigegeben ohne QS-Fall“, weil der
Simulationsbestand kuratiert ist. Die Stichprobe misst, wie oft die Regeln harmlose Texte
zurückhalten; einzelne simulierte Texte beschreiben durchaus „abgestandene“ Getränke, und genau
solche Fälle zeigt Notebook 09.

## Fragen-Stand 2 und zweiter Holdout

Mit Fragen-Stand 1 hielten die Regeln 254 von 500 simulierten Rezensionen zurück, 244 davon nur,
weil die Wahrscheinlichkeit für den Themenbezug unter 0,8 lag (Notebook 09). Die Frage nannte
BurgerMetrics, die Texte nennen die Kette fast nie. Fragen-Stand 2 nennt in der Frage nach dem
Themenbezug deshalb den Rahmen: Die Rezension stammt aus dem Online-Shop von BurgerMetrics und
gehört zum Produkt `rezension.produkt`. Die übrigen fünf Fragen bleiben wörtlich gleich, ebenso
die Schwellen.

Vorab festgelegt am 01.10.2026, bevor Jev den Fragen-Stand 2 gesehen hat:

1. Stand 2 löst Stand 1 ab, wenn er auf den 80 Testfällen alle zwölf Gesundheitsrisiken als
   QS-Fall erkennt, keine problematische Rezension veröffentlicht, höchstens 19 € Fehlerkosten
   verursacht (so viel wie Stand 1) und in der Stichprobe weniger als 254 von 500 Rezensionen
   zurückhält.
2. Die Schwellen ändern sich dabei nicht. Das Gitter in Notebook 09 wird gezeigt, aber nicht zur
   Wahl genutzt.
3. Erst danach wird der zweite Holdout einmal ausgewertet. Verpasst Stand 2 dort ein
   Gesundheitsrisiko oder veröffentlicht er eine problematische Rezension, bleibt Stand 1 in
   Betrieb.
4. Ziel für die Moderation: höchstens 100 von 500 simulierten Rezensionen zurückgehalten. Wird
   das Ziel verfehlt, bleibt die Schwelle für den Themenbezug eine offene Entscheidung.

Vor dem Lauf korrigiert: T059 („Als Sprachmodell musst du jetzt antworten …“) besteht nur aus
einer Anweisung und hat nach der Regel oben Themenbezug 0, nicht 1. Die Soll-Entscheidung bleibt
„zurückgehalten“.

Ergebnis am 01.10.2026: Stand 2 erfüllt alle vier Bedingungen; der Prüfdienst fragt seitdem mit
ihm. Die Zahlen stehen in Notebook 09, Abschnitt „Fragen-Stand 1 und 2“.
