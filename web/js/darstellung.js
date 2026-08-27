// darstellung.js — was die Oberflaechen zeigen, das Datenmodell aber nicht kennt.
//
// Bilder, Beschreibungstexte, Oeffnungszeiten und die Schnellwahl der Kasse
// sind keine Messwerte. Sie stehen in keiner CSV-Datei und in keiner Tabelle,
// und sie dort hineinzuschreiben, nur damit alles aus einer Quelle kommt,
// waere der umgekehrte Fehler.
//
// Sie stehen aber auch nicht mehr verstreut in den Seiten, sondern hier — an
// einer Stelle, sichtbar getrennt von dem, was gemessen ist. Wer die Trennung
// pruefen will: Alles in dieser Datei darf man aendern, ohne dass eine Zahl
// im Dashboard anders wird.
//
// Artikel ohne eigenes Bild bekommen das Rueckfallbild ihrer Kategorie. Das
// ist besser als eine Luecke und ehrlicher als ein erfundenes Bild.

export const BILDER = {
  "Classic Burger": "photo-1568901346375-23c9450c58cd",
  "Cheeseburger": "photo-1550547660-d9450f859349",
  "Double Burger": "photo-1594212699903-ec8a3eca50f5",
  "Bacon King": "photo-1553979459-d2229ba7433b",
  "Chicken Burger": "photo-1606755962773-d324e0a13086",
  "Crispy Chicken Deluxe": "photo-1513185158878-8d8c2a2a3da3",
  "Veggie Burger": "photo-1525059696034-4967a8e1dca2",
  "Medium Fries": "photo-1573080496219-bb080dd4f877",
  "Large Fries": "photo-1598679253544-2c97992403ea",
  "Chicken Nuggets 6pc": "photo-1562967916-eb82221dfb92",
  "Chicken Nuggets 9pc": "photo-1562967916-eb82221dfb92",
  "Onion Rings": "photo-1639024471283-03518883512d",
  "Side Salad": "photo-1512621776951-a57141f2eefd",
  "Mozzarella Sticks": "photo-1531749668029-2db88e4276c7",
  "Cola 0.3l": "photo-1622483767028-3f66f32aef97",
  "Cola 0.5l": "photo-1622483767028-3f66f32aef97",
  "Cappuccino": "photo-1572442388796-11668a67e53d",
  "Milkshake Vanilla": "photo-1572490122747-3968b75cc699",
  "Milkshake Chocolate": "photo-1572490122747-3968b75cc699",
  "Soft Ice Vanilla": "photo-1570197571499-166b36435e9f",
  "Sundae Caramel": "photo-1563805042-7684c019e1cb",
  "Apple Pie": "photo-1568571780765-9276ac8b75a2",
  "Cookie Chocolate": "photo-1499636136210-6f4ee915583e",
  "Breakfast Burger": "photo-1525351484163-7529414344d8",
  "Pancakes": "photo-1567620905732-2d1ec7ab7445",
  "Scrambled Eggs & Toast": "photo-1528735602780-2552fd46c7af",
  "Breakfast Wrap": "photo-1626700051175-6818013e1d4f",
  "Ketchup Extra": "photo-1472476443507-c7a5948772fc",
  "BBQ Sauce": "photo-1472476443507-c7a5948772fc",
  "Cheese Dip": "photo-1472476443507-c7a5948772fc"
};

export const RUECKFALLBILD = {
  "Breakfast": "photo-1525351484163-7529414344d8",
  "Burger": "photo-1553979459-d2229ba7433b",
  "Dessert": "photo-1568571780765-9276ac8b75a2",
  "Drink": "photo-1572442388796-11668a67e53d",
  "Extra": "photo-1472476443507-c7a5948772fc",
  "Side": "photo-1562967916-eb82221dfb92"
};

