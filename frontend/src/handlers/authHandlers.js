export async function handleSubmitLogin(event, deps) {
  const {
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
  } = deps;

  event.preventDefault();
  const formData = new FormData(event.target);
  const email = (formData.get("email") || "").toString().trim();
  const password = (formData.get("password") || "").toString();

  state.authForm.email = email;
  state.authForm.password = "";

  if (!email || !password) {
    setFeedback("error", "Email and password are required.");
    render();
    return;
  }

  try {
    state.loading = true;
    setFeedback("notice", "Signing in...");
    render();

    clearStoredAccessToken();

    const response = await loginWithEmail({ email, password });

    if (!response?.access_token) {
      throw new Error("Login succeeded but no access token was returned.");
    }

    storeAccessToken(response.access_token);

    const identity = await getCurrentUser(response.access_token);

    state.authSubject = response.email || response.user_id || "";
    state.currentUser = {
      user_id: identity.user_id,
      email: identity.email,
      display_name: identity.display_name,
    };

    storeCurrentUser(state.currentUser);

    setFeedback("success", `Signed in as ${identity.email}.`);
    await Promise.all([loadFoodEntries(false), loadCupboardItems(false)]);
  } catch (error) {
    clearLocalSession();
    setFeedback("error", getLoginErrorMessage(error));
  } finally {
    state.loading = false;
    render();
  }
}

export function handleLogout(deps) {
  const { clearLocalSession, setFeedback, render } = deps;

  clearLocalSession();
  setFeedback("notice", "Signed out.");
  render();
}
