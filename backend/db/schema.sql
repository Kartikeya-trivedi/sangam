-- SETU central store: Postgres + pgvector (spec §6)
create extension if not exists vector;

create table if not exists persons (
  id uuid primary key default gen_random_uuid(),
  role text not null,
  profile jsonb not null,           -- the structured Person fields
  face_embedding vector(512),
  is_minor boolean default false,
  status text default 'open',       -- open | matched | reunited | expired
  centre_id text,                   -- which camp logged it
  created_at timestamptz default now(),
  ttl_expires_at timestamptz
);

create index if not exists persons_face_embedding_idx
  on persons using ivfflat (face_embedding vector_cosine_ops);

create table if not exists audit_log (
  id uuid primary key default gen_random_uuid(),
  actor text,
  action text,
  person_id uuid,
  meta jsonb,
  at timestamptz default now()
);
