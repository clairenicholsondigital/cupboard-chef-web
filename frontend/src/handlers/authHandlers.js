export async function handleSubmitLogin(
  event,
  {
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
    loadShoppingLists,
  },
) {
  event.preventDefault();

  const form = event.currentTarget;
  const formData = new FormData(form);

  const email = String(formData.get("email") || "").trim();
  const password = String(formData.get("password") || "");

  state.authForm.email = email;
  state.authForm.password = password;

  if (!email || !password) {
    setFeedback("error", "Please enter your email and password.");
    render();
    return;
  }

  state.loading = true;
  setFeedback("notice", "Signing in...");
  render();

  try {
    clearStoredAccessToken();

    const loginResponse = await loginWithEmail({ email, password });
    console.log("[auth] login response", loginResponse);

    const token =
      loginResponse?.access_token ||
      loginResponse?.token ||
      loginResponse?.auth_token ||
      loginResponse?.data?.access_token ||
      loginResponse?.data?.token ||
      "";

    if (!token) {
      throw new Error("Login succeeded, but no access token was returned.");
    }

    storeAccessToken(token);
    console.log("[auth] token stored");

    const identity = await getCurrentUser();
    console.log("[auth] current user", identity);

    if (!identity?.user_id) {
      throw new Error("Signed in, but could not load the current user.");
    }

    state.currentUser = {
      user_id: identity.user_id,
      email: identity.email || email,
      display_name: identity.display_name || "",
    };
    state.authSubject = identity.email || identity.user_id || "";
    storeCurrentUser(state.currentUser);

    state.loading = false;
    state.authForm.password = "";

    setFeedback("success", "Signed in successfully.");

    state.route = "dashboard";
    window.location.hash = "#/dashboard";

    await Promise.all([
      loadFoodEntries(render, false),
      loadCupboardItems(render, false),
      loadRecipes(render, false),
      loadShoppingLists(render, false),
    ]);

    render();
  } catch (error) {
    console.error("[auth] login failed", error);

    state.loading = false;
    clearLocalSession();

    setFeedback("error", getLoginErrorMessage(error));
    render();
  }
}

export function handleLogout({ clearLocalSession, setFeedback, render }) {
  clearLocalSession();
  setFeedback("success", "You have been logged out.");
  window.location.hash = "#/login";
  render();
}