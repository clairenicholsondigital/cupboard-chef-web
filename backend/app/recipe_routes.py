from typing import Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.db import get_conn


router = APIRouter(prefix="/recipes", tags=["recipes"])


# -------------------------------------------------------------------
# Models
# -------------------------------------------------------------------

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


def server_error(detail: str):
    raise HTTPException(status_code=500, detail=detail)


def not_found(detail: str):
    raise HTTPException(status_code=404, detail=detail)


# -------------------------------------------------------------------
# Routes
# -------------------------------------------------------------------

@router.get("", response_model=RecipeListResponse)
def list_recipes(
    q: Optional[str] = Query(default=None, min_length=1),
    created_by_user_id: Optional[UUID] = None,
    is_system: Optional[bool] = None,
    limit: int = Query(default=25, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
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

    where_sql = f"where {' and '.join(where_clauses)}" if where_clauses else ""

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"select count(*) from recipe_catalogue {where_sql}",
                    tuple(params),
                )
                total = cur.fetchone()[0]

                cur.execute(
                    f"""
                    select id, title, description, instructions, source_url,
                           created_by_user_id, is_system
                    from recipe_catalogue
                    {where_sql}
                    order by created_at desc
                    limit %s offset %s
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
                "id": r[0],
                "title": r[1],
                "description": r[2],
                "instructions": r[3],
                "source_url": r[4],
                "created_by_user_id": r[5],
                "is_system": r[6],
            }
            for r in rows
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.post("", response_model=RecipeOut)
def create_recipe(payload: RecipeCreate):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into recipe_catalogue (
                        title, description, instructions,
                        source_url, created_by_user_id, is_system
                    )
                    values (%s, %s, %s, %s, %s, %s)
                    returning id, title, description, instructions,
                              source_url, created_by_user_id, is_system
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


@router.get("/{recipe_id}", response_model=RecipeOut)
def get_recipe(recipe_id: UUID):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "select id, title, description, instructions, source_url, created_by_user_id, is_system from recipe_catalogue where id = %s",
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