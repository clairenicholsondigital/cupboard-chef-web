function parseIngredientForm(formData) {
  const hasSeasonalFields = formData.has("is_seasonal") || formData.has("seasonal_months");
  const isSeasonal = hasSeasonalFields ? formData.get("is_seasonal") === "on" : null;
  const seasonalMonthsRaw = hasSeasonalFields
    ? (formData.get("seasonal_months") || "").toString().trim()
    : "";
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
    is_seasonal: hasSeasonalFields ? isSeasonal : null,
    seasonal_months: hasSeasonalFields ? (isSeasonal ? seasonalMonths : []) : null,
  };

  return { payload, seasonalMonthsRaw, seasonalMonths, isSeasonal };
}

function ingredientPayloadIsInvalid({ payload, isSeasonal, seasonalMonths, seasonalMonthsRaw }) {
  if (!payload.canonical_name || !payload.display_name || !payload.category) {
    return "Canonical name, display name, and category are required.";
  }

  if (isSeasonal && !seasonalMonths.length && seasonalMonthsRaw) {
    return "Seasonal months must be comma-separated numbers from 1 to 12.";
  }

  return "";
}

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
  const { payload, seasonalMonthsRaw, seasonalMonths, isSeasonal } = parseIngredientForm(formData);

  state.ingredientForm = {
    canonical_name: payload.canonical_name,
    display_name: payload.display_name,
    category: payload.category,
    is_seasonal: payload.is_seasonal,
    seasonal_months: seasonalMonthsRaw,
  };

  const validationError = ingredientPayloadIsInvalid({ payload, isSeasonal, seasonalMonths, seasonalMonthsRaw });
  if (validationError) {
    setFeedback("error", validationError);
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

export async function handleSubmitIngredientUpdate(event, deps) {
  const {
    state,
    render,
    setFeedback,
    ensureAuthenticated,
    updateIngredient,
    loadIngredientById,
    handlePossiblyStaleSession,
  } = deps;

  event.preventDefault();
  if (!ensureAuthenticated("updating ingredients")) {
    return;
  }

  if (!state.selectedIngredientId) {
    setFeedback("error", "No ingredient selected.");
    render();
    return;
  }

  const formData = new FormData(event.target);
  const { payload, seasonalMonthsRaw, seasonalMonths, isSeasonal } = parseIngredientForm(formData);
  const validationError = ingredientPayloadIsInvalid({ payload, isSeasonal, seasonalMonths, seasonalMonthsRaw });
  if (validationError) {
    setFeedback("error", validationError);
    render();
    return;
  }

  state.ingredientDetailForm = {
    canonical_name: payload.canonical_name,
    display_name: payload.display_name,
    category: payload.category,
    is_seasonal: payload.is_seasonal,
    seasonal_months: seasonalMonthsRaw,
  };

  try {
    state.loading = true;
    setFeedback("notice", "Updating ingredient...");
    render();
    await updateIngredient(state.selectedIngredientId, payload);
    setFeedback("success", "Ingredient updated.");
    await loadIngredientById(state.selectedIngredientId);
  } catch (error) {
    if (!handlePossiblyStaleSession(error)) {
      setFeedback("error", `Could not update ingredient: ${error.message}`);
    }
  } finally {
    state.loading = false;
    render();
  }
}

export async function handleDeleteIngredient(event, deps) {
  const {
    state,
    render,
    setFeedback,
    ensureAuthenticated,
    deleteIngredient,
    loadIngredients,
    handlePossiblyStaleSession,
  } = deps;

  event.preventDefault();
  if (!ensureAuthenticated("deleting ingredients")) {
    return;
  }

  if (!state.selectedIngredientId) {
    setFeedback("error", "No ingredient selected.");
    render();
    return;
  }

  try {
    state.loading = true;
    setFeedback("notice", "Deleting ingredient...");
    render();

    await deleteIngredient(state.selectedIngredientId);
    await loadIngredients();
    state.selectedIngredientId = "";
    state.selectedIngredient = null;
    state.ingredientDetailForm = null;
    window.location.hash = "#/ingredients";
    setFeedback("success", "Ingredient deleted.");
  } catch (error) {
    if (!handlePossiblyStaleSession(error)) {
      setFeedback("error", `Could not delete ingredient: ${error.message}`);
    }
  } finally {
    state.loading = false;
    render();
  }
}
