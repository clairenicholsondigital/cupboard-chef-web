import {
  ApiError,
  createRecipe,
  createIngredient,
  deleteIngredient,
  deleteRecipe,
  createUserFoodEntry,
  createUserStorecupboardItem,
  getIngredient,
  getRecipe,
  getRecipes,
  deleteUserStorecupboardItem,
  getApiBaseUrl,
  getCurrentUser,
  getIngredients,
  getUserFoodEntries,
  getUserStorecupboardItems,
  healthCheck,
  loginWithEmail,
  updateRecipe,
  updateIngredient,
  updateUserStorecupboardItem,
} from "./api.js";

import { handleSubmitLogin, handleLogout } from "./handlers/authHandlers.js";
import { handleSubmitFoodEntry } from "./handlers/foodHandlers.js";
import {
  handleCancelCupboardEdit,
  handleDeleteCupboardItem,
  handleStartCupboardEdit,
  handleSubmitCupboardItem,
  handleSubmitCupboardUpdate,
} from "./handlers/cupboardHandlers.js";
import {
  handleDeleteIngredient,
  handleSubmitIngredient,
  handleSubmitIngredientUpdate,
} from "./handlers/ingredientHandlers.js";
import {
  handleDeleteRecipe,
  handleSubmitRecipe,
  handleSubmitRecipeUpdate,
} from "./handlers/recipeHandlers.js";
import React from "https://esm.sh/react@18.3.1";
import { renderToStaticMarkup } from "https://esm.sh/react-dom@18.3.1/server";
import {
  BookOpen,
  ClipboardList,
  CookingPot,
  Home,
  MoreHorizontal,
  Pencil,
  PlusCircle,
  ScrollText,
  Soup,
  SquarePlus,
  Trash2,
  UtensilsCrossed,
} from "https://esm.sh/lucide-react@0.469.0?deps=react@18.3.1";

const mealTimeOptions = ["am", "breakfast", "lunch", "pm", "dinner", "evening", "snack", "late_night"];
const inputMethodOptions = ["text", "voice", "imported"];
const stockStatusOptions = ["in_stock", "low", "out_of_stock"];
const ROUTE_META = [
  { route: "dashboard", label: "Dashboard", icon: Home },
  { route: "log-food", label: "Log food", icon: UtensilsCrossed },
  { route: "entries", label: "Food entries", icon: ClipboardList },
  { route: "cupboard", label: "Cupboard", icon: CookingPot },
  { route: "add-cupboard-item", label: "Add cupboard item", icon: PlusCircle },
  { route: "add-ingredient", label: "Add ingredient", icon: SquarePlus },
  { route: "ingredients", label: "Ingredients list", icon: Soup },
  { route: "recipes", label: "Recipes", icon: BookOpen },
  { route: "add-recipe", label: "Add recipe", icon: ScrollText },
];
const PRIMARY_TAB_ROUTES = ["dashboard", "ingredients", "cupboard", "recipes"];
const PAGE_META = {
  dashboard: { title: "Dashboard", subtitle: "Track meals, cupboard stock, and recipes in one place." },
  login: { title: "Login", subtitle: "Sign in to access your synced Cupboard Chef data." },
  profile: { title: "Profile", subtitle: "View your current session and API connection status." },
  "log-food": { title: "Log food", subtitle: "Capture what you ate in seconds." },
  entries: { title: "Food entries", subtitle: "Review your recent meal logs." },
  cupboard: { title: "Cupboard", subtitle: "Keep your ingredients and stock levels up to date." },
  "add-cupboard-item": { title: "Add cupboard item", subtitle: "Add an ingredient to your cupboard inventory." },
  "add-ingredient": { title: "Add ingredient", subtitle: "Create a reusable ingredient in your catalog." },
  ingredients: { title: "Ingredients", subtitle: "Browse and edit your ingredient catalog." },
  "ingredient-detail": { title: "Ingredient detail", subtitle: "Update ingredient information." },
  recipes: { title: "Recipes", subtitle: "Browse and manage saved recipes." },
  "add-recipe": { title: "Add recipe", subtitle: "Create a new recipe for your collection." },
  "recipe-detail": { title: "Recipe detail", subtitle: "Edit recipe information and instructions." },
};

// Use multiple keys so the frontend stays compatible with whichever key api.js is reading.
const AUTH_STORAGE_KEYS = [
  "cupboard_chef_access_token",
  "access_token",
  "auth_token",
  "token",
];

const USER_STORAGE_KEYS = {
  userId: "cupboard_chef_user_id",
  email: "cupboard_chef_email",
  displayName: "cupboard_chef_display_name",
};

const defaultFoodForm = () => ({
  description: "",
  raw_input: "",
  input_method: "text",
  meal_time: "",
  rating: "",
});

const defaultCupboardForm = () => ({
  ingredient_id: "",
  quantity: "",
  unit: "",
  stock_status: "in_stock",
  shelf_name: "",
  best_before_date: "",
  next_reminder_at: "",
});

const defaultIngredientForm = () => ({
  canonical_name: "",
  display_name: "",
  category: "veg",
  is_seasonal: false,
  seasonal_months: "",
});

const defaultRecipeForm = () => ({
  title: "",
  description: "",
  instructions: "",
  source_url: "",
  is_system: false,
});

const state = {
  route: "dashboard",
  error: "",
  loading: false,
  currentUser: null,
  authSubject: "",
  foodEntries: [],
  ingredients: [],
  recipes: [],
  recipesMeta: { total: 0, limit: 25, offset: 0 },
  cupboardItems: [],
  cupboardLoading: false,
  cupboardLoaded: false,
  cupboardSubmitting: false,
  cupboardError: "",
  cupboardSuccess: "",
  foodForm: defaultFoodForm(),
  cupboardForm: defaultCupboardForm(),
  ingredientForm: defaultIngredientForm(),
  recipeForm: defaultRecipeForm(),
  ingredientDetailForm: null,
  recipeDetailForm: null,
  selectedIngredientId: "",
  selectedRecipeId: "",
  selectedIngredient: null,
  selectedRecipe: null,
  authForm: {
    email: "",
    password: "",
  },
  cupboardEditingId: "",
  cupboardQuery: "",
  cupboardSort: "shelf",
  feedback: { type: "", message: "" },
  health: null,
};

function safeStorageGet(key) {
  try {
    return localStorage.getItem(key);
  } catch {
    return "";
  }
}

function safeStorageSet(key, value) {
  try {
    localStorage.setItem(key, value);
  } catch {
    // Ignore storage write failures (private mode / blocked storage).
  }
}

function safeStorageRemove(key) {
  try {
    localStorage.removeItem(key);
  } catch {
    // Ignore storage delete failures.
  }
}

function setFeedback(type, message) {
  state.feedback = { type, message };
}

function clearFeedback() {
  state.feedback = { type: "", message: "" };
}

function currentUserId() {
  return state.currentUser?.user_id || "";
}

function getStoredAccessToken() {
  for (const key of AUTH_STORAGE_KEYS) {
    const value = safeStorageGet(key);
    if (value) {
      return value;
    }
  }
  return "";
}

function storeAccessToken(token) {
  for (const key of AUTH_STORAGE_KEYS) {
    safeStorageSet(key, token);
  }
}

function clearStoredAccessToken() {
  for (const key of AUTH_STORAGE_KEYS) {
    safeStorageRemove(key);
  }
}

function storeCurrentUser(user) {
  if (!user) {
    return;
  }

  safeStorageSet(USER_STORAGE_KEYS.userId, user.user_id || "");
  safeStorageSet(USER_STORAGE_KEYS.email, user.email || "");
  safeStorageSet(USER_STORAGE_KEYS.displayName, user.display_name || "");
}

function clearStoredCurrentUser() {
  safeStorageRemove(USER_STORAGE_KEYS.userId);
  safeStorageRemove(USER_STORAGE_KEYS.email);
  safeStorageRemove(USER_STORAGE_KEYS.displayName);
}

function clearLocalSession() {
  state.currentUser = null;
  state.authSubject = "";
  state.foodEntries = [];
  state.recipes = [];
  state.recipesMeta = { total: 0, limit: 25, offset: 0 };
  state.cupboardItems = [];
  state.cupboardLoaded = false;
  state.cupboardLoading = false;
  state.cupboardSubmitting = false;
  state.cupboardError = "";
  state.cupboardSuccess = "";
  state.cupboardEditingId = "";
  state.selectedRecipeId = "";
  state.selectedRecipe = null;
  state.recipeDetailForm = null;
  clearStoredAccessToken();
  clearStoredCurrentUser();
}

function isAuthError(error) {
  const message = error instanceof ApiError || error instanceof Error ? error.message : String(error || "");
  const normalized = message.toLowerCase();

  return (
    normalized.includes("invalid authentication token") ||
    normalized.includes("authentication token has expired") ||
    normalized.includes("unauthorized") ||
    normalized.includes("authenticated user was not found")
  );
}

function handlePossiblyStaleSession(error) {
  if (!isAuthError(error)) {
    return false;
  }

  clearLocalSession();
  setFeedback("error", "Your session expired or the saved token is no longer valid. Please sign in again.");
  return true;
}

function ensureAuthenticated(actionLabel) {
  if (currentUserId()) {
    return true;
  }

  setFeedback("error", `Please sign in before ${actionLabel}.`);
  render();
  return false;
}

function getLoginErrorMessage(error) {
  if (error instanceof ApiError) {
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Unable to sign in.";
}

function setRouteFromHash() {
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
    "/login": "login",
    "/profile": "profile",
  };

  state.route = pathnameRouteMap[window.location.pathname] || "dashboard";
}

