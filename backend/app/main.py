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


class NestedRecipeCreate(BaseModel):
    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    instructions: Optional[str] = None
    source_url: Optional[str] = None
    is_system: bool = False


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


class AISuggestionGenerateRequest(BaseModel):
    suggestion_type: str = "recipe"
    context: Optional[str] = None


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


@app.get("/users/{user_id}/food-entries", response_model=List[FoodEntryOut])
def list_user_food_entries(
    user_id: UUID,
    status: Optional[str] = Query(default=None),
    from_date: Optional[date] = Query(default=None),
    to_date: Optional[date] = Query(default=None),
):
    sql = """
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
    """
    params: List[Any] = [str(user_id)]

    if status:
        sql += " and status::text = %s"
        params.append(status)
    if from_date:
        sql += " and logged_at::date >= %s"
        params.append(from_date.isoformat())
    if to_date:
        sql += " and logged_at::date <= %s"
        params.append(to_date.isoformat())
    sql += " order by logged_at desc"

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, tuple(params))
                rows = cur.fetchall()
    except Exception:
        import traceback
        traceback.print_exc()
        server_error("Could not load user food entries.")

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


@app.post("/users/{user_id}/food-entries", response_model=FoodEntryOut)
def create_user_food_entry(user_id: UUID, payload: NestedFoodEntryCreate):
    create_payload = FoodEntryCreate(
        user_id=user_id,
        description=payload.description,
        raw_input=payload.raw_input,
        input_method=payload.input_method,
        meal_time=payload.meal_time,
        rating=payload.rating,
        status=payload.status,
    )
    return create_food_entry(create_payload)


@app.get("/users/{user_id}/storecupboard", response_model=List[StorecupboardItemOut])
@app.get("/users/{user_id}/storecupboard-items", response_model=List[StorecupboardItemOut], include_in_schema=False)
def list_user_storecupboard_items(
    user_id: UUID,
    stock_status: Optional[str] = Query(default=None),
):
    sql = """
        select
            s.id,
            s.user_id,
            s.ingredient_id,
            s.quantity,
            s.unit,
            s.stock_status::text,
            s.shelf_name,
            i.display_name,
            i.canonical_name
        from user_storecupboard_items s
        join ingredient_catalogue i on i.id = s.ingredient_id
        where s.user_id = %s
    """
    params: List[Any] = [str(user_id)]
    if stock_status:
        sql += " and s.stock_status::text = %s"
        params.append(stock_status)
    sql += " order by i.display_name asc"

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, tuple(params))
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


@app.post("/users/{user_id}/storecupboard", response_model=StorecupboardItemOut)
@app.post("/users/{user_id}/storecupboard-items", response_model=StorecupboardItemOut, include_in_schema=False)
def create_user_storecupboard_item(user_id: UUID, payload: NestedStorecupboardItemCreate):
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
                        quantity,
                        unit,
                        stock_status::text,
                        shelf_name
                    """,
                    (
                        str(user_id),
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


@app.get("/users/{user_id}/recipes", response_model=List[RecipeOut])
def list_user_recipes(user_id: UUID):
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
                    where created_by_user_id = %s
                    order by created_at desc
                    """,
                    (str(user_id),),
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


@app.post("/users/{user_id}/recipes", response_model=RecipeOut)
def create_user_recipe(user_id: UUID, payload: NestedRecipeCreate):
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
                        payload.title,
                        payload.description,
                        payload.instructions,
                        payload.source_url,
                        str(user_id),
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


@app.get("/users/{user_id}/ai-suggestions", response_model=List[AISuggestionOut])
def list_user_ai_suggestions(
    user_id: UUID,
    suggestion_type: Optional[str] = Query(default=None),
):
    sql = """
        select
            id,
            user_id,
            suggestion_type::text,
            title,
            body,
            created_at::text
        from ai_suggestions
        where user_id = %s
    """
    params: List[Any] = [str(user_id)]

    if suggestion_type:
        sql += " and suggestion_type::text = %s"
        params.append(suggestion_type)
    sql += " order by created_at desc"

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, tuple(params))
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


@app.post("/users/{user_id}/ai-suggestions/generate", response_model=AISuggestionOut)
def generate_user_ai_suggestion(user_id: UUID, payload: AISuggestionGenerateRequest):
    generated_title = f"{payload.suggestion_type.title()} suggestion"
    generated_body = payload.context or "Generated suggestion based on your recent activity."

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
                        str(user_id),
                        payload.suggestion_type,
                        generated_title,
                        generated_body,
                    ),
                )
                row = cur.fetchone()
            conn.commit()
    except Exception:
        import traceback
        traceback.print_exc()
        server_error("Could not generate AI suggestion.")

    return {
        "id": row[0],
        "user_id": row[1],
        "suggestion_type": row[2],
        "title": row[3],
        "body": row[4],
        "created_at": row[5],
    }
