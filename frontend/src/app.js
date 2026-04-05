import { getCurrentUser } from "./api.js";
import { state } from "./state.js";
import { renderApp } from "./renderers.js";
import { setRouteFromHash, syncSelectedIdsFromHash } from "./router.js";
import { attachEvents } from "./domEvents.js";
import { createLoaders } from "./loaders.js";
import { createActions } from "./actions.js";
import { clearFeedback, isAuthenticated, setFeedback } from "./helpers.js";
import { clearLocalSession, handlePossiblyStaleSession, restoreSessionIfPossible } from "./session.js";

function feedbackSetter(type, message) {
  setFeedback(state, type, message);
}

const loaders = createLoaders({
  state,
  setFeedback: feedbackSetter,
  handlePossiblyStaleSession: (error) => handlePossiblyStaleSession(state, feedbackSetter, error),
});

let actions;

function render() {
  const app = document.querySelector("#app");
  if (!app) return;

  const protectedRoutes = new Set([
    "dashboard",
    "profile",
    "log-food",
    "entries",
    "cupboard",
    "add-cupboard-item",
    "add-ingredient",
    "ingredients",
    "ingredient-detail",
    "recipes",
    "add-recipe",
    "recipe-detail",
    "shopping-lists",
    "add-shopping-list",
    "shopping-list-detail",
  ]);

  if (!isAuthenticated(state) && protectedRoutes.has(state.route)) {
    state.route = "login";
  }

  if (isAuthenticated(state) && state.route === "login") {
    state.route = "dashboard";
  }

  app.innerHTML = renderApp(state);
  attachEvents({ state, render, actions });
}
actions = createActions({
  state,
  render,
  setFeedback: feedbackSetter,
  clearLocalSession: () => clearLocalSession(state),
  handlePossiblyStaleSession: (error) => handlePossiblyStaleSession(state, feedbackSetter, error),
  loaders,
});

async function bootstrap() {
  setRouteFromHash(state);
  syncSelectedIdsFromHash(state);

  await Promise.all([
    loaders.loadHealth(),
    loaders.loadIngredients(),
  ]);

  await restoreSessionIfPossible(state, feedbackSetter, getCurrentUser);

  if (isAuthenticated(state)) {
    await Promise.all([
      loaders.loadFoodEntries(render, false),
      loaders.loadCupboardItems(render, false),
      loaders.loadRecipes(render, false),
      loaders.loadShoppingLists(render, false),
    ]);
  }

  if (state.route === "ingredient-detail") {
    await loaders.loadIngredientById(state.selectedIngredientId, render, false);
  }

  if (state.route === "recipe-detail") {
    await loaders.loadRecipeById(state.selectedRecipeId, render, false);
  }

  if (state.route === "shopping-list-detail") {
    await Promise.all([
      loaders.loadShoppingListDetail(state.selectedShoppingListId, render, false),
      loaders.loadShoppingListItems(state.selectedShoppingListId, render, false),
    ]);
  }

  render();
}

window.addEventListener("hashchange", async () => {
  try {
    setRouteFromHash(state);
    syncSelectedIdsFromHash(state);

    if (state.route === "entries") {
      await loaders.loadFoodEntries(render, false);
    }

    if (state.route === "cupboard") {
      await loaders.loadCupboardItems(render, false);
    }

    if (state.route === "ingredients") {
      await loaders.loadIngredients();
    }

    if (state.route === "ingredient-detail") {
      await loaders.loadIngredientById(state.selectedIngredientId, render, false);
    }

    if (state.route === "recipes") {
      await loaders.loadRecipes(render, false);
    }

    if (state.route === "recipe-detail") {
      await loaders.loadRecipeById(state.selectedRecipeId, render, false);
    }

    if (state.route === "shopping-lists") {
      await loaders.loadShoppingLists(render, false);
    }

    if (state.route === "shopping-list-detail") {
      await Promise.all([
        loaders.loadShoppingListDetail(state.selectedShoppingListId, render, false),
        loaders.loadShoppingListItems(state.selectedShoppingListId, render, false),
      ]);
    }

    clearFeedback(state);
    render();
  } catch (error) {
    feedbackSetter("error", `App navigation failed: ${error.message}`);
    render();
  }
});

bootstrap().catch((error) => {
  const app = document.querySelector("#app");
  if (app) {
    app.innerHTML = `<section class="card error"><h2>App failed to load</h2><p>${String(error?.message || "Unknown error")}</p></section>`;
  }
});