function isAuthenticated() {
  return Boolean(currentUserId());
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function formatDateForDateInput(value) {
  if (!value) {
    return "";
  }
  const datePart = String(value).split("T")[0].split(" ")[0];
  return /^\d{4}-\d{2}-\d{2}$/.test(datePart) ? datePart : "";
}

function formatDateTimeForInput(value) {
  if (!value) {
    return "";
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return "";
  }
  const year = parsed.getFullYear();
  const month = String(parsed.getMonth() + 1).padStart(2, "0");
  const day = String(parsed.getDate()).padStart(2, "0");
  const hours = String(parsed.getHours()).padStart(2, "0");
  const minutes = String(parsed.getMinutes()).padStart(2, "0");
  return `${year}-${month}-${day}T${hours}:${minutes}`;
}

function formatFriendlyDate(value) {
  if (!value) return "Not set";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return String(value);
  return parsed.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
}

function formatFriendlyDateTime(value) {
  if (!value) return "Not set";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return String(value);
  return parsed.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function formatStockLabel(value) {
  return String(value || "unknown").replaceAll("_", " ");
}

function stockStatusClass(value) {
  const normalized = String(value || "").toLowerCase();
  if (normalized === "in_stock") return "status-in-stock";
  if (normalized === "low") return "status-low";
  if (normalized === "out_of_stock") return "status-out-of-stock";
  return "status-unknown";
}

function isExpiringSoon(value) {
  if (!value) return false;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return false;
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  date.setHours(0, 0, 0, 0);
  const diffDays = Math.ceil((date - now) / (1000 * 60 * 60 * 24));
  return diffDays >= 0 && diffDays <= 3;
}

function getCupboardVisibleItems() {
  const query = state.cupboardQuery.trim().toLowerCase();
  const normalizedItems = [...state.cupboardItems];

  const filtered = query
    ? normalizedItems.filter((item) => {
      const name = item.ingredient_display_name || item.ingredient_canonical_name || item.ingredient_id || "";
      const shelf = item.shelf_name || "";
      return String(name).toLowerCase().includes(query) || String(shelf).toLowerCase().includes(query);
    })
    : normalizedItems;

  const alphabetical = (a, b) => {
    const aName = String(a.ingredient_display_name || a.ingredient_canonical_name || a.ingredient_id || "").toLowerCase();
    const bName = String(b.ingredient_display_name || b.ingredient_canonical_name || b.ingredient_id || "").toLowerCase();
    return aName.localeCompare(bName);
  };

  if (state.cupboardSort === "expiry") {
    return filtered.sort((a, b) => {
      const aDate = a.best_before_date ? new Date(a.best_before_date).getTime() : Number.POSITIVE_INFINITY;
      const bDate = b.best_before_date ? new Date(b.best_before_date).getTime() : Number.POSITIVE_INFINITY;
      if (aDate !== bDate) return aDate - bDate;
      return alphabetical(a, b);
    });
  }

  if (state.cupboardSort === "name") {
    return filtered.sort(alphabetical);
  }

  return filtered.sort((a, b) => {
    const aShelf = String(a.shelf_name || "zzzz").toLowerCase();
    const bShelf = String(b.shelf_name || "zzzz").toLowerCase();
    if (aShelf !== bShelf) return aShelf.localeCompare(bShelf);
    return alphabetical(a, b);
  });
}

function renderLayout(content) {
  const app = document.querySelector("#app");
  const authenticated = isAuthenticated();
  const activePage = PAGE_META[state.route] || { title: "Cupboard Chef", subtitle: "" };
  const primaryTabs = ROUTE_META.filter((item) => PRIMARY_TAB_ROUTES.includes(item.route));
  app.innerHTML = `
    <div class="app-shell app-mobile-shell">
      <header class="app-bar">
        <p class="app-badge">Cupboard Chef</p>
        <div class="app-bar-row">
          <h1>${escapeHtml(activePage.title)}</h1>
          ${authenticated ? `
            <div class="actions actions-compact">
              <a class="button button-ghost ${state.route === "profile" ? "active" : ""}" href="#/profile">Account</a>
              <button id="logout" type="button" class="button button-ghost">Log out</button>
            </div>
          ` : ""}
        </div>
        ${activePage.subtitle ? `<p class="app-subtitle">${escapeHtml(activePage.subtitle)}</p>` : ""}
      </header>
      <main class="screen-content">${content}</main>
      ${authenticated ? `
        <nav class="bottom-tabs" aria-label="Bottom navigation tabs">
          ${primaryTabs.map((item) => navLink(item.route, item.label, item.icon, "tab")).join("")}
        </nav>
      ` : ""}
    </div>
  `;

  document.querySelector("#logout")?.addEventListener("click", onLogout);
}

function navLink(route, label, Icon, style = "pill") {
  const active = state.route === route ? "active" : "";
  const iconSize = style === "tab" ? 18 : 16;
  const icon = renderToStaticMarkup(React.createElement(Icon, { size: iconSize, strokeWidth: 2 }));
  return `<a class="${style} ${active}" href="#/${route}" aria-label="${escapeHtml(label)}">${icon}<span>${label}</span></a>`;
}

function card(title, body, className = "") {
  return `<article class="card ${className}"><h2>${title}</h2>${body}</article>`;
}

function renderDashboard() {
  const preview = state.foodEntries.slice(0, 3);
  const previewHtml = preview.length
    ? `<ul class="list">${preview
      .map((entry) => `<li><strong>${escapeHtml(entry.description)}</strong> <span class="meta">${escapeHtml(entry.meal_time || "meal unspecific")}</span></li>`)
      .join("")}</ul>`
    : "<p class='empty'>No entries yet. Start by logging your first meal.</p>";

  return `
    ${card("Quick actions", `
      <p class="meta">Move quickly between common tasks.</p>
      <div class="actions">
        <a class="button button-primary" href="#/log-food">Log food</a>
        <a class="button button-secondary" href="#/add-cupboard-item">Add cupboard item</a>
        <a class="button button-secondary" href="#/add-ingredient">Add ingredient</a>
        <a class="button button-secondary" href="#/add-recipe">Add recipe</a>
      </div>
    `, "card-soft")}
    ${card("Recent food entries", previewHtml, "card-soft")}
  `;
}

function renderLogin() {
  return card("Sign in", `
    <p class="meta">Sign in to manage cupboard items, ingredients, meal logs, and recipes.</p>
    <form id="login-form" class="form-grid">
      <label>Email address
        <input name="email" type="email" value="${escapeHtml(state.authForm.email)}" autocomplete="email" required />
      </label>
      <label>Password
        <input name="password" type="password" value="${escapeHtml(state.authForm.password)}" autocomplete="current-password" required />
      </label>
      <button type="submit" class="button button-primary button-block">${state.loading && !currentUserId() ? "Signing in..." : "Sign in"}</button>
    </form>
  `, "card-soft");
}

function renderProfile() {
  return card("Account", `
    <p class="meta">Signed in as <strong>${escapeHtml(state.currentUser?.email || "Not signed in")}</strong></p>
    <p class="meta">Display name: <code>${escapeHtml(state.currentUser?.display_name || "Not set")}</code></p>
    <p class="meta">User ID: <code>${escapeHtml(state.currentUser?.user_id || "Not signed in")}</code></p>
    <p class="meta">API base URL: <code>${escapeHtml(getApiBaseUrl())}</code></p>
    ${state.health ? `<p class="${state.health.status === "ok" ? "success" : "error"}">API health: ${escapeHtml(state.health.status)}</p>` : ""}
    <div class="actions">
      <button id="logout-inline" type="button" class="button button-secondary button-block">Log out</button>
    </div>
  `, "card-soft");
}

function renderFoodForm() {
  return card("Log food", `
    <form id="food-form" class="form-grid">
      <label>Description *
        <input name="description" value="${escapeHtml(state.foodForm.description)}" required minlength="1" />
      </label>
      <label>Raw input (optional)
        <textarea name="raw_input" rows="3">${escapeHtml(state.foodForm.raw_input)}</textarea>
      </label>
      <label>Input method
        <select name="input_method">
          ${inputMethodOptions.map((value) => `<option value="${value}" ${state.foodForm.input_method === value ? "selected" : ""}>${value}</option>`).join("")}
        </select>
      </label>
      <label>Meal time
        <select name="meal_time">
          <option value="">(optional)</option>
          ${mealTimeOptions.map((value) => `<option value="${value}" ${state.foodForm.meal_time === value ? "selected" : ""}>${value}</option>`).join("")}
        </select>
      </label>
      <label>Rating (1-5)
        <input name="rating" type="number" min="1" max="5" value="${escapeHtml(state.foodForm.rating)}" />
      </label>
      <button type="submit" class="button button-primary button-block">${state.loading ? "Saving..." : "Save food entry"}</button>
    </form>
  `, "card-soft");
}

function renderEntries() {
  if (state.loading) {
    return card("Food entries", "<p>Loading entries...</p>");
  }

  if (state.error) {
    return card("Food entries", `<p class="error">${escapeHtml(state.error)}</p>`);
  }

  if (!state.foodEntries.length) {
    return card("Food entries", "<p class='empty'>No food entries found for this user yet.</p>");
  }

  return card("Food entries", `
    <ul class="list list-polished">
      ${state.foodEntries
        .map((entry) => `
          <li>
            <div><strong>${escapeHtml(entry.description)}</strong></div>
            <div class="meta">Meal: ${escapeHtml(entry.meal_time || "n/a")} · Input: ${escapeHtml(entry.input_method || "n/a")} · Rating: ${entry.rating ?? "n/a"}</div>
          </li>
        `)
        .join("")}
    </ul>
  `, "card-soft");
}

function renderCupboardRows() {
  const visibleItems = getCupboardVisibleItems();

  if (state.cupboardLoading) {
    return "<p>Loading cupboard items...</p>";
  }

  if (state.cupboardError) {
    return `<p class="error">${escapeHtml(state.cupboardError)}</p>`;
  }

  if (!state.cupboardLoaded) {
    return "<p class='meta'>Load your cupboard to view items.</p>";
  }

  if (!state.cupboardItems.length) {
    return "<p class='empty'>No cupboard items yet. Add one to get started.</p>";
  }

  if (!visibleItems.length) {
    return "<p class='empty'>No ingredients match your search.</p>";
  }

  const moreIcon = renderToStaticMarkup(React.createElement(MoreHorizontal, { size: 18, strokeWidth: 2 }));
  const editIcon = renderToStaticMarkup(React.createElement(Pencil, { size: 16, strokeWidth: 2 }));
  const deleteIcon = renderToStaticMarkup(React.createElement(Trash2, { size: 16, strokeWidth: 2 }));

  return `<ul class="list list-polished cupboard-compact-list">${visibleItems.map((item) => {
    const isEditing = state.cupboardEditingId === item.id;
    if (isEditing) {
      return `
        <li class="cupboard-row-editing">
          <form class="form-grid cupboard-update-form" data-item-id="${item.id}">
            <label>Quantity
              <input name="quantity" type="number" step="0.01" value="${escapeHtml(item.quantity ?? "")}" />
            </label>
            <label>Unit
              <input name="unit" value="${escapeHtml(item.unit || "")}" />
            </label>
            <label>Stock status
              <select name="stock_status">
                ${stockStatusOptions.map((status) => `<option value="${status}" ${item.stock_status === status ? "selected" : ""}>${status}</option>`).join("")}
              </select>
            </label>
            <label>Shelf name
              <input name="shelf_name" value="${escapeHtml(item.shelf_name || "")}" />
            </label>
            <label>Best before
              <input name="best_before_date" type="date" value="${escapeHtml(formatDateForDateInput(item.best_before_date))}" />
            </label>
            <label>Next reminder
              <input name="next_reminder_at" type="datetime-local" value="${escapeHtml(formatDateTimeForInput(item.next_reminder_at))}" />
            </label>
            <div class="actions">
              <button type="submit" class="button button-primary">Save update</button>
              <button type="button" class="button button-secondary cupboard-cancel-edit">Cancel</button>
            </div>
          </form>
        </li>
      `;
    }

    return `
      <li class="cupboard-item-row">
        <div class="cupboard-row-main">
          <div class="cupboard-row-topline">
            <strong class="cupboard-item-name">${escapeHtml(item.ingredient_display_name || item.ingredient_canonical_name || item.ingredient_id)}</strong>
            <span class="chip chip-stock ${stockStatusClass(item.stock_status)}">${escapeHtml(formatStockLabel(item.stock_status || "n/a"))}</span>
          </div>
          <p class="meta cupboard-inline-meta">${escapeHtml(item.quantity ?? "n/a")} ${escapeHtml(item.unit || "")} • ${escapeHtml(item.shelf_name || "No shelf")}</p>
          <p class="meta cupboard-inline-meta">${item.best_before_date ? `Best before ${escapeHtml(formatFriendlyDate(item.best_before_date))}` : "No best before date"} ${isExpiringSoon(item.best_before_date) ? '<span class="chip chip-warning">Expiring soon</span>' : ""}</p>
        </div>
        <div class="cupboard-row-actions">
          <details class="row-menu">
            <summary class="row-menu-trigger" aria-label="Open actions for ${escapeHtml(item.ingredient_display_name || item.ingredient_canonical_name || item.ingredient_id)}">
              ${moreIcon}
            </summary>
            <div class="row-menu-panel">
              <button type="button" class="button button-secondary cupboard-edit" data-item-id="${item.id}">${editIcon}<span>Edit</span></button>
              <button type="button" class="button button-danger-outline cupboard-delete" data-item-id="${item.id}">${deleteIcon}<span>Delete</span></button>
            </div>
          </details>
        </div>
      </li>
    `;
  }).join("")}</ul>`;
}

function renderCupboard() {
  return card("Cupboard", `
    <div class="cupboard-toolbar">
      <input id="cupboard-search" type="search" placeholder="Search ingredient or shelf" value="${escapeHtml(state.cupboardQuery)}" aria-label="Search cupboard items" />
      <select id="cupboard-sort" aria-label="Sort cupboard items">
        <option value="shelf" ${state.cupboardSort === "shelf" ? "selected" : ""}>Sort: Shelf</option>
        <option value="expiry" ${state.cupboardSort === "expiry" ? "selected" : ""}>Sort: Expiry</option>
        <option value="name" ${state.cupboardSort === "name" ? "selected" : ""}>Sort: Name</option>
      </select>
      <a class="button button-primary cupboard-add-button" href="#/add-cupboard-item">Add</a>
    </div>
    ${state.cupboardSuccess ? `<p class="success">${escapeHtml(state.cupboardSuccess)}</p>` : ""}
    ${renderCupboardRows()}
  `, "card-soft");
}

function renderAddCupboardItem() {
  const hasIngredients = state.ingredients.length > 0;
  const ingredientOptions = state.ingredients.length
    ? state.ingredients
      .map((ingredient) => `<option value="${ingredient.id}" ${state.cupboardForm.ingredient_id === ingredient.id ? "selected" : ""}>${escapeHtml(ingredient.display_name)}</option>`)
      .join("")
    : "<option value=''>No ingredients loaded</option>";

  return card("Add cupboard item", `
    <p class="meta">Create a cupboard entry linked to one ingredient.</p>
    ${state.cupboardSuccess ? `<p class="success">${escapeHtml(state.cupboardSuccess)}</p>` : ""}
    ${state.cupboardError ? `<p class="error">${escapeHtml(state.cupboardError)}</p>` : ""}
    <form id="cupboard-form" class="form-grid">
      <label>Ingredient
        <select name="ingredient_id" required ${hasIngredients ? "" : "disabled"}>${ingredientOptions}</select>
      </label>
      <label>Quantity
        <input name="quantity" type="number" step="0.01" value="${escapeHtml(state.cupboardForm.quantity)}" />
      </label>
      <label>Unit
        <input name="unit" value="${escapeHtml(state.cupboardForm.unit)}" placeholder="e.g. g, ml, tin" />
      </label>
      <label>Stock status
        <select name="stock_status">
          ${stockStatusOptions.map((value) => `<option value="${value}" ${state.cupboardForm.stock_status === value ? "selected" : ""}>${value}</option>`).join("")}
        </select>
      </label>
      <label>Shelf name
        <input name="shelf_name" value="${escapeHtml(state.cupboardForm.shelf_name)}" placeholder="e.g. Pantry" />
      </label>
      <label>Best before
        <input name="best_before_date" type="date" value="${escapeHtml(state.cupboardForm.best_before_date)}" />
      </label>
      <label>Next reminder
        <input name="next_reminder_at" type="datetime-local" value="${escapeHtml(state.cupboardForm.next_reminder_at)}" />
      </label>
      <button type="submit" class="button button-primary button-block" ${hasIngredients && !state.cupboardSubmitting ? "" : "disabled"}>${state.cupboardSubmitting ? "Adding..." : "Add cupboard item"}</button>
    </form>
  `, "card-soft");
}

function renderAddIngredient() {
  return card("Add ingredient", `
    <p class="meta">Create a new ingredient in the shared ingredient catalog.</p>
    <form id="ingredient-form" class="form-grid">
      <label>Canonical name *
        <input name="canonical_name" value="${escapeHtml(state.ingredientForm.canonical_name)}" required placeholder="e.g. broccoli" />
      </label>
      <label>Display name *
        <input name="display_name" value="${escapeHtml(state.ingredientForm.display_name)}" required placeholder="e.g. Broccoli" />
      </label>
      <label>Category *
        <input name="category" value="${escapeHtml(state.ingredientForm.category)}" required placeholder="e.g. veg" />
      </label>
      <label class="inline-checkbox">
        <input name="is_seasonal" type="checkbox" ${state.ingredientForm.is_seasonal ? "checked" : ""} />
        Is seasonal
      </label>
      <label>Seasonal months
        <input
          name="seasonal_months"
          value="${escapeHtml(state.ingredientForm.seasonal_months)}"
          placeholder="comma-separated months, e.g. 6,7,8,9"
        />
      </label>
      <button type="submit" class="button button-primary button-block">${state.loading ? "Creating..." : "Create ingredient"}</button>
    </form>
  `, "card-soft");
}

function toIngredientDetailRoute(ingredientId) {
  return `#/ingredient-detail?id=${encodeURIComponent(ingredientId)}`;
}

function renderIngredientsList() {
  if (state.loading && !state.ingredients.length) {
    return card("Ingredients list", "<p>Loading ingredients...</p>");
  }

  if (!state.ingredients.length) {
    return card("Ingredients list", `
      <p class="empty">No ingredients found.</p>
      <div class="actions">
        <a class="button button-primary" href="#/add-ingredient">Add ingredient</a>
      </div>
    `);
  }

  return card("Ingredients list", `
    <p class="meta">View all ingredients and open one to edit details.</p>
    <ul class="list list-polished">
      ${state.ingredients.map((ingredient) => `
        <li>
          <div><strong>${escapeHtml(ingredient.display_name)}</strong></div>
          <div class="meta">${escapeHtml(ingredient.canonical_name)} · Category: ${escapeHtml(ingredient.category || "uncategorized")}</div>
          <div class="actions">
            <a class="button button-secondary" href="${toIngredientDetailRoute(ingredient.id)}">View details</a>
          </div>
        </li>
      `).join("")}
    </ul>
  `, "card-soft");
}

function renderIngredientDetail() {
  if (!state.selectedIngredientId) {
    return card("Ingredient detail", "<p class='empty'>No ingredient selected.</p>");
  }

  if (!state.selectedIngredient || !state.ingredientDetailForm) {
    return card("Ingredient detail", "<p>Loading ingredient details...</p>");
  }

  return card("Ingredient detail", `
    <p class="meta">Edit or delete this ingredient.</p>
    <form id="ingredient-detail-form" class="form-grid">
      <label>Canonical name *
        <input name="canonical_name" value="${escapeHtml(state.ingredientDetailForm.canonical_name)}" required />
      </label>
      <label>Display name *
        <input name="display_name" value="${escapeHtml(state.ingredientDetailForm.display_name)}" required />
      </label>
      <label>Category *
        <input name="category" value="${escapeHtml(state.ingredientDetailForm.category)}" required />
      </label>
      <label class="inline-checkbox">
        <input name="is_seasonal" type="checkbox" ${state.ingredientDetailForm.is_seasonal ? "checked" : ""} />
        Is seasonal
      </label>
      <label>Seasonal months
        <input name="seasonal_months" value="${escapeHtml(state.ingredientDetailForm.seasonal_months)}" placeholder="comma-separated months, e.g. 6,7,8,9" />
      </label>
      <div class="actions">
        <button type="submit" class="button button-primary">${state.loading ? "Saving..." : "Save changes"}</button>
        <button type="button" id="delete-ingredient" class="button button-danger" ${state.loading ? "disabled" : ""}>Delete ingredient</button>
      </div>
    </form>
  `, "card-soft");
}

function toRecipeDetailRoute(recipeId) {
  return `#/recipe-detail?id=${encodeURIComponent(recipeId)}`;
}

function renderRecipesList() {
  if (state.loading && !state.recipes.length) {
    return card("Recipes", "<p>Loading recipes...</p>");
  }

  if (!state.recipes.length) {
    return card("Recipes", `
      <p class="empty">No recipes found.</p>
      <div class="actions">
        <a class="button button-primary" href="#/add-recipe">Add recipe</a>
      </div>
    `);
  }

  return card("Recipes", `
    <p class="meta">Browse, view, and edit recipes.</p>
    <p class="meta">Total recipes: ${state.recipesMeta.total}</p>
    <ul class="list list-polished">
      ${state.recipes.map((recipe) => `
        <li>
          <div><strong>${escapeHtml(recipe.title)}</strong></div>
          <div class="meta">${escapeHtml(recipe.description || "No description")}</div>
          <div class="actions">
            <a class="button button-secondary" href="${toRecipeDetailRoute(recipe.id)}">View details</a>
          </div>
        </li>
      `).join("")}
    </ul>
  `, "card-soft");
}

function renderAddRecipe() {
  return card("Add recipe", `
    <p class="meta">Create a recipe in the recipe catalogue.</p>
    <form id="recipe-form" class="form-grid">
      <label>Title *
        <input name="title" value="${escapeHtml(state.recipeForm.title)}" required minlength="1" />
      </label>
      <label>Description
        <textarea name="description" rows="3">${escapeHtml(state.recipeForm.description)}</textarea>
      </label>
      <label>Instructions
        <textarea name="instructions" rows="6">${escapeHtml(state.recipeForm.instructions)}</textarea>
      </label>
      <label>Source URL
        <input name="source_url" type="url" value="${escapeHtml(state.recipeForm.source_url)}" placeholder="https://example.com/recipe" />
      </label>
      <label class="inline-checkbox">
        <input name="is_system" type="checkbox" ${state.recipeForm.is_system ? "checked" : ""} />
        System recipe
      </label>
      <button type="submit" class="button button-primary button-block">${state.loading ? "Creating..." : "Create recipe"}</button>
    </form>
  `, "card-soft");
}

function renderRecipeDetail() {
  if (!state.selectedRecipeId) {
    return card("Recipe detail", "<p class='empty'>No recipe selected.</p>");
  }

  if (!state.selectedRecipe || !state.recipeDetailForm) {
    return card("Recipe detail", "<p>Loading recipe details...</p>");
  }

  return card("Recipe detail", `
    <p class="meta">Edit or delete this recipe.</p>
    <form id="recipe-detail-form" class="form-grid">
      <label>Title *
        <input name="title" value="${escapeHtml(state.recipeDetailForm.title)}" required minlength="1" />
      </label>
      <label>Description
        <textarea name="description" rows="3">${escapeHtml(state.recipeDetailForm.description)}</textarea>
      </label>
      <label>Instructions
        <textarea name="instructions" rows="6">${escapeHtml(state.recipeDetailForm.instructions)}</textarea>
      </label>
      <label>Source URL
        <input name="source_url" type="url" value="${escapeHtml(state.recipeDetailForm.source_url)}" placeholder="https://example.com/recipe" />
      </label>
      <label>Created by user UUID (optional)
        <input name="created_by_user_id" value="${escapeHtml(state.recipeDetailForm.created_by_user_id)}" placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" />
      </label>
      <label class="inline-checkbox">
        <input name="is_system" type="checkbox" ${state.recipeDetailForm.is_system ? "checked" : ""} />
        System recipe
      </label>
      <div class="actions">
        <button type="submit" class="button button-primary">${state.loading ? "Saving..." : "Save changes"}</button>
        <button type="button" id="delete-recipe" class="button button-danger" ${state.loading ? "disabled" : ""}>Delete recipe</button>
      </div>
    </form>
  `, "card-soft");
}

function attachEvents() {
  const loginForm = document.querySelector("#login-form");
  if (loginForm) {
    loginForm.addEventListener("submit", onSubmitLogin);
  }

  const foodForm = document.querySelector("#food-form");
  if (foodForm) {
    foodForm.addEventListener("submit", onSubmitFoodEntry);
  }

  const cupboardForm = document.querySelector("#cupboard-form");
  if (cupboardForm) {
    cupboardForm.addEventListener("submit", onSubmitCupboardItem);
  }

  const ingredientForm = document.querySelector("#ingredient-form");
  if (ingredientForm) {
    ingredientForm.addEventListener("submit", onSubmitIngredient);
  }

  const ingredientDetailForm = document.querySelector("#ingredient-detail-form");
  if (ingredientDetailForm) {
    ingredientDetailForm.addEventListener("submit", onSubmitIngredientUpdate);
  }

  const recipeForm = document.querySelector("#recipe-form");
  if (recipeForm) {
    recipeForm.addEventListener("submit", onSubmitRecipe);
  }

  const recipeDetailForm = document.querySelector("#recipe-detail-form");
  if (recipeDetailForm) {
    recipeDetailForm.addEventListener("submit", onSubmitRecipeUpdate);
  }

  document.querySelector("#delete-ingredient")?.addEventListener("click", onDeleteIngredient);
  document.querySelector("#delete-recipe")?.addEventListener("click", onDeleteRecipe);

  document.querySelectorAll(".cupboard-edit").forEach((button) => {
    button.addEventListener("click", (event) => {
      onStartCupboardEdit(event);
    });
  });

  document.querySelectorAll(".cupboard-cancel-edit").forEach((button) => {
    button.addEventListener("click", () => {
      onCancelCupboardEdit();
    });
  });

  document.querySelectorAll(".cupboard-update-form").forEach((form) => {
    form.addEventListener("submit", onSubmitCupboardUpdate);
  });

  document.querySelectorAll(".cupboard-delete").forEach((button) => {
    button.addEventListener("click", onDeleteCupboardItem);
  });

  const cupboardSearch = document.querySelector("#cupboard-search");
  if (cupboardSearch) {
    cupboardSearch.addEventListener("input", (event) => {
      state.cupboardQuery = event.target.value;
      render();
    });
  }

  const cupboardSort = document.querySelector("#cupboard-sort");
  if (cupboardSort) {
    cupboardSort.addEventListener("change", (event) => {
      state.cupboardSort = event.target.value;
      render();
    });
  }

  document.querySelector("#logout-inline")?.addEventListener("click", onLogout);
}

async function onSubmitLogin(event) {
  await handleSubmitLogin(event, {
    state,
    render,
    setFeedback,
    clearStoredAccessToken,
    clearLocalSession,
    getLoginErrorMessage,
    loginWithEmail,
    storeAccessToken,
    getCurrentUser,
    storeCurrentUser,
    loadFoodEntries,
    loadCupboardItems,
    loadRecipes,
  });
}

async function onSubmitFoodEntry(event) {
  await handleSubmitFoodEntry(event, {
    state,
    render,
    setFeedback,
    ensureAuthenticated,
    currentUserId,
    createUserFoodEntry,
    defaultFoodForm,
    loadFoodEntries,
    handlePossiblyStaleSession,
  });
}

async function onSubmitCupboardItem(event) {
  await handleSubmitCupboardItem(event, {
    state,
    render,
    setFeedback,
    ensureAuthenticated,
    currentUserId,
    createUserStorecupboardItem,
    defaultCupboardForm,
    loadCupboardItems,
    handlePossiblyStaleSession,
  });
}

async function onSubmitCupboardUpdate(event) {
  await handleSubmitCupboardUpdate(event, {
    state,
    render,
    setFeedback,
    ensureAuthenticated,
    currentUserId,
    updateUserStorecupboardItem,
    loadCupboardItems,
    handlePossiblyStaleSession,
  });
}

async function onDeleteCupboardItem(event) {
  await handleDeleteCupboardItem(event, {
    state,
    render,
    setFeedback,
    ensureAuthenticated,
    currentUserId,
    deleteUserStorecupboardItem,
    loadCupboardItems,
    handlePossiblyStaleSession,
  });
}

async function onSubmitIngredient(event) {
  await handleSubmitIngredient(event, {
    state,
    render,
    setFeedback,
    ensureAuthenticated,
    createIngredient,
    defaultIngredientForm,
    loadIngredients,
    handlePossiblyStaleSession,
  });
}

async function onSubmitIngredientUpdate(event) {
  await handleSubmitIngredientUpdate(event, {
    state,
    render,
    setFeedback,
    ensureAuthenticated,
    updateIngredient,
    loadIngredientById,
    handlePossiblyStaleSession,
  });
}

async function onDeleteIngredient(event) {
  await handleDeleteIngredient(event, {
    state,
    render,
    setFeedback,
    ensureAuthenticated,
    deleteIngredient,
    loadIngredients,
    handlePossiblyStaleSession,
  });
}

async function onSubmitRecipe(event) {
  await handleSubmitRecipe(event, {
    state,
    render,
    setFeedback,
    ensureAuthenticated,
    currentUserId,
    createRecipe,
    defaultRecipeForm,
    loadRecipes,
    handlePossiblyStaleSession,
  });
}

async function onSubmitRecipeUpdate(event) {
  await handleSubmitRecipeUpdate(event, {
    state,
    render,
    setFeedback,
    ensureAuthenticated,
    updateRecipe,
    loadRecipeById,
    handlePossiblyStaleSession,
  });
}

async function onDeleteRecipe(event) {
  await handleDeleteRecipe(event, {
    state,
    render,
    setFeedback,
    ensureAuthenticated,
    deleteRecipe,
    loadRecipes,
    handlePossiblyStaleSession,
  });
}

function onLogout() {
  handleLogout({ clearLocalSession, setFeedback, render });
}

function onStartCupboardEdit(event) {
  handleStartCupboardEdit(event, { state, render });
}

function onCancelCupboardEdit() {
  handleCancelCupboardEdit({ state, render });
}

async function loadHealth() {
  try {
    state.health = await healthCheck();
  } catch {
    state.health = { status: "unavailable" };
  }
}

async function loadFoodEntries(renderOnComplete = true) {
  state.error = "";

  if (!currentUserId()) {
    state.foodEntries = [];
    if (renderOnComplete) {
      render();
    }
    return;
  }

  try {
    state.foodEntries = await getUserFoodEntries(currentUserId());
  } catch (error) {
    state.foodEntries = [];
    if (!handlePossiblyStaleSession(error)) {
      state.error = error instanceof ApiError ? error.message : "Could not load food entries.";
    }
  }

  if (renderOnComplete) {
    render();
  }
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

async function loadIngredientById(ingredientId, renderOnComplete = true) {
  if (!ingredientId) {
    state.selectedIngredient = null;
    state.ingredientDetailForm = null;
    if (renderOnComplete) {
      render();
    }
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

  if (renderOnComplete) {
    render();
  }
}

async function loadRecipes(renderOnComplete = true) {
  if (!currentUserId()) {
    state.recipes = [];
    state.recipesMeta = { total: 0, limit: 25, offset: 0 };
    if (renderOnComplete) {
      render();
    }
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

  if (renderOnComplete) {
    render();
  }
}

async function loadRecipeById(recipeId, renderOnComplete = true) {
  if (!recipeId) {
    state.selectedRecipe = null;
    state.recipeDetailForm = null;
    if (renderOnComplete) {
      render();
    }
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

  if (renderOnComplete) {
    render();
  }
}

async function loadCupboardItems(renderOnComplete = true) {
  state.cupboardError = "";
  state.cupboardLoading = true;

  if (!currentUserId()) {
    state.cupboardItems = [];
    state.cupboardLoaded = true;
    state.cupboardLoading = false;
    if (renderOnComplete) {
      render();
    }
    return;
  }

  try {
    const response = await getUserStorecupboardItems(currentUserId());
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

  if (renderOnComplete) {
    render();
  }
}

async function restoreSessionIfPossible() {
  const token = getStoredAccessToken();
  if (!token) {
    return;
  }

  try {
    const identity = await getCurrentUser();
    state.authSubject = identity.email || identity.user_id || "";
    state.currentUser = {
      user_id: identity.user_id,
      email: identity.email,
      display_name: identity.display_name,
    };
    storeCurrentUser(state.currentUser);
  } catch (error) {
    clearLocalSession();
    if (!isAuthError(error)) {
      setFeedback("error", "Could not restore your session.");
    }
  }
}

function render() {
  if (!isAuthenticated()) {
    state.route = "login";
  }

  if (isAuthenticated() && state.route === "login") {
    state.route = "dashboard";
  }

  let content = "";

  if (state.route === "dashboard") content = renderDashboard();
  if (state.route === "login") content = renderLogin();
  if (state.route === "profile") content = renderProfile();
  if (state.route === "log-food") content = renderFoodForm();
  if (state.route === "entries") content = renderEntries();
  if (state.route === "cupboard") content = renderCupboard();
  if (state.route === "add-cupboard-item") content = renderAddCupboardItem();
  if (state.route === "add-ingredient") content = renderAddIngredient();
  if (state.route === "ingredients") content = renderIngredientsList();
  if (state.route === "ingredient-detail") content = renderIngredientDetail();
  if (state.route === "recipes") content = renderRecipesList();
  if (state.route === "add-recipe") content = renderAddRecipe();
  if (state.route === "recipe-detail") content = renderRecipeDetail();

  const bannerClass = state.feedback.type || "notice";
  const banner = state.feedback.message ? `<section class="card ${bannerClass}">${escapeHtml(state.feedback.message)}</section>` : "";
  renderLayout(`${banner}${content}`);
  attachEvents();
}

async function bootstrap() {
  setRouteFromHash();
  const hashParams = new URLSearchParams(window.location.hash.split("?")[1] || "");
  state.selectedIngredientId = hashParams.get("id") || "";
  state.selectedRecipeId = hashParams.get("id") || "";
  await Promise.all([loadHealth(), loadIngredients()]);
  await restoreSessionIfPossible();

  if (currentUserId()) {
    await Promise.all([loadFoodEntries(false), loadCupboardItems(false), loadRecipes(false)]);
  }

  if (state.route === "ingredient-detail") {
    await loadIngredientById(state.selectedIngredientId, false);
  }

  if (state.route === "recipe-detail") {
    await loadRecipeById(state.selectedRecipeId, false);
  }

  render();
}

window.addEventListener("hashchange", async () => {
  setRouteFromHash();
  const hashParams = new URLSearchParams(window.location.hash.split("?")[1] || "");
  state.selectedIngredientId = hashParams.get("id") || "";
  state.selectedRecipeId = hashParams.get("id") || "";

  if (state.route === "entries") {
    await loadFoodEntries(false);
  }

  if (state.route === "cupboard") {
    await loadCupboardItems(false);
  }

  if (state.route === "ingredients") {
    await loadIngredients();
  }

  if (state.route === "ingredient-detail") {
    await loadIngredientById(state.selectedIngredientId, false);
  }

  if (state.route === "recipes") {
    await loadRecipes(false);
  }

  if (state.route === "recipe-detail") {
    await loadRecipeById(state.selectedRecipeId, false);
  }

  clearFeedback();
  render();
});

bootstrap();
