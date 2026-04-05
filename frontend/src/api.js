const DEFAULT_API_BASE_URL = "https://api.food.helixscribe.cloud";

const trimTrailingSlash = (value) => value.replace(/\/+$/, "");

const buildQueryString = (params = {}) => {
  const search = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value === undefined || value === null || value === "") {
      return;
    }

    if (Array.isArray(value)) {
      value.forEach((item) => {
        if (item !== undefined && item !== null && item !== "") {
          search.append(key, String(item));
        }
      });
      return;
    }

    search.append(key, String(value));
  });

  const query = search.toString();
  return query ? `?${query}` : "";
};

export function getApiBaseUrl() {
  const configuredBaseUrl = window.CUPBOARD_CHEF_API_URL || localStorage.getItem("cupboardChef.apiBaseUrl");
  return trimTrailingSlash(configuredBaseUrl || DEFAULT_API_BASE_URL);
}

export class ApiError extends Error {
  constructor(message, status, details) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}

async function request(path, options = {}) {
  const baseUrl = getApiBaseUrl();
  let response;
  try {
    response = await fetch(`${baseUrl}${path}`, {
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
      ...options,
    });
  } catch (error) {
    throw new ApiError(
      `Unable to reach API at ${baseUrl}. Check network/CORS configuration and API availability.`,
      0,
      { cause: error instanceof Error ? error.message : String(error) },
    );
  }

  let payload = null;
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    payload = await response.json();
  }

  if (!response.ok) {
    throw new ApiError(
      payload?.detail || `Request failed with status ${response.status}`,
      response.status,
      payload,
    );
  }

  return payload;
}

export function healthCheck() {
  return request("/health", { method: "GET" });
}

export function getIngredients() {
  return request("/ingredients", { method: "GET" });
}

export function createIngredient(data) {
  return request("/ingredients", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function getFoodEntries(params = {}) {
  return request(`/food-entries${buildQueryString(params)}`, { method: "GET" });
}

export function createFoodEntry(data) {
  return request("/food-entries", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function getUserFoodEntries(userId, params = {}) {
  return request(`/users/${encodeURIComponent(userId)}/food-entries${buildQueryString(params)}`, {
    method: "GET",
  });
}

export function createUserFoodEntry(userId, data) {
  return request(`/users/${encodeURIComponent(userId)}/food-entries`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function getUserStorecupboardItems(userId, params = {}) {
  return request(`/users/${encodeURIComponent(userId)}/storecupboard${buildQueryString(params)}`, {
    method: "GET",
  });
}

export function createUserStorecupboardItem(userId, data) {
  return request(`/users/${encodeURIComponent(userId)}/storecupboard`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function updateUserStorecupboardItem(userId, itemId, data) {
  return request(`/users/${encodeURIComponent(userId)}/storecupboard/${encodeURIComponent(itemId)}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export function deleteUserStorecupboardItem(userId, itemId) {
  return request(`/users/${encodeURIComponent(userId)}/storecupboard/${encodeURIComponent(itemId)}`, {
    method: "DELETE",
  });
}

export function getRecipes(params = {}) {
  return request(`/recipes${buildQueryString(params)}`, { method: "GET" });
}

export function getRecipe(recipeId) {
  return request(`/recipes/${encodeURIComponent(recipeId)}`, { method: "GET" });
}

export function createRecipe(data) {
  return request("/recipes", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function updateRecipe(recipeId, data) {
  return request(`/recipes/${encodeURIComponent(recipeId)}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export function deleteRecipe(recipeId) {
  return request(`/recipes/${encodeURIComponent(recipeId)}`, { method: "DELETE" });
}

export function getTags(params = {}) {
  return request(`/tags${buildQueryString(params)}`, { method: "GET" });
}

export function createTag(data) {
  return request("/tags", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function getUserAiSuggestions(userId, params = {}) {
  return request(`/users/${encodeURIComponent(userId)}/ai-suggestions${buildQueryString(params)}`, {
    method: "GET",
  });
}

export function createUserAiSuggestion(userId, data) {
  return request(`/users/${encodeURIComponent(userId)}/ai-suggestions`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function loginWithEmail(data) {
  return request("/auth/login", {
    method: "POST",
    body: JSON.stringify(data),
  }).catch((error) => {
    if (error instanceof ApiError && error.status === 404) {
      return request("/login", {
        method: "POST",
        body: JSON.stringify(data),
      });
    }
    throw error;
  });
}
