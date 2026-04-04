from typing import Any, Dict, List, Optional
from uuid import UUID
import os

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.db import get_conn


app = FastAPI(title="Cupboard Chef API")


DEFAULT_ALLOWED_ORIGINS = [
    "https://helixscribe.cloud",
    "https://www.helixscribe.cloud",
    "https://food.helixscribe.cloud",
    "https://www.food.helixscribe.cloud",
    "http://localhost:5173",
    "http://localhost:3000",
]

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ALLOWED_ORIGINS",
        ",".join(DEFAULT_ALLOWED_ORIGINS),
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://([a-z0-9-]+\.)?helixscribe\.cloud",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def server_error(detail: str) -> None:
    raise HTTPException(status_code=500, detail=detail)


def not_found(detail: str) -> None:
    raise HTTPException(status_code=404, detail=detail)


# -------------------------------------------------------------------
# Pydantic models
# -------------------------------------------------------------------

class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    user_id: UUID
    email: str


class AppUserCreate(BaseModel):
    email: str = Field(..., min_length=3)
    display_name: Optional[str] = None
    auth_user_id: Optional[UUID] = None


class AppUserOut(BaseModel):
    id: UUID
    auth_user_id: Optional[UUID]
    email: str
    display_name: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]


class UserProfileUpsert(BaseModel):
    app_theme: Optional[str] = None
    preferred_meal_time_labels: Optional[Dict[str, str]] = None
    onboarding_completed: Optional[bool] = None
    timezone: Optional[str] = None
    locale: Optional[str] = None


class UserProfileOut(BaseModel):
    id: UUID
    user_id: UUID
    app_theme: Optional[str]
    preferred_meal_time_labels: Optional[Dict[str, str]]
    onboarding_completed: Optional[bool]
    timezone: Optional[str]
    locale: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]


class IngredientCreate(BaseModel):
    canonical_name: str = Field(..., min_length=1)
    display_name: str = Field(..., min_length=1)
    category: Optional[str] = None
    is_seasonal: bool = False
    seasonal_months: Optional[List[int]] = None


class IngredientOut(BaseModel):
    id: UUID
    canonical_name: str
    display_name: str
    category: Optional[str]
    is_seasonal: Optional[bool] = None
    seasonal_months: Optional[List[int]] = None


class JoinIngredientCreate(BaseModel):
    ingredient_id: UUID
    quantity: Optional[float] = None
    unit: Optional[str] = None


class RecipeIngredientPatch(BaseModel):
    quantity: Optional[float] = None
    unit: Optional[str] = None


class JoinIngredientOut(BaseModel):
    id: UUID
    ingredient_id: UUID
    quantity: Optional[float] = None
    unit: Optional[str] = None


class TagCreate(BaseModel):
    slug: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1)
    description: Optional[str] = None
    colour_hex: Optional[str] = None
    is_system: bool = False
    display_order: Optional[int] = None


class TagOut(BaseModel):
    id: UUID
    slug: str
    label: str
    description: Optional[str]
    colour_hex: Optional[str]
    is_system: Optional[bool]
    display_order: Optional[int]


class FoodEntryCreate(BaseModel):
    user_id: UUID
    description: str = Field(..., min_length=1)
    raw_input: Optional[str] = None
    input_method: str = "text"
    meal_time: Optional[str] = None
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    status: str = "logged"


class FoodEntryUpdate(BaseModel):
    description: Optional[str] = None
    raw_input: Optional[str] = None
    input_method: Optional[str] = None
    meal_time: Optional[str] = None
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    status: Optional[str] = None


class FoodEntryOut(BaseModel):
    id: UUID
    user_id: Optional[UUID]
    description: str
    raw_input: Optional[str]
    input_method: Optional[str]
    meal_time: Optional[str]
    status: Optional[str]
    rating: Optional[int]


class StorecupboardItemCreate(BaseModel):
    user_id: UUID
    ingredient_id: UUID
    quantity: Optional[float] = None
    unit: Optional[str] = None
    stock_status: str = "in_stock"
    shelf_name: Optional[str] = None


