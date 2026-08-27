-- 0001_schema_und_dimensionen.sql
-- Zweck: Schema burgermetrics und die zehn Dimensionstabellen des
--        Galaxy-Schemas, spaltengleich mit dataset/*.csv und den Folien.
-- Objekte: Schema burgermetrics; dim_branch, dim_customer, dim_date,
--          dim_employee, dim_payment_method, dim_product, dim_promotion,
--          dim_supplier, dim_time_slot, dim_weather.
-- Ruecknahme: DROP SCHEMA burgermetrics CASCADE;
-- Idempotent: ja.

CREATE SCHEMA IF NOT EXISTS burgermetrics;
SET search_path TO burgermetrics;

CREATE TABLE IF NOT EXISTS dim_branch (
  branch_id          bigint PRIMARY KEY,
  branch_name        text NOT NULL,
  address            text,
  district           text,
  city               text,
  postal_code        text,
  latitude           double precision,
  longitude          double precision,
  size_sqm           integer,
  seats_indoor       integer,
  seats_outdoor      integer,
  has_drive_through  boolean,
  has_playground     boolean,
  parking_spots      integer,
  opening_date       date,
  monthly_rent_eur   numeric(10,2),
  branch_type        text
);

CREATE TABLE IF NOT EXISTS dim_customer (
  customer_id         bigint PRIMARY KEY,
  age_group           text,
  gender              text,
  home_district       text,
  first_visit_year    integer,
  has_app             boolean,
  app_registered_date date,
  loyalty_tier        text            -- enthaelt bewusst den Text 'None'
);

CREATE TABLE IF NOT EXISTS dim_date (
  date_id        bigint PRIMARY KEY,
  date           date NOT NULL UNIQUE,
  year           integer,
  quarter        text,
  month          integer,
  month_name     text,
  calendar_week  integer,
  day_of_month   integer,
  day_of_week    integer,
  day_name       text,
  is_weekend     boolean,
  is_holiday     boolean,
  holiday_name   text,
  special_event  text,
  season         text
);

CREATE TABLE IF NOT EXISTS dim_employee (
  employee_id  bigint PRIMARY KEY,
  branch_id    bigint REFERENCES dim_branch(branch_id),
  role         text,
  hire_date    date,
  hourly_wage  numeric(6,2),
  is_fulltime  boolean
);

CREATE TABLE IF NOT EXISTS dim_payment_method (
  payment_id           bigint PRIMARY KEY,
  payment_type         text,
  payment_provider     text,
  transaction_fee_pct  numeric(5,2)
);

CREATE TABLE IF NOT EXISTS dim_product (
  product_id       bigint PRIMARY KEY,
  product_name     text NOT NULL,
  category         text,
  subcategory      text,
  base_price_2017  numeric(6,2),
  cost_price_2017  numeric(6,2),
  is_vegetarian    boolean,
  is_vegan         boolean,
  calories         integer,
  allergens        text,
  introduced       date,
  unit_price       numeric(6,2),
  cost_price       numeric(6,2)
);

CREATE TABLE IF NOT EXISTS dim_promotion (
  promo_id      bigint PRIMARY KEY,
  promo_name    text,
  promo_type    text,
  discount_pct  integer
);

CREATE TABLE IF NOT EXISTS dim_supplier (
  supplier_id         bigint PRIMARY KEY,
  supplier_name       text,
  category            text,
  city                text,
  contract_start      date,
  payment_terms_days  integer
);

CREATE TABLE IF NOT EXISTS dim_time_slot (
  hour       integer PRIMARY KEY,
  time_slot  text
);

CREATE TABLE IF NOT EXISTS dim_weather (
  date                 date PRIMARY KEY,
  temperature_celsius  numeric(5,1),
  condition            text,
  precipitation_mm     numeric(6,1),
  wind_speed_kmh       numeric(6,1)
);
