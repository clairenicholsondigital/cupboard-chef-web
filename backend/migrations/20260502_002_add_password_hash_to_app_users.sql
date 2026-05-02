alter table if exists app_users
  add column if not exists password_hash text;

create index if not exists idx_app_users_email_lower
  on app_users (lower(email));