class StorecupboardItemUpdate(BaseModel):
    quantity: Optional[float] = None
    unit: Optional[str] = None
    stock_status: Optional[str] = None
    shelf_name: Optional[str] = None


class StorecupboardItemOut(BaseModel):
    id: UUID
    user_id: UUID
    ingredient_id: UUID
    quantity: Optional[float]
    unit: Optional[str]
    stock_status: Optional[str]
    shelf_name: Optional[str]
    ingredient_display_name: Optional[str] = None
    ingredient_canonical_name: Optional[str] = None


class RecipeCreate(BaseModel):
    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    instructions: Optional[str] = None
    source_url: Optional[str] = None
    created_by_user_id: Optional[UUID] = None
    is_system: bool = False


class RecipeOut(BaseModel):
    id: UUID
    title: str
    description: Optional[str]
    instructions: Optional[str]
    source_url: Optional[str]
    created_by_user_id: Optional[UUID]
    is_system: Optional[bool]


class AISuggestionCreate(BaseModel):
    user_id: UUID
    suggestion_type: str
    title: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)


class AISuggestionOut(BaseModel):
    id: UUID
    user_id: UUID
    suggestion_type: str
    title: str
    body: str
    created_at: Optional[str]


class AppEventCreate(BaseModel):
    user_id: Optional[UUID] = None
    event_name: str = Field(..., min_length=1)
    payload: Optional[Dict[str, Any]] = None


class AppEventOut(BaseModel):
    id: UUID
    user_id: Optional[UUID]
    event_name: str
    payload: Optional[Dict[str, Any]]
    created_at: Optional[str]


# -------------------------------------------------------------------
# Core routes
# -------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}


# -------------------------------------------------------------------
# Auth
# -------------------------------------------------------------------

@app.post("/auth/login", response_model=LoginResponse)
@app.post("/login", response_model=LoginResponse, include_in_schema=False)
def login(payload: LoginRequest):
    email = payload.email.strip().lower()
    password = payload.password.strip()

    if not email or not password:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select id, email
                    from app_users
                    where lower(email) = %s
                    limit 1
                    """,
                    (email,),
                )
                row = cur.fetchone()
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail="Login failed because the API could not connect to the database.",
        )

    # Temporary auth logic:
    # any non-empty password is accepted if the email exists in app_users.
    if not row:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return {
        "user_id": str(row[0]),
        "email": row[1],
    }


# -------------------------------------------------------------------
# Users
# -------------------------------------------------------------------

@app.post("/users", response_model=AppUserOut)
def create_user(payload: AppUserCreate):
    email = payload.email.strip().lower()

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into app_users (auth_user_id, email, display_name)
                    values (%s, %s, %s)
                    returning id, auth_user_id, email, display_name, created_at::text, updated_at::text
                    """,
                    (
                        str(payload.auth_user_id) if payload.auth_user_id else None,
                        email,
                        payload.display_name,
                    ),
                )
                row = cur.fetchone()
            conn.commit()
    except Exception as e:
        import traceback
        traceback.print_exc()
        server_error("Could not create user.")

    return {
        "id": row[0],
        "auth_user_id": row[1],
        "email": row[2],
        "display_name": row[3],
        "created_at": row[4],
        "updated_at": row[5],
    }


@app.get("/users/{user_id}", response_model=AppUserOut)
def get_user(user_id: UUID):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select id, auth_user_id, email, display_name, created_at::text, updated_at::text
                    from app_users
                    where id = %s
                    """,
                    (str(user_id),),
                )
                row = cur.fetchone()
    except Exception as e:
        import traceback
        traceback.print_exc()
        server_error("Could not load user.")

    if not row:
        not_found("User not found.")

    return {
        "id": row[0],
        "auth_user_id": row[1],
        "email": row[2],
        "display_name": row[3],
        "created_at": row[4],
        "updated_at": row[5],
    }


# -------------------------------------------------------------------
# User profiles
# -------------------------------------------------------------------

@app.get("/users/{user_id}/profile", response_model=UserProfileOut)
def get_user_profile(user_id: UUID):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select
                        id,
                        user_id,
                        app_theme,
                        preferred_meal_time_labels,
                        onboarding_completed,
                        timezone,
                        locale,
                        created_at::text,
                        updated_at::text
                    from user_profiles
                    where user_id = %s
                    limit 1
                    """,
                    (str(user_id),),
                )
                row = cur.fetchone()
    except Exception as e:
        import traceback
        traceback.print_exc()
        server_error("Could not load user profile.")

    if not row:
        not_found("User profile not found.")

    return {
        "id": row[0],
        "user_id": row[1],
        "app_theme": row[2],
        "preferred_meal_time_labels": row[3],
        "onboarding_completed": row[4],
        "timezone": row[5],
        "locale": row[6],
        "created_at": row[7],
        "updated_at": row[8],
    }


