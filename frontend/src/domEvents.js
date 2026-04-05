export function attachEvents({ state, render, actions }) {
  document.querySelector("#logout")?.addEventListener("click", actions.onLogout);
  document.querySelector("#logout-inline")?.addEventListener("click", actions.onLogout);

  document.querySelector("#login-form")?.addEventListener("submit", actions.onSubmitLogin);
  document.querySelector("#food-form")?.addEventListener("submit", actions.onSubmitFoodEntry);
  document.querySelector("#cupboard-form")?.addEventListener("submit", actions.onSubmitCupboardItem);
  document.querySelector("#ingredient-form")?.addEventListener("submit", actions.onSubmitIngredient);
  document.querySelector("#ingredient-detail-form")?.addEventListener("submit", actions.onSubmitIngredientUpdate);
  document.querySelector("#recipe-form")?.addEventListener("submit", actions.onSubmitRecipe);
  document.querySelector("#recipe-detail-form")?.addEventListener("submit", actions.onSubmitRecipeUpdate);
  document.querySelector("#shopping-list-form")?.addEventListener("submit", actions.onSubmitShoppingList);
  document.querySelector("#shopping-list-detail-form")?.addEventListener("submit", actions.onSubmitShoppingListUpdate);
  document.querySelector("#shopping-list-item-form")?.addEventListener("submit", actions.onSubmitShoppingListItem);

  document.querySelector("#delete-ingredient")?.addEventListener("click", actions.onDeleteIngredient);
  document.querySelector("#delete-recipe")?.addEventListener("click", actions.onDeleteRecipe);
  document.querySelector("#delete-shopping-list")?.addEventListener("click", actions.onDeleteShoppingList);

  document.querySelectorAll(".cupboard-edit").forEach((button) => {
    button.addEventListener("click", actions.onStartCupboardEdit);
  });

  document.querySelectorAll(".cupboard-cancel-edit").forEach((button) => {
    button.addEventListener("click", actions.onCancelCupboardEdit);
  });

  document.querySelectorAll(".cupboard-update-form").forEach((form) => {
    form.addEventListener("submit", actions.onSubmitCupboardUpdate);
  });

  document.querySelectorAll(".cupboard-delete").forEach((button) => {
    button.addEventListener("click", actions.onDeleteCupboardItem);
  });

  document.querySelectorAll(".shopping-item-toggle").forEach((button) => {
    button.addEventListener("click", actions.onToggleShoppingListItem);
  });

  document.querySelectorAll(".shopping-item-edit").forEach((button) => {
    button.addEventListener("click", actions.onStartShoppingListItemEdit);
  });

  document.querySelectorAll(".shopping-item-cancel-edit").forEach((button) => {
    button.addEventListener("click", actions.onCancelShoppingListItemEdit);
  });

  document.querySelectorAll(".shopping-item-update-form").forEach((form) => {
    form.addEventListener("submit", actions.onSubmitShoppingListItemUpdate);
  });

  document.querySelectorAll(".shopping-item-delete").forEach((button) => {
    button.addEventListener("click", actions.onDeleteShoppingListItem);
  });

  const cupboardSearch = document.querySelector("#cupboard-search");
  if (cupboardSearch) {
    cupboardSearch.addEventListener("input", (event) => {
      state.cupboardQuery = event.target.value;
      render();
    });
  }

  const cupboardSort = document.querySelector("#cupboard-sort");
  if (cupboardSort) {
    cupboardSort.addEventListener("change", (event) => {
      state.cupboardSort = event.target.value;
      render();
    });
  }
}