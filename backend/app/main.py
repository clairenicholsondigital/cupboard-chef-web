from datetime import date
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


class TagUpdate(BaseModel):
    slug: Optional[str] = None
    label: Optional[str] = None
    description: Optional[str] = None
    colour_hex: Optional[str] = None
    is_system: Optional[bool] = None
    display_order: Optional[int] = None


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


class NestedFoodEntryCreate(BaseModel):
    description: str = Field(..., min_length=1)
    raw_input: Optional[str] = None
    input_method: str = "text"
    meal_time: Optional[str] = None
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    status: str = "logged"


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


class NestedStorecupboardItemCreate(BaseModel):
    ingredient_id: UUID
    quantity: Optional[float] = None
    unit: Optional[str] = None
    stock_status: str = "in_stock"
    shelf_name: Optional[str] = None


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


class RecipeUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    instructions: Optional[str] = None
    source_url: Optional[str] = None
    created_by_user_id: Optional[UUID] = None
    is_system: Optional[bool] = None


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


class AISuggestionUpdate(BaseModel):
    suggestion_type: Optional[str] = None
    title: Optional[str] = None
    body: Optional[str] = None


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
                    values (%s, %s, %s, %s::input_method, %s::meal_time_code, %s, %s::entry_status)
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


@app.get("/food-entries/{entry_id}", response_model=FoodEntryOut)
def get_food_entry(entry_id: UUID):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
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
                    where id = %s
                    limit 1
                    """,
                    (str(entry_id),),
                )
                row = cur.fetchone()
    except Exception:
        import traceback
        traceback.print_exc()
        server_error("Could not load food entry.")

    if not row:
        not_found("Food entry not found.")

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


@app.put("/food-entries/{entry_id}", response_model=FoodEntryOut)
def update_food_entry(entry_id: UUID, payload: FoodEntryUpdate):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    update food_entries
                    set
                        description = coalesce(%s, description),
                        raw_input = coalesce(%s, raw_input),
                        input_method = coalesce(%s::input_method, input_method),
                        meal_time = coalesce(%s::meal_time_code, meal_time),
                        rating = coalesce(%s, rating),
                        status = coalesce(%s::entry_status, status),
                        updated_at = now()
                    where id = %s
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
                        payload.description,
                        payload.raw_input,
                        payload.input_method,
                        payload.meal_time,
                        payload.rating,
                        payload.status,
                        str(entry_id),
                    ),
                )
                row = cur.fetchone()
            conn.commit()
    except Exception:
        import traceback
        traceback.print_exc()
        server_error("Could not update food entry.")

    if not row:
        not_found("Food entry not found.")

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


@app.delete("/food-entries/{entry_id}")
def delete_food_entry(entry_id: UUID):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    delete from food_entries
                    where id = %s
                    returning id
                    """,
                    (str(entry_id),),
                )
                row = cur.fetchone()
            conn.commit()
    except Exception:
        import traceback
        traceback.print_exc()
        server_error("Could not delete food entry.")

    if not row:
        not_found("Food entry not found.")

    return {"deleted": True, "id": row[0]}


# -------------------------------------------------------------------
# Tags
# -------------------------------------------------------------------

