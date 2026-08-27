-- 0003_obt.sql
-- Zweck: One Big Table obt_orders — nicht hochgeladen, sondern aus dem
--        Galaxy-Schema erzeugt. Derselbe Join, den dataset/generate_obt.py
--        auf den CSVs rechnet; Spaltenfolge exakt wie obt_orders.csv.
-- Ruecknahme: DROP TABLE burgermetrics.obt_orders;
-- Idempotent: ja (DROP + CREATE).

SET search_path TO burgermetrics;

DROP TABLE IF EXISTS obt_orders;
CREATE TABLE obt_orders AS
SELECT o.order_id, o.date, o.time, o.hour, o.branch_id, o.customer_id,
       o.payment_id, o.promo_id, o.order_channel, o.item_count,
       o.distinct_items, o.gross_total, o.discount_amount, o.net_total,
       o.order_duration_min, o.satisfaction_score,
       b.branch_name, b.district, b.branch_type, b.has_drive_through,
       b.opening_date,
       c.age_group, c.gender, c.has_app, c.loyalty_tier, c.home_district,
       p.payment_type,
       pr.promo_name, pr.promo_type, pr.discount_pct,
       d.year, d.quarter, d.month, d.month_name, d.day_name, d.is_weekend,
       d.is_holiday, d.special_event, d.season,
       w.temperature_celsius, w.condition
FROM fact_orders o
JOIN dim_branch          b  USING (branch_id)
JOIN dim_customer        c  USING (customer_id)
JOIN dim_payment_method  p  USING (payment_id)
JOIN dim_promotion       pr USING (promo_id)
JOIN dim_date            d  USING (date)
LEFT JOIN dim_weather    w  USING (date);

ALTER TABLE obt_orders ADD PRIMARY KEY (order_id);
CREATE INDEX ix_obt_year   ON obt_orders(year);
CREATE INDEX ix_obt_branch ON obt_orders(branch_id);