export const BESCHREIBUNGEN = {
  "Classic Burger": "Saftiges Rindfleisch-Patty, frischer Salat, Tomate, Zwiebel, hauseigene Sauce.",
  "Cheeseburger": "Unser Classic mit geschmolzenem Cheddar. Der Liebling aller Gäste.",
  "Double Burger": "Doppeltes Patty, doppelter Genuss. Für den großen Hunger.",
  "Bacon King": "Smoky Bacon, karamellisierte Zwiebeln, BBQ-Sauce. Unser kräftigster Burger.",
  "Chicken Burger": "Zartes Hähnchenbrustfilet, knusprig paniert, mit Coleslaw.",
  "Crispy Chicken Deluxe": "Crispy Chicken mit Jalapeños, Avocado-Creme und Rucola.",
  "Veggie Burger": "Hausgemachtes Gemüse-Patty mit Röstzwiebeln und Kräuterquark.",
  "Medium Fries": "Die perfekte Beilage in der beliebten Größe.",
  "Large Fries": "Für die, die nicht genug kriegen können.",
  "Chicken Nuggets 6pc": "6 knusprige Nuggets mit Dip nach Wahl.",
  "Chicken Nuggets 9pc": "9 Nuggets — ideal zum Teilen oder ganz für dich.",
  "Onion Rings": "Dicke Zwiebelringe in knuspriger Panade.",
  "Side Salad": "Blattsalat mit Cherry-Tomaten und Vinaigrette.",
  "Mozzarella Sticks": "Panierte Mozzarella-Sticks mit Marinara-Dip.",
  "Cola 0.3l": "Coca-Cola Classic, eiskalt serviert.",
  "Cola 0.5l": "Mehr Cola, mehr Erfrischung.",
  "Cappuccino": "Espresso mit cremigem Milchschaum.",
  "Milkshake Vanilla": "Handgerührter Vanille-Milkshake. Thick & creamy.",
  "Milkshake Chocolate": "Schokolade pur. Für Chocoholics.",
  "Soft Ice Vanilla": "Klassisches Softeis im Waffelbecher.",
  "Sundae Caramel": "Vanilleeis mit warmem Karamell und gerösteten Nüssen.",
  "Apple Pie": "Warmer Apfelkuchen mit Zimtzucker.",
  "Cookie Chocolate": "Soft-baked Cookie mit belgischer Schokolade.",
  "Breakfast Burger": "Spiegelei, Bacon und Cheddar auf dem Frühstücksbun.",
  "Pancakes": "Drei fluffige Pancakes mit Ahornsirup und Butter.",
  "Scrambled Eggs & Toast": "Cremiges Rührei auf Vollkorn-Toast.",
  "Breakfast Wrap": "Tortilla mit Rührei, Bacon, Käse und Avocado.",
  "Ketchup Extra": "Hauseigener Ketchup — extra Portion.",
  "BBQ Sauce": "Smoky BBQ Sauce — der perfekte Dip.",
  "Cheese Dip": "Cremiger Cheddar-Dip zum Dippen."
};

export const ANFAHRT = {
  "BM Hauptbahnhof": "Direkt am Hauptbahnhof, Ausgang Süd. 1 Min. Fußweg. Kein eigener Parkplatz — Tiefgarage Hauptbahnhof empfohlen.",
  "BM Sanderring": "Gegenüber der Uni am Sanderring, Straßenbahn-Haltestelle 'Sanderring'. 10 Parkplätze vor Ort.",
  "BM Europastern": "A3 Ausfahrt Würzburg-Heidingsfeld, Richtung Europastern. Großer Parkplatz, Drive-Through mit 2 Spuren.",
  "BM Mainfrankenpark": "Im Mainfrankenpark neben MediaMarkt. Direkte Zufahrt vom Parkplatz P3.",
  "BM Grombühl": "Nähe Uniklinikum Würzburg, 5 Min. zu Fuß von der Straßenbahn-Haltestelle 'Grombühlstraße'.",
  "BM Heuchelhof": "Im Heuchelhof-Center, Bus-Linie 14 Haltestelle 'Heuchelhof Mitte'. Großer Parkplatz, Spielplatz.",
  "BM Lengfeld": "Im Gewerbegebiet Lengfeld, neben dem Baumarkt. Gute Erreichbarkeit über B19.",
  "BM Zellerau": "In der Zellerau, 3 Min. von der Straßenbahn-Haltestelle 'Zellerau'. 12 Stellplätze direkt vor der Tür."
};

export const OEFFNUNGSZEITEN = {
  "BM Hauptbahnhof": "Mo-Sa 6:00-23:00, So 8:00-22:00",
  "BM Sanderring": "Mo-Sa 7:00-23:00, So 9:00-22:00",
  "BM Europastern": "Mo-So 6:00-24:00",
  "BM Mainfrankenpark": "Mo-Sa 9:00-22:00, So 10:00-21:00",
  "BM Grombühl": "Mo-Fr 6:30-21:00, Sa 8:00-21:00, So 9:00-20:00",
  "BM Heuchelhof": "Mo-So 7:00-23:00",
  "BM Lengfeld": "Mo-Fr 6:00-22:00, Sa 7:00-22:00, So 8:00-21:00",
  "BM Zellerau": "Mo-Sa 8:00-22:00, So 9:00-21:00"
};

// Die Kasse zeigt diese Artikel als Schnellwahl. Eine Bedienentscheidung,
// keine Eigenschaft des Artikels.
export const SCHNELLWAHL = ["Classic Burger", "Cheeseburger", "Medium Fries", "Cola 0.5l"];

/** Bild eines Artikels, mit Rueckfall auf die Kategorie. */
export function bildVon(name, kategorie) {
  return BILDER[name] || RUECKFALLBILD[kategorie] || RUECKFALLBILD.Burger;
}