@app.get("/tags", response_model=List[TagOut])
def list_tags():
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select
                        id,
                        slug,
                        label,
                        description,
                        colour_hex,
                        is_system,
                        display_order
                    from tag_definitions
                    order by coalesce(display_order, 999999), label asc
                    """
                )
                rows = cur.fetchall()
    except Exception:
        import traceback
        traceback.print_exc()
        server_error("Could not load tags.")

    return [
        {
            "id": row[0],
            "slug": row[1],
            "label": row[2],
            "description": row[3],
            "colour_hex": row[4],
            "is_system": row[5],
            "display_order": row[6],
        }
        for row in rows
    ]


@app.post("/tags", response_model=TagOut)
def create_tag(payload: TagCreate):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into tag_definitions (
                        slug,
                        label,
                        description,
                        colour_hex,
                        is_system,
                        display_order
                    )
                    values (%s, %s, %s, %s, %s, %s)
                    returning
                        id,
                        slug,
                        label,
                        description,
                        colour_hex,
                        is_system,
                        display_order
                    """,
                    (
                        payload.slug.strip().lower(),
                        payload.label.strip(),
                        payload.description,
                        payload.colour_hex,
                        payload.is_system,
                        payload.display_order,
                    ),
                )
                row = cur.fetchone()
            conn.commit()
    except Exception:
        import traceback
        traceback.print_exc()
        server_error("Could not create tag.")

    return {
        "id": row[0],
        "slug": row[1],
        "label": row[2],
        "description": row[3],
        "colour_hex": row[4],
        "is_system": row[5],
        "display_order": row[6],
    }


@app.get("/tags/{tag_id}", response_model=TagOut)
def get_tag(tag_id: UUID):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select
                        id,
                        slug,
                        label,
                        description,
                        colour_hex,
                        is_system,
                        display_order
                    from tag_definitions
                    where id = %s
                    limit 1
                    """,
                    (str(tag_id),),
                )
                row = cur.fetchone()
    except Exception:
        import traceback
        traceback.print_exc()
        server_error("Could not load tag.")

    if not row:
        not_found("Tag not found.")

    return {
        "id": row[0],
        "slug": row[1],
        "label": row[2],
        "description": row[3],
        "colour_hex": row[4],
        "is_system": row[5],
        "display_order": row[6],
    }


@app.put("/tags/{tag_id}", response_model=TagOut)
def update_tag(tag_id: UUID, payload: TagUpdate):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    update tag_definitions
                    set
                        slug = coalesce(%s, slug),
                        label = coalesce(%s, label),
                        description = coalesce(%s, description),
                        colour_hex = coalesce(%s, colour_hex),
                        is_system = coalesce(%s, is_system),
                        display_order = coalesce(%s, display_order)
                    where id = %s
                    returning
                        id,
                        slug,
                        label,
                        description,
                        colour_hex,
                        is_system,
                        display_order
                    """,
                    (
                        payload.slug.strip().lower() if payload.slug else None,
                        payload.label.strip() if payload.label else None,
                        payload.description,
                        payload.colour_hex,
                        payload.is_system,
                        payload.display_order,
                        str(tag_id),
                    ),
                )
                row = cur.fetchone()
            conn.commit()
    except Exception:
        import traceback
        traceback.print_exc()
        server_error("Could not update tag.")

    if not row:
        not_found("Tag not found.")

    return {
        "id": row[0],
        "slug": row[1],
        "label": row[2],
        "description": row[3],
        "colour_hex": row[4],
        "is_system": row[5],
        "display_order": row[6],
    }


@app.delete("/tags/{tag_id}")
def delete_tag(tag_id: UUID):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    delete from tag_definitions
                    where id = %s
                    returning id
                    """,
                    (str(tag_id),),
                )
                row = cur.fetchone()
            conn.commit()
    except Exception:
        import traceback
        traceback.print_exc()
        server_error("Could not delete tag.")

    if not row:
        not_found("Tag not found.")

    return {"deleted": True, "id": row[0]}


# -------------------------------------------------------------------
# Storecupboard items
# -------------------------------------------------------------------

@app.get("/storecupboard-items", response_model=List[StorecupboardItemOut])
def list_storecupboard_items(user_id: Optional[UUID] = None):
    where_sql = "where s.user_id = %s" if user_id else ""
    params = (str(user_id),) if user_id else ()

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    select
                        s.id,
                        s.user_id,
                        s.ingredient_id,
                        s.quantity::float8,
                        s.unit,
                        s.stock_status::text,
                        s.shelf_name,
                        i.display_name,
                        i.canonical_name
                    from user_storecupboard_items s
                    join ingredient_catalogue i on i.id = s.ingredient_id
                    {where_sql}
                    order by i.display_name asc
                    """,
                    params,
                )
                rows = cur.fetchall()
    except Exception:
        import traceback
        traceback.print_exc()
        server_error("Could not load storecupboard items.")

    return [
        {
            "id": row[0],
            "user_id": row[1],
            "ingredient_id": row[2],
            "quantity": row[3],
            "unit": row[4],
            "stock_status": row[5],
            "shelf_name": row[6],
            "ingredient_display_name": row[7],
            "ingredient_canonical_name": row[8],
        }
        for row in rows
    ]


