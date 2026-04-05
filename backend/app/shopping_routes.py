from typing import Any, Dict, List, Optional
from uuid import UUID
import base64
import hashlib
import hmac
import os
import time

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.db import get_conn


router = APIRouter(tags=["shopping"])

AUTH_TOKEN_SECRET = os.getenv("AUTH_TOKEN_SECRET", "dev-insecure-change-me")


def server_error(detail: str):
    raise HTTPException(status_code=500, detail=detail)


def not_found(detail: str):
    raise HTTPException(status_code=404, detail=detail)


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("utf-8"))


def _verify_auth_token(token: str) -> Dict[str, Any]:
    try:
        token_value = token.strip()
        signing_input, signature_segment = token_value.rsplit(".", 1)
        expected_signature = hmac.new(
            AUTH_TOKEN_SECRET.encode("utf-8"),
            signing_input.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        provided_signature = _b64url_decode(signature_segment)
        if not hmac.compare_digest(expected_signature, provided_signature):
            raise ValueError("bad signature")

        payload_segment = signing_input.split(".", 1)[1]
        payload_bytes = _b64url_decode(payload_segment)
        payload = __import__("json").loads(payload_bytes.decode("utf-8"))

        if int(payload.get("exp", 0)) < int(time.time()):
            raise ValueError("expired")

        user_id = str(payload.get("sub") or "").strip()
        email = str(payload.get("email") or "").strip().lower()
        if not user_id or not email:
            raise ValueError("missing claims")

        return {
            "user_id": user_id,
            "email": email,
        }
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid authentication token.")


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
                    (auth_claims["user_id"], auth_claims["email"]),
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


def ensure_list_ownership(cur: Any, shopping_list_id: UUID, authenticated_user: Dict[str, Any]):
    cur.execute(
        """
        select id, user_id, name, status, created_at::text, updated_at::text
        from shopping_lists
        where id = %s
        limit 1
        """,
        (str(shopping_list_id),),
    )
    row = cur.fetchone()
    if not row:
        not_found("Shopping list not found.")
    if str(row[1]) != str(authenticated_user["user_id"]):
        raise HTTPException(status_code=403, detail="Forbidden for requested shopping list.")
    return row


class ShoppingListCreate(BaseModel):
    name: str = Field(..., min_length=1)
    status: str = "active"


class ShoppingListUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1)
    status: Optional[str] = None


class ShoppingListOut(BaseModel):
    id: UUID
    user_id: UUID
    name: str
    status: str
    created_at: str
    updated_at: str


class ShoppingListListResponse(BaseModel):
    items: List[ShoppingListOut]
    total: int


class ShoppingListItemCreate(BaseModel):
    ingredient_id: Optional[UUID] = None
    item_name: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    is_checked: bool = False
    note: Optional[str] = None
    sort_order: int = 0
    source_type: str = "manual"
    source_ingredient_id: Optional[UUID] = None
    source_cupboard_item_id: Optional[UUID] = None
    source_recipe_id: Optional[UUID] = None


class ShoppingListItemUpdate(BaseModel):
    ingredient_id: Optional[UUID] = None
    item_name: Optional[str] = None
    quantity: Optional[float] = None
    unit: Optional[str] = None
    is_checked: Optional[bool] = None
    note: Optional[str] = None
    sort_order: Optional[int] = None
    source_type: Optional[str] = None
    source_ingredient_id: Optional[UUID] = None
    source_cupboard_item_id: Optional[UUID] = None
    source_recipe_id: Optional[UUID] = None


class ShoppingListItemOut(BaseModel):
    id: UUID
    shopping_list_id: UUID
    ingredient_id: Optional[UUID]
    item_name: Optional[str]
    quantity: Optional[float]
    unit: Optional[str]
    is_checked: bool
    note: Optional[str]
    sort_order: int
    source_type: str
    source_ingredient_id: Optional[UUID]
    source_cupboard_item_id: Optional[UUID]
    source_recipe_id: Optional[UUID]
    ingredient_display_name: Optional[str] = None
    ingredient_canonical_name: Optional[str] = None
    created_at: str
    updated_at: str


