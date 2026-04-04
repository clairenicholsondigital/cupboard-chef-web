# Cupboard Chef API Contract

This contract defines endpoint path conventions used by backend route registration.

## 1) User-scoped collections are nested

Collections that belong to exactly one user MUST be registered under:

- `/users/{user_id}/{resource-plural}`

Examples:

- `GET /users/{user_id}/food-entries`
- `POST /users/{user_id}/food-entries`
- `GET /users/{user_id}/profile` (single nested user resource)
- `PUT /users/{user_id}/profile`

## 2) Direct entity CRUD by id is top-level

When operating on one entity by its own id, endpoints MUST be top-level:

- `GET /{resource-plural}/{id}`
- `PATCH /{resource-plural}/{id}`
- `DELETE /{resource-plural}/{id}`

Example:

- `GET /food-entries/{food_entry_id}`
- `PATCH /food-entries/{food_entry_id}`
- `DELETE /food-entries/{food_entry_id}`

## 3) Naming consistency rules

- Use **kebab-case** for path segments (e.g. `food-entries`, `storecupboard-items`).
- Use **plural nouns** for collection segments (`/users`, `/food-entries`, `/ingredients`).
- Use **singular path params** with `_id` suffix (`{user_id}`, `{food_entry_id}`, `{ingredient_id}`).
- Join/association resources MUST use explicit plural names that describe membership, not verbs.
  - Preferred examples: `food-entry-ingredients`, `food-entry-tags`, `recipe-ingredients`.

## 4) Registration order policy

Before adding new feature endpoints, route registration should follow this order:

1. Core/system routes (`/health`, auth)
2. Top-level entity routes (CRUD by id and collection)
3. User-nested collection routes
4. Join resource routes

This keeps discovery and future endpoint additions predictable.

## 5) Backward compatibility note

Legacy routes that do not follow this contract may remain temporarily but should be hidden from API docs and migrated to contract-compliant paths.
