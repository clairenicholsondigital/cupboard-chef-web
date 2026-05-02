from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.db import get_conn


router = APIRouter(tags=["mobile-api"])


class ApiError(BaseModel):
    error: str
    code: str


class RecipeSuggestRequest(BaseModel):
    ingredients: Any
    dietary: Optional[List[str]] = None
    timeMinutes: Optional[int] = None
    useFirst: Optional[List[str]] = None
    servings: Optional[int] = None


class ShoppingListRequest(BaseModel):
    selectedRecipes: List[Dict[str, Any]] = Field(default_factory=list)


class SwapsRequest(BaseModel):
    missingIngredients: List[str] = Field(default_factory=list)


class FoodWasteScoreRequest(BaseModel):
    ingredients: List[str] = Field(default_factory=list)
    useFirst: Optional[List[str]] = None


def _norm(value: str) -> str:
    return " ".join(value.strip().lower().split())


def _clean_string_list(values: Optional[List[str]]) -> List[str]:
    if not values:
        return []
    cleaned: List[str] = []
    for value in values:
        if isinstance(value, str):
            item = _norm(value)
            if item:
                cleaned.append(item)
    return cleaned


SWAPS: Dict[str, List[str]] = {
    "cream": ["Greek yoghurt", "milk with butter", "coconut milk"],
    "eggs": ["flax egg", "mashed banana", "silken tofu"],
    "milk": ["oat milk", "soy milk", "water + butter"],
    "butter": ["olive oil", "margarine", "coconut oil"],
    "cheese": ["nutritional yeast", "feta", "toasted breadcrumbs"],
    "rice": ["quinoa", "couscous", "cauliflower rice"],
    "pasta": ["noodles", "gnocchi", "courgetti"],
    "bread": ["wraps", "pita", "crackers"],
    "flour": ["oat flour", "self-raising flour", "almond flour"],
    "tomatoes": ["tinned tomatoes", "passata", "red pepper"],
    "onion": ["shallots", "spring onion", "onion powder"],
    "garlic": ["garlic powder", "onion powder", "dried herbs"],
    "chicken": ["turkey", "tofu", "chickpeas"],
    "mince": ["lentils", "chopped mushrooms", "plant mince"],
    "beans": ["lentils", "chickpeas", "peas"],
    "lentils": ["beans", "chickpeas", "split peas"],
    "yoghurt": ["Greek yoghurt", "sour cream", "coconut yoghurt"],
    "spinach": ["kale", "chard", "frozen spinach"],
    "herbs": ["mixed dried herbs", "parsley", "basil"],
    "oil": ["butter", "ghee", "coconut oil"],
}


RULE_RECIPES = [
    {
        "title": "Tomato and spinach pasta",
        "base": ["pasta", "tomatoes", "spinach", "cheese"],
        "dietary": ["vegetarian"],
        "method": ["Cook the pasta.", "Simmer tomatoes with herbs.", "Stir through spinach.", "Top with cheese."],
    },
    {
        "title": "Herby bean tomato stew",
        "base": ["beans", "tomatoes", "onion", "garlic", "herbs"],
        "dietary": ["vegetarian", "vegan", "gluten-free"],
        "method": ["Soften onion and garlic.", "Add tomatoes and beans.", "Simmer with herbs.", "Serve hot."],
    },
    {
        "title": "Quick fried rice bowl",
        "base": ["rice", "eggs", "onion", "spinach", "oil"],
        "dietary": [],
        "method": ["Cook rice if needed.", "Fry onion in oil.", "Add eggs and scramble.", "Stir in rice and spinach."],
    },
    {
        "title": "Creamy lentil soup",
        "base": ["lentils", "tomatoes", "onion", "cream", "herbs"],
        "dietary": ["vegetarian"],
        "method": ["Cook onion until soft.", "Add lentils and tomatoes.", "Simmer until tender.", "Finish with cream and herbs."],
    },
]


