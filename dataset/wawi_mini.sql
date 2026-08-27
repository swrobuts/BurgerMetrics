-- wawi_mini.sql
-- Ausschnitt des operativen Warenwirtschaftsmodells (3NF, deutsche Namen),
-- befuellt mit denselben 19 Bestellungen wie burgermetrics_mini.sql.
--
-- Zweck: den Weg VOM operativen Modell ZUM analytischen vorfuehrbar machen.
-- Nach diesem Skript wawi_zu_analytisch.sql ausfuehren — es baut per JOIN
-- und Umbenennung Sichten, die zeilengleich mit den Tabellen aus
-- burgermetrics_mini.sql sind. Der Beweis steht am Ende jener Datei.
--
-- Vereinfachungen gegenueber dem Gesamtmodell (dataset/erp_datenmodell.excalidraw):
--   * 14 der 26 Tabellen — Einkauf, Lager, Personal und Wetter fehlen, weil
--     sie fuer den Verkaufs-Abzug nicht gebraucht werden.
--   * mitarbeiter_id in kundenbestellung bleibt NULL (im Mini nicht belegt).
--   * preishistorie fuehrt nur den aktuellen Listenpreis; die historischen
--     Verkaufspreise stehen — wie im echten Betrieb — in bestellposition.
--   * rechnung: brutto/mwst/netto sind STEUERLICHE Begriffe (19 % vereinfacht).
--     Nicht verwechseln mit brutto_gesamt/netto_gesamt der Bestellung, die
--     VOR und NACH RABATT bedeuten. Zwei Fachsprachen, ein Wort.
--
-- Laeuft unveraendert in DuckDB und PostgreSQL.

DROP TABLE IF EXISTS filialtyp; CREATE TABLE filialtyp (filialtyp_id INTEGER PRIMARY KEY, name VARCHAR(30));
INSERT INTO filialtyp VALUES (1, 'City Center'), (2, 'Commercial'), (3, 'Highway'), (4, 'Hospital'), (5, 'Mixed'), (6, 'Residential'), (7, 'Shopping'), (8, 'University');

DROP TABLE IF EXISTS filiale; CREATE TABLE filiale (filiale_id INTEGER PRIMARY KEY, name VARCHAR(50), stadtteil VARCHAR(50), filialtyp_id INTEGER, hat_drive_through BOOLEAN, eroeffnet_am DATE, monatsmiete DECIMAL(10,2), sitzplaetze_innen INTEGER);
INSERT INTO filiale VALUES
  (1, 'BM Europastern', 'Europastern', 3, TRUE, '2017-03-15', 6800, 100),
  (2, 'BM Hauptbahnhof', 'Altstadt', 1, FALSE, '2018-06-01', 8500, 60),
  (3, 'BM Sanderring', 'Sanderau', 8, FALSE, '2019-02-01', 5200, 80),
  (4, 'BM Heuchelhof', 'Heuchelhof', 6, TRUE, '2019-09-01', 4800, 85),
  (5, 'BM Lengfeld', 'Lengfeld', 2, TRUE, '2020-08-01', 5500, 70),
  (6, 'BM Mainfrankenpark', 'Mainfrankenpark', 7, TRUE, '2021-04-01', 7200, 90),
  (7, 'BM Grombühl', 'Grombühl', 4, FALSE, '2022-01-15', 4500, 50),
  (8, 'BM Zellerau', 'Zellerau', 5, FALSE, '2023-03-01', 4000, 65);

DROP TABLE IF EXISTS artikelkategorie; CREATE TABLE artikelkategorie (kategorie_id INTEGER PRIMARY KEY, name VARCHAR(30));
INSERT INTO artikelkategorie VALUES (1, 'Breakfast'), (2, 'Burger'), (3, 'Dessert'), (4, 'Drink'), (5, 'Extra'), (6, 'Side');