@app.put("/users/{user_id}/profile", response_model=UserProfileOut)
def upsert_user_profile(user_id: UUID, payload: UserProfileUpsert):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select id
                    from user_profiles
                    where user_id = %s
                    limit 1
                    """,
                    (str(user_id),),
                )
                existing = cur.fetchone()

                if existing:
                    cur.execute(
                        """
                        update user_profiles
                        set
                            app_theme = %s,
                            preferred_meal_time_labels = %s,
                            onboarding_completed = %s,
                            timezone = %s,
                            locale = %s,
                            updated_at = now()
                        where user_id = %s
                        returning
                            id,
                            user_id,
                            app_theme,
                            preferred_meal_time_labels,
                            onboarding_completed,
                            timezone,
                            locale,
                            created_at::text,
                            updated_at::text
                        """,
                        (
                            payload.app_theme,
                            payload.preferred_meal_time_labels,
                            payload.onboarding_completed,
                            payload.timezone,
                            payload.locale,
                            str(user_id),
                        ),
                    )
                else:
                    cur.execute(
                        """
                        insert into user_profiles (
                            user_id,
                            app_theme,
                            preferred_meal_time_labels,
                            onboarding_completed,
                            timezone,
                            locale
                        )
                        values (%s, %s, %s, %s, %s, %s)
                        returning
                            id,
                            user_id,
                            app_theme,
                            preferred_meal_time_labels,
                            onboarding_completed,
                            timezone,
                            locale,
                            created_at::text,
                            updated_at::text
                        """,
                        (
                            str(user_id),
                            payload.app_theme,
                            payload.preferred_meal_time_labels,
                            payload.onboarding_completed,
                            payload.timezone,
                            payload.locale,
                        ),
                    )

                row = cur.fetchone()
            conn.commit()
    except Exception as e:
        import traceback
        traceback.print_exc()
        server_error("Could not save user profile.")

    return {
        "id": row[0],
        "user_id": row[1],
        "app_theme": row[2],
        "preferred_meal_time_labels": row[3],
        "onboarding_completed": row[4],
        "timezone": row[5],
        "locale": row[6],
        "created_at": row[7],
        "updated_at": row[8],
    }


# -------------------------------------------------------------------
# Ingredients
# -------------------------------------------------------------------

@app.get("/ingredients", response_model=List[IngredientOut])
def list_ingredients():
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select
                        id,
                        canonical_name,
                        display_name,
                        category,
                        is_seasonal,
                        seasonal_months
                    from ingredient_catalogue
                    order by display_name asc
                    """
                )
                rows = cur.fetchall()
    except Exception as e:
        import traceback
        traceback.print_exc()
        server_error("Could not load ingredients.")

    return [
        {
            "id": row[0],
            "canonical_name": row[1],
            "display_name": row[2],
            "category": row[3],
            "is_seasonal": row[4],
            "seasonal_months": row[5],
        }
        for row in rows
    ]


