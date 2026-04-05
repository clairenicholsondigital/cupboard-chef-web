function parseShoppingListItemForm(formData) {
  const payload = {
    ingredient_id: (formData.get("ingredient_id") || "").toString().trim() || null,
    item_name: (formData.get("item_name") || "").toString().trim() || null,
    quantity: formData.get("quantity") ? Number(formData.get("quantity")) : null,
    unit: (formData.get("unit") || "").toString().trim() || null,
    note: (formData.get("note") || "").toString().trim() || null,
    is_checked: formData.get("is_checked") === "on",
    source_type: (formData.get("source_type") || "manual").toString(),
  };

  if (!payload.ingredient_id && !payload.item_name) {
    return { payload, error: "Add an item name or choose an ingredient." };
  }

  return { payload, error: "" };
}

export async function handleSubmitShoppingList(event, deps) {
  const {
    state,
    render,
    setFeedback,
    ensureAuthenticated,
    currentUserId,
    createShoppingList,
    defaultShoppingListForm,
    loadShoppingLists,
    handlePossiblyStaleSession,
  } = deps;

  event.preventDefault();
  if (!ensureAuthenticated("creating shopping lists")) return;

  const formData = new FormData(event.target);
  const payload = {
    name: (formData.get("name") || "").toString().trim(),
    status: (formData.get("status") || "active").toString(),
  };

  state.shoppingListForm = { ...payload };

  if (!payload.name) {
    setFeedback("error", "List name is required.");
    render();
    return;
  }

  try {
    state.shoppingListLoading = true;
    setFeedback("notice", "Creating shopping list...");
    render();
    await createShoppingList(currentUserId(), payload);
    state.shoppingListForm = defaultShoppingListForm();
    setFeedback("success", "Shopping list created.");
    await loadShoppingLists(false);
    window.location.hash = "#/shopping-lists";
  } catch (error) {
    if (!handlePossiblyStaleSession(error)) {
      setFeedback("error", `Could not create shopping list: ${error.message}`);
    }
  } finally {
    state.shoppingListLoading = false;
    render();
  }
}

export async function handleSubmitShoppingListUpdate(event, deps) {
  const {
    state,
    render,
    setFeedback,
    ensureAuthenticated,
    updateShoppingList,
    loadShoppingListDetail,
    handlePossiblyStaleSession,
  } = deps;

  event.preventDefault();
  if (!ensureAuthenticated("updating shopping lists")) return;
  if (!state.selectedShoppingListId) {
    setFeedback("error", "No shopping list selected.");
    render();
    return;
  }

  const formData = new FormData(event.target);
  const payload = {
    name: (formData.get("name") || "").toString().trim(),
    status: (formData.get("status") || "active").toString(),
  };

  if (!payload.name) {
    setFeedback("error", "List name is required.");
    render();
    return;
  }

  state.shoppingListDetailForm = { ...payload };

  try {
    state.shoppingListLoading = true;
    setFeedback("notice", "Saving shopping list...");
    render();
    await updateShoppingList(state.selectedShoppingListId, payload);
    setFeedback("success", "Shopping list updated.");
    await Promise.all([loadShoppingListDetail(state.selectedShoppingListId, false), deps.loadShoppingLists(false)]);
  } catch (error) {
    if (!handlePossiblyStaleSession(error)) {
      setFeedback("error", `Could not update shopping list: ${error.message}`);
    }
  } finally {
    state.shoppingListLoading = false;
    render();
  }
}

export async function handleDeleteShoppingList(event, deps) {
  const {
    state,
    render,
    setFeedback,
    ensureAuthenticated,
    deleteShoppingList,
    loadShoppingLists,
    handlePossiblyStaleSession,
  } = deps;

  event.preventDefault();
  if (!ensureAuthenticated("deleting shopping lists")) return;
  if (!state.selectedShoppingListId) return;

  if (!window.confirm("Delete this shopping list? This cannot be undone.")) return;

  try {
    state.shoppingListLoading = true;
    setFeedback("notice", "Deleting shopping list...");
    render();
    await deleteShoppingList(state.selectedShoppingListId);
    state.selectedShoppingListId = "";
    state.selectedShoppingList = null;
    state.shoppingListItems = [];
    await loadShoppingLists(false);
    window.location.hash = "#/shopping-lists";
    setFeedback("success", "Shopping list deleted.");
  } catch (error) {
    if (!handlePossiblyStaleSession(error)) {
      setFeedback("error", `Could not delete shopping list: ${error.message}`);
    }
  } finally {
    state.shoppingListLoading = false;
    render();
  }
}

export async function handleSubmitShoppingListItem(event, deps) {
  const {
    state,
    render,
    setFeedback,
    ensureAuthenticated,
    createShoppingListItem,
    defaultShoppingListItemForm,
    loadShoppingListItems,
    loadShoppingListDetail,
    handlePossiblyStaleSession,
  } = deps;

  event.preventDefault();
  if (!ensureAuthenticated("adding shopping list items")) return;
  if (!state.selectedShoppingListId) return;

  const formData = new FormData(event.target);
  const { payload, error } = parseShoppingListItemForm(formData);
  state.shoppingListItemForm = {
    ingredient_id: payload.ingredient_id || "",
    item_name: payload.item_name || "",
    quantity: payload.quantity ?? "",
    unit: payload.unit || "",
    note: payload.note || "",
    source_type: payload.source_type || "manual",
  };

  if (error) {
    setFeedback("error", error);
    render();
    return;
  }

  try {
    state.shoppingListLoading = true;
    setFeedback("notice", "Adding item...");
    render();
    await createShoppingListItem(state.selectedShoppingListId, payload);
    state.shoppingListItemForm = defaultShoppingListItemForm();
    setFeedback("success", "Item added.");
    await Promise.all([loadShoppingListItems(state.selectedShoppingListId, false), loadShoppingListDetail(state.selectedShoppingListId, false)]);
  } catch (errorObj) {
    if (!handlePossiblyStaleSession(errorObj)) {
      setFeedback("error", `Could not add item: ${errorObj.message}`);
    }
  } finally {
    state.shoppingListLoading = false;
    render();
  }
}

export async function handleSubmitShoppingListItemUpdate(event, deps) {
  const {
    state,
    render,
    setFeedback,
    ensureAuthenticated,
    updateShoppingListItem,
    loadShoppingListItems,
    loadShoppingListDetail,
    handlePossiblyStaleSession,
  } = deps;

  event.preventDefault();
  if (!ensureAuthenticated("updating shopping list items")) return;

  const itemId = event.currentTarget.getAttribute("data-item-id");
  if (!itemId) return;

  const formData = new FormData(event.currentTarget);
  const { payload, error } = parseShoppingListItemForm(formData);
  if (error) {
    setFeedback("error", error);
    render();
    return;
  }

  try {
    state.shoppingListLoading = true;
    setFeedback("notice", "Saving item...");
    render();
    await updateShoppingListItem(itemId, payload);
    state.shoppingListEditingItemId = "";
    setFeedback("success", "Item updated.");
    await Promise.all([loadShoppingListItems(state.selectedShoppingListId, false), loadShoppingListDetail(state.selectedShoppingListId, false)]);
  } catch (errorObj) {
    if (!handlePossiblyStaleSession(errorObj)) {
      setFeedback("error", `Could not update item: ${errorObj.message}`);
    }
  } finally {
    state.shoppingListLoading = false;
    render();
  }
}

export async function handleToggleShoppingListItem(event, deps) {
  const { state, render, setFeedback, updateShoppingListItem, loadShoppingListItems, loadShoppingListDetail, handlePossiblyStaleSession } = deps;
  const itemId = event.currentTarget.getAttribute("data-item-id");
  const isChecked = event.currentTarget.getAttribute("data-is-checked") === "true";
  if (!itemId) return;

  try {
    await updateShoppingListItem(itemId, { is_checked: !isChecked });
    await Promise.all([loadShoppingListItems(state.selectedShoppingListId, false), loadShoppingListDetail(state.selectedShoppingListId, false)]);
    setFeedback("success", !isChecked ? "Item ticked off." : "Item unticked.");
  } catch (error) {
    if (!handlePossiblyStaleSession(error)) {
      setFeedback("error", `Could not update item: ${error.message}`);
    }
  }
  render();
}

export async function handleDeleteShoppingListItem(event, deps) {
  const { state, render, setFeedback, deleteShoppingListItem, loadShoppingListItems, loadShoppingListDetail, handlePossiblyStaleSession } = deps;
  const itemId = event.currentTarget.getAttribute("data-item-id");
  if (!itemId) return;

  if (!window.confirm("Delete this item?")) return;

  try {
    await deleteShoppingListItem(itemId);
    await Promise.all([loadShoppingListItems(state.selectedShoppingListId, false), loadShoppingListDetail(state.selectedShoppingListId, false)]);
    setFeedback("success", "Item deleted.");
  } catch (error) {
    if (!handlePossiblyStaleSession(error)) {
      setFeedback("error", `Could not delete item: ${error.message}`);
    }
  }
  render();
}

export function handleStartShoppingListItemEdit(event, deps) {
  const { state, render } = deps;
  state.shoppingListEditingItemId = event.currentTarget.getAttribute("data-item-id") || "";
  render();
}

export function handleCancelShoppingListItemEdit(deps) {
  const { state, render } = deps;
  state.shoppingListEditingItemId = "";
  render();
}