DROP TABLE IF EXISTS artikelunterkategorie; CREATE TABLE artikelunterkategorie (unterkategorie_id INTEGER PRIMARY KEY, name VARCHAR(30), kategorie_id INTEGER);
INSERT INTO artikelunterkategorie VALUES
  (1, 'Burger', 1),
  (2, 'Beef', 2),
  (3, 'Chicken', 2),
  (4, 'Kids', 2),
  (5, 'Vegan', 2),
  (6, 'Ice Cream', 3),
  (7, 'Pastry', 3),
  (8, 'Alcohol', 4),
  (9, 'Hot Drink', 4),
  (10, 'Juice', 4),
  (11, 'Milkshake', 4),
  (12, 'Soft Drink', 4),
  (13, 'Sauce', 5),
  (14, 'Fried', 6),
  (15, 'Fries', 6),
  (16, 'Nuggets', 6),
  (17, 'Salad', 6);

DROP TABLE IF EXISTS artikel; CREATE TABLE artikel (artikel_id INTEGER PRIMARY KEY, name VARCHAR(50), unterkategorie_id INTEGER, vegetarisch BOOLEAN, listenpreis DECIMAL(6,2));
INSERT INTO artikel VALUES
  (4, 'Bacon King', 2, FALSE, 10.51),
  (5, 'Chicken Burger', 3, FALSE, 7.88),
  (8, 'Kids Burger', 4, FALSE, 3.93),
  (10, 'Beyond Burger', 5, TRUE, 10.51),
  (13, 'Green Goddess Bowl', 5, TRUE, 11.82),
  (15, 'Small Fries', 15, TRUE, 2.62),
  (16, 'Medium Fries', 15, TRUE, 3.27),
  (17, 'Large Fries', 15, TRUE, 3.93),
  (18, 'Chicken Nuggets 6pc', 16, FALSE, 4.59),
  (20, 'Onion Rings', 14, TRUE, 3.93),
  (21, 'Side Salad', 17, TRUE, 3.93),
  (22, 'Coleslaw', 17, TRUE, 3.01),
  (26, 'Cola 0.3l', 12, TRUE, 2.88),
  (27, 'Cola 0.5l', 12, TRUE, 3.8),
  (28, 'Fanta 0.3l', 12, TRUE, 2.88),
  (29, 'Sprite 0.3l', 12, TRUE, 2.88),
  (31, 'Ice Tea 0.3l', 12, TRUE, 3.27),
  (32, 'Coffee', 9, TRUE, 2.62),
  (33, 'Cappuccino', 9, TRUE, 3.93),
  (34, 'Milkshake Vanilla', 11, TRUE, 5.25),
  (36, 'Milkshake Strawberry', 11, TRUE, 5.25),
  (37, 'Fresh OJ', 10, TRUE, 4.19),
  (38, 'Beer 0.3l', 8, TRUE, 4.59),
  (39, 'Hot Chocolate', 9, TRUE, 4.19),
  (40, 'Craft Lemonade', 12, TRUE, 4.59),
  (42, 'Soft Ice Chocolate', 6, TRUE, 2.35),
  (45, 'Apple Pie', 7, TRUE, 2.62),
  (46, 'Cookie Chocolate', 7, TRUE, 1.7),
  (49, 'Breakfast Burger', 1, FALSE, 5.9),
  (54, 'Ketchup Extra', 13, TRUE, 0.53),
  (56, 'BBQ Sauce', 13, TRUE, 0.53);

