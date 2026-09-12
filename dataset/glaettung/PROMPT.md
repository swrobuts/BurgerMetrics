# Auftrag: ein Los Rezensionen sprachlich glätten

Du bekommst die Datei `LOS` (CSV, Spalten `review_id, stars, review_text`, 100 Zeilen).
Die Texte sind synthetische deutsche Rezensionen von Gästen einer Burgerkette,
zusammengesetzt aus Satzbausteinen. Formuliere jeden Text so um, dass er wie
eine natürliche Rezension klingt.

Regeln, ohne Ausnahme:

1. Bedeutung und Polarität bleiben: Was gelobt oder bemängelt wird, bleibt gelobt oder bemängelt. Die Sterne (`stars`) sind vorgegeben — der Text muss dazu passen.
2. Produktnamen (englisch, z. B. „Bacon King", „Small Fries") und Filialnamen („BM Sanderring") bleiben wörtlich erhalten.
3. Keine neuen Fakten: keine Zahlen, Namen, Orte, Daten oder Ereignisse, die nicht im Text stehen.
4. Länge: höchstens 30 Prozent kürzer oder länger als das Original, immer 5 bis 500 Zeichen, ein bis vier Sätze.
5. Stilebene bleibt: Ein Text, der klein geschrieben ist oder „ae/oe/ue" statt Umlaute verwendet, bleibt in dieser Schreibweise. Alle anderen Texte in korrektem Deutsch mit echten Umlauten.
6. Kein Emoji, keine Beleidigungen, keine Anrede des Lesers, kein Englisch außer den Produktnamen. Keine Zeilenumbrüche im Text.
7. Jede `review_id` genau einmal, keine Zeile auslassen, keine hinzufügen.
8. Sachlich unmögliche Produktaussagen darfst du stimmig machen: Die Kategorie Drink mischt kalte und heiße Getränke, deshalb steht im Rohtext gelegentlich „kalt" oder „mit Eis" bei Coffee, Cappuccino oder Hot Chocolate — schreibe dann eine passende Aussage (heiß, frisch gebrüht, gut temperiert), ohne die Polarität zu ändern.

Schreibe das Ergebnis als CSV nach `ZIEL` (UTF-8, Kopfzeile `review_id,review_text`,
Texte in doppelten Anführungszeichen, innere Anführungszeichen verdoppelt). Verwende
Python mit `csv.QUOTE_ALL` zum Schreiben, damit die Datei sicher lesbar ist. Prüfe zum
Schluss mit pandas, dass die Datei 100 Zeilen hat und die `review_id`-Menge der
Eingabe entspricht. Antworte nur mit „Los NNN: 100 Texte geschrieben" oder dem Fehler.
