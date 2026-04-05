import { ApiError } from "./api.js";

export function setFeedback(state, type, message) {
  state.feedback = { type, message };
}

export function clearFeedback(state) {
  state.feedback = { type: "", message: "" };
}

export function currentUserId(state) {
  return state.currentUser?.user_id || "";
}

export function isAuthenticated(state) {
  return Boolean(currentUserId(state));
}

export function ensureAuthenticated(state, render, setFeedbackFn, actionLabel) {
  if (currentUserId(state)) {
    return true;
  }

  setFeedbackFn("error", `Please sign in before ${actionLabel}.`);
  render();
  return false;
}

export function getLoginErrorMessage(error) {
  if (error instanceof ApiError) return error.message;
  if (error instanceof Error) return error.message;
  return "Unable to sign in.";
}

export function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

export function formatDateForDateInput(value) {
  if (!value) return "";
  const datePart = String(value).split("T")[0].split(" ")[0];
  return /^\d{4}-\d{2}-\d{2}$/.test(datePart) ? datePart : "";
}

export function formatDateTimeForInput(value) {
  if (!value) return "";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "";
  const year = parsed.getFullYear();
  const month = String(parsed.getMonth() + 1).padStart(2, "0");
  const day = String(parsed.getDate()).padStart(2, "0");
  const hours = String(parsed.getHours()).padStart(2, "0");
  const minutes = String(parsed.getMinutes()).padStart(2, "0");
  return `${year}-${month}-${day}T${hours}:${minutes}`;
}

export function formatFriendlyDate(value) {
  if (!value) return "Not set";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return String(value);
  return parsed.toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
}

export function formatFriendlyDateTime(value) {
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

export function formatStockLabel(value) {
  return String(value || "unknown").replaceAll("_", " ");
}

export function stockStatusClass(value) {
  const normalized = String(value || "").toLowerCase();
  if (normalized === "in_stock") return "status-in-stock";
  if (normalized === "low") return "status-low";
  if (normalized === "out_of_stock") return "status-out-of-stock";
  return "status-unknown";
}

export function isExpiringSoon(value) {
  if (!value) return false;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return false;
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  date.setHours(0, 0, 0, 0);
  const diffDays = Math.ceil((date - now) / (1000 * 60 * 60 * 24));
  return diffDays >= 0 && diffDays <= 3;
}

export function getCupboardVisibleItems(state) {
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