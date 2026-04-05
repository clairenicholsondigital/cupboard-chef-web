export async function handleSubmitIngredient(event, deps) {
  const {
    state,
    render,
    setFeedback,
    ensureAuthenticated,
    createIngredient,
    defaultIngredientForm,
    loadIngredients,
    handlePossiblyStaleSession,
  } = deps;

  event.preventDefault();
  if (!ensureAuthenticated("adding ingredients")) {
    return;
  }

  const formData = new FormData(event.target);
  const isSeasonal = formData.get("is_seasonal") === "on";
  const seasonalMonthsRaw = (formData.get("seasonal_months") || "").toString().trim();
  const seasonalMonths = seasonalMonthsRaw
    ? seasonalMonthsRaw
      .split(",")
      .map((value) => Number(value.trim()))
      .filter((value) => Number.isInteger(value) && value >= 1 && value <= 12)
    : [];

  const payload = {
    canonical_name: (formData.get("canonical_name") || "").toString().trim(),
    display_name: (formData.get("display_name") || "").toString().trim(),
    category: (formData.get("category") || "").toString().trim(),
    is_seasonal: isSeasonal,
    seasonal_months: isSeasonal ? seasonalMonths : [],
  };

  state.ingredientForm = {
    canonical_name: payload.canonical_name,
    display_name: payload.display_name,
    category: payload.category,
    is_seasonal: payload.is_seasonal,
    seasonal_months: seasonalMonthsRaw,
  };

  if (!payload.canonical_name || !payload.display_name || !payload.category) {
    setFeedback("error", "Canonical name, display name, and category are required.");
    render();
    return;
  }

  if (isSeasonal && !seasonalMonths.length && seasonalMonthsRaw) {
    setFeedback("error", "Seasonal months must be comma-separated numbers from 1 to 12.");
    render();
    return;
  }

  try {
    state.loading = true;
    setFeedback("notice", "Creating ingredient...");
    render();

    await createIngredient(payload);
    state.ingredientForm = defaultIngredientForm();
    setFeedback("success", "Ingredient created.");
    await loadIngredients();
  } catch (error) {
    if (!handlePossiblyStaleSession(error)) {
      setFeedback("error", `Could not create ingredient: ${error.message}`);
    }
  } finally {
    state.loading = false;
    render();
  }
}