class ShoppingListItemListResponse(BaseModel):
    items: List[ShoppingListItemOut]
    total: int


def _validate_source_type(source_type: Optional[str]):
    if source_type is None:
        return
    valid = {"manual", "ingredient", "cupboard_item", "recipe"}
    if source_type not in valid:
        raise HTTPException(status_code=400, detail="source_type must be one of: manual, ingredient, cupboard_item, recipe.")


@router.get("/shopping-lists", response_model=ShoppingListListResponse)
def list_shopping_lists(
    status: Optional[str] = Query(default=None),
    authenticated_user: Dict[str, Any] = Depends(resolve_authenticated_user),
):
    if status and status not in {"active", "archived"}:
        raise HTTPException(status_code=400, detail="status must be active or archived.")

    where_sql = "where user_id = %s"
    params: List[Any] = [str(authenticated_user["user_id"])]
    if status:
        where_sql += " and status = %s"
        params.append(status)

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(f"select count(*) from shopping_lists {where_sql}", tuple(params))
                total = cur.fetchone()[0]
                cur.execute(
                    f"""
                    select id, user_id, name, status, created_at::text, updated_at::text
                    from shopping_lists
                    {where_sql}
                    order by updated_at desc
                    """,
                    tuple(params),
                )
                rows = cur.fetchall()
    except Exception:
        import traceback
        traceback.print_exc()
        server_error("Could not load shopping lists.")

    return {
        "items": [
            {
                "id": r[0],
                "user_id": r[1],
                "name": r[2],
                "status": r[3],
                "created_at": r[4],
                "updated_at": r[5],
            }
            for r in rows
        ],
        "total": total,
    }


