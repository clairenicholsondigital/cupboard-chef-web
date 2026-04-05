const DEFAULT_API_BASE_URL = "https://api.food.helixscribe.cloud";

const AUTH_STORAGE_KEYS = [
  "cupboard_chef_access_token",
  "access_token",
  "auth_token",
  "token",
];

const trimTrailingSlash = (value) => String(value || "").replace(/\/+$/, "");

function safeStorageGet(key) {
  try {
    return localStorage.getItem(key) || "";
  } catch {
    return "";
  }
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
  const configuredBaseUrl =
    window.CUPBOARD_CHEF_API_URL || safeStorageGet("cupboardChef.apiBaseUrl");

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
  const { auth = true, ...fetchOptions } = options;

  const existingHeaders = fetchOptions.headers || {};
  const hasAuthorizationHeader =
    Object.prototype.hasOwnProperty.call(existingHeaders, "Authorization") ||
    Object.prototype.hasOwnProperty.call(existingHeaders, "authorization");

  const headers = {
    ...existingHeaders,
  };

  const hasBody = fetchOptions.body !== undefined && fetchOptions.body !== null;

  if (hasBody && !headers["Content-Type"] && !headers["content-type"]) {
    headers["Content-Type"] = "application/json";
  }

  const storedToken = getStoredAccessToken();
  if (auth && storedToken && !hasAuthorizationHeader) {
    headers.Authorization = `Bearer ${storedToken}`;
  }

  let response;
  try {
    response = await fetch(`${baseUrl}${path}`, {
      ...fetchOptions,
      headers,
    });
  } catch (error) {
    throw new ApiError(
      `Unable to reach API at ${baseUrl}. Check network, CORS, and API availability.`,
      0,
      { cause: error instanceof Error ? error.message : String(error) },
    );
  }

  let payload = null;
  const contentType = response.headers.get("content-type") || "";

  if (contentType.includes("application/json")) {
    try {
      payload = await response.json();
    } catch {
      payload = null;
    }
  } else {
    try {
      const text = await response.text();
      payload = text || null;
    } catch {
      payload = null;
    }
  }

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;

    if (payload && typeof payload === "object" && payload.detail) {
      message = payload.detail;
    } else if (typeof payload === "string" && payload.trim()) {
      message = payload.trim();
    }

    throw new ApiError(message, response.status, payload);
  }

  return payload;
}

export function healthCheck() {
  return request("/health", { method: "GET", auth: false });
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

export function getIngredient(ingredientId) {
  return request(`/ingredients/${encodeURIComponent(ingredientId)}`, { method: "GET" });
}

export function updateIngredient(ingredientId, data) {
  return request(`/ingredients/${encodeURIComponent(ingredientId)}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
}

export function deleteIngredient(ingredientId) {
  return request(`/ingredients/${encodeURIComponent(ingredientId)}`, {
    method: "DELETE",
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
  return request(
    `/users/${encodeURIComponent(userId)}/food-entries${buildQueryString(params)}`,
    { method: "GET" },
  );
}

export function createUserFoodEntry(userId, data) {
  return request(`/users/${encodeURIComponent(userId)}/food-entries`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function getUserStorecupboardItems(userId, params = {}) {
  return request(
    `/users/${encodeURIComponent(userId)}/storecupboard${buildQueryString(params)}`,
    { method: "GET" },
  );
}

export function createUserStorecupboardItem(userId, data) {
  return request(`/users/${encodeURIComponent(userId)}/storecupboard`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function updateUserStorecupboardItem(userId, itemId, data) {
  return request(
    `/users/${encodeURIComponent(userId)}/storecupboard/${encodeURIComponent(itemId)}`,
    {
      method: "PUT",
      body: JSON.stringify(data),
    },
  );
}

export function deleteUserStorecupboardItem(userId, itemId) {
  return request(
    `/users/${encodeURIComponent(userId)}/storecupboard/${encodeURIComponent(itemId)}`,
    {
      method: "DELETE",
    },
  );
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
  return request(`/recipes/${encodeURIComponent(recipeId)}`, {
    method: "DELETE",
  });
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
  return request(
    `/users/${encodeURIComponent(userId)}/ai-suggestions${buildQueryString(params)}`,
    { method: "GET" },
  );
}

export function createUserAiSuggestion(userId, data) {
  return request(`/users/${encodeURIComponent(userId)}/ai-suggestions`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export function getCurrentUser(accessToken) {
  const token = accessToken || getStoredAccessToken();

  if (!token) {
    throw new ApiError("No access token available.", 401, null);
  }

  return request("/auth/me", {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
}

export function loginWithEmail(data) {
  return request("/auth/login", {
    method: "POST",
    body: JSON.stringify(data),
    auth: false,
  }).catch((error) => {
    if (error instanceof ApiError && error.status === 404) {
      return request("/login", {
        method: "POST",
        body: JSON.stringify(data),
        auth: false,
      });
    }
    throw error;
  });
}
