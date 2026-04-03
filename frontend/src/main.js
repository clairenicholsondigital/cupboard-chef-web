import {
  ApiError,
  cupboardApiAvailable,
  createFoodEntry,
  getApiBaseUrl,
  getFoodEntries,
  getIngredients,
  healthCheck,
} from "./api.js";

const mealTimeOptions = ["am", "breakfast", "lunch", "pm", "dinner", "evening", "snack", "late_night"];
const inputMethodOptions = ["text", "voice", "imported"];
const stockStatusOptions = ["in_stock", "low", "out_of_stock"];

const state = {
  route: "dashboard",
  loading: false,
  error: "",
  foodEntries: [],
  ingredients: [],
  foodForm: {
    description: "",
    raw_input: "",
    input_method: "text",
    meal_time: "",
    rating: "",
  },
  cupboardForm: {
    ingredient_id: "",
    quantity: "",
    unit: "",
    stock_status: "in_stock",
    shelf_name: "",
  },
  feedback: "",
  health: null,
};

function getUserId() {
  return localStorage.getItem("cupboardChef.userId") || "";
}

function setUserId(value) {
  if (value) {
    localStorage.setItem("cupboardChef.userId", value);
  } else {
    localStorage.removeItem("cupboardChef.userId");
  }
}

function setRouteFromHash() {
  const value = window.location.hash.replace(/^#\/?/, "") || "dashboard";
  state.route = value;
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
    </nav>
    <section class="settings card">
      <h2>Session settings</h2>
      <label>User UUID (required by POST /food-entries)
        <input id="user-id-input" value="${escapeHtml(getUserId())}" placeholder="e.g. 11111111-1111-1111-1111-111111111111" />
      </label>
      <button id="save-user-id" type="button">Save user</button>
      <p class="meta">API base URL: <code>${escapeHtml(getApiBaseUrl())}</code></p>
      ${state.health ? `<p class="success">API health: ${escapeHtml(state.health.status)}</p>` : ""}
    </section>
    <main>${content}</main>
  `;

  document.querySelector("#save-user-id")?.addEventListener("click", () => {
    const value = document.querySelector("#user-id-input").value.trim();
    setUserId(value);
    state.feedback = value ? "User ID saved." : "User ID cleared.";
    render();
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
    ${card("Home", `
      <p>Track meals and keep a practical view of what is in your cupboard.</p>
      <div class="actions">
        <a class="button" href="#/log-food">Log food</a>
        <a class="button secondary" href="#/cupboard">View cupboard</a>
        <a class="button secondary" href="#/add-cupboard-item">Add cupboard item</a>
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
      <button type="submit">Save food entry</button>
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

function renderCupboard() {
  const integrationMessage = cupboardApiAvailable()
    ? "Cupboard API connected."
    : "Cupboard endpoints are not available in backend/app/main.py yet. This view is scaffolded and ready for API hookup.";

  return card("Cupboard", `
    <p>${integrationMessage}</p>
    <p class="meta">Planned fields: ingredient, quantity, unit, stock status, shelf name.</p>
  `);
}

function renderAddCupboardItem() {
  const ingredientOptions = state.ingredients.length
    ? state.ingredients.map((ingredient) => `<option value="${ingredient.id}">${escapeHtml(ingredient.display_name)}</option>`).join("")
    : "<option value=''>No ingredients loaded</option>";

  return card("Add cupboard item", `
    <p class="meta">This form is ready, but submit is disabled until backend cupboard endpoints are implemented.</p>
    <form id="cupboard-form" class="form-grid">
      <label>Ingredient
        <select name="ingredient_id">${ingredientOptions}</select>
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
      <button type="submit" disabled>Submit pending backend support</button>
    </form>
  `);
}

function attachEvents() {
  const foodForm = document.querySelector("#food-form");
  if (foodForm) {
    foodForm.addEventListener("submit", onSubmitFoodEntry);
  }

  const cupboardForm = document.querySelector("#cupboard-form");
  if (cupboardForm) {
    cupboardForm.addEventListener("submit", (event) => {
      event.preventDefault();
    });
  }
}

async function onSubmitFoodEntry(event) {
  event.preventDefault();
  const userId = getUserId();
  if (!userId) {
    state.feedback = "A valid user UUID is required before posting food entries.";
    render();
    return;
  }

  const formData = new FormData(event.target);
  const payload = {
    user_id: userId,
    description: (formData.get("description") || "").toString().trim(),
    raw_input: (formData.get("raw_input") || "").toString().trim() || null,
    input_method: formData.get("input_method"),
    meal_time: formData.get("meal_time") || null,
    rating: formData.get("rating") ? Number(formData.get("rating")) : null,
  };

  if (!payload.description) {
    state.feedback = "Description is required.";
    render();
    return;
  }

  try {
    state.feedback = "Saving food entry...";
    render();
    await createFoodEntry(payload);
    state.foodForm = { description: "", raw_input: "", input_method: "text", meal_time: "", rating: "" };
    state.feedback = "Food entry saved.";
    await loadFoodEntries();
    window.location.hash = "#/entries";
  } catch (error) {
    state.feedback = `Could not save food entry: ${error.message}`;
    render();
  }
}

async function loadHealth() {
  try {
    state.health = await healthCheck();
  } catch {
    state.health = { status: "unavailable" };
  }
}

async function loadFoodEntries() {
  state.loading = true;
  state.error = "";
  render();

  try {
    state.foodEntries = await getFoodEntries(getUserId());
  } catch (error) {
    state.foodEntries = [];
    state.error = error instanceof ApiError ? error.message : "Could not load food entries.";
  } finally {
    state.loading = false;
    render();
  }
}

async function loadIngredients() {
  try {
    state.ingredients = await getIngredients();
  } catch {
    state.ingredients = [];
  }
}

function render() {
  let content = "";

  if (state.route === "dashboard") content = renderDashboard();
  if (state.route === "log-food") content = renderFoodForm();
  if (state.route === "entries") content = renderEntries();
  if (state.route === "cupboard") content = renderCupboard();
  if (state.route === "add-cupboard-item") content = renderAddCupboardItem();

  const banner = state.feedback ? `<section class="card notice">${escapeHtml(state.feedback)}</section>` : "";
  renderLayout(`${banner}${content}`);
  attachEvents();
}

async function bootstrap() {
  setRouteFromHash();
  await Promise.all([loadHealth(), loadIngredients(), loadFoodEntries()]);
  render();
}

window.addEventListener("hashchange", () => {
  setRouteFromHash();
  render();
});

bootstrap();