@app.post("/ingredients", response_model=IngredientOut)
def create_ingredient(payload: IngredientCreate):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into ingredient_catalogue (
                        canonical_name,
                        display_name,
                        category,
                        is_seasonal,
                        seasonal_months
                    )
                    values (%s, %s, %s, %s, %s)
                    returning
                        id,
                        canonical_name,
                        display_name,
                        category,
                        is_seasonal,
                        seasonal_months
                    """,
                    (
                        payload.canonical_name.strip().lower(),
                        payload.display_name.strip(),
                        payload.category,
                        payload.is_seasonal,
                        payload.seasonal_months,
                    ),
                )
                row = cur.fetchone()
            conn.commit()
    except Exception as e:
        import traceback
        traceback.print_exc()
        server_error("Could not create ingredient.")

    return {
        "id": row[0],
        "canonical_name": row[1],
        "display_name": row[2],
        "category": row[3],
        "is_seasonal": row[4],
        "seasonal_months": row[5],
    }


# -------------------------------------------------------------------
# Food entries
# -------------------------------------------------------------------

@app.get("/food-entries", response_model=List[FoodEntryOut])
def list_food_entries(user_id: Optional[UUID] = None):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                if user_id:
                    cur.execute(
                        """
                        select
                            id,
                            user_id,
                            description,
                            raw_input,
                            input_method::text,
                            meal_time::text,
                            status::text,
                            rating
                        from food_entries
                        where user_id = %s
                        order by logged_at desc
                        """,
                        (str(user_id),),
                    )
                else:
                    cur.execute(
                        """
                        select
                            id,
                            user_id,
                            description,
                            raw_input,
                            input_method::text,
                            meal_time::text,
                            status::text,
                            rating
                        from food_entries
                        order by logged_at desc
                        """
                    )
                rows = cur.fetchall()
    except Exception as e:
        import traceback
        traceback.print_exc()
        server_error("Could not load food entries.")

    return [
        {
            "id": row[0],
            "user_id": row[1],
            "description": row[2],
            "raw_input": row[3],
            "input_method": row[4],
            "meal_time": row[5],
            "status": row[6],
            "rating": row[7],
        }
        for row in rows
    ]


@app.post("/food-entries", response_model=FoodEntryOut)
def create_food_entry(payload: FoodEntryCreate):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into food_entries (
                        user_id,
                        description,
                        raw_input,
                        input_method,
                        meal_time,
                        rating,
                        status
                    )
                    values (%s, %s, %s, %s::input_method, %s::meal_time_code, %s, %s::food_entry_status)
                    returning
                        id,
                        user_id,
                        description,
                        raw_input,
                        input_method::text,
                        meal_time::text,
                        status::text,
                        rating
                    """,
                    (
                        str(payload.user_id),
                        payload.description,
                        payload.raw_input,
                        payload.input_method,
                        payload.meal_time,
                        payload.rating,
                        payload.status,
                    ),
                )
                row = cur.fetchone()
            conn.commit()
    except Exception as e:
        import traceback
        traceback.print_exc()
        server_error("Could not create food entry.")

    return {
        "id": row[0],
        "user_id": row[1],
        "description": row[2],
        "raw_input": row[3],
        "input_method": row[4],
        "meal_time": row[5],
        "status": row[6],
        "rating": row[7],
    }


def _entity_exists(cur: Any, table: str, entity_id: UUID) -> bool:
    cur.execute(
        f"select 1 from {table} where id = %s limit 1",
        (str(entity_id),),
    )
    return cur.fetchone() is not None


@app.get("/recipes/{recipe_id}/ingredients", response_model=List[JoinIngredientOut])
def list_recipe_ingredients(recipe_id: UUID):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                if not _entity_exists(cur, "recipe_catalogue", recipe_id):
                    not_found("Recipe not found.")

                cur.execute(
                    """
                    select id, ingredient_id, quantity, unit
                    from recipe_ingredients
                    where recipe_id = %s
                    order by created_at asc
                    """,
                    (str(recipe_id),),
                )
                rows = cur.fetchall()
    except HTTPException:
        raise
    except Exception:
        import traceback
        traceback.print_exc()
        server_error("Could not load recipe ingredients.")

    return [
        {
            "id": row[0],
            "ingredient_id": row[1],
            "quantity": row[2],
            "unit": row[3],
        }
        for row in rows
    ]