@router.post("/users/{user_id}/shopping-lists", response_model=ShoppingListOut)
def create_shopping_list(
    user_id: UUID,
    payload: ShoppingListCreate,
    authenticated_user: Dict[str, Any] = Depends(resolve_authenticated_user),
):
    enforce_path_user(user_id, authenticated_user)
    if payload.status not in {"active", "archived"}:
        raise HTTPException(status_code=400, detail="status must be active or archived.")

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into shopping_lists (user_id, name, status)
                    values (%s, %s, %s)
                    returning id, user_id, name, status, created_at::text, updated_at::text
                    """,
                    (str(user_id), payload.name.strip(), payload.status),
                )
                row = cur.fetchone()
            conn.commit()
    except Exception:
        import traceback
        traceback.print_exc()
        server_error("Could not create shopping list.")

    return {
        "id": row[0],
        "user_id": row[1],
        "name": row[2],
        "status": row[3],
        "created_at": row[4],
        "updated_at": row[5],
    }


@router.get("/users/{user_id}/shopping-lists", response_model=ShoppingListListResponse)
def list_user_shopping_lists(
    user_id: UUID,
    status: Optional[str] = Query(default=None),
    authenticated_user: Dict[str, Any] = Depends(resolve_authenticated_user),
):
    enforce_path_user(user_id, authenticated_user)
    if status and status not in {"active", "archived"}:
        raise HTTPException(status_code=400, detail="status must be active or archived.")

    where_sql = "where user_id = %s"
    params: List[Any] = [str(user_id)]
    if status:
        where_sql += " and status = %s"
        params.append(status)

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(f"select count(*) from shopping_lists {where_sql}", tuple(params))
                total = cur.fetchone()[0]
                cur.execute(
                    f"""
                    select id, user_id, name, status, created_at::text, updated_at::text
                    from shopping_lists
                    {where_sql}
                    order by updated_at desc
                    """,
                    tuple(params),
                )
                rows = cur.fetchall()
    except Exception:
        import traceback
        traceback.print_exc()
        server_error("Could not load shopping lists.")

    return {
        "items": [
            {
                "id": r[0],
                "user_id": r[1],
                "name": r[2],
                "status": r[3],
                "created_at": r[4],
                "updated_at": r[5],
            }
            for r in rows
        ],
        "total": total,
    }


@router.get("/shopping-lists/{shopping_list_id}", response_model=ShoppingListOut)
def get_shopping_list(
    shopping_list_id: UUID,
    authenticated_user: Dict[str, Any] = Depends(resolve_authenticated_user),
):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                row = ensure_list_ownership(cur, shopping_list_id, authenticated_user)
    except HTTPException:
        raise
    except Exception:
        import traceback
        traceback.print_exc()
        server_error("Could not load shopping list.")

    return {
        "id": row[0],
        "user_id": row[1],
        "name": row[2],
        "status": row[3],
        "created_at": row[4],
        "updated_at": row[5],
    }


@router.put("/shopping-lists/{shopping_list_id}", response_model=ShoppingListOut)
def update_shopping_list(
    shopping_list_id: UUID,
    payload: ShoppingListUpdate,
    authenticated_user: Dict[str, Any] = Depends(resolve_authenticated_user),
):
    if payload.status and payload.status not in {"active", "archived"}:
        raise HTTPException(status_code=400, detail="status must be active or archived.")

    if payload.name is None and payload.status is None:
        raise HTTPException(status_code=400, detail="Provide at least one field to update.")

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                ensure_list_ownership(cur, shopping_list_id, authenticated_user)
                cur.execute(
                    """
                    update shopping_lists
                    set
                      name = coalesce(%s, name),
                      status = coalesce(%s, status),
                      updated_at = now()
                    where id = %s
                    returning id, user_id, name, status, created_at::text, updated_at::text
                    """,
                    (
                        payload.name.strip() if payload.name else None,
                        payload.status,
                        str(shopping_list_id),
                    ),
                )
                row = cur.fetchone()
            conn.commit()
    except HTTPException:
        raise
    except Exception:
        import traceback
        traceback.print_exc()
        server_error("Could not update shopping list.")

    return {
        "id": row[0],
        "user_id": row[1],
        "name": row[2],
        "status": row[3],
        "created_at": row[4],
        "updated_at": row[5],
    }


@router.delete("/shopping-lists/{shopping_list_id}")
def delete_shopping_list(
    shopping_list_id: UUID,
    authenticated_user: Dict[str, Any] = Depends(resolve_authenticated_user),
):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                ensure_list_ownership(cur, shopping_list_id, authenticated_user)
                cur.execute("delete from shopping_lists where id = %s", (str(shopping_list_id),))
            conn.commit()
    except HTTPException:
        raise
    except Exception:
        import traceback
        traceback.print_exc()
        server_error("Could not delete shopping list.")

    return {"ok": True}


@router.get("/shopping-lists/{shopping_list_id}/items", response_model=ShoppingListItemListResponse)
def list_shopping_list_items(
    shopping_list_id: UUID,
    sort_by: str = Query(default="sort_order"),
    sort_dir: str = Query(default="asc"),
    authenticated_user: Dict[str, Any] = Depends(resolve_authenticated_user),
):
    allowed_sort_fields = {"sort_order", "created_at", "updated_at", "is_checked"}
    if sort_by not in allowed_sort_fields:
        raise HTTPException(status_code=400, detail="Invalid sort_by value.")
    if sort_dir.lower() not in {"asc", "desc"}:
        raise HTTPException(status_code=400, detail="sort_dir must be asc or desc.")

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                ensure_list_ownership(cur, shopping_list_id, authenticated_user)
                cur.execute(
                    f"""
                    select
                        i.id,
                        i.shopping_list_id,
                        i.ingredient_id,
                        i.item_name,
                        i.quantity,
                        i.unit,
                        i.is_checked,
                        i.note,
                        i.sort_order,
                        i.source_type,
                        i.source_ingredient_id,
                        i.source_cupboard_item_id,
                        i.source_recipe_id,
                        c.display_name as ingredient_display_name,
                        c.canonical_name as ingredient_canonical_name,
                        i.created_at::text,
                        i.updated_at::text
                    from shopping_list_items i
                    left join ingredient_catalogue c on c.id = i.ingredient_id
                    where i.shopping_list_id = %s
                    order by i.{sort_by} {sort_dir.upper()}, i.created_at asc
                    """,
                    (str(shopping_list_id),),
                )
                rows = cur.fetchall()
    except HTTPException:
        raise
    except Exception:
        import traceback
        traceback.print_exc()
        server_error("Could not load shopping list items.")

    return {
        "items": [
            {
                "id": r[0],
                "shopping_list_id": r[1],
                "ingredient_id": r[2],
                "item_name": r[3],
                "quantity": float(r[4]) if r[4] is not None else None,
                "unit": r[5],
                "is_checked": r[6],
                "note": r[7],
                "sort_order": r[8],
                "source_type": r[9],
                "source_ingredient_id": r[10],
                "source_cupboard_item_id": r[11],
                "source_recipe_id": r[12],
                "ingredient_display_name": r[13],
                "ingredient_canonical_name": r[14],
                "created_at": r[15],
                "updated_at": r[16],
            }
            for r in rows
        ],
        "total": len(rows),
    }


@router.post("/shopping-lists/{shopping_list_id}/items", response_model=ShoppingListItemOut)
def create_shopping_list_item(
    shopping_list_id: UUID,
    payload: ShoppingListItemCreate,
    authenticated_user: Dict[str, Any] = Depends(resolve_authenticated_user),
):
    _validate_source_type(payload.source_type)
    if not payload.ingredient_id and not (payload.item_name or "").strip():
        raise HTTPException(status_code=400, detail="Provide item_name when ingredient_id is not set.")

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                ensure_list_ownership(cur, shopping_list_id, authenticated_user)
                cur.execute(
                    """
                    insert into shopping_list_items (
                        shopping_list_id, ingredient_id, item_name, quantity, unit, is_checked,
                        note, sort_order, source_type, source_ingredient_id,
                        source_cupboard_item_id, source_recipe_id
                    )
                    values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    returning id
                    """,
                    (
                        str(shopping_list_id),
                        str(payload.ingredient_id) if payload.ingredient_id else None,
                        payload.item_name.strip() if payload.item_name else None,
                        payload.quantity,
                        payload.unit.strip() if payload.unit else None,
                        payload.is_checked,
                        payload.note.strip() if payload.note else None,
                        payload.sort_order,
                        payload.source_type or "manual",
                        str(payload.source_ingredient_id) if payload.source_ingredient_id else None,
                        str(payload.source_cupboard_item_id) if payload.source_cupboard_item_id else None,
                        str(payload.source_recipe_id) if payload.source_recipe_id else None,
                    ),
                )
                item_id = cur.fetchone()[0]
                cur.execute(
                    "update shopping_lists set updated_at = now() where id = %s",
                    (str(shopping_list_id),),
                )
                cur.execute(
                    """
                    select
                        i.id,
                        i.shopping_list_id,
                        i.ingredient_id,
                        i.item_name,
                        i.quantity,
                        i.unit,
                        i.is_checked,
                        i.note,
                        i.sort_order,
                        i.source_type,
                        i.source_ingredient_id,
                        i.source_cupboard_item_id,
                        i.source_recipe_id,
                        c.display_name,
                        c.canonical_name,
                        i.created_at::text,
                        i.updated_at::text
                    from shopping_list_items i
                    left join ingredient_catalogue c on c.id = i.ingredient_id
                    where i.id = %s
                    """,
                    (str(item_id),),
                )
                row = cur.fetchone()
            conn.commit()
    except HTTPException:
        raise
    except Exception:
        import traceback
        traceback.print_exc()
        server_error("Could not create shopping list item.")

    return {
        "id": row[0],
        "shopping_list_id": row[1],
        "ingredient_id": row[2],
        "item_name": row[3],
        "quantity": float(row[4]) if row[4] is not None else None,
        "unit": row[5],
        "is_checked": row[6],
        "note": row[7],
        "sort_order": row[8],
        "source_type": row[9],
        "source_ingredient_id": row[10],
        "source_cupboard_item_id": row[11],
        "source_recipe_id": row[12],
        "ingredient_display_name": row[13],
        "ingredient_canonical_name": row[14],
        "created_at": row[15],
        "updated_at": row[16],
    }


@router.get("/shopping-list-items/{item_id}", response_model=ShoppingListItemOut)
def get_shopping_list_item(
    item_id: UUID,
    authenticated_user: Dict[str, Any] = Depends(resolve_authenticated_user),
):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select
                        i.id,
                        i.shopping_list_id,
                        i.ingredient_id,
                        i.item_name,
                        i.quantity,
                        i.unit,
                        i.is_checked,
                        i.note,
                        i.sort_order,
                        i.source_type,
                        i.source_ingredient_id,
                        i.source_cupboard_item_id,
                        i.source_recipe_id,
                        c.display_name,
                        c.canonical_name,
                        i.created_at::text,
                        i.updated_at::text,
                        l.user_id
                    from shopping_list_items i
                    join shopping_lists l on l.id = i.shopping_list_id
                    left join ingredient_catalogue c on c.id = i.ingredient_id
                    where i.id = %s
                    limit 1
                    """,
                    (str(item_id),),
                )
                row = cur.fetchone()
    except Exception:
        import traceback
        traceback.print_exc()
        server_error("Could not load shopping list item.")

    if not row:
        not_found("Shopping list item not found.")
    if str(row[17]) != str(authenticated_user["user_id"]):
        raise HTTPException(status_code=403, detail="Forbidden for requested shopping list item.")

    return {
        "id": row[0],
        "shopping_list_id": row[1],
        "ingredient_id": row[2],
        "item_name": row[3],
        "quantity": float(row[4]) if row[4] is not None else None,
        "unit": row[5],
        "is_checked": row[6],
        "note": row[7],
        "sort_order": row[8],
        "source_type": row[9],
        "source_ingredient_id": row[10],
        "source_cupboard_item_id": row[11],
        "source_recipe_id": row[12],
        "ingredient_display_name": row[13],
        "ingredient_canonical_name": row[14],
        "created_at": row[15],
        "updated_at": row[16],
    }


@router.put("/shopping-list-items/{item_id}", response_model=ShoppingListItemOut)
def update_shopping_list_item(
    item_id: UUID,
    payload: ShoppingListItemUpdate,
    authenticated_user: Dict[str, Any] = Depends(resolve_authenticated_user),
):
    if payload.source_type is not None:
        _validate_source_type(payload.source_type)

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select i.shopping_list_id, l.user_id, i.ingredient_id, i.item_name
                    from shopping_list_items i
                    join shopping_lists l on l.id = i.shopping_list_id
                    where i.id = %s
                    limit 1
                    """,
                    (str(item_id),),
                )
                item_row = cur.fetchone()
                if not item_row:
                    not_found("Shopping list item not found.")
                shopping_list_id = item_row[0]
                if str(item_row[1]) != str(authenticated_user["user_id"]):
                    raise HTTPException(status_code=403, detail="Forbidden for requested shopping list item.")

                effective_ingredient_id = str(payload.ingredient_id) if payload.ingredient_id is not None else (
                    str(item_row[2]) if item_row[2] is not None else None
                )
                effective_item_name = payload.item_name.strip() if payload.item_name is not None else (item_row[3] or "")
                if not effective_ingredient_id and not effective_item_name:
                    raise HTTPException(status_code=400, detail="item_name is required when ingredient_id is not set.")

                cur.execute(
                    """
                    update shopping_list_items
                    set
                        ingredient_id = coalesce(%s, ingredient_id),
                        item_name = coalesce(%s, item_name),
                        quantity = coalesce(%s, quantity),
                        unit = coalesce(%s, unit),
                        is_checked = coalesce(%s, is_checked),
                        note = coalesce(%s, note),
                        sort_order = coalesce(%s, sort_order),
                        source_type = coalesce(%s, source_type),
                        source_ingredient_id = coalesce(%s, source_ingredient_id),
                        source_cupboard_item_id = coalesce(%s, source_cupboard_item_id),
                        source_recipe_id = coalesce(%s, source_recipe_id),
                        updated_at = now()
                    where id = %s
                    returning id, shopping_list_id, ingredient_id, item_name, quantity, unit,
                              is_checked, note, sort_order, source_type,
                              source_ingredient_id, source_cupboard_item_id, source_recipe_id,
                              created_at::text, updated_at::text
                    """,
                    (
                        str(payload.ingredient_id) if payload.ingredient_id else None,
                        payload.item_name.strip() if payload.item_name else None,
                        payload.quantity,
                        payload.unit.strip() if payload.unit else None,
                        payload.is_checked,
                        payload.note.strip() if payload.note else None,
                        payload.sort_order,
                        payload.source_type,
                        str(payload.source_ingredient_id) if payload.source_ingredient_id else None,
                        str(payload.source_cupboard_item_id) if payload.source_cupboard_item_id else None,
                        str(payload.source_recipe_id) if payload.source_recipe_id else None,
                        str(item_id),
                    ),
                )
                updated = cur.fetchone()
                cur.execute("update shopping_lists set updated_at = now() where id = %s", (str(shopping_list_id),))
                cur.execute(
                    """
                    select c.display_name, c.canonical_name
                    from shopping_list_items i
                    left join ingredient_catalogue c on c.id = i.ingredient_id
                    where i.id = %s
                    """,
                    (str(item_id),),
                )
                ingredient_row = cur.fetchone()
            conn.commit()
    except HTTPException:
        raise
    except Exception:
        import traceback
        traceback.print_exc()
        server_error("Could not update shopping list item.")

    return {
        "id": updated[0],
        "shopping_list_id": updated[1],
        "ingredient_id": updated[2],
        "item_name": updated[3],
        "quantity": float(updated[4]) if updated[4] is not None else None,
        "unit": updated[5],
        "is_checked": updated[6],
        "note": updated[7],
        "sort_order": updated[8],
        "source_type": updated[9],
        "source_ingredient_id": updated[10],
        "source_cupboard_item_id": updated[11],
        "source_recipe_id": updated[12],
        "ingredient_display_name": ingredient_row[0] if ingredient_row else None,
        "ingredient_canonical_name": ingredient_row[1] if ingredient_row else None,
        "created_at": updated[13],
        "updated_at": updated[14],
    }


@router.delete("/shopping-list-items/{item_id}")
def delete_shopping_list_item(
    item_id: UUID,
    authenticated_user: Dict[str, Any] = Depends(resolve_authenticated_user),
):
    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select i.shopping_list_id, l.user_id
                    from shopping_list_items i
                    join shopping_lists l on l.id = i.shopping_list_id
                    where i.id = %s
                    limit 1
                    """,
                    (str(item_id),),
                )
                row = cur.fetchone()
                if not row:
                    not_found("Shopping list item not found.")
                if str(row[1]) != str(authenticated_user["user_id"]):
                    raise HTTPException(status_code=403, detail="Forbidden for requested shopping list item.")

                cur.execute("delete from shopping_list_items where id = %s", (str(item_id),))
                cur.execute("update shopping_lists set updated_at = now() where id = %s", (str(row[0]),))
            conn.commit()
    except HTTPException:
        raise
    except Exception:
        import traceback
        traceback.print_exc()
        server_error("Could not delete shopping list item.")

    return {"ok": True}
