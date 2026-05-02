create extension if not exists pgcrypto;

create table if not exists cupboard_ingredients (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  normalised_name text not null unique,
  category text,
  common_swaps jsonb not null default '[]'::jsonb,
  dietary_tags text[] not null default '{}'::text[],
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists recipe_suggestions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid null,
  input_ingredients text[] not null default '{}'::text[],
  dietary_filters text[] not null default '{}'::text[],
  use_first text[] not null default '{}'::text[],
  time_minutes integer,
  servings integer,
  recipes jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists shopping_lists (
  id uuid primary key default gen_random_uuid(),
  user_id uuid null,
  source_recipe_titles text[] not null default '{}'::text[],
  items text[] not null default '{}'::text[],
  created_at timestamptz not null default now()
);

create table if not exists recipe_feedback (
  id uuid primary key default gen_random_uuid(),
  user_id uuid null,
  recipe_suggestion_id uuid null,
  recipe_title text not null,
  feedback_type text not null,
  notes text,
  created_at timestamptz not null default now()
);

create index if not exists idx_cupboard_ingredients_normalised_name on cupboard_ingredients(normalised_name);
create index if not exists idx_recipe_suggestions_created_at on recipe_suggestions(created_at);
create index if not exists idx_shopping_lists_created_at on shopping_lists(created_at);
create index if not exists idx_recipe_feedback_recipe_title on recipe_feedback(recipe_title);
create index if not exists idx_recipe_feedback_created_at on recipe_feedback(created_at);