DROP TABLE IF EXISTS preishistorie; CREATE TABLE preishistorie (preis_id INTEGER PRIMARY KEY, artikel_id INTEGER, gueltig_ab DATE, gueltig_bis DATE, verkaufspreis DECIMAL(6,2));
INSERT INTO preishistorie VALUES
  (1, 4, '2026-01-01', NULL, 10.51),
  (2, 5, '2026-01-01', NULL, 7.88),
  (3, 8, '2026-01-01', NULL, 3.93),
  (4, 10, '2026-01-01', NULL, 10.51),
  (5, 13, '2026-01-01', NULL, 11.82),
  (6, 15, '2026-01-01', NULL, 2.62),
  (7, 16, '2026-01-01', NULL, 3.27),
  (8, 17, '2026-01-01', NULL, 3.93),
  (9, 18, '2026-01-01', NULL, 4.59),
  (10, 20, '2026-01-01', NULL, 3.93),
  (11, 21, '2026-01-01', NULL, 3.93),
  (12, 22, '2026-01-01', NULL, 3.01),
  (13, 26, '2026-01-01', NULL, 2.88),
  (14, 27, '2026-01-01', NULL, 3.8),
  (15, 28, '2026-01-01', NULL, 2.88),
  (16, 29, '2026-01-01', NULL, 2.88),
  (17, 31, '2026-01-01', NULL, 3.27),
  (18, 32, '2026-01-01', NULL, 2.62),
  (19, 33, '2026-01-01', NULL, 3.93),
  (20, 34, '2026-01-01', NULL, 5.25),
  (21, 36, '2026-01-01', NULL, 5.25),
  (22, 37, '2026-01-01', NULL, 4.19),
  (23, 38, '2026-01-01', NULL, 4.59),
  (24, 39, '2026-01-01', NULL, 4.19),
  (25, 40, '2026-01-01', NULL, 4.59),
  (26, 42, '2026-01-01', NULL, 2.35),
  (27, 45, '2026-01-01', NULL, 2.62),
  (28, 46, '2026-01-01', NULL, 1.7),
  (29, 49, '2026-01-01', NULL, 5.9),
  (30, 54, '2026-01-01', NULL, 0.53),
  (31, 56, '2026-01-01', NULL, 0.53);

DROP TABLE IF EXISTS loyalty_stufe; CREATE TABLE loyalty_stufe (stufe_id INTEGER PRIMARY KEY, name VARCHAR(10));
INSERT INTO loyalty_stufe VALUES (1, 'None'), (2, 'Bronze'), (3, 'Silver'), (4, 'Gold');

DROP TABLE IF EXISTS kunde; CREATE TABLE kunde (kunde_id INTEGER PRIMARY KEY, altersgruppe VARCHAR(10), geschlecht VARCHAR(15), heimat_stadtteil VARCHAR(30), hat_app BOOLEAN, loyalty_stufe_id INTEGER);
INSERT INTO kunde VALUES
  (249, '65+', 'Male', 'Rottenbauer', FALSE, 1),
  (459, '<18', 'Male', 'Sanderau', FALSE, 1),
  (1250, '35-44', 'Male', 'Lengfeld', TRUE, 2),
  (1943, '45-54', 'Male', 'Sanderau', FALSE, 1),
  (2691, '25-34', 'Female', 'Heidingsfeld', TRUE, 2),
  (5967, '55-64', 'Male', 'Sanderau', FALSE, 1),
  (6923, '18-24', 'Male', 'Versbach', TRUE, 4),
  (8315, '25-34', 'Male', 'Lindleinsmühle', TRUE, 2),
  (8662, '25-34', 'Female', 'Grombühl', TRUE, 3),
  (9669, '35-44', 'Female', 'Zellerau', TRUE, 1),
  (14240, '18-24', 'Female', 'Frauenland', FALSE, 1),
  (16010, '25-34', 'Female', 'Lengfeld', TRUE, 4),
  (18641, '55-64', 'Male', 'Heidingsfeld', FALSE, 1),
  (19890, '55-64', 'Male', 'Grombühl', FALSE, 1),
  (21454, '45-54', 'Female', 'Rottenbauer', FALSE, 1),
  (21966, '65+', 'Female', 'Frauenland', FALSE, 1),
  (22612, '35-44', 'Female', 'Sanderau', TRUE, 3),
  (23371, '<18', 'Male', 'Sanderau', FALSE, 1),
  (24815, '55-64', 'Male', 'Heidingsfeld', FALSE, 1);

