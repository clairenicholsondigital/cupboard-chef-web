import {
  ApiError,
  createIngredient,
  createUserFoodEntry,
  createUserStorecupboardItem,
  deleteUserStorecupboardItem,
  getApiBaseUrl,
  getCurrentUser,
  getIngredients,
  getUserFoodEntries,
  getUserStorecupboardItems,
  healthCheck,
  loginWithEmail,
  updateUserStorecupboardItem,
} from "./api.js";

import { handleSubmitLogin, handleLogout } from "./handlers/authHandlers.js";
import { handleSubmitFoodEntry } from "./handlers/foodHandlers.js";
import {
  handleCancelCupboardEdit,
  handleDeleteCupboardItem,
  handleRefreshCupboard,
  handleStartCupboardEdit,
  handleSubmitCupboardItem,
  handleSubmitCupboardUpdate,
} from "./handlers/cupboardHandlers.js";
import { handleSubmitIngredient } from "./handlers/ingredientHandlers.js";

const mealTimeOptions = ["am", "breakfast", "lunch", "pm", "dinner", "evening", "snack", "late_night"];
const inputMethodOptions = ["text", "voice", "imported"];
const stockStatusOptions = ["in_stock", "low", "out_of_stock"];

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
});

const defaultIngredientForm = () => ({
  canonical_name: "",
  display_name: "",
  category: "veg",
  is_seasonal: false,
  seasonal_months: "",
});

const state = {
  route: "dashboard",
  error: "",
  loading: false,
  currentUser: null,
  authSubject: "",
  foodEntries: [],
  ingredients: [],
  cupboardItems: [],
  cupboardLoading: false,
  cupboardLoaded: false,
  cupboardSubmitting: false,
  cupboardError: "",
  cupboardSuccess: "",
  foodForm: defaultFoodForm(),
  cupboardForm: defaultCupboardForm(),
  ingredientForm: defaultIngredientForm(),
  authForm: {
    email: "",
    password: "",
  },
  cupboardEditingId: "",
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
  state.cupboardItems = [];
  state.cupboardLoaded = false;
  state.cupboardLoading = false;
  state.cupboardSubmitting = false;
  state.cupboardError = "";
  state.cupboardSuccess = "";
  state.cupboardEditingId = "";
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
  const hashRoute = window.location.hash.replace(/^#\/?/, "");
  if (hashRoute) {
    state.route = hashRoute;
    return;
  }

  const pathnameRouteMap = {
    "/": "dashboard",
    "/dashboard": "dashboard",
    "/ingredients": "add-ingredient",
    "/add-ingredient": "add-ingredient",
    "/log-food": "log-food",
    "/entries": "entries",
    "/cupboard": "cupboard",
    "/add-cupboard-item": "add-cupboard-item",
  };

  state.route = pathnameRouteMap[window.location.pathname] || "dashboard";
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function renderLayout(content) {
  const app = document.querySelector("#app");
  const userId = currentUserId();
  app.innerHTML = `
    <header class="header">
      <h1>Cupboard Chef</h1>
      <p>Food logging and cupboard tracking connected to your live API.</p>
    </header>
    <nav class="nav">
      ${navLink("dashboard", "Dashboard")}
      ${navLink("log-food", "Log food")}
      ${navLink("entries", "Food entries")}
      ${navLink("cupboard", "Cupboard")}
      ${navLink("add-cupboard-item", "Add cupboard item")}
      ${navLink("add-ingredient", "Add ingredient")}
    </nav>
    <section class="settings card">
      <h2>Session</h2>
      <p class="meta">Current user UUID: <code>${escapeHtml(userId || "Not signed in")}</code></p>
      <p class="meta">Current email: <code>${escapeHtml(state.currentUser?.email || "Not signed in")}</code></p>
      <p class="meta">Stored token: <code>${getStoredAccessToken() ? "Present" : "None"}</code></p>
      <button id="logout" type="button" ${!userId ? "disabled" : ""}>Log out</button>
      <p class="meta">API base URL: <code>${escapeHtml(getApiBaseUrl())}</code></p>
      ${state.health ? `<p class="${state.health.status === "ok" ? "success" : "error"}">API health: ${escapeHtml(state.health.status)}</p>` : ""}
    </section>
    <main>${content}</main>
  `;

  document.querySelector("#logout")?.addEventListener("click", () => {
    onLogout();
  });
}

function navLink(route, label) {
  const active = state.route === route ? "active" : "";
  return `<a class="${active}" href="#/${route}">${label}</a>`;
}

function card(title, body) {
  return `<article class="card"><h2>${title}</h2>${body}</article>`;
}

function renderDashboard() {
  const preview = state.foodEntries.slice(0, 3);
  const previewHtml = preview.length
    ? `<ul class="list">${preview
      .map((entry) => `<li><strong>${escapeHtml(entry.description)}</strong> <span class="meta">${escapeHtml(entry.meal_time || "meal unspecific")}</span></li>`)
      .join("")}</ul>`
    : "<p class='empty'>No entries yet. Start by logging your first meal.</p>";

  return `
    ${card("Sign in", `
      <p>Authenticate against the backend and we will resolve your user identity via <code>/auth/me</code>.</p>
      <form id="login-form" class="form-grid">
        <label>Email address
          <input name="email" type="email" value="${escapeHtml(state.authForm.email)}" autocomplete="email" required />
        </label>
        <label>Password
          <input name="password" type="password" value="${escapeHtml(state.authForm.password)}" autocomplete="current-password" required />
        </label>
        <button type="submit">${state.loading && !currentUserId() ? "Signing in..." : "Sign in"}</button>
      </form>
    `)}
    ${card("Home", `
      <p>Track meals and keep a practical view of what is in your cupboard.</p>
      <div class="actions">
        <a class="button" href="#/log-food">Log food</a>
        <a class="button secondary" href="#/cupboard">View cupboard</a>
        <a class="button secondary" href="#/add-cupboard-item">Add cupboard item</a>
        <a class="button secondary" href="#/add-ingredient">Add ingredient</a>
      </div>
    `)}
    ${card("Recent food entries", previewHtml)}
  `;
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
      <button type="submit">${state.loading ? "Saving..." : "Save food entry"}</button>
    </form>
  `);
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
    <ul class="list">
      ${state.foodEntries
        .map((entry) => `
          <li>
            <div><strong>${escapeHtml(entry.description)}</strong></div>
            <div class="meta">Meal: ${escapeHtml(entry.meal_time || "n/a")} · Input: ${escapeHtml(entry.input_method || "n/a")} · Rating: ${entry.rating ?? "n/a"}</div>
          </li>
        `)
        .join("")}
    </ul>
  `);
}

function renderCupboardRows() {
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

  return `<ul class="list">${state.cupboardItems.map((item) => {
    const isEditing = state.cupboardEditingId === item.id;
    if (isEditing) {
      return `
        <li>
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
            <div class="actions">
              <button type="submit">Save update</button>
              <button type="button" class="cupboard-cancel-edit">Cancel</button>
            </div>
          </form>
        </li>
      `;
    }

    return `
      <li>
        <div><strong>${escapeHtml(item.ingredient_display_name || item.ingredient_canonical_name || item.ingredient_id)}</strong></div>
        <div class="meta">Qty: ${escapeHtml(item.quantity ?? "n/a")} ${escapeHtml(item.unit || "")} · Status: ${escapeHtml(item.stock_status || "n/a")} · Shelf: ${escapeHtml(item.shelf_name || "n/a")}</div>
        <div class="actions">
          <button type="button" class="cupboard-edit" data-item-id="${item.id}">Edit</button>
          <button type="button" class="cupboard-delete" data-item-id="${item.id}">Delete</button>
        </div>
      </li>
    `;
  }).join("")}</ul>`;
}

function renderCupboard() {
  return card("Cupboard", `
    <p>Manage your cupboard items with full create/read/update/delete support.</p>
    <div class="actions">
      <a class="button" href="#/add-cupboard-item">Add cupboard item</a>
      <button id="refresh-cupboard" type="button" ${state.cupboardLoading ? "disabled" : ""}>${state.cupboardLoading ? "Refreshing..." : "Refresh"}</button>
    </div>
    ${state.cupboardSuccess ? `<p class="success">${escapeHtml(state.cupboardSuccess)}</p>` : ""}
    ${renderCupboardRows()}
  `);
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
      <button type="submit" ${hasIngredients && !state.cupboardSubmitting ? "" : "disabled"}>${state.cupboardSubmitting ? "Adding..." : "Add cupboard item"}</button>
    </form>
  `);
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
      <button type="submit">${state.loading ? "Creating..." : "Create ingredient"}</button>
    </form>
  `);
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

  document.querySelector("#refresh-cupboard")?.addEventListener("click", async () => {
    await onRefreshCupboard();
  });

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

function onLogout() {
  handleLogout({ clearLocalSession, setFeedback, render });
}

async function onRefreshCupboard() {
  await handleRefreshCupboard({ loadCupboardItems });
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
  let content = "";

  if (state.route === "dashboard") content = renderDashboard();
  if (state.route === "log-food") content = renderFoodForm();
  if (state.route === "entries") content = renderEntries();
  if (state.route === "cupboard") content = renderCupboard();
  if (state.route === "add-cupboard-item") content = renderAddCupboardItem();
  if (state.route === "add-ingredient") content = renderAddIngredient();

  const bannerClass = state.feedback.type || "notice";
  const banner = state.feedback.message ? `<section class="card ${bannerClass}">${escapeHtml(state.feedback.message)}</section>` : "";
  renderLayout(`${banner}${content}`);
  attachEvents();
}

async function bootstrap() {
  setRouteFromHash();
  await Promise.all([loadHealth(), loadIngredients()]);
  await restoreSessionIfPossible();

  if (currentUserId()) {
    await Promise.all([loadFoodEntries(false), loadCupboardItems(false)]);
  }

  render();
}

window.addEventListener("hashchange", async () => {
  setRouteFromHash();

  if (state.route === "entries") {
    await loadFoodEntries(false);
  }

  if (state.route === "cupboard") {
    await loadCupboardItems(false);
  }

  clearFeedback();
  render();
});

bootstrap();