@router.post("/api/recipes/suggest")
def suggest_recipes(payload: RecipeSuggestRequest):
    if not isinstance(payload.ingredients, list) or not _clean_string_list(payload.ingredients):
        return JSONResponse(status_code=400, content={"error": "ingredients must be a non-empty array of strings", "code": "VALIDATION_ERROR"})

    ingredients = _clean_string_list(payload.ingredients)
    ingredient_set = set(ingredients)
    dietary = set(_clean_string_list(payload.dietary))
    use_first = set(_clean_string_list(payload.useFirst))
    time_limit = payload.timeMinutes or 30
    servings = payload.servings or 2

    ranked: List[Dict[str, Any]] = []
    for template in RULE_RECIPES:
        if dietary and template["dietary"] and any(d not in template["dietary"] for d in dietary):
            continue
        uses = [i for i in template["base"] if i in ingredient_set]
        missing = [i for i in template["base"] if i not in ingredient_set]
        use_first_hits = len([i for i in uses if i in use_first])
        score = len(uses) * 10 + use_first_hits * 15 - len(missing) * 3
        ranked.append({
            "template": template,
            "uses": uses,
            "missing": missing,
            "score": score,
            "use_first_hits": use_first_hits,
        })

    ranked.sort(key=lambda x: (x["score"], x["use_first_hits"]), reverse=True)

    recipes: List[Dict[str, Any]] = []
    for item in ranked[:3]:
        template = item["template"]
        missing = item["missing"]
        recipes.append(
            {
                "title": template["title"],
                "timeMinutes": min(time_limit, 30 if len(missing) > 1 else 20),
                "servings": servings,
                "uses": item["uses"],
                "missing": missing,
                "swaps": [{"missing": m, "swap": ", ".join(SWAPS.get(m, ["Use a similar pantry staple."]))} for m in missing],
                "method": template["method"],
                "whyThisWorks": "Prioritises your available cupboard ingredients with minimal extras.",
                "wasteSavingNote": "Good save: prioritised use-first ingredients." if item["use_first_hits"] else "Balanced plan using common cupboard staples.",
            }
        )

    while len(recipes) < 3:
        recipes.append(
            {
                "title": "Flexible cupboard omelette" if "eggs" in ingredient_set else "Flexible cupboard stir-fry",
                "timeMinutes": min(time_limit, 15),
                "servings": servings,
                "uses": ingredients[:4],
                "missing": [],
                "swaps": [],
                "method": ["Heat a pan.", "Cook your main ingredients.", "Season and serve."],
                "whyThisWorks": "Designed as a fallback when ingredient variety is limited.",
                "wasteSavingNote": "Uses what you already have to reduce waste.",
            }
        )

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    insert into recipe_suggestions (input_ingredients, dietary_filters, use_first, time_minutes, servings, recipes)
                    values (%s, %s, %s, %s, %s, %s::jsonb)
                    """,
                    (ingredients, list(dietary), list(use_first), payload.timeMinutes, payload.servings, __import__("json").dumps(recipes)),
                )
            conn.commit()
    except Exception as exc:
        print(f"recipe_suggestions persistence skipped: {exc}")

    return {"recipes": recipes}


@router.post("/api/shopping-list")
def generate_shopping_list(payload: ShoppingListRequest):
    items = set()
    for recipe in payload.selectedRecipes or []:
        for missing in recipe.get("missing", []) if isinstance(recipe, dict) else []:
            if isinstance(missing, str):
                item = _norm(missing)
                if item:
                    items.add(item)

    deduped = sorted(items)

    try:
        with get_conn() as conn:
            with conn.cursor() as cur:
                titles = [r.get("title", "") for r in payload.selectedRecipes if isinstance(r, dict)]
                cur.execute(
                    "insert into shopping_lists (source_recipe_titles, items) values (%s, %s)",
                    (titles, deduped),
                )
            conn.commit()
    except Exception as exc:
        print(f"shopping_lists persistence skipped: {exc}")

    return {"items": deduped}


@router.post("/api/swaps")
def suggest_swaps(payload: SwapsRequest):
    cleaned = _clean_string_list(payload.missingIngredients)
    swaps = [
        {
            "ingredient": ingredient,
            "options": SWAPS.get(ingredient, ["Use a similar ingredient you already have", "Skip if optional", "Add to shopping list"]),
        }
        for ingredient in cleaned
    ]
    return {"swaps": swaps}


@router.post("/api/food-waste-score")
def food_waste_score(payload: FoodWasteScoreRequest):
    ingredients = set(_clean_string_list(payload.ingredients))
    use_first = set(_clean_string_list(payload.useFirst))

    if not use_first:
        score = 60 if ingredients else 0
    else:
        hits = len(ingredients.intersection(use_first))
        score = int(max(0, min(100, (hits / len(use_first)) * 100)))

    if score >= 80:
        message = "Good save: this plan uses your use-first ingredients before they go off."
    elif score >= 40:
        message = "Decent save: you are using some priority ingredients."
    else:
        message = "Low waste-saving score: try meals that include more use-first ingredients."

    return {"score": score, "message": message}
