from typing import Any, Dict, List, Optional
from uuid import UUID
import base64
import bcrypt
import hashlib
import hmac
import os
import time

from fastapi import Depends, FastAPI, Header, HTTPException, Query
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


AUTH_TOKEN_TTL_SECONDS = int(os.getenv("AUTH_TOKEN_TTL_SECONDS", "604800"))
AUTH_TOKEN_SECRET = os.getenv("AUTH_TOKEN_SECRET", "dev-insecure-change-me")


# -------------------------------------------------------------------
# Pydantic models
# -------------------------------------------------------------------


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    user_id: UUID
    email: str
    access_token: str
    token_type: str = "bearer"


class AuthIdentity(BaseModel):
    user_id: UUID
    email: str
    display_name: Optional[str] = None
    profile_flags: Dict[str, bool]


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


class TagUpdate(BaseModel):
    slug: Optional[str] = None
    label: Optional[str] = None
    description: Optional[str] = None
    colour_hex: Optional[str] = None
    is_system: Optional[bool] = None
    display_order: Optional[int] = None


class FoodEntryCreate(BaseModel):
    description: str = Field(..., min_length=1)
    raw_input: Optional[str] = None
    input_method: str = "text"
    meal_time: Optional[str] = None
    rating: Optional[int] = Field(default=None, ge=1, le=5)
    status: str = "logged"


class UserFoodEntryCreate(BaseModel):
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
    ingredient_id: UUID
    quantity: Optional[float] = None
    unit: Optional[str] = None
    stock_status: str = "in_stock"
    shelf_name: Optional[str] = None


class NestedStorecupboardItemCreate(BaseModel):
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


class RecipeUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    instructions: Optional[str] = None
    source_url: Optional[str] = None
    created_by_user_id: Optional[UUID] = None
    is_system: Optional[bool] = None


class RecipeListResponse(BaseModel):
    items: List[RecipeOut]
    total: int
    limit: int
    offset: int


class AISuggestionCreate(BaseModel):
    suggestion_type: str
    title: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)


class NestedAISuggestionCreate(BaseModel):
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


def _b64_urlsafe_decode(value: str) -> str:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}".encode("utf-8")).decode("utf-8")


def _issue_auth_token(user_id: str, email: str) -> str:
    issued_at = int(time.time())
    expires_at = issued_at + AUTH_TOKEN_TTL_SECONDS
    payload = f"{user_id}:{email}:{expires_at}"
    signature = hmac.new(
        AUTH_TOKEN_SECRET.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    token_raw = f"{payload}:{signature}"
    return base64.urlsafe_b64encode(token_raw.encode("utf-8")).decode("utf-8").rstrip("=")


def _verify_auth_token(token: str) -> Dict[str, str]:
    try:
        decoded = _b64_urlsafe_decode(token.strip())
        user_id, email, expires_at, signature = decoded.split(":", 3)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authentication token.")

    payload = f"{user_id}:{email}:{expires_at}"
    expected_signature = hmac.new(
        AUTH_TOKEN_SECRET.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(signature, expected_signature):
        raise HTTPException(status_code=401, detail="Invalid authentication token.")

    if int(expires_at) < int(time.time()):
        raise HTTPException(status_code=401, detail="Authentication token has expired.")

    return {"user_id": user_id, "email": email}


def _candidate_password_hashes(stored_hash: Optional[str]) -> List[str]:
    if not stored_hash:
        return []

    raw = stored_hash.strip()
    candidates: List[str] = [raw]

    if raw.startswith("2"):
        candidates.append(f"${raw}")

    if raw.startswith("2a$") or raw.startswith("2b$") or raw.startswith("2y$"):
        candidates.append(f"${raw}")

    if raw.startswith("b$") or raw.startswith("a$") or raw.startswith("y$"):
        candidates.append(f"$2{raw}")

    seen = set()
    deduped: List[str] = []
    for item in candidates:
        if item and item not in seen:
            seen.add(item)
            deduped.append(item)

    return deduped


def _bcrypt_password_matches(password: str, stored_hash: Optional[str]) -> bool:
    if not stored_hash:
        return False

    password_bytes = password.encode("utf-8")

    for candidate_hash in _candidate_password_hashes(stored_hash):
        try:
            if bcrypt.checkpw(password_bytes, candidate_hash.encode("utf-8")):
                return True
        except ValueError:
            continue

    return False


def _verify_password_for_user(cur: Any, email: str, password: str):
    cur.execute(
        """
        select column_name
        from information_schema.columns
        where table_schema = current_schema()
          and table_name = 'app_users'
          and column_name in ('password_hash', 'password')
        """
    )
    columns = {row[0] for row in cur.fetchall()}

    if "password_hash" in columns:
        cur.execute(
            """
            select id, email, password_hash
            from app_users
            where lower(email) = %s
            limit 1
            """,
            (email,),
        )
        row = cur.fetchone()
        if not row:
            return None

        user_id, user_email, password_hash = row

        if _bcrypt_password_matches(password, password_hash):
            return (user_id, user_email)

        return None

    if "password" in columns:
        cur.execute(
            """
            select id, email
            from app_users
            where lower(email) = %s
              and password = %s
            limit 1
            """,
            (email, password),
        )
        return cur.fetchone()

    server_error(
        "Password-based login is not configured for app_users. Add password_hash or password column."
    )


def resolve_authenticated_user(
    authorization: Optional[str] = Header(default=None),
) -> Dict[str, Any]:
    if not authorization:
        raise HTTPException(status_code=401, detail="Unauthorized. Provide Authorization: Bearer <token>.")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(status_code=401, detail="Unauthorized. Provide Authorization: Bearer <token>.")

    auth_claims = _verify_auth_token(token.strip())

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select id, email, display_name
                    from app_users
                    where id = %s and lower(email) = %s
                    limit 1
                    """,
                    (auth_claims["user_id"], auth_claims["email"].lower()),
                )
                row = cur.fetchone()
    except Exception:
        import traceback
        traceback.print_exc()
        server_error("Could not resolve authenticated user.")

    if not row:
        raise HTTPException(status_code=401, detail="Authenticated user was not found.")

    return {
        "user_id": row[0],
        "email": row[1],
        "display_name": row[2],
    }


def enforce_path_user(path_user_id: UUID, authenticated_user: Dict[str, Any]) -> None:
    if str(path_user_id) != str(authenticated_user["user_id"]):
        raise HTTPException(status_code=403, detail="Forbidden for requested user_id.")


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
                row = _verify_password_for_user(cur, email, password)
    except HTTPException:
        raise
    except Exception:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail="Login failed because the API could not connect to the database.",
        )

    if not row:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return {
        "user_id": str(row[0]),
        "email": row[1],
        "access_token": _issue_auth_token(str(row[0]), row[1].lower()),
        "token_type": "bearer",
    }


@app.get("/auth/me", response_model=AuthIdentity)
def auth_me(authenticated_user: Dict[str, Any] = Depends(resolve_authenticated_user)):
    query = """
        select
            u.id,
            u.email,
            u.display_name,
            p.id is not null as has_profile,
            coalesce(p.onboarding_completed, false) as onboarding_completed
        from app_users u
        left join user_profiles p on p.user_id = u.id
        where u.id = %s
        limit 1
    """
    params = (str(authenticated_user["user_id"]),)

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                row = cur.fetchone()
    except Exception:
        import traceback
        traceback.print_exc()
        server_error("Could not resolve current user.")

    if not row:
        raise HTTPException(status_code=401, detail="Authenticated user was not found.")

    return {
        "user_id": row[0],
        "email": row[1],
        "display_name": row[2],
        "profile_flags": {
            "has_profile": bool(row[3]),
            "onboarding_completed": bool(row[4]),
        },
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
    except Exception:
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
def get_user(user_id: UUID, authenticated_user: Dict[str, Any] = Depends(resolve_authenticated_user)):
    enforce_path_user(user_id, authenticated_user)
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
    except Exception:
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
def get_user_profile(user_id: UUID, authenticated_user: Dict[str, Any] = Depends(resolve_authenticated_user)):
    enforce_path_user(user_id, authenticated_user)
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
    except Exception:
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
def upsert_user_profile(
    user_id: UUID,
    payload: UserProfileUpsert,
    authenticated_user: Dict[str, Any] = Depends(resolve_authenticated_user),
):
    enforce_path_user(user_id, authenticated_user)
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
    except Exception:
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
    except Exception:
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
    except Exception:
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


@app.get("/food-entries", response_model=FoodEntryListResponse)
def list_food_entries(
    authenticated_user: Dict[str, Any] = Depends(resolve_authenticated_user),
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

    where_clauses.append("user_id = %s")
    params.append(str(authenticated_user["user_id"]))
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
    except Exception:
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
def create_food_entry(
    payload: FoodEntryCreate,
    authenticated_user: Dict[str, Any] = Depends(resolve_authenticated_user),
):
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
                        str(authenticated_user["user_id"]),
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
    except Exception:
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
    authenticated_user: Dict[str, Any] = Depends(resolve_authenticated_user),
):
    enforce_path_user(user_id, authenticated_user)
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
                    where user_id = %s
                    order by created_at desc, id desc
                    """,
                    (str(user_id),),
                )
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
def create_user_food_entry(
    user_id: UUID,
    payload: UserFoodEntryCreate,
    authenticated_user: Dict[str, Any] = Depends(resolve_authenticated_user),
):
    enforce_path_user(user_id, authenticated_user)
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
                        str(user_id),
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
    except Exception:
        import traceback
        traceback.print_exc()
        server_error("Could not create user food entry.")

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
def get_food_entry(entry_id: UUID, authenticated_user: Dict[str, Any] = Depends(resolve_authenticated_user)):
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
                    where id = %s and user_id = %s
                    limit 1
                    """,
                    (str(entry_id), str(authenticated_user["user_id"])),
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
def update_food_entry(
    entry_id: UUID,
    payload: FoodEntryUpdate,
    authenticated_user: Dict[str, Any] = Depends(resolve_authenticated_user),
):
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
                    where id = %s and user_id = %s
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
                        str(authenticated_user["user_id"]),
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
def delete_food_entry(entry_id: UUID, authenticated_user: Dict[str, Any] = Depends(resolve_authenticated_user)):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    delete from food_entries
                    where id = %s and user_id = %s
                    returning id
                    """,
                    (str(entry_id), str(authenticated_user["user_id"])),
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
# Storecupboard
# -------------------------------------------------------------------


@app.get("/storecupboard", response_model=StorecupboardListResponse)
def list_storecupboard(
    authenticated_user: Dict[str, Any] = Depends(resolve_authenticated_user),
    q: Optional[str] = Query(default=None, min_length=1),
    stock_status: Optional[str]