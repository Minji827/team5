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