@app.post("/recipes/{recipe_id}/ingredients", response_model=JoinIngredientOut)
def create_recipe_ingredient(recipe_id: UUID, payload: JoinIngredientCreate):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                if not _entity_exists(cur, "recipe_catalogue", recipe_id):
                    not_found("Recipe not found.")
                if not _entity_exists(cur, "ingredient_catalogue", payload.ingredient_id):
                    not_found("Ingredient not found.")

                cur.execute(
                    """
                    insert into recipe_ingredients (recipe_id, ingredient_id, quantity, unit)
                    values (%s, %s, %s, %s)
                    on conflict (recipe_id, ingredient_id)
                    do update set
                        quantity = excluded.quantity,
                        unit = excluded.unit
                    returning id, ingredient_id, quantity, unit
                    """,
                    (
                        str(recipe_id),
                        str(payload.ingredient_id),
                        payload.quantity,
                        payload.unit,
                    ),
                )
                row = cur.fetchone()
            conn.commit()
    except HTTPException:
        raise
    except Exception:
        import traceback
        traceback.print_exc()
        server_error("Could not save recipe ingredient.")

    return {
        "id": row[0],
        "ingredient_id": row[1],
        "quantity": row[2],
        "unit": row[3],
    }


@app.patch("/recipes/{recipe_id}/ingredients/{ingredient_id}", response_model=JoinIngredientOut)
def patch_recipe_ingredient(recipe_id: UUID, ingredient_id: UUID, payload: RecipeIngredientPatch):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                if not _entity_exists(cur, "recipe_catalogue", recipe_id):
                    not_found("Recipe not found.")

                cur.execute(
                    """
                    update recipe_ingredients
                    set
                        quantity = coalesce(%s, quantity),
                        unit = coalesce(%s, unit)
                    where recipe_id = %s and ingredient_id = %s
                    returning id, ingredient_id, quantity, unit
                    """,
                    (
                        payload.quantity,
                        payload.unit,
                        str(recipe_id),
                        str(ingredient_id),
                    ),
                )
                row = cur.fetchone()
            conn.commit()
    except HTTPException:
        raise
    except Exception:
        import traceback
        traceback.print_exc()
        server_error("Could not update recipe ingredient.")

    if not row:
        not_found("Recipe ingredient not found.")

    return {
        "id": row[0],
        "ingredient_id": row[1],
        "quantity": row[2],
        "unit": row[3],
    }


@app.delete("/recipes/{recipe_id}/ingredients/{ingredient_id}")
def delete_recipe_ingredient(recipe_id: UUID, ingredient_id: UUID):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                if not _entity_exists(cur, "recipe_catalogue", recipe_id):
                    not_found("Recipe not found.")

                cur.execute(
                    """
                    delete from recipe_ingredients
                    where recipe_id = %s and ingredient_id = %s
                    returning id
                    """,
                    (str(recipe_id), str(ingredient_id)),
                )
                deleted = cur.fetchone()
            conn.commit()
    except HTTPException:
        raise
    except Exception:
        import traceback
        traceback.print_exc()
        server_error("Could not delete recipe ingredient.")

    if not deleted:
        not_found("Recipe ingredient not found.")

    return {"deleted": True}


@app.get("/food-entries/{food_entry_id}/ingredients", response_model=List[JoinIngredientOut])
def list_food_entry_ingredients(food_entry_id: UUID):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                if not _entity_exists(cur, "food_entries", food_entry_id):
                    not_found("Food entry not found.")

                cur.execute(
                    """
                    select id, ingredient_id, quantity, unit
                    from food_entry_ingredients
                    where food_entry_id = %s
                    order by created_at asc
                    """,
                    (str(food_entry_id),),
                )
                rows = cur.fetchall()
    except HTTPException:
        raise
    except Exception:
        import traceback
        traceback.print_exc()
        server_error("Could not load food entry ingredients.")

    return [
        {
            "id": row[0],
            "ingredient_id": row[1],
            "quantity": row[2],
            "unit": row[3],
        }
        for row in rows
    ]