DROP TABLE IF EXISTS zahlungsart; CREATE TABLE zahlungsart (zahlungsart_id INTEGER PRIMARY KEY, bezeichnung VARCHAR(30), anbieter VARCHAR(30));
INSERT INTO zahlungsart VALUES
  (1, 'Cash', 'Cash'),
  (2, 'EC Card', 'Girocard'),
  (3, 'Credit Card', 'Visa/Mastercard'),
  (4, 'Mobile Payment', 'Apple Pay/Google Pay');

DROP TABLE IF EXISTS promotionstyp; CREATE TABLE promotionstyp (promotionstyp_id INTEGER PRIMARY KEY, name VARCHAR(30));
INSERT INTO promotionstyp VALUES (1, 'App'), (2, 'Bundle'), (3, 'Delivery'), (4, 'Loyalty'), (5, 'Opening'), (6, 'Seasonal'), (7, 'Segment'), (8, 'Time-Based');

-- Keine Zeile fuer 'keine Aktion': Operativ ist das schlicht NULL am Beleg.
DROP TABLE IF EXISTS promotion; CREATE TABLE promotion (promotion_id INTEGER PRIMARY KEY, name VARCHAR(40), promotionstyp_id INTEGER, rabatt_pct INTEGER);
INSERT INTO promotion VALUES
  (1, 'Grand Opening 15%', 5, 15),
  (2, 'Happy Hour 15%', 8, 15),
  (3, 'Student Discount 8%', 7, 8),
  (4, 'Family Bundle 12%', 2, 12),
  (5, 'App Welcome 10%', 1, 10),
  (6, 'Loyalty Gold 20%', 4, 20),
  (7, 'Seasonal Special 10%', 6, 10),
  (8, 'Weekend Deal 10%', 8, 10),
  (9, 'Birthday Offer 25%', 7, 25),
  (10, 'Combo Saver 15%', 2, 15),
  (11, 'Vegan Week 10%', 6, 10),
  (12, 'COVID Delivery 10%', 3, 10);

DROP TABLE IF EXISTS kundenbestellung; CREATE TABLE kundenbestellung (bestellung_id INTEGER PRIMARY KEY, bestelldatum DATE, bestellzeit TIME, filiale_id INTEGER, kunde_id INTEGER, mitarbeiter_id INTEGER, zahlungsart_id INTEGER, promotion_id INTEGER, bestellkanal VARCHAR(20), artikel_anzahl INTEGER, brutto_gesamt DECIMAL(8,2), rabatt_betrag DECIMAL(8,2), netto_gesamt DECIMAL(8,2), bestelldauer_min INTEGER, zufriedenheit DECIMAL(3,2));
INSERT INTO kundenbestellung VALUES
  (1954, '2017-05-18', '17:00:00', 1, 18641, NULL, 1, NULL, 'Drive-Through', 3, 11.37, 0, 11.37, 3, NULL),
  (9770, '2017-10-20', '20:00:00', 1, 1250, NULL, 2, NULL, 'Counter', 3, 8.47, 0, 8.47, 4, NULL),
  (19540, '2018-05-13', '12:00:00', 1, 21454, NULL, 2, 8, 'Drive-Through', 4, 16.27, 1.63, 14.64, 5, NULL),
  (33218, '2018-10-11', '14:00:00', 2, 22612, NULL, 1, NULL, 'Counter', 4, 11.95, 0, 11.95, 9, NULL),
  (50804, '2019-04-05', '11:00:00', 3, 5967, NULL, 2, NULL, 'Counter', 4, 16.97, 0, 16.97, 9, NULL),
  (78160, '2019-10-03', '17:00:00', 3, 21966, NULL, 1, NULL, 'Counter', 3, 8.05, 0, 8.05, 8, NULL),
  (107470, '2020-04-23', '10:00:00', 1, 1943, NULL, 3, NULL, 'Drive-Through', 5, 16.8, 0, 16.8, 3, NULL),
  (130918, '2020-10-03', '08:00:00', 3, 249, NULL, 3, NULL, 'Counter', 2, 5.28, 0, 5.28, 14, NULL),
  (149481, '2021-04-02', '19:00:00', 1, 6923, NULL, 3, NULL, 'Drive-Through', 2, 6.49, 0, 6.49, 4, NULL),
  (191492, '2021-10-04', '20:00:00', 3, 16010, NULL, 2, NULL, 'App Order', 3, 8, 0, 8, 2, NULL),
  (247181, '2022-05-01', '17:00:00', 4, 459, NULL, 3, NULL, 'Drive-Through', 2, 2.53, 0, 2.53, 3, NULL),
  (298962, '2022-10-02', '17:00:00', 1, 8315, NULL, 1, NULL, 'Counter', 5, 21.2, 0, 21.2, 7, NULL),
  (353674, '2023-04-01', '13:00:00', 4, 8662, NULL, 3, NULL, 'Drive-Through', 4, 15.21, 0, 15.21, 6, NULL),
  (424018, '2023-10-07', '18:00:00', 4, 23371, NULL, 2, NULL, 'Drive-Through', 2, 6.69, 0, 6.69, 6, 3),
  (494362, '2024-05-01', '07:00:00', 6, 9669, NULL, 4, NULL, 'Drive-Through', 2, 7.16, 0, 7.16, 5, NULL),
  (554936, '2024-10-02', '14:00:00', 6, 24815, NULL, 1, NULL, 'Drive-Through', 2, 7.79, 0, 7.79, 6, NULL),
  (617464, '2025-04-01', '16:00:00', 1, 2691, NULL, 4, NULL, 'App Order', 2, 5.78, 0, 5.78, 1, NULL),
  (690739, '2025-10-03', '12:00:00', 2, 14240, NULL, 3, NULL, 'Counter', 2, 14.43, 0, 14.43, 11, 4),
  (737635, '2026-02-12', '15:00:00', 4, 19890, NULL, 3, NULL, 'Counter', 4, 12.04, 0, 12.04, 3, 3);

DROP TABLE IF EXISTS bestellposition; CREATE TABLE bestellposition (position_id INTEGER PRIMARY KEY, bestellung_id INTEGER, artikel_id INTEGER, menge INTEGER, einzelpreis DECIMAL(6,2), positionsbetrag DECIMAL(8,2));
INSERT INTO bestellposition VALUES
  (7861, 1954, 5, 1, 5.99, 5.99),
  (7862, 1954, 16, 1, 2.49, 2.49),
  (7863, 1954, 27, 1, 2.89, 2.89),
  (38539, 9770, 17, 1, 2.99, 2.99),
  (38540, 9770, 45, 1, 1.99, 1.99),
  (38541, 9770, 38, 1, 3.49, 3.49),
  (77605, 19540, 4, 1, 8.19, 8.19),
  (77606, 19540, 34, 1, 4.09, 4.09),
  (77607, 19540, 18, 1, 3.58, 3.58),
  (77608, 19540, 56, 1, 0.41, 0.41),
  (130739, 33218, 16, 1, 2.55, 2.55),
  (130740, 33218, 36, 1, 4.09, 4.09),
  (130741, 33218, 37, 1, 3.27, 3.27),
  (130742, 33218, 45, 1, 2.04, 2.04),
  (197984, 50804, 26, 1, 2.3, 2.3),
  (197985, 50804, 33, 1, 3.14, 3.14),
  (197986, 50804, 10, 1, 8.39, 8.39),
  (197987, 50804, 21, 1, 3.14, 3.14),
  (303016, 78160, 28, 1, 2.3, 2.3),
  (303017, 78160, 15, 1, 2.09, 2.09),
  (303018, 78160, 38, 1, 3.66, 3.66),
  (416672, 107470, 27, 1, 3.06, 3.06),
  (416673, 107470, 8, 2, 3.17, 6.34),
  (416674, 107470, 49, 1, 4.76, 4.76),
  (416675, 107470, 31, 1, 2.64, 2.64),
  (507149, 130918, 45, 1, 2.11, 2.11),
  (507150, 130918, 21, 1, 3.17, 3.17),
  (578842, 149481, 32, 1, 2.16, 2.16),
  (578843, 149481, 36, 1, 4.33, 4.33),
  (742253, 191492, 37, 1, 3.46, 3.46),
  (742254, 191492, 27, 1, 3.14, 3.14),
  (742255, 191492, 46, 1, 1.4, 1.4),
  (958222, 247181, 42, 1, 2.07, 2.07),
  (958223, 247181, 54, 1, 0.46, 0.46),
  (1156573, 298962, 32, 1, 2.3, 2.3),
  (1156574, 298962, 10, 1, 9.23, 9.23),
  (1156575, 298962, 16, 1, 2.88, 2.88),
  (1156576, 298962, 27, 1, 3.34, 3.34),
  (1156577, 298962, 21, 1, 3.45, 3.45),
  (1369416, 353674, 18, 1, 4.26, 4.26),
  (1369417, 353674, 15, 1, 2.43, 2.43),
  (1369418, 353674, 38, 2, 4.26, 8.52),
  (1645569, 424018, 20, 1, 3.65, 3.65),
  (1645570, 424018, 16, 1, 3.04, 3.04),
  (1922690, 494362, 40, 1, 4.4, 4.4),
  (1922691, 494362, 26, 1, 2.76, 2.76),
  (2161409, 554936, 17, 1, 3.77, 3.77),
  (2161410, 554936, 39, 1, 4.02, 4.02),
  (2407832, 617464, 22, 1, 2.95, 2.95),
  (2407833, 617464, 29, 1, 2.83, 2.83),
  (2697003, 690739, 26, 1, 2.83, 2.83),
  (2697004, 690739, 13, 1, 11.6, 11.6),
  (2883128, 737635, 31, 2, 3.27, 6.54),
  (2883129, 737635, 28, 1, 2.88, 2.88),
  (2883130, 737635, 32, 1, 2.62, 2.62);