@app.post("/storecupboard-items", response_model=StorecupboardItemOut)
def create_storecupboard_item(payload: StorecupboardItemCreate):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into user_storecupboard_items (
                        user_id,
                        ingredient_id,
                        quantity,
                        unit,
                        stock_status,
                        shelf_name
                    )
                    values (%s, %s, %s, %s, %s::stock_status, %s)
                    returning
                        id,
                        user_id,
                        ingredient_id,
                        quantity::float8,
                        unit,
                        stock_status::text,
                        shelf_name
                    """,
                    (
                        str(payload.user_id),
                        str(payload.ingredient_id),
                        payload.quantity,
                        payload.unit,
                        payload.stock_status,
                        payload.shelf_name,
                    ),
                )
                row = cur.fetchone()
                cur.execute(
                    """
                    select display_name, canonical_name
                    from ingredient_catalogue
                    where id = %s
                    """,
                    (str(payload.ingredient_id),),
                )
                ingredient = cur.fetchone()
            conn.commit()
    except Exception:
        import traceback
        traceback.print_exc()
        server_error("Could not create storecupboard item.")

    return {
        "id": row[0],
        "user_id": row[1],
        "ingredient_id": row[2],
        "quantity": row[3],
        "unit": row[4],
        "stock_status": row[5],
        "shelf_name": row[6],
        "ingredient_display_name": ingredient[0] if ingredient else None,
        "ingredient_canonical_name": ingredient[1] if ingredient else None,
    }


@app.get("/storecupboard-items/{item_id}", response_model=StorecupboardItemOut)
def get_storecupboard_item(item_id: UUID):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select
                        s.id,
                        s.user_id,
                        s.ingredient_id,
                        s.quantity::float8,
                        s.unit,
                        s.stock_status::text,
                        s.shelf_name,
                        i.display_name,
                        i.canonical_name
                    from user_storecupboard_items s
                    join ingredient_catalogue i on i.id = s.ingredient_id
                    where s.id = %s
                    limit 1
                    """,
                    (str(item_id),),
                )
                row = cur.fetchone()
    except Exception:
        import traceback
        traceback.print_exc()
        server_error("Could not load storecupboard item.")

    if not row:
        not_found("Storecupboard item not found.")

    return {
        "id": row[0],
        "user_id": row[1],
        "ingredient_id": row[2],
        "quantity": row[3],
        "unit": row[4],
        "stock_status": row[5],
        "shelf_name": row[6],
        "ingredient_display_name": row[7],
        "ingredient_canonical_name": row[8],
    }


