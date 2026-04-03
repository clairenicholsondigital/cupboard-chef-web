from typing import List, Optional
from uuid import UUID
import os

from fastapi import FastAPI, HTTPException
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


class FoodEntryCreate(BaseModel):
    user_id: UUID
    description: str = Field(..., min_length=1)
    raw_input: Optional[str] = None
    input_method: str = "text"
    meal_time: Optional[str] = None
    rating: Optional[int] = Field(default=None, ge=1, le=5)


class FoodEntryOut(BaseModel):
    id: UUID
    user_id: Optional[UUID]
    description: str
    raw_input: Optional[str]
    input_method: Optional[str]
    meal_time: Optional[str]
    status: Optional[str]
    rating: Optional[int]


class IngredientOut(BaseModel):
    id: UUID
    canonical_name: str
    display_name: str
    category: Optional[str]


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    user_id: UUID
    email: str


@app.get("/health")
def health():
    return {"status": "ok"}


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
        "user_id": row[0],
        "email": row[1],
    }


@app.get("/ingredients", response_model=List[IngredientOut])
def list_ingredients():
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select id, canonical_name, display_name, category
                    from ingredient_catalogue
                    order by display_name asc
                    """
                )
                rows = cur.fetchall()
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail="Could not load ingredients.",
        )

    return [
        {
            "id": row[0],
            "canonical_name": row[1],
            "display_name": row[2],
            "category": row[3],
        }
        for row in rows
    ]


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
        raise HTTPException(
            status_code=500,
            detail="Could not load food entries.",
        )

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
                        rating
                    )
                    values (%s, %s, %s, %s::input_method, %s::meal_time_code, %s)
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
                    ),
                )
                row = cur.fetchone()
            conn.commit()
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail="Could not create food entry.",
        )

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