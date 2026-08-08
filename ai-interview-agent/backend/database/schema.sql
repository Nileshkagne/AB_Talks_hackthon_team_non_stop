-- 1. interview_sessions
create table if not exists interview_sessions (
  session_id           text primary key,
  candidate_id         text not null,
  status               text not null default 'active',
  question_count       int not null default 0,
  follow_up_count      int not null default 0,
  current_day          int,
  current_topic        text,
  difficulty           text not null default 'intermediate',
  covered_days         int[] not null default '{}',
  strengths            text[] not null default '{}',
  weaknesses           text[] not null default '{}',
  created_at           timestamptz not null default now(),
  updated_at           timestamptz not null default now()
);

-- 2. interview_messages
create table if not exists interview_messages (
  id                   bigserial primary key,
  session_id           text not null references interview_sessions(session_id) on delete cascade,
  role                 text not null,
  content              text not null,
  question_number      int,
  curriculum_day       int,
  topic                text,
  question_type        text,
  created_at           timestamptz not null default now()
);

-- 3. answer_evaluations
create table if not exists answer_evaluations (
  id                   bigserial primary key,
  session_id           text not null references interview_sessions(session_id) on delete cascade,
  question_number      int not null,
  question             text not null,
  answer               text not null,
  curriculum_day       int,
  topic                text,
  correctness          numeric default 0,
  technical_depth      numeric default 0,
  reasoning            numeric default 0,
  practicality         numeric default 0,
  communication        numeric default 0,
  overall_score        numeric default 0,
  confidence           numeric default 1.0,
  missing_concepts     text[] default '{}',
  follow_up_needed     boolean default false,
  evaluation_summary   text,
  created_at           timestamptz not null default now()
);

-- 4. interview_feedback
create table if not exists interview_feedback (
  session_id           text primary key references interview_sessions(session_id) on delete cascade,
  summary              text not null,
  strengths            text[] not null default '{}',
  gaps                 text[] not null default '{}',
  next_steps           text[] not null default '{}',
  overall_score        numeric,
  created_at           timestamptz not null default now()
);

-- Indexes
create index if not exists idx_messages_session on interview_messages(session_id);
create index if not exists idx_evaluations_session on answer_evaluations(session_id);
create index if not exists idx_sessions_status on interview_sessions(status);