@app.put("/storecupboard-items/{item_id}", response_model=StorecupboardItemOut)
def update_storecupboard_item(item_id: UUID, payload: StorecupboardItemUpdate):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    update user_storecupboard_items s
                    set
                        quantity = coalesce(%s, s.quantity),
                        unit = coalesce(%s, s.unit),
                        stock_status = coalesce(%s::stock_status, s.stock_status),
                        shelf_name = coalesce(%s, s.shelf_name),
                        updated_at = now()
                    where s.id = %s
                    returning
                        s.id,
                        s.user_id,
                        s.ingredient_id,
                        s.quantity::float8,
                        s.unit,
                        s.stock_status::text,
                        s.shelf_name
                    """,
                    (
                        payload.quantity,
                        payload.unit,
                        payload.stock_status,
                        payload.shelf_name,
                        str(item_id),
                    ),
                )
                row = cur.fetchone()
                if row:
                    cur.execute(
                        """
                        select display_name, canonical_name
                        from ingredient_catalogue
                        where id = %s
                        """,
                        (str(row[2]),),
                    )
                    ingredient = cur.fetchone()
                else:
                    ingredient = None
            conn.commit()
    except Exception:
        import traceback
        traceback.print_exc()
        server_error("Could not update storecupboard item.")

    if not row:
        not_found("Storecupboard item not found.")

    return {
        "id": row[0],
        "user_id": row[1],
        "ingredient_id": row[2],
        "quantity": row[3],
        "unit": row[4],
        "stock_status": row[5],
        "shelf_name": row[6],
        "ingredient_display_name": ingredient[0] if ingredient else None,
        "ingredient_canonical_name": ingredient[1] if ingredient else None,
    }


@app.delete("/storecupboard-items/{item_id}")
def delete_storecupboard_item(item_id: UUID):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    delete from user_storecupboard_items
                    where id = %s
                    returning id
                    """,
                    (str(item_id),),
                )
                row = cur.fetchone()
            conn.commit()
    except Exception:
        import traceback
        traceback.print_exc()
        server_error("Could not delete storecupboard item.")

    if not row:
        not_found("Storecupboard item not found.")

    return {"deleted": True, "id": row[0]}


# -------------------------------------------------------------------
# Recipes
# -------------------------------------------------------------------

@app.get("/recipes", response_model=List[RecipeOut])
def list_recipes(created_by_user_id: Optional[UUID] = None):
    where_sql = "where created_by_user_id = %s" if created_by_user_id else ""
    params = (str(created_by_user_id),) if created_by_user_id else ()
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    select
                        id,
                        title,
                        description,
                        instructions,
                        source_url,
                        created_by_user_id,
                        is_system
                    from recipe_catalogue
                    {where_sql}
                    order by title asc
                    """,
                    params,
                )
                rows = cur.fetchall()
    except Exception:
        import traceback
        traceback.print_exc()
        server_error("Could not load recipes.")

    return [
        {
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "instructions": row[3],
            "source_url": row[4],
            "created_by_user_id": row[5],
            "is_system": row[6],
        }
        for row in rows
    ]


@app.post("/recipes", response_model=RecipeOut)
def create_recipe(payload: RecipeCreate):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into recipe_catalogue (
                        title,
                        description,
                        instructions,
                        source_url,
                        created_by_user_id,
                        is_system
                    )
                    values (%s, %s, %s, %s, %s, %s)
                    returning
                        id,
                        title,
                        description,
                        instructions,
                        source_url,
                        created_by_user_id,
                        is_system
                    """,
                    (
                        payload.title.strip(),
                        payload.description,
                        payload.instructions,
                        payload.source_url,
                        str(payload.created_by_user_id) if payload.created_by_user_id else None,
                        payload.is_system,
                    ),
                )
                row = cur.fetchone()
            conn.commit()
    except Exception:
        import traceback
        traceback.print_exc()
        server_error("Could not create recipe.")

    return {
        "id": row[0],
        "title": row[1],
        "description": row[2],
        "instructions": row[3],
        "source_url": row[4],
        "created_by_user_id": row[5],
        "is_system": row[6],
    }