-- Steuerliche Sicht, 19 % vereinfacht. netto_steuer + mwst = zahlbetrag = netto_gesamt der Bestellung.
DROP TABLE IF EXISTS rechnung; CREATE TABLE rechnung (rechnung_id INTEGER PRIMARY KEY, bestellung_id INTEGER, rechnungsdatum DATE, zahlbetrag DECIMAL(8,2), mwst_betrag DECIMAL(8,2), zahlungsart_id INTEGER);
INSERT INTO rechnung VALUES
  (1, 1954, '2017-05-18', 11.37, 1.82, 1),
  (2, 9770, '2017-10-20', 8.47, 1.35, 2),
  (3, 19540, '2018-05-13', 14.64, 2.34, 2),
  (4, 33218, '2018-10-11', 11.95, 1.91, 1),
  (5, 50804, '2019-04-05', 16.97, 2.71, 2),
  (6, 78160, '2019-10-03', 8.05, 1.29, 1),
  (7, 107470, '2020-04-23', 16.8, 2.68, 3),
  (8, 130918, '2020-10-03', 5.28, 0.84, 3),
  (9, 149481, '2021-04-02', 6.49, 1.04, 3),
  (10, 191492, '2021-10-04', 8, 1.28, 2),
  (11, 247181, '2022-05-01', 2.53, 0.4, 3),
  (12, 298962, '2022-10-02', 21.2, 3.38, 1),
  (13, 353674, '2023-04-01', 15.21, 2.43, 3),
  (14, 424018, '2023-10-07', 6.69, 1.07, 2),
  (15, 494362, '2024-05-01', 7.16, 1.14, 4),
  (16, 554936, '2024-10-02', 7.79, 1.24, 1),
  (17, 617464, '2025-04-01', 5.78, 0.92, 4),
  (18, 690739, '2025-10-03', 14.43, 2.3, 3),
  (19, 737635, '2026-02-12', 12.04, 1.92, 3);
