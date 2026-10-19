-- Busan Full-Course 프로젝트 Supabase 스키마
-- 전부 `id`(deterministic md5, scripts/clean_data.py에서 생성)를 PK로 써서
-- load_to_supabase.py가 upsert로 재실행해도 중복이 생기지 않는다 (멱등성).

create table if not exists merchants (
  id              text primary key,
  source          text not null,
  source_id       text,
  name            text not null,
  category_major  text,
  category_minor  text,
  address         text,
  lon             double precision,
  lat             double precision,
  data_date       text
);

create table if not exists tourist_spots (
  id              text primary key,
  source          text not null,
  source_id       text,
  name            text not null,
  category_major  text,
  category_minor  text,
  address         text,
  lon             double precision,
  lat             double precision,
  data_date       text
);

create table if not exists consumption (
  id                text primary key,
  year_month        integer not null,
  gu                text,
  dong_region_code  bigint,
  dong_name         text,
  lon               double precision,
  lat               double precision,
  category          text,
  amount_krw        bigint
);

create table if not exists visitors (
  id                text primary key,
  period            text,
  region            text,
  foreign_visitors  numeric
);

create table if not exists commercial_density (
  id              text primary key,
  snapshot_date   text,
  gu              text,
  dong            text,
  category_major  text,
  store_count     integer,
  lon             double precision,
  lat             double precision
);

create index if not exists idx_merchants_geo on merchants (lon, lat);
create index if not exists idx_tourist_spots_geo on tourist_spots (lon, lat);
create index if not exists idx_consumption_region_month on consumption (dong_region_code, year_month);
create index if not exists idx_commercial_density_geo on commercial_density (lon, lat);
