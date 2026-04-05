import { AUTH_STORAGE_KEYS, USER_STORAGE_KEYS } from "./constants.js";

export function safeStorageGet(key) {
  try {
    return localStorage.getItem(key);
  } catch {
    return "";
  }
}

export function safeStorageSet(key, value) {
  try {
    localStorage.setItem(key, value);
  } catch {
    // Ignore storage write failures.
  }
}

export function safeStorageRemove(key) {
  try {
    localStorage.removeItem(key);
  } catch {
    // Ignore storage delete failures.
  }
}

export function getStoredAccessToken() {
  for (const key of AUTH_STORAGE_KEYS) {
    const value = safeStorageGet(key);
    if (value) {
      return value;
    }
  }
  return "";
}

export function storeAccessToken(token) {
  for (const key of AUTH_STORAGE_KEYS) {
    safeStorageSet(key, token);
  }
}

export function clearStoredAccessToken() {
  for (const key of AUTH_STORAGE_KEYS) {
    safeStorageRemove(key);
  }
}

export function storeCurrentUser(user) {
  if (!user) return;

  safeStorageSet(USER_STORAGE_KEYS.userId, user.user_id || "");
  safeStorageSet(USER_STORAGE_KEYS.email, user.email || "");
  safeStorageSet(USER_STORAGE_KEYS.displayName, user.display_name || "");
}

export function clearStoredCurrentUser() {
  safeStorageRemove(USER_STORAGE_KEYS.userId);
  safeStorageRemove(USER_STORAGE_KEYS.email);
  safeStorageRemove(USER_STORAGE_KEYS.displayName);
}