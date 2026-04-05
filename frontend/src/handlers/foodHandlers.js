export async function handleSubmitFoodEntry(event, deps) {
  const {
    state,
    render,
    setFeedback,
    ensureAuthenticated,
    currentUserId,
    createUserFoodEntry,
    defaultFoodForm,
    loadFoodEntries,
    handlePossiblyStaleSession,
  } = deps;

  event.preventDefault();
  if (!ensureAuthenticated("logging food")) {
    return;
  }

  const userId = currentUserId();
  const formData = new FormData(event.target);
  const payload = {
    description: (formData.get("description") || "").toString().trim(),
    raw_input: (formData.get("raw_input") || "").toString().trim() || null,
    input_method: formData.get("input_method"),
    meal_time: formData.get("meal_time") || null,
    rating: formData.get("rating") ? Number(formData.get("rating")) : null,
  };

  state.foodForm = {
    description: payload.description,
    raw_input: payload.raw_input || "",
    input_method: payload.input_method,
    meal_time: payload.meal_time || "",
    rating: payload.rating ?? "",
  };

  if (!payload.description) {
    setFeedback("error", "Description is required.");
    render();
    return;
  }

  try {
    state.loading = true;
    setFeedback("notice", "Saving food entry...");
    render();
    await createUserFoodEntry(userId, payload);
    state.foodForm = defaultFoodForm();
    setFeedback("success", "Food entry saved.");
    await loadFoodEntries(false);
    window.location.hash = "#/entries";
  } catch (error) {
    if (!handlePossiblyStaleSession(error)) {
      setFeedback("error", `Could not save food entry: ${error.message}`);
    }
  } finally {
    state.loading = false;
    render();
  }
}