@app.post("/food-entries/{food_entry_id}/ingredients", response_model=JoinIngredientOut)
def create_food_entry_ingredient(food_entry_id: UUID, payload: JoinIngredientCreate):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                if not _entity_exists(cur, "food_entries", food_entry_id):
                    not_found("Food entry not found.")
                if not _entity_exists(cur, "ingredient_catalogue", payload.ingredient_id):
                    not_found("Ingredient not found.")

                cur.execute(
                    """
                    select id from food_entry_ingredients
                    where food_entry_id = %s and ingredient_id = %s
                    limit 1
                    """,
                    (str(food_entry_id), str(payload.ingredient_id)),
                )
                existing = cur.fetchone()
                if existing:
                    raise HTTPException(status_code=409, detail="Food entry ingredient already exists.")

                cur.execute(
                    """
                    insert into food_entry_ingredients (food_entry_id, ingredient_id, quantity, unit)
                    values (%s, %s, %s, %s)
                    returning id, ingredient_id, quantity, unit
                    """,
                    (
                        str(food_entry_id),
                        str(payload.ingredient_id),
                        payload.quantity,
                        payload.unit,
                    ),
                )
                row = cur.fetchone()
            conn.commit()
    except HTTPException:
        raise
    except Exception:
        import traceback
        traceback.print_exc()
        server_error("Could not create food entry ingredient.")

    return {
        "id": row[0],
        "ingredient_id": row[1],
        "quantity": row[2],
        "unit": row[3],
    }


@app.delete("/food-entries/{food_entry_id}/ingredients/{ingredient_id}")
def delete_food_entry_ingredient(food_entry_id: UUID, ingredient_id: UUID):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                if not _entity_exists(cur, "food_entries", food_entry_id):
                    not_found("Food entry not found.")

                cur.execute(
                    """
                    delete from food_entry_ingredients
                    where food_entry_id = %s and ingredient_id = %s
                    returning id
                    """,
                    (str(food_entry_id), str(ingredient_id)),
                )
                deleted = cur.fetchone()
            conn.commit()
    except HTTPException:
        raise
    except Exception:
        import traceback
        traceback.print_exc()
        server_error("Could not delete food entry ingredient.")

    if not deleted:
        not_found("Food entry ingredient not found.")

    return {"deleted": True}


@app.post("/food-entries/{food_entry_id}/tags/{tag_id}")
def add_food_entry_tag(food_entry_id: UUID, tag_id: UUID):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                if not _entity_exists(cur, "food_entries", food_entry_id):
                    not_found("Food entry not found.")
                if not _entity_exists(cur, "tag_definitions", tag_id):
                    not_found("Tag not found.")

                cur.execute(
                    """
                    insert into food_entry_tags (food_entry_id, tag_id)
                    values (%s, %s)
                    on conflict (food_entry_id, tag_id) do nothing
                    returning id
                    """,
                    (str(food_entry_id), str(tag_id)),
                )
                inserted = cur.fetchone()

                if inserted:
                    link_id = inserted[0]
                else:
                    cur.execute(
                        """
                        select id
                        from food_entry_tags
                        where food_entry_id = %s and tag_id = %s
                        limit 1
                        """,
                        (str(food_entry_id), str(tag_id)),
                    )
                    existing = cur.fetchone()
                    link_id = existing[0]
            conn.commit()
    except HTTPException:
        raise
    except Exception:
        import traceback
        traceback.print_exc()
        server_error("Could not attach tag to food entry.")

    return {"id": link_id, "food_entry_id": food_entry_id, "tag_id": tag_id}


@app.delete("/food-entries/{food_entry_id}/tags/{tag_id}")
def remove_food_entry_tag(food_entry_id: UUID, tag_id: UUID):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                if not _entity_exists(cur, "food_entries", food_entry_id):
                    not_found("Food entry not found.")

                cur.execute(
                    """
                    delete from food_entry_tags
                    where food_entry_id = %s and tag_id = %s
                    returning id
                    """,
                    (str(food_entry_id), str(tag_id)),
                )
                deleted = cur.fetchone()
            conn.commit()
    except HTTPException:
        raise
    except Exception:
        import traceback
        traceback.print_exc()
        server_error("Could not detach tag from food entry.")

    if not deleted:
        not_found("Food entry tag not found.")

    return {"deleted": True}
