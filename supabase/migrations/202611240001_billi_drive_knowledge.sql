-- BILLI R-20 private Drive knowledge store.
-- Apply this migration in the Supabase SQL Editor before configuring Vercel.
create extension if not exists vector with schema extensions;

create table if not exists public.billi_drive_files (
    drive_file_id text primary key,
    name text not null,
    mime_type text not null default 'application/octet-stream',
    modified_time timestamptz,
    version_key text not null,
    web_view_link text,
    language text not null default 'en' check (language in ('en', 'ta', 'si')),
    status text not null default 'indexed' check (status in ('indexed', 'skipped', 'error')),
    chunk_count integer not null default 0,
    indexed_at timestamptz,
    last_error text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.billi_knowledge_chunks (
    id bigint generated always as identity primary key,
    drive_file_id text not null references public.billi_drive_files(drive_file_id) on delete cascade,
    chunk_index integer not null,
    language text not null check (language in ('en', 'ta', 'si')),
    content text not null,
    embedding extensions.vector(768),
    metadata jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    unique (drive_file_id, chunk_index)
);

create index if not exists billi_knowledge_chunks_drive_file_idx
    on public.billi_knowledge_chunks (drive_file_id);
create index if not exists billi_knowledge_chunks_language_idx
    on public.billi_knowledge_chunks (language);
create index if not exists billi_knowledge_chunks_embedding_idx
    on public.billi_knowledge_chunks
    using hnsw (embedding extensions.vector_cosine_ops)
    where embedding is not null;

create table if not exists public.billi_drive_sync_jobs (
    id uuid primary key,
    folder_id text not null,
    status text not null default 'running' check (status in ('running', 'completed', 'failed')),
    state jsonb not null default '{}'::jsonb,
    files_seen integer not null default 0,
    files_indexed integer not null default 0,
    files_skipped integer not null default 0,
    error text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

-- Replace one Drive source and all of its chunks atomically.
create or replace function public.replace_billi_knowledge_file(p_file jsonb, p_chunks jsonb)
returns void
language plpgsql
security definer
set search_path = public, extensions
as $$
declare
    item jsonb;
begin
    insert into public.billi_drive_files (
        drive_file_id, name, mime_type, modified_time, version_key, web_view_link,
        language, status, chunk_count, indexed_at, last_error, updated_at
    ) values (
        p_file->>'drive_file_id',
        coalesce(p_file->>'name', p_file->>'drive_file_id'),
        coalesce(p_file->>'mime_type', 'application/octet-stream'),
        nullif(p_file->>'modified_time', '')::timestamptz,
        coalesce(p_file->>'version_key', ''),
        nullif(p_file->>'web_view_link', ''),
        coalesce(p_file->>'language', 'en'),
        coalesce(p_file->>'status', 'indexed'),
        coalesce((p_file->>'chunk_count')::integer, 0),
        nullif(p_file->>'indexed_at', '')::timestamptz,
        nullif(p_file->>'last_error', ''),
        now()
    )
    on conflict (drive_file_id) do update set
        name = excluded.name,
        mime_type = excluded.mime_type,
        modified_time = excluded.modified_time,
        version_key = excluded.version_key,
        web_view_link = excluded.web_view_link,
        language = excluded.language,
        status = excluded.status,
        chunk_count = excluded.chunk_count,
        indexed_at = excluded.indexed_at,
        last_error = excluded.last_error,
        updated_at = now();

    delete from public.billi_knowledge_chunks
    where drive_file_id = p_file->>'drive_file_id';

    for item in select value from jsonb_array_elements(coalesce(p_chunks, '[]'::jsonb))
    loop
        insert into public.billi_knowledge_chunks (
            drive_file_id, chunk_index, language, content, embedding, metadata
        ) values (
            p_file->>'drive_file_id',
            (item->>'chunk_index')::integer,
            coalesce(item->>'language', p_file->>'language', 'en'),
            item->>'content',
            case
                when item->'embedding' is null or item->'embedding' = 'null'::jsonb then null
                else (item->>'embedding')::extensions.vector(768)
            end,
            coalesce(item->'metadata', '{}'::jsonb)
        );
    end loop;
end;
$$;

create or replace function public.match_billi_knowledge(
    p_query_embedding extensions.vector(768),
    p_match_count integer default 8,
    p_language text default null
)
returns table (
    drive_file_id text,
    source_name text,
    web_view_link text,
    language text,
    chunk_index integer,
    content text,
    similarity double precision
)
language sql
stable
security definer
set search_path = public, extensions
as $$
    select
        c.drive_file_id,
        f.name,
        f.web_view_link,
        c.language,
        c.chunk_index,
        c.content,
        (1 - (c.embedding <=> p_query_embedding))::double precision as similarity
    from public.billi_knowledge_chunks c
    join public.billi_drive_files f on f.drive_file_id = c.drive_file_id
    where c.embedding is not null
      and (p_language is null or p_language = '' or c.language = p_language)
    order by c.embedding <=> p_query_embedding
    limit greatest(1, least(coalesce(p_match_count, 8), 20));
$$;

create or replace function public.search_billi_knowledge_keyword(
    p_query text,
    p_match_count integer default 8,
    p_language text default null
)
returns table (
    drive_file_id text,
    source_name text,
    web_view_link text,
    language text,
    chunk_index integer,
    content text,
    similarity double precision
)
language sql
stable
security definer
set search_path = public
as $$
    select
        c.drive_file_id,
        f.name,
        f.web_view_link,
        c.language,
        c.chunk_index,
        c.content,
        ts_rank(to_tsvector('simple', c.content), plainto_tsquery('simple', p_query))::double precision as similarity
    from public.billi_knowledge_chunks c
    join public.billi_drive_files f on f.drive_file_id = c.drive_file_id
    where length(trim(coalesce(p_query, ''))) > 0
      and to_tsvector('simple', c.content) @@ plainto_tsquery('simple', p_query)
      and (p_language is null or p_language = '' or c.language = p_language)
    order by similarity desc
    limit greatest(1, least(coalesce(p_match_count, 8), 20));
$$;

-- Private-by-default. Only the FastAPI backend's service role can read or write.
alter table public.billi_drive_files enable row level security;
alter table public.billi_knowledge_chunks enable row level security;
alter table public.billi_drive_sync_jobs enable row level security;

revoke all on public.billi_drive_files from public, anon, authenticated;
revoke all on public.billi_knowledge_chunks from public, anon, authenticated;
revoke all on public.billi_drive_sync_jobs from public, anon, authenticated;
grant all on public.billi_drive_files to service_role;
grant all on public.billi_knowledge_chunks to service_role;
grant all on public.billi_drive_sync_jobs to service_role;
grant usage, select on sequence public.billi_knowledge_chunks_id_seq to service_role;

revoke all on function public.replace_billi_knowledge_file(jsonb, jsonb) from public, anon, authenticated;
revoke all on function public.match_billi_knowledge(extensions.vector, integer, text) from public, anon, authenticated;
revoke all on function public.search_billi_knowledge_keyword(text, integer, text) from public, anon, authenticated;
grant execute on function public.replace_billi_knowledge_file(jsonb, jsonb) to service_role;
grant execute on function public.match_billi_knowledge(extensions.vector, integer, text) to service_role;
grant execute on function public.search_billi_knowledge_keyword(text, integer, text) to service_role;
