# Cupboard Chef Database Schema (v1)

This document describes the current PostgreSQL schema for the Cupboard Chef application.

---

## Extensions

- `pgcrypto` — used for UUID generation

---

## Enums

### `input_method`
- text
- voice
- imported

### `meal_time_code`
- am
- breakfast
- lunch
- pm
- dinner
- evening
- snack
- late_night

### `entry_status`
- draft
- logged
- archived
- deleted

### `stock_status`
- in_stock
- low
- out_of_stock

### `achievement_type`
- streak
- logging
- variety
- ingredient
- consistency
- challenge
- custom

### `challenge_status`
- draft
- active
- completed
- expired
- cancelled

### `suggestion_type`
- recipe
- ingredient
- meal_repeat
- challenge
- seasonal
- storecupboard

---

## Core Function

### `set_updated_at()`
Automatically updates `updated_at` timestamps on row updates.

---

## Tables

### `app_users`
| Column         | Type        |
|----------------|------------|
| id             | uuid (PK)  |
| auth_user_id   | uuid       |
| email          | text       |
| display_name   | text       |
| created_at     | timestamptz|
| updated_at     | timestamptz|

---

### `user_profiles`
| Column                     | Type        |
|----------------------------|------------|
| id                         | uuid (PK)  |
| user_id                    | uuid (FK)  |
| app_theme                  | text       |
| preferred_meal_time_labels | jsonb      |
| onboarding_completed       | boolean    |
| timezone                   | text       |
| locale                     | text       |
| created_at                 | timestamptz|
| updated_at                 | timestamptz|

---

### `ingredient_catalogue`
| Column           | Type        |
|------------------|------------|
| id               | uuid (PK)  |
| canonical_name   | text (unique) |
| display_name     | text       |
| category         | text       |
| is_seasonal      | boolean    |
| seasonal_months  | integer[]  |
| created_at       | timestamptz|
| updated_at       | timestamptz|

---

### `recipe_catalogue`
| Column             | Type        |
|--------------------|------------|
| id                 | uuid (PK)  |
| title              | text       |
| description        | text       |
| instructions       | text       |
| source_url         | text       |
| created_by_user_id | uuid (FK)  |
| is_system          | boolean    |
| created_at         | timestamptz|
| updated_at         | timestamptz|

---

### `recipe_ingredients`
| Column         | Type        |
|----------------|------------|
| id             | uuid (PK)  |
| recipe_id      | uuid (FK)  |
| ingredient_id  | uuid (FK)  |
| quantity       | numeric    |
| unit           | text       |

**Constraint:**
- unique (recipe_id, ingredient_id)

---

### `food_entries`
| Column       | Type        |
|--------------|------------|
| id           | uuid (PK)  |
| user_id      | uuid (FK)  |
| description  | text       |
| raw_input    | text       |
| input_method | enum       |
| meal_time    | enum       |
| logged_at    | timestamptz|
| status       | enum       |
| rating       | smallint   |
| created_at   | timestamptz|
| updated_at   | timestamptz|

**Constraint:**
- rating between 1–5

---

### `food_entry_ingredients`
| Column         | Type        |
|----------------|------------|
| id             | uuid (PK)  |
| food_entry_id  | uuid (FK)  |
| ingredient_id  | uuid (FK)  |
| quantity       | numeric    |
| unit           | text       |

---

### `food_entry_tags`
| Column         | Type        |
|----------------|------------|
| id             | uuid (PK)  |
| food_entry_id  | uuid (FK)  |
| tag_id         | uuid (FK)  |

**Constraint:**
- unique (food_entry_id, tag_id)

---

### `tag_definitions`
| Column         | Type        |
|----------------|------------|
| id             | uuid (PK)  |
| slug           | text (unique) |
| label          | text       |
| description    | text       |
| colour_hex     | text       |
| is_system      | boolean    |
| display_order  | integer    |
| created_at     | timestamptz|

---

### `user_storecupboard_items`
| Column         | Type        |
|----------------|------------|
| id             | uuid (PK)  |
| user_id        | uuid (FK)  |
| ingredient_id  | uuid (FK)  |
| quantity       | numeric    |
| unit           | text       |
| stock_status   | enum       |
| shelf_name     | text       |
| best_before_date | date     |
| next_reminder_at | timestamptz |
| created_at     | timestamptz|
| updated_at     | timestamptz|

**Index:**
- unique (user_id, ingredient_id, coalesce(shelf_name, 'default'))

---

### `ai_suggestions`
| Column           | Type        |
|------------------|------------|
| id               | uuid (PK)  |
| user_id          | uuid (FK)  |
| suggestion_type  | enum       |
| title            | text       |
| body             | text       |
| created_at       | timestamptz|

---

### `app_events`
| Column     | Type        |
|------------|------------|
| id         | uuid (PK)  |
| user_id    | uuid (FK)  |
| event_name | text       |
| payload    | jsonb      |
| created_at | timestamptz|

---

## Triggers

### `trg_food_entries_updated_at`
- Before update → updates `updated_at`

### `trg_storecupboard_updated_at`
- Before update → updates `updated_at`

---

## Relationships Overview

- `app_users` is the core user table
- `user_profiles` extends user data
- `food_entries` → linked to users
- `food_entry_tags` → links entries to tags
- `food_entry_ingredients` → links entries to ingredients
- `recipe_catalogue` → reusable recipes
- `user_storecupboard_items` → personal pantry
- `ai_suggestions` → generated insights
- `app_events` → analytics / tracking

---

## Notes

- UUIDs used across all primary keys
- JSONB used for flexible fields
- Designed for incremental expansion (achievements, challenges, AI workflows) 
