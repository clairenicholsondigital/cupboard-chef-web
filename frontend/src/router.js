export function setRouteFromHash(state) {
  const hashRoute = window.location.hash.replace(/^#\/?/, "").split("?")[0];
  if (hashRoute) {
    state.route = hashRoute;
    return;
  }

  const pathnameRouteMap = {
    "/": "dashboard",
    "/dashboard": "dashboard",
    "/ingredients": "ingredients",
    "/ingredients-list": "ingredients",
    "/ingredient-detail": "ingredient-detail",
    "/add-ingredient": "add-ingredient",
    "/log-food": "log-food",
    "/entries": "entries",
    "/cupboard": "cupboard",
    "/add-cupboard-item": "add-cupboard-item",
    "/recipes": "recipes",
    "/add-recipe": "add-recipe",
    "/recipe-detail": "recipe-detail",
    "/shopping-lists": "shopping-lists",
    "/add-shopping-list": "add-shopping-list",
    "/shopping-list-detail": "shopping-list-detail",
    "/login": "login",
    "/profile": "profile",
  };

  state.route = pathnameRouteMap[window.location.pathname] || "dashboard";
}

export function syncSelectedIdsFromHash(state) {
  const hashParams = new URLSearchParams(window.location.hash.split("?")[1] || "");
  state.selectedIngredientId = hashParams.get("id") || "";
  state.selectedRecipeId = hashParams.get("id") || "";
  state.selectedShoppingListId = hashParams.get("id") || "";
}