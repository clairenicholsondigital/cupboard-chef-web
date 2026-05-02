# Cupboard Chef API Backend

FastAPI backend for Cupboard Chef, intended to support a separate mobile-first Replit app via JSON endpoints.

## Framework + run command
- Backend framework: **FastAPI** (`backend/app/main.py`)
- Run locally:
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 3000
```

## Environment variables
- `DATABASE_URL` - Postgres connection string
- `ALLOWED_ORIGINS` or `CORS_ORIGIN` or `CORS_ALLOWED_ORIGINS` - comma-separated CORS allowlist
- `AUTH_TOKEN_SECRET` - auth token signing secret
- `AUTH_TOKEN_TTL_SECONDS` - token ttl seconds

## Mobile-focused endpoints
- `GET /health`
- `POST /api/recipes/suggest`
- `POST /api/shopping-list`
- `POST /api/swaps`
- `POST /api/food-waste-score`

## Existing core endpoints (selected)
- Auth: `/auth/login`, `/auth/me`
- Users/profile: `/users`, `/users/{user_id}`, `/users/{user_id}/profile`
- Ingredients: `/ingredients`, `/ingredients/{ingredient_id}`
- Food entries: `/food-entries`, `/users/{user_id}/food-entries`
- Recipes: `/recipes`, `/recipes/{recipe_id}`
- Shopping lists/items: `/shopping-lists`, `/users/{user_id}/shopping-lists`, `/shopping-list-items/{item_id}`

## cURL examples
```bash
curl -s http://localhost:3000/health

curl -s -X POST http://localhost:3000/api/recipes/suggest \
  -H "Content-Type: application/json" \
  -d '{"ingredients":["pasta","tomatoes","spinach","cheese"],"dietary":["vegetarian"],"timeMinutes":20,"useFirst":["spinach"],"servings":2}'

curl -s -X POST http://localhost:3000/api/shopping-list \
  -H "Content-Type: application/json" \
  -d '{"selectedRecipes":[{"title":"Tomato pasta","missing":["garlic","olive oil"]}]}'

curl -s -X POST http://localhost:3000/api/swaps \
  -H "Content-Type: application/json" \
  -d '{"missingIngredients":["cream","eggs","rice"]}'

curl -s -X POST http://localhost:3000/api/food-waste-score \
  -H "Content-Type: application/json" \
  -d '{"ingredients":["spinach","tomatoes","cheese"],"useFirst":["spinach"]}'
```

## SQL migrations
A new migration is included at `backend/migrations/20260502_001_cupboard_chef_mobile_api.sql`.

Apply manually (example):
```bash
psql "$DATABASE_URL" -f backend/migrations/20260502_001_cupboard_chef_mobile_api.sql
```

The new endpoints work without DB writes; persistence failures are logged server-side and API responses still return.

## Replit mobile app connection
Set the mobile app API base URL to your deployed backend, e.g.:
- local: `http://localhost:3000`
- hosted: `https://<your-api-domain>`
