export function handleStartCupboardEdit(event, deps) {
  const { state, render } = deps;
  const itemId = event.currentTarget.getAttribute("data-item-id");
  state.cupboardEditingId = itemId || "";
  render();
}

export function handleCancelCupboardEdit(deps) {
  const { state, render } = deps;
  state.cupboardEditingId = "";
  render();
}

export async function handleRefreshCupboard(deps) {
  const { loadCupboardItems } = deps;
  await loadCupboardItems();
}

export async function handleSubmitCupboardItem(event, deps) {
  const {
    state,
    render,
    setFeedback,
    ensureAuthenticated,
    currentUserId,
    createUserStorecupboardItem,
    defaultCupboardForm,
    loadCupboardItems,
    handlePossiblyStaleSession,
  } = deps;

  event.preventDefault();
  if (!ensureAuthenticated("adding cupboard items")) {
    return;
  }

  const formData = new FormData(event.target);
  const payload = {
    ingredient_id: (formData.get("ingredient_id") || "").toString(),
    quantity: formData.get("quantity") ? Number(formData.get("quantity")) : null,
    unit: (formData.get("unit") || "").toString().trim() || null,
    stock_status: (formData.get("stock_status") || "in_stock").toString(),
    shelf_name: (formData.get("shelf_name") || "").toString().trim() || null,
    best_before_date: (formData.get("best_before_date") || "").toString().trim() || null,
    next_reminder_at: (formData.get("next_reminder_at") || "").toString().trim() || null,
  };

  state.cupboardForm = {
    ingredient_id: payload.ingredient_id,
    quantity: payload.quantity ?? "",
    unit: payload.unit || "",
    stock_status: payload.stock_status,
    shelf_name: payload.shelf_name || "",
    best_before_date: payload.best_before_date || "",
    next_reminder_at: payload.next_reminder_at || "",
  };

  if (!payload.ingredient_id) {
    state.cupboardError = "Ingredient is required.";
    setFeedback("error", "Ingredient is required.");
    render();
    return;
  }

  try {
    state.cupboardSubmitting = true;
    state.cupboardError = "";
    state.cupboardSuccess = "";
    setFeedback("notice", "Adding cupboard item...");
    render();

    await createUserStorecupboardItem(currentUserId(), payload);
    state.cupboardForm = defaultCupboardForm();
    state.cupboardSuccess = "Cupboard item added.";
    setFeedback("success", "Cupboard item added.");

    await loadCupboardItems(false);
    window.location.hash = "#/cupboard";
  } catch (error) {
    if (!handlePossiblyStaleSession(error)) {
      state.cupboardError = `Could not add cupboard item: ${error.message}`;
      setFeedback("error", `Could not add cupboard item: ${error.message}`);
    }
  } finally {
    state.cupboardSubmitting = false;
    render();
  }
}

export async function handleSubmitCupboardUpdate(event, deps) {
  const {
    state,
    render,
    setFeedback,
    ensureAuthenticated,
    currentUserId,
    updateUserStorecupboardItem,
    loadCupboardItems,
    handlePossiblyStaleSession,
  } = deps;

  event.preventDefault();
  if (!ensureAuthenticated("updating cupboard items")) {
    return;
  }

  const itemId = event.currentTarget.getAttribute("data-item-id");
  if (!itemId) {
    setFeedback("error", "Could not determine cupboard item ID.");
    render();
    return;
  }

  const formData = new FormData(event.currentTarget);
  const payload = {
    quantity: formData.get("quantity") ? Number(formData.get("quantity")) : null,
    unit: (formData.get("unit") || "").toString().trim() || null,
    stock_status: (formData.get("stock_status") || "").toString() || null,
    shelf_name: (formData.get("shelf_name") || "").toString().trim() || null,
    best_before_date: (formData.get("best_before_date") || "").toString().trim() || null,
    next_reminder_at: (formData.get("next_reminder_at") || "").toString().trim() || null,
  };

  try {
    state.cupboardSubmitting = true;
    state.cupboardError = "";
    state.cupboardSuccess = "";
    setFeedback("notice", "Updating cupboard item...");
    render();

    await updateUserStorecupboardItem(currentUserId(), itemId, payload);
    state.cupboardEditingId = "";
    state.cupboardSuccess = "Cupboard item updated.";
    setFeedback("success", "Cupboard item updated.");
    await loadCupboardItems(false);
  } catch (error) {
    if (!handlePossiblyStaleSession(error)) {
      state.cupboardError = `Could not update cupboard item: ${error.message}`;
      setFeedback("error", `Could not update cupboard item: ${error.message}`);
    }
  } finally {
    state.cupboardSubmitting = false;
    render();
  }
}

export async function handleDeleteCupboardItem(event, deps) {
  const {
    state,
    render,
    setFeedback,
    ensureAuthenticated,
    currentUserId,
    deleteUserStorecupboardItem,
    loadCupboardItems,
    handlePossiblyStaleSession,
  } = deps;

  if (!ensureAuthenticated("deleting cupboard items")) {
    return;
  }

  const itemId = event.currentTarget.getAttribute("data-item-id");
  if (!itemId) {
    setFeedback("error", "Could not determine cupboard item ID.");
    render();
    return;
  }

  try {
    state.cupboardSubmitting = true;
    state.cupboardError = "";
    state.cupboardSuccess = "";
    setFeedback("notice", "Deleting cupboard item...");
    render();

    await deleteUserStorecupboardItem(currentUserId(), itemId);
    state.cupboardEditingId = "";
    state.cupboardSuccess = "Cupboard item deleted.";
    setFeedback("success", "Cupboard item deleted.");
    await loadCupboardItems(false);
  } catch (error) {
    if (!handlePossiblyStaleSession(error)) {
      state.cupboardError = `Could not delete cupboard item: ${error.message}`;
      setFeedback("error", `Could not delete cupboard item: ${error.message}`);
    }
  } finally {
    state.cupboardSubmitting = false;
    render();
  }
}
