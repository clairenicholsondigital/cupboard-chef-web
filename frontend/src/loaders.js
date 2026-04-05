import {
  ApiError,
  getIngredient,
  getIngredients,
  getRecipe,
  getRecipes,
  getShoppingList,
  getShoppingListItems,
  getUserFoodEntries,
  getUserShoppingLists,
  getUserStorecupboardItems,
  healthCheck,
} from "./api.js";
import { currentUserId } from "./helpers.js";

export function createLoaders({ state, setFeedback, handlePossiblyStaleSession }) {
  async function loadHealth() {
    try {
      state.health = await healthCheck();
    } catch {
      state.health = { status: "unavailable" };
    }
  }

  async function loadFoodEntries(render, renderOnComplete = true) {
    state.error = "";

    if (!currentUserId(state)) {
      state.foodEntries = [];
      if (renderOnComplete) render();
      return;
    }

    try {
      state.foodEntries = await getUserFoodEntries(currentUserId(state));
    } catch (error) {
      state.foodEntries = [];
      if (!handlePossiblyStaleSession(error)) {
        state.error = error instanceof ApiError ? error.message : "Could not load food entries.";
      }
    }

    if (renderOnComplete) render();
  }

  async function loadIngredients() {
    try {
      const ingredientResponse = await getIngredients();
      if (Array.isArray(ingredientResponse)) {
        state.ingredients = ingredientResponse;
      } else {
        state.ingredients = ingredientResponse?.items || [];
      }

      if (!state.cupboardForm.ingredient_id && state.ingredients.length) {
        state.cupboardForm.ingredient_id = state.ingredients[0].id;
      }
    } catch {
      state.ingredients = [];
    }
  }

  async function loadIngredientById(ingredientId, render, renderOnComplete = true) {
    if (!ingredientId) {
      state.selectedIngredient = null;
      state.ingredientDetailForm = null;
      if (renderOnComplete) render();
      return;
    }

    try {
      const ingredient = await getIngredient(ingredientId);
      state.selectedIngredient = ingredient;
      state.ingredientDetailForm = {
        canonical_name: ingredient.canonical_name || "",
        display_name: ingredient.display_name || "",
        category: ingredient.category || "",
        is_seasonal: Boolean(ingredient.is_seasonal),
        seasonal_months: Array.isArray(ingredient.seasonal_months) ? ingredient.seasonal_months.join(",") : "",
      };
    } catch (error) {
      state.selectedIngredient = null;
      state.ingredientDetailForm = null;
      if (!handlePossiblyStaleSession(error)) {
        setFeedback("error", `Could not load ingredient detail: ${error.message}`);
      }
    }

    if (renderOnComplete) render();
  }

  async function loadRecipes(render, renderOnComplete = true) {
    if (!currentUserId(state)) {
      state.recipes = [];
      state.recipesMeta = { total: 0, limit: 25, offset: 0 };
      if (renderOnComplete) render();
      return;
    }

    try {
      const response = await getRecipes();
      state.recipes = Array.isArray(response) ? response : response?.items || [];
      state.recipesMeta = {
        total: Number(response?.total || state.recipes.length),
        limit: Number(response?.limit || 25),
        offset: Number(response?.offset || 0),
      };
    } catch (error) {
      state.recipes = [];
      state.recipesMeta = { total: 0, limit: 25, offset: 0 };
      if (!handlePossiblyStaleSession(error)) {
        setFeedback("error", `Could not load recipes: ${error.message}`);
      }
    }

    if (renderOnComplete) render();
  }

  async function loadRecipeById(recipeId, render, renderOnComplete = true) {
    if (!recipeId) {
      state.selectedRecipe = null;
      state.recipeDetailForm = null;
      if (renderOnComplete) render();
      return;
    }

    try {
      const recipe = await getRecipe(recipeId);
      state.selectedRecipe = recipe;
      state.recipeDetailForm = {
        title: recipe.title || "",
        description: recipe.description || "",
        instructions: recipe.instructions || "",
        source_url: recipe.source_url || "",
        created_by_user_id: recipe.created_by_user_id || "",
        is_system: Boolean(recipe.is_system),
      };
    } catch (error) {
      state.selectedRecipe = null;
      state.recipeDetailForm = null;
      if (!handlePossiblyStaleSession(error)) {
        setFeedback("error", `Could not load recipe detail: ${error.message}`);
      }
    }

    if (renderOnComplete) render();
  }

  async function loadShoppingLists(render, renderOnComplete = true) {
    if (!currentUserId(state)) {
      state.shoppingLists = [];
      if (renderOnComplete) render();
      return;
    }

    try {
      const response = await getUserShoppingLists(currentUserId(state));
      state.shoppingLists = Array.isArray(response) ? response : response?.items || [];
    } catch (error) {
      state.shoppingLists = [];
      if (!handlePossiblyStaleSession(error)) {
        setFeedback("error", `Could not load shopping lists: ${error.message}`);
      }
    }

    if (renderOnComplete) render();
  }

  async function loadShoppingListDetail(shoppingListId, render, renderOnComplete = true) {
    if (!shoppingListId) {
      state.selectedShoppingList = null;
      state.shoppingListDetailForm = null;
      if (renderOnComplete) render();
      return;
    }

    try {
      const list = await getShoppingList(shoppingListId);
      state.selectedShoppingList = list;
      state.shoppingListDetailForm = { name: list.name || "", status: list.status || "active" };
    } catch (error) {
      state.selectedShoppingList = null;
      state.shoppingListDetailForm = null;
      if (!handlePossiblyStaleSession(error)) {
        setFeedback("error", `Could not load shopping list detail: ${error.message}`);
      }
    }

    if (renderOnComplete) render();
  }

  async function loadShoppingListItems(shoppingListId, render, renderOnComplete = true) {
    if (!shoppingListId) {
      state.shoppingListItems = [];
      if (renderOnComplete) render();
      return;
    }

    try {
      const response = await getShoppingListItems(shoppingListId, { sort_by: "sort_order", sort_dir: "asc" });
      state.shoppingListItems = Array.isArray(response) ? response : response?.items || [];
    } catch (error) {
      state.shoppingListItems = [];
      if (!handlePossiblyStaleSession(error)) {
        setFeedback("error", `Could not load shopping list items: ${error.message}`);
      }
    }

    if (renderOnComplete) render();
  }

  async function loadCupboardItems(render, renderOnComplete = true) {
    state.cupboardError = "";
    state.cupboardLoading = true;

    if (!currentUserId(state)) {
      state.cupboardItems = [];
      state.cupboardLoaded = true;
      state.cupboardLoading = false;
      if (renderOnComplete) render();
      return;
    }

    try {
      const response = await getUserStorecupboardItems(currentUserId(state));
      state.cupboardItems = Array.isArray(response) ? response : response?.items || [];
      state.cupboardLoaded = true;
    } catch (error) {
      state.cupboardItems = [];
      state.cupboardLoaded = true;

      if (!handlePossiblyStaleSession(error)) {
        state.cupboardError = `Could not load cupboard items: ${error.message}`;
        setFeedback("error", state.cupboardError);
      }
    }

    state.cupboardLoading = false;

    if (renderOnComplete) render();
  }

  return {
    loadHealth,
    loadFoodEntries,
    loadIngredients,
    loadIngredientById,
    loadRecipes,
    loadRecipeById,
    loadShoppingLists,
    loadShoppingListDetail,
    loadShoppingListItems,
    loadCupboardItems,
  };
}