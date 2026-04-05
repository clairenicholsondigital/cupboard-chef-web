function parseRecipeForm(formData) {
  const createdByUserIdRaw = (formData.get("created_by_user_id") || "").toString().trim();

  const payload = {
    title: (formData.get("title") || "").toString().trim(),
    description: (formData.get("description") || "").toString().trim(),
    instructions: (formData.get("instructions") || "").toString().trim(),
    source_url: (formData.get("source_url") || "").toString().trim(),
    created_by_user_id: createdByUserIdRaw || null,
    is_system: formData.get("is_system") === "on",
  };

  return {
    payload,
    createdByUserIdRaw,
  };
}

function recipePayloadIsInvalid({ payload }) {
  if (!payload.title) {
    return "Recipe title is required.";
  }

  return "";
}

export async function handleSubmitRecipe(event, deps) {
  const {
    state,
    render,
    setFeedback,
    ensureAuthenticated,
    createRecipe,
    defaultRecipeForm,
    loadRecipes,
    handlePossiblyStaleSession,
  } = deps;

  event.preventDefault();
  if (!ensureAuthenticated("adding recipes")) {
    return;
  }

  const formData = new FormData(event.target);
  const { payload, createdByUserIdRaw } = parseRecipeForm(formData);

  state.recipeForm = {
    title: payload.title,
    description: payload.description,
    instructions: payload.instructions,
    source_url: payload.source_url,
    created_by_user_id: createdByUserIdRaw,
    is_system: payload.is_system,
  };

  const validationError = recipePayloadIsInvalid({ payload });
  if (validationError) {
    setFeedback("error", validationError);
    render();
    return;
  }

  try {
    state.loading = true;
    setFeedback("notice", "Creating recipe...");
    render();

    await createRecipe(payload);
    state.recipeForm = defaultRecipeForm();
    setFeedback("success", "Recipe created.");
    await loadRecipes();
  } catch (error) {
    if (!handlePossiblyStaleSession(error)) {
      setFeedback("error", `Could not create recipe: ${error.message}`);
    }
  } finally {
    state.loading = false;
    render();
  }
}

export async function handleSubmitRecipeUpdate(event, deps) {
  const {
    state,
    render,
    setFeedback,
    ensureAuthenticated,
    updateRecipe,
    loadRecipeById,
    handlePossiblyStaleSession,
  } = deps;

  event.preventDefault();
  if (!ensureAuthenticated("updating recipes")) {
    return;
  }

  if (!state.selectedRecipeId) {
    setFeedback("error", "No recipe selected.");
    render();
    return;
  }

  const formData = new FormData(event.target);
  const { payload, createdByUserIdRaw } = parseRecipeForm(formData);

  const validationError = recipePayloadIsInvalid({ payload });
  if (validationError) {
    setFeedback("error", validationError);
    render();
    return;
  }

  state.recipeDetailForm = {
    title: payload.title,
    description: payload.description,
    instructions: payload.instructions,
    source_url: payload.source_url,
    created_by_user_id: createdByUserIdRaw,
    is_system: payload.is_system,
  };

  try {
    state.loading = true;
    setFeedback("notice", "Updating recipe...");
    render();

    await updateRecipe(state.selectedRecipeId, payload);
    setFeedback("success", "Recipe updated.");
    await loadRecipeById(state.selectedRecipeId);
  } catch (error) {
    if (!handlePossiblyStaleSession(error)) {
      setFeedback("error", `Could not update recipe: ${error.message}`);
    }
  } finally {
    state.loading = false;
    render();
  }
}

export async function handleDeleteRecipe(event, deps) {
  const {
    state,
    render,
    setFeedback,
    ensureAuthenticated,
    deleteRecipe,
    loadRecipes,
    handlePossiblyStaleSession,
  } = deps;

  event.preventDefault();
  if (!ensureAuthenticated("deleting recipes")) {
    return;
  }

  if (!state.selectedRecipeId) {
    setFeedback("error", "No recipe selected.");
    render();
    return;
  }

  try {
    state.loading = true;
    setFeedback("notice", "Deleting recipe...");
    render();

    await deleteRecipe(state.selectedRecipeId);
    await loadRecipes();

    state.selectedRecipeId = "";
    state.selectedRecipe = null;
    state.recipeDetailForm = null;

    window.location.hash = "#/recipes";
    setFeedback("success", "Recipe deleted.");
  } catch (error) {
    if (!handlePossiblyStaleSession(error)) {
      setFeedback("error", `Could not delete recipe: ${error.message}`);
    }
  } finally {
    state.loading = false;
    render();
  }
}