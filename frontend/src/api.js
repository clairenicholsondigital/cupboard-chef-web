const DEFAULT_API_BASE_URL = "https://api.food.helixscribe.cloud";

const trimTrailingSlash = (value) => value.replace(/\/+$/, "");

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
  const response = await fetch(`${baseUrl}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

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

export function getFoodEntries(userId) {
  const query = userId ? `?user_id=${encodeURIComponent(userId)}` : "";
  return request(`/food-entries${query}`, { method: "GET" });
}

export function createFoodEntry(data) {
  return request("/food-entries", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

// Backend routes for cupboard items are not available yet in backend/app/main.py.
// These methods are intentionally left as explicit stubs so UI can show honest status.
export function cupboardApiAvailable() {
  return false;
}
