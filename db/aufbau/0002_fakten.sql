-- 0002_fakten.sql
-- Zweck: die beiden Faktentabellen des Galaxy-Schemas.
--        fact_orders: Grain eine Bestellung. fact_order_items: Grain eine
--        Position. Genau die zwei Granularitaeten der Folien.
-- Ruecknahme: DROP TABLE burgermetrics.fact_order_items, burgermetrics.fact_orders;
-- Idempotent: ja.

SET search_path TO burgermetrics;

CREATE TABLE IF NOT EXISTS fact_orders (
  order_id            bigint PRIMARY KEY,
  date                date NOT NULL REFERENCES dim_date(date),
  time                time,
  hour                integer,
  branch_id           bigint REFERENCES dim_branch(branch_id),
  customer_id         bigint REFERENCES dim_customer(customer_id),
  payment_id          bigint REFERENCES dim_payment_method(payment_id),
  promo_id            bigint REFERENCES dim_promotion(promo_id),
  order_channel       text,
  item_count          integer,
  distinct_items      integer,
  gross_total         numeric(10,2),
  discount_amount     numeric(10,2),
  net_total           numeric(10,2),
  order_duration_min  integer,
  satisfaction_score  numeric(3,2)
);

CREATE TABLE IF NOT EXISTS fact_order_items (
  order_item_id  bigint PRIMARY KEY,
  order_id       bigint NOT NULL REFERENCES fact_orders(order_id),
  product_id     bigint NOT NULL REFERENCES dim_product(product_id),
  quantity       integer NOT NULL,
  unit_price     numeric(8,2),
  line_total     numeric(10,2)
);

CREATE INDEX IF NOT EXISTS ix_orders_date    ON fact_orders(date);
CREATE INDEX IF NOT EXISTS ix_orders_branch  ON fact_orders(branch_id);
CREATE INDEX IF NOT EXISTS ix_items_order    ON fact_order_items(order_id);
CREATE INDEX IF NOT EXISTS ix_items_product  ON fact_order_items(product_id);
