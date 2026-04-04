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


class IngredientListResponse(BaseModel):
    items: List[IngredientOut]
    total: int
    limit: int
    offset: int


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


class FoodEntryListResponse(BaseModel):
    items: List[FoodEntryOut]
    total: int
    limit: int
    offset: int


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


class StorecupboardListResponse(BaseModel):
    items: List[StorecupboardItemOut]
    total: int
    limit: int
    offset: int


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


class RecipeListResponse(BaseModel):
    items: List[RecipeOut]
    total: int
    limit: int
    offset: int


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

@app.get("/ingredients", response_model=IngredientListResponse)
def list_ingredients(
    q: Optional[str] = Query(default=None, min_length=1),
    category: Optional[str] = None,
    is_seasonal: Optional[bool] = None,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    sort: str = Query(default="display_name"),
    order: str = Query(default="asc"),
):
    sort_map = {
        "display_name": "display_name",
        "canonical_name": "canonical_name",
        "created_at": "created_at",
        "category": "category",
    }
    sort_column = sort_map.get(sort, "display_name")
    order_direction = "desc" if order.lower() == "desc" else "asc"
    where_clauses = []
    params: List[Any] = []

    if q:
        where_clauses.append("(display_name ILIKE %s OR canonical_name ILIKE %s OR category ILIKE %s)")
        q_like = f"%{q.strip()}%"
        params.extend([q_like, q_like, q_like])
    if category:
        where_clauses.append("category = %s")
        params.append(category)
    if is_seasonal is not None:
        where_clauses.append("is_seasonal = %s")
        params.append(is_seasonal)

    where_sql = f"where {' and '.join(where_clauses)}" if where_clauses else ""
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    select count(*)
                    from ingredient_catalogue
                    {where_sql}
                    """,
                    tuple(params),
                )
                total = cur.fetchone()[0]
                cur.execute(
                    f"""
                    select
                        id,
                        canonical_name,
                        display_name,
                        category,
                        is_seasonal,
                        seasonal_months
                    from ingredient_catalogue
                    {where_sql}
                    order by {sort_column} {order_direction}, id asc
                    limit %s
                    offset %s
                    """,
                    tuple(params + [limit, offset]),
                )
                rows = cur.fetchall()
    except Exception as e:
        import traceback
        traceback.print_exc()
        server_error("Could not load ingredients.")

    return {
        "items": [
            {
                "id": row[0],
                "canonical_name": row[1],
                "display_name": row[2],
                "category": row[3],
                "is_seasonal": row[4],
                "seasonal_months": row[5],
            }
            for row in rows
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


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
# Recipes
# -------------------------------------------------------------------

@app.get("/recipes", response_model=RecipeListResponse)
def list_recipes(
    q: Optional[str] = Query(default=None, min_length=1),
    created_by_user_id: Optional[UUID] = None,
    is_system: Optional[bool] = None,
    from_date: Optional[str] = Query(default=None, alias="from"),
    to_date: Optional[str] = Query(default=None, alias="to"),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    sort: str = Query(default="created_at"),
    order: str = Query(default="desc"),
):
    sort_map = {
        "title": "title",
        "created_at": "created_at",
        "updated_at": "updated_at",
    }
    sort_column = sort_map.get(sort, "created_at")
    order_direction = "desc" if order.lower() == "desc" else "asc"
    where_clauses = []
    params: List[Any] = []

    if q:
        where_clauses.append("(title ILIKE %s OR coalesce(description, '') ILIKE %s)")
        q_like = f"%{q.strip()}%"
        params.extend([q_like, q_like])
    if created_by_user_id:
        where_clauses.append("created_by_user_id = %s")
        params.append(str(created_by_user_id))
    if is_system is not None:
        where_clauses.append("is_system = %s")
        params.append(is_system)
    if from_date:
        where_clauses.append("created_at >= %s::timestamptz")
        params.append(from_date)
    if to_date:
        where_clauses.append("created_at <= %s::timestamptz")
        params.append(to_date)

    where_sql = f"where {' and '.join(where_clauses)}" if where_clauses else ""
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    select count(*)
                    from recipe_catalogue
                    {where_sql}
                    """,
                    tuple(params),
                )
                total = cur.fetchone()[0]
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
                    order by {sort_column} {order_direction}, id asc
                    limit %s
                    offset %s
                    """,
                    tuple(params + [limit, offset]),
                )
                rows = cur.fetchall()
    except Exception:
        import traceback
        traceback.print_exc()
        server_error("Could not load recipes.")

    return {
        "items": [
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
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


# -------------------------------------------------------------------
# Storecupboard
# -------------------------------------------------------------------

@app.get("/storecupboard", response_model=StorecupboardListResponse)
def list_storecupboard_items(
    user_id: UUID,
    q: Optional[str] = Query(default=None, min_length=1),
    stock_status: Optional[str] = None,
    shelf_name: Optional[str] = None,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    sort: str = Query(default="updated_at"),
    order: str = Query(default="desc"),
):
    sort_map = {
        "updated_at": "s.updated_at",
        "created_at": "s.created_at",
        "stock_status": "s.stock_status",
        "ingredient": "i.display_name",
        "quantity": "s.quantity",
    }
    sort_column = sort_map.get(sort, "s.updated_at")
    order_direction = "desc" if order.lower() == "desc" else "asc"
    where_clauses = ["s.user_id = %s"]
    params: List[Any] = [str(user_id)]

    if q:
        where_clauses.append(
            "(i.display_name ILIKE %s OR i.canonical_name ILIKE %s OR coalesce(s.shelf_name, '') ILIKE %s)"
        )
        q_like = f"%{q.strip()}%"
        params.extend([q_like, q_like, q_like])
    if stock_status:
        where_clauses.append("s.stock_status::text = %s")
        params.append(stock_status)
    if shelf_name:
        where_clauses.append("coalesce(s.shelf_name, '') ILIKE %s")
        params.append(f"%{shelf_name.strip()}%")

    where_sql = f"where {' and '.join(where_clauses)}"
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    select count(*)
                    from user_storecupboard_items s
                    join ingredient_catalogue i on i.id = s.ingredient_id
                    {where_sql}
                    """,
                    tuple(params),
                )
                total = cur.fetchone()[0]
                cur.execute(
                    f"""
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
                    {where_sql}
                    order by {sort_column} {order_direction}, s.id asc
                    limit %s
                    offset %s
                    """,
                    tuple(params + [limit, offset]),
                )
                rows = cur.fetchall()
    except Exception:
        import traceback
        traceback.print_exc()
        server_error("Could not load storecupboard items.")

    return {
        "items": [
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
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


# -------------------------------------------------------------------
# Food entries
# -------------------------------------------------------------------

@app.get("/food-entries", response_model=FoodEntryListResponse)
def list_food_entries(
    user_id: Optional[UUID] = None,
    q: Optional[str] = Query(default=None, min_length=1),
    meal_time: Optional[str] = None,
    status: Optional[str] = None,
    from_date: Optional[str] = Query(default=None, alias="from"),
    to_date: Optional[str] = Query(default=None, alias="to"),
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    sort: str = Query(default="logged_at"),
    order: str = Query(default="desc"),
):
    sort_map = {
        "logged_at": "logged_at",
        "created_at": "created_at",
        "updated_at": "updated_at",
        "meal_time": "meal_time",
        "status": "status",
    }
    sort_column = sort_map.get(sort, "logged_at")
    order_direction = "desc" if order.lower() == "desc" else "asc"
    where_clauses = []
    params: List[Any] = []

    if user_id:
        where_clauses.append("user_id = %s")
        params.append(str(user_id))
    if q:
        where_clauses.append("(description ILIKE %s OR coalesce(raw_input, '') ILIKE %s)")
        q_like = f"%{q.strip()}%"
        params.extend([q_like, q_like])
    if meal_time:
        where_clauses.append("meal_time::text = %s")
        params.append(meal_time)
    if status:
        where_clauses.append("status::text = %s")
        params.append(status)
    if from_date:
        where_clauses.append("logged_at >= %s::timestamptz")
        params.append(from_date)
    if to_date:
        where_clauses.append("logged_at <= %s::timestamptz")
        params.append(to_date)

    where_sql = f"where {' and '.join(where_clauses)}" if where_clauses else ""
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    select count(*)
                    from food_entries
                    {where_sql}
                    """,
                    tuple(params),
                )
                total = cur.fetchone()[0]
                cur.execute(
                    f"""
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
                    {where_sql}
                    order by {sort_column} {order_direction}, id asc
                    limit %s
                    offset %s
                    """,
                    tuple(params + [limit, offset]),
                )
                rows = cur.fetchall()
    except Exception as e:
        import traceback
        traceback.print_exc()
        server_error("Could not load food entries.")

    return {
        "items": [
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
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


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