@app.get("/recipes/{recipe_id}", response_model=RecipeOut)
def get_recipe(recipe_id: UUID):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select
                        id,
                        title,
                        description,
                        instructions,
                        source_url,
                        created_by_user_id,
                        is_system
                    from recipe_catalogue
                    where id = %s
                    limit 1
                    """,
                    (str(recipe_id),),
                )
                row = cur.fetchone()
    except Exception:
        import traceback
        traceback.print_exc()
        server_error("Could not load recipe.")

    if not row:
        not_found("Recipe not found.")

    return {
        "id": row[0],
        "title": row[1],
        "description": row[2],
        "instructions": row[3],
        "source_url": row[4],
        "created_by_user_id": row[5],
        "is_system": row[6],
    }


@app.put("/recipes/{recipe_id}", response_model=RecipeOut)
def update_recipe(recipe_id: UUID, payload: RecipeUpdate):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    update recipe_catalogue
                    set
                        title = coalesce(%s, title),
                        description = coalesce(%s, description),
                        instructions = coalesce(%s, instructions),
                        source_url = coalesce(%s, source_url),
                        created_by_user_id = coalesce(%s, created_by_user_id),
                        is_system = coalesce(%s, is_system),
                        updated_at = now()
                    where id = %s
                    returning
                        id,
                        title,
                        description,
                        instructions,
                        source_url,
                        created_by_user_id,
                        is_system
                    """,
                    (
                        payload.title.strip() if payload.title else None,
                        payload.description,
                        payload.instructions,
                        payload.source_url,
                        str(payload.created_by_user_id) if payload.created_by_user_id else None,
                        payload.is_system,
                        str(recipe_id),
                    ),
                )
                row = cur.fetchone()
            conn.commit()
    except Exception:
        import traceback
        traceback.print_exc()
        server_error("Could not update recipe.")

    if not row:
        not_found("Recipe not found.")

    return {
        "id": row[0],
        "title": row[1],
        "description": row[2],
        "instructions": row[3],
        "source_url": row[4],
        "created_by_user_id": row[5],
        "is_system": row[6],
    }


@app.delete("/recipes/{recipe_id}")
def delete_recipe(recipe_id: UUID):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    delete from recipe_catalogue
                    where id = %s
                    returning id
                    """,
                    (str(recipe_id),),
                )
                row = cur.fetchone()
            conn.commit()
    except Exception:
        import traceback
        traceback.print_exc()
        server_error("Could not delete recipe.")

    if not row:
        not_found("Recipe not found.")

    return {"deleted": True, "id": row[0]}


# -------------------------------------------------------------------
# AI suggestions
# -------------------------------------------------------------------

@app.get("/ai-suggestions", response_model=List[AISuggestionOut])
def list_ai_suggestions(user_id: Optional[UUID] = None):
    where_sql = "where user_id = %s" if user_id else ""
    params = (str(user_id),) if user_id else ()
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    select
                        id,
                        user_id,
                        suggestion_type::text,
                        title,
                        body,
                        created_at::text
                    from ai_suggestions
                    {where_sql}
                    order by created_at desc
                    """,
                    params,
                )
                rows = cur.fetchall()
    except Exception:
        import traceback
        traceback.print_exc()
        server_error("Could not load AI suggestions.")

    return [
        {
            "id": row[0],
            "user_id": row[1],
            "suggestion_type": row[2],
            "title": row[3],
            "body": row[4],
            "created_at": row[5],
        }
        for row in rows
    ]


@app.post("/ai-suggestions", response_model=AISuggestionOut)
def create_ai_suggestion(payload: AISuggestionCreate):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into ai_suggestions (
                        user_id,
                        suggestion_type,
                        title,
                        body
                    )
                    values (%s, %s::suggestion_type, %s, %s)
                    returning
                        id,
                        user_id,
                        suggestion_type::text,
                        title,
                        body,
                        created_at::text
                    """,
                    (
                        str(payload.user_id),
                        payload.suggestion_type,
                        payload.title.strip(),
                        payload.body.strip(),
                    ),
                )
                row = cur.fetchone()
            conn.commit()
    except Exception:
        import traceback
        traceback.print_exc()
        server_error("Could not create AI suggestion.")

    return {
        "id": row[0],
        "user_id": row[1],
        "suggestion_type": row[2],
        "title": row[3],
        "body": row[4],
        "created_at": row[5],
    }


@app.get("/ai-suggestions/{suggestion_id}", response_model=AISuggestionOut)
def get_ai_suggestion(suggestion_id: UUID):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select
                        id,
                        user_id,
                        suggestion_type::text,
                        title,
                        body,
                        created_at::text
                    from ai_suggestions
                    where id = %s
                    limit 1
                    """,
                    (str(suggestion_id),),
                )
                row = cur.fetchone()
    except Exception:
        import traceback
        traceback.print_exc()
        server_error("Could not load AI suggestion.")

    if not row:
        not_found("AI suggestion not found.")

    return {
        "id": row[0],
        "user_id": row[1],
        "suggestion_type": row[2],
        "title": row[3],
        "body": row[4],
        "created_at": row[5],
    }


@app.put("/ai-suggestions/{suggestion_id}", response_model=AISuggestionOut)
def update_ai_suggestion(suggestion_id: UUID, payload: AISuggestionUpdate):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    update ai_suggestions
                    set
                        suggestion_type = coalesce(%s::suggestion_type, suggestion_type),
                        title = coalesce(%s, title),
                        body = coalesce(%s, body)
                    where id = %s
                    returning
                        id,
                        user_id,
                        suggestion_type::text,
                        title,
                        body,
                        created_at::text
                    """,
                    (
                        payload.suggestion_type,
                        payload.title.strip() if payload.title else None,
                        payload.body.strip() if payload.body else None,
                        str(suggestion_id),
                    ),
                )
                row = cur.fetchone()
            conn.commit()
    except Exception:
        import traceback
        traceback.print_exc()
        server_error("Could not update AI suggestion.")

    if not row:
        not_found("AI suggestion not found.")

    return {
        "id": row[0],
        "user_id": row[1],
        "suggestion_type": row[2],
        "title": row[3],
        "body": row[4],
        "created_at": row[5],
    }


@app.delete("/ai-suggestions/{suggestion_id}")
def delete_ai_suggestion(suggestion_id: UUID):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    delete from ai_suggestions
                    where id = %s
                    returning id
                    """,
                    (str(suggestion_id),),
                )
                row = cur.fetchone()
            conn.commit()
    except Exception:
        import traceback
        traceback.print_exc()
        server_error("Could not delete AI suggestion.")

    if not row:
        not_found("AI suggestion not found.")

    return {"deleted": True, "id": row[0]}


# -------------------------------------------------------------------
# App events
# -------------------------------------------------------------------

@app.get("/app-events", response_model=List[AppEventOut])
def list_app_events(user_id: Optional[UUID] = Query(default=None)):
    where_sql = "where user_id = %s" if user_id else ""
    params = (str(user_id),) if user_id else ()

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    select
                        id,
                        user_id,
                        event_name,
                        payload,
                        created_at::text
                    from app_events
                    {where_sql}
                    order by created_at desc
                    """,
                    params,
                )
                rows = cur.fetchall()
    except Exception:
        import traceback
        traceback.print_exc()
        server_error("Could not load app events.")

    return [
        {
            "id": row[0],
            "user_id": row[1],
            "event_name": row[2],
            "payload": row[3],
            "created_at": row[4],
        }
        for row in rows
    ]


@app.get("/users/{user_id}/app-events", response_model=List[AppEventOut])
def list_user_app_events(user_id: UUID):
    return list_app_events(user_id=user_id)


@app.post("/app-events", response_model=AppEventOut)
def create_app_event(payload: AppEventCreate):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into app_events (
                        user_id,
                        event_name,
                        payload
                    )
                    values (%s, %s, %s)
                    returning
                        id,
                        user_id,
                        event_name,
                        payload,
                        created_at::text
                    """,
                    (
                        str(payload.user_id) if payload.user_id else None,
                        payload.event_name.strip(),
                        payload.payload,
                    ),
                )
                row = cur.fetchone()
            conn.commit()
    except Exception:
        import traceback
        traceback.print_exc()
        server_error("Could not create app event.")

    return {
        "id": row[0],
        "user_id": row[1],
        "event_name": row[2],
        "payload": row[3],
        "created_at": row[4],
    }
