-- burgermetrics_mini.sql
-- Miniaturbestand des BurgerMetrics-Galaxy-Schemas.
--
-- 19 Bestellungen aus zehn Jahren, 55 Positionen, dazu alle benoetigten
-- Dimensionszeilen. Echte Namen, Preise und Betraege aus dem Vollbestand.
--
-- Zweck: Jedes SQL-Beispiel der Fallstudie laesst sich sofort ausfuehren, ohne
-- 311 MB CSV zu laden. Auch der Fan Trap ist auf diesen Zeilen sichtbar und
-- von Hand nachrechenbar.
--
-- Laeuft unveraendert in DuckDB, PostgreSQL und MySQL 8.
--
-- Kontrollzahlen nach dem Import:
--   SELECT COUNT(*) FROM fact_orders;                  -->  19
--   SELECT COUNT(*) FROM fact_order_items;             -->  55
--   SELECT ROUND(SUM(net_total), 2) FROM fact_orders;  -->  200.85
--
-- Der Fan Trap, zum Selbstausprobieren:
--   SELECT ROUND(SUM(o.net_total), 2)
--   FROM fact_orders o JOIN fact_order_items i ON o.order_id = i.order_id;
--   --> 649.16 statt 200.85  (Faktor 3.23)


DROP TABLE IF EXISTS dim_branch;
CREATE TABLE dim_branch (branch_id INTEGER PRIMARY KEY, branch_name VARCHAR(50), district VARCHAR(50), branch_type VARCHAR(30), has_drive_through BOOLEAN, opening_date DATE, monthly_rent_eur DECIMAL(10,2), seats_indoor INTEGER);
INSERT INTO dim_branch (branch_id, branch_name, district, branch_type, has_drive_through, opening_date, monthly_rent_eur, seats_indoor) VALUES
  (1, 'BM Europastern', 'Europastern', 'Highway', TRUE, '2017-03-15', 6800, 100),
  (2, 'BM Hauptbahnhof', 'Altstadt', 'City Center', FALSE, '2018-06-01', 8500, 60),
  (3, 'BM Sanderring', 'Sanderau', 'University', FALSE, '2019-02-01', 5200, 80),
  (4, 'BM Heuchelhof', 'Heuchelhof', 'Residential', TRUE, '2019-09-01', 4800, 85),
  (5, 'BM Lengfeld', 'Lengfeld', 'Commercial', TRUE, '2020-08-01', 5500, 70),
  (6, 'BM Mainfrankenpark', 'Mainfrankenpark', 'Shopping', TRUE, '2021-04-01', 7200, 90),
  (7, 'BM Grombühl', 'Grombühl', 'Hospital', FALSE, '2022-01-15', 4500, 50),
  (8, 'BM Zellerau', 'Zellerau', 'Mixed', FALSE, '2023-03-01', 4000, 65);

DROP TABLE IF EXISTS dim_product;
CREATE TABLE dim_product (product_id INTEGER PRIMARY KEY, product_name VARCHAR(50), category VARCHAR(30), subcategory VARCHAR(30), is_vegetarian BOOLEAN, unit_price DECIMAL(10,2));
INSERT INTO dim_product (product_id, product_name, category, subcategory, is_vegetarian, unit_price) VALUES
  (4, 'Bacon King', 'Burger', 'Beef', 0, 10.51),
  (5, 'Chicken Burger', 'Burger', 'Chicken', 0, 7.88),
  (8, 'Kids Burger', 'Burger', 'Kids', 0, 3.93),
  (10, 'Beyond Burger', 'Burger', 'Vegan', 1, 10.51),
  (13, 'Green Goddess Bowl', 'Burger', 'Vegan', 1, 11.82),
  (15, 'Small Fries', 'Side', 'Fries', 1, 2.62),
  (16, 'Medium Fries', 'Side', 'Fries', 1, 3.27),
  (17, 'Large Fries', 'Side', 'Fries', 1, 3.93),
  (18, 'Chicken Nuggets 6pc', 'Side', 'Nuggets', 0, 4.59),
  (20, 'Onion Rings', 'Side', 'Fried', 1, 3.93),
  (21, 'Side Salad', 'Side', 'Salad', 1, 3.93),
  (22, 'Coleslaw', 'Side', 'Salad', 1, 3.01),
  (26, 'Cola 0.3l', 'Drink', 'Soft Drink', 1, 2.88),
  (27, 'Cola 0.5l', 'Drink', 'Soft Drink', 1, 3.8),
  (28, 'Fanta 0.3l', 'Drink', 'Soft Drink', 1, 2.88),
  (29, 'Sprite 0.3l', 'Drink', 'Soft Drink', 1, 2.88),
  (31, 'Ice Tea 0.3l', 'Drink', 'Soft Drink', 1, 3.27),
  (32, 'Coffee', 'Drink', 'Hot Drink', 1, 2.62),
  (33, 'Cappuccino', 'Drink', 'Hot Drink', 1, 3.93),
  (34, 'Milkshake Vanilla', 'Drink', 'Milkshake', 1, 5.25),
  (36, 'Milkshake Strawberry', 'Drink', 'Milkshake', 1, 5.25),
  (37, 'Fresh OJ', 'Drink', 'Juice', 1, 4.19),
  (38, 'Beer 0.3l', 'Drink', 'Alcohol', 1, 4.59),
  (39, 'Hot Chocolate', 'Drink', 'Hot Drink', 1, 4.19),
  (40, 'Craft Lemonade', 'Drink', 'Soft Drink', 1, 4.59),
  (42, 'Soft Ice Chocolate', 'Dessert', 'Ice Cream', 1, 2.35),
  (45, 'Apple Pie', 'Dessert', 'Pastry', 1, 2.62),
  (46, 'Cookie Chocolate', 'Dessert', 'Pastry', 1, 1.7),
  (49, 'Breakfast Burger', 'Breakfast', 'Burger', 0, 5.9),
  (54, 'Ketchup Extra', 'Extra', 'Sauce', 1, 0.53),
  (56, 'BBQ Sauce', 'Extra', 'Sauce', 1, 0.53);

DROP TABLE IF EXISTS dim_customer;
CREATE TABLE dim_customer (customer_id INTEGER PRIMARY KEY, age_group VARCHAR(10), gender VARCHAR(15), home_district VARCHAR(30), has_app BOOLEAN, loyalty_tier VARCHAR(10));
INSERT INTO dim_customer (customer_id, age_group, gender, home_district, has_app, loyalty_tier) VALUES
  (249, '65+', 'Male', 'Rottenbauer', FALSE, 'None'),
  (459, '<18', 'Male', 'Sanderau', FALSE, 'None'),
  (1250, '35-44', 'Male', 'Lengfeld', TRUE, 'Bronze'),
  (1943, '45-54', 'Male', 'Sanderau', FALSE, 'None'),
  (2691, '25-34', 'Female', 'Heidingsfeld', TRUE, 'Bronze'),
  (5967, '55-64', 'Male', 'Sanderau', FALSE, 'None'),
  (6923, '18-24', 'Male', 'Versbach', TRUE, 'Gold'),
  (8315, '25-34', 'Male', 'Lindleinsmühle', TRUE, 'Bronze'),
  (8662, '25-34', 'Female', 'Grombühl', TRUE, 'Silver'),
  (9669, '35-44', 'Female', 'Zellerau', TRUE, 'None'),
  (14240, '18-24', 'Female', 'Frauenland', FALSE, 'None'),
  (16010, '25-34', 'Female', 'Lengfeld', TRUE, 'Gold'),
  (18641, '55-64', 'Male', 'Heidingsfeld', FALSE, 'None'),
  (19890, '55-64', 'Male', 'Grombühl', FALSE, 'None'),
  (21454, '45-54', 'Female', 'Rottenbauer', FALSE, 'None'),
  (21966, '65+', 'Female', 'Frauenland', FALSE, 'None'),
  (22612, '35-44', 'Female', 'Sanderau', TRUE, 'Silver'),
  (23371, '<18', 'Male', 'Sanderau', FALSE, 'None'),
  (24815, '55-64', 'Male', 'Heidingsfeld', FALSE, 'None');

DROP TABLE IF EXISTS dim_payment_method;
CREATE TABLE dim_payment_method (payment_id INTEGER PRIMARY KEY, payment_type VARCHAR(30), payment_provider VARCHAR(30));
INSERT INTO dim_payment_method (payment_id, payment_type, payment_provider) VALUES
  (1, 'Cash', 'Cash'),
  (2, 'EC Card', 'Girocard'),
  (3, 'Credit Card', 'Visa/Mastercard'),
  (4, 'Mobile Payment', 'Apple Pay/Google Pay');

DROP TABLE IF EXISTS dim_promotion;
CREATE TABLE dim_promotion (promo_id INTEGER PRIMARY KEY, promo_name VARCHAR(40), promo_type VARCHAR(30), discount_pct INTEGER);
INSERT INTO dim_promotion (promo_id, promo_name, promo_type, discount_pct) VALUES
  (0, 'No Promotion', 'None', 0),
  (1, 'Grand Opening 15%', 'Opening', 15),
  (2, 'Happy Hour 15%', 'Time-Based', 15),
  (3, 'Student Discount 8%', 'Segment', 8),
  (4, 'Family Bundle 12%', 'Bundle', 12),
  (5, 'App Welcome 10%', 'App', 10),
  (6, 'Loyalty Gold 20%', 'Loyalty', 20),
  (7, 'Seasonal Special 10%', 'Seasonal', 10),
  (8, 'Weekend Deal 10%', 'Time-Based', 10),
  (9, 'Birthday Offer 25%', 'Segment', 25),
  (10, 'Combo Saver 15%', 'Bundle', 15),
  (11, 'Vegan Week 10%', 'Seasonal', 10),
  (12, 'COVID Delivery 10%', 'Delivery', 10);

DROP TABLE IF EXISTS dim_date;
CREATE TABLE dim_date (date DATE PRIMARY KEY, year INTEGER, quarter VARCHAR(2), month INTEGER, month_name VARCHAR(15), day_name VARCHAR(15), is_weekend BOOLEAN, season VARCHAR(10));
INSERT INTO dim_date (date, year, quarter, month, month_name, day_name, is_weekend, season) VALUES
  ('2017-05-18', 2017, 'Q2', 5, 'May', 'Thursday', FALSE, 'Spring'),
  ('2017-10-20', 2017, 'Q4', 10, 'October', 'Friday', FALSE, 'Autumn'),
  ('2018-05-13', 2018, 'Q2', 5, 'May', 'Sunday', TRUE, 'Spring'),
  ('2018-10-11', 2018, 'Q4', 10, 'October', 'Thursday', FALSE, 'Autumn'),
  ('2019-04-05', 2019, 'Q2', 4, 'April', 'Friday', FALSE, 'Spring'),
  ('2019-10-03', 2019, 'Q4', 10, 'October', 'Thursday', FALSE, 'Autumn'),
  ('2020-04-23', 2020, 'Q2', 4, 'April', 'Thursday', FALSE, 'Spring'),
  ('2020-10-03', 2020, 'Q4', 10, 'October', 'Saturday', TRUE, 'Autumn'),
  ('2021-04-02', 2021, 'Q2', 4, 'April', 'Friday', FALSE, 'Spring'),
  ('2021-10-04', 2021, 'Q4', 10, 'October', 'Monday', FALSE, 'Autumn'),
  ('2022-05-01', 2022, 'Q2', 5, 'May', 'Sunday', TRUE, 'Spring'),
  ('2022-10-02', 2022, 'Q4', 10, 'October', 'Sunday', TRUE, 'Autumn'),
  ('2023-04-01', 2023, 'Q2', 4, 'April', 'Saturday', TRUE, 'Spring'),
  ('2023-10-07', 2023, 'Q4', 10, 'October', 'Saturday', TRUE, 'Autumn'),
  ('2024-05-01', 2024, 'Q2', 5, 'May', 'Wednesday', FALSE, 'Spring'),
  ('2024-10-02', 2024, 'Q4', 10, 'October', 'Wednesday', FALSE, 'Autumn'),
  ('2025-04-01', 2025, 'Q2', 4, 'April', 'Tuesday', FALSE, 'Spring'),
  ('2025-10-03', 2025, 'Q4', 10, 'October', 'Friday', FALSE, 'Autumn'),
  ('2026-02-12', 2026, 'Q1', 2, 'February', 'Thursday', FALSE, 'Winter');

DROP TABLE IF EXISTS dim_supplier;
CREATE TABLE dim_supplier (supplier_id INTEGER PRIMARY KEY, supplier_name VARCHAR(50), category VARCHAR(30), city VARCHAR(30));
INSERT INTO dim_supplier (supplier_id, supplier_name, category, city) VALUES
  (1, 'Franken Fleisch GmbH', 'Meat', 'Würzburg'),
  (2, 'BioGemüse Bayern', 'Vegetables', 'Veitshöchheim'),
  (3, 'Würzburger Bäckerei', 'Bakery', 'Würzburg'),
  (4, 'Main-Getränke AG', 'Beverages', 'Kitzingen'),
  (5, 'Süßes Franken', 'Desserts', 'Ochsenfurt'),
  (6, 'TiefkühlProfi GmbH', 'Frozen', 'Schweinfurt'),
  (7, 'Verpackung Plus', 'Packaging', 'Nürnberg'),
  (8, 'Clean & Fresh Services', 'Cleaning', 'Würzburg');

DROP TABLE IF EXISTS fact_orders;
CREATE TABLE fact_orders (order_id INTEGER PRIMARY KEY, date DATE, hour INTEGER, branch_id INTEGER, customer_id INTEGER, payment_id INTEGER, promo_id INTEGER, order_channel VARCHAR(20), item_count INTEGER, gross_total DECIMAL(10,2), discount_amount DECIMAL(10,2), net_total DECIMAL(10,2), order_duration_min INTEGER, satisfaction_score DECIMAL(3,2));
INSERT INTO fact_orders (order_id, date, hour, branch_id, customer_id, payment_id, promo_id, order_channel, item_count, gross_total, discount_amount, net_total, order_duration_min, satisfaction_score) VALUES
  (1954, '2017-05-18', 17, 1, 18641, 1, 0, 'Drive-Through', 3, 11.37, 0.0, 11.37, 3, NULL),
  (9770, '2017-10-20', 20, 1, 1250, 2, 0, 'Counter', 3, 8.47, 0.0, 8.47, 4, NULL),
  (19540, '2018-05-13', 12, 1, 21454, 2, 8, 'Drive-Through', 4, 16.27, 1.63, 14.64, 5, NULL),
  (33218, '2018-10-11', 14, 2, 22612, 1, 0, 'Counter', 4, 11.95, 0.0, 11.95, 9, NULL),
  (50804, '2019-04-05', 11, 3, 5967, 2, 0, 'Counter', 4, 16.97, 0.0, 16.97, 9, NULL),
  (78160, '2019-10-03', 17, 3, 21966, 1, 0, 'Counter', 3, 8.05, 0.0, 8.05, 8, NULL),
  (107470, '2020-04-23', 10, 1, 1943, 3, 0, 'Drive-Through', 5, 16.8, 0.0, 16.8, 3, NULL),
  (130918, '2020-10-03', 8, 3, 249, 3, 0, 'Counter', 2, 5.28, 0.0, 5.28, 14, NULL),
  (149481, '2021-04-02', 19, 1, 6923, 3, 0, 'Drive-Through', 2, 6.49, 0.0, 6.49, 4, NULL),
  (191492, '2021-10-04', 20, 3, 16010, 2, 0, 'App Order', 3, 8.0, 0.0, 8.0, 2, NULL),
  (247181, '2022-05-01', 17, 4, 459, 3, 0, 'Drive-Through', 2, 2.53, 0.0, 2.53, 3, NULL),
  (298962, '2022-10-02', 17, 1, 8315, 1, 0, 'Counter', 5, 21.2, 0.0, 21.2, 7, NULL),
  (353674, '2023-04-01', 13, 4, 8662, 3, 0, 'Drive-Through', 4, 15.21, 0.0, 15.21, 6, NULL),
  (424018, '2023-10-07', 18, 4, 23371, 2, 0, 'Drive-Through', 2, 6.69, 0.0, 6.69, 6, 3.0),
  (494362, '2024-05-01', 7, 6, 9669, 4, 0, 'Drive-Through', 2, 7.16, 0.0, 7.16, 5, NULL),
  (554936, '2024-10-02', 14, 6, 24815, 1, 0, 'Drive-Through', 2, 7.79, 0.0, 7.79, 6, NULL),
  (617464, '2025-04-01', 16, 1, 2691, 4, 0, 'App Order', 2, 5.78, 0.0, 5.78, 1, NULL),
  (690739, '2025-10-03', 12, 2, 14240, 3, 0, 'Counter', 2, 14.43, 0.0, 14.43, 11, 4.0),
  (737635, '2026-02-12', 15, 4, 19890, 3, 0, 'Counter', 4, 12.04, 0.0, 12.04, 3, 3.0);

DROP TABLE IF EXISTS fact_order_items;
CREATE TABLE fact_order_items (order_item_id INTEGER PRIMARY KEY, order_id INTEGER, product_id INTEGER, quantity INTEGER, unit_price DECIMAL(10,2), line_total DECIMAL(10,2));
INSERT INTO fact_order_items (order_item_id, order_id, product_id, quantity, unit_price, line_total) VALUES
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
