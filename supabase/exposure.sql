-- Server-only exposure history, separate from public/anonymous API tables.
create schema if not exists app_private;
revoke all on schema app_private from public, anon, authenticated;

create table if not exists app_private.exposure_lists (
  id text primary key,
  created double precision not null,
  shown double precision,
  places text not null check (jsonb_typeof(places::jsonb) = 'array')
);
create index if not exists exposure_lists_shown on app_private.exposure_lists(shown);
create index if not exists exposure_lists_pending on app_private.exposure_lists(created) where shown is null;
alter table app_private.exposure_lists enable row level security;
revoke all on app_private.exposure_lists from public, anon, authenticated;

-- Additive migration: old rows remain legacy, without reconstructed candidate history.
alter table app_private.exposure_lists add column if not exists policy text not null default 'legacy';
alter table app_private.exposure_lists add column if not exists policy_version text not null default 'legacy';
alter table app_private.exposure_lists add column if not exists mode text not null default 'production';
alter table app_private.exposure_lists add column if not exists run_id text;
alter table app_private.exposure_lists add column if not exists context text;
create index if not exists exposure_lists_analysis on app_private.exposure_lists(mode,policy,run_id,created);

create table if not exists app_private.exposure_candidates (
  request_id text not null references app_private.exposure_lists(id) on delete cascade,
  place_id text not null,
  walk_seconds double precision not null check (walk_seconds >= 0),
  duration_min double precision not null check (duration_min > 0),
  projected_total_seconds double precision not null check (projected_total_seconds >= 0),
  assigned_rank integer check (assigned_rank between 1 and 3),
  expected_exposure double precision not null check (expected_exposure between 0 and 1),
  primary key (request_id,place_id),
  unique (request_id,assigned_rank)
);
create index if not exists exposure_candidates_place on app_private.exposure_candidates(place_id,request_id);
alter table app_private.exposure_candidates enable row level security;
revoke all on app_private.exposure_candidates from public, anon, authenticated;
