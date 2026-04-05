import {
  ApiError,
  createIngredient,
  createRecipe,
  createShoppingList,
  createShoppingListItem,
  createUserFoodEntry,
  createUserStorecupboardItem,
  deleteIngredient,
  deleteRecipe,
  deleteShoppingList,
  deleteShoppingListItem,
  deleteUserStorecupboardItem,
  getCurrentUser,
  loginWithEmail,
  updateIngredient,
  updateRecipe,
  updateShoppingList,
  updateShoppingListItem,
  updateUserStorecupboardItem,
} from "./api.js";

import { handleSubmitLogin, handleLogout } from "./handlers/authHandlers.js";
import { handleSubmitFoodEntry } from "./handlers/foodHandlers.js";
import {
  handleCancelCupboardEdit,
  handleDeleteCupboardItem,
  handleStartCupboardEdit,
  handleSubmitCupboardItem,
  handleSubmitCupboardUpdate,
} from "./handlers/cupboardHandlers.js";
import {
  handleDeleteIngredient,
  handleSubmitIngredient,
  handleSubmitIngredientUpdate,
} from "./handlers/ingredientHandlers.js";
import {
  handleDeleteRecipe,
  handleSubmitRecipe,
  handleSubmitRecipeUpdate,
} from "./handlers/recipeHandlers.js";
import {
  handleDeleteShoppingList,
  handleDeleteShoppingListItem,
  handleStartShoppingListItemEdit,
  handleCancelShoppingListItemEdit,
  handleSubmitShoppingList,
  handleSubmitShoppingListItem,
  handleSubmitShoppingListItemUpdate,
  handleSubmitShoppingListUpdate,
  handleToggleShoppingListItem,
} from "./handlers/shoppingHandlers.js";

import {
  defaultCupboardForm,
  defaultFoodForm,
  defaultIngredientForm,
  defaultRecipeForm,
  defaultShoppingListForm,
  defaultShoppingListItemForm,
} from "./constants.js";
import { clearStoredAccessToken, storeAccessToken, storeCurrentUser } from "./storage.js";
import { currentUserId, ensureAuthenticated, getLoginErrorMessage } from "./helpers.js";

export function createActions({
  state,
  render,
  setFeedback,
  clearLocalSession,
  handlePossiblyStaleSession,
  loaders,
}) {
  async function onSubmitLogin(event) {
    await handleSubmitLogin(event, {
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
      loadFoodEntries: loaders.loadFoodEntries,
      loadCupboardItems: loaders.loadCupboardItems,
      loadRecipes: loaders.loadRecipes,
      loadShoppingLists: loaders.loadShoppingLists,
    });
  }

  async function onSubmitFoodEntry(event) {
    await handleSubmitFoodEntry(event, {
      state,
      render,
      setFeedback,
      ensureAuthenticated: (label) => ensureAuthenticated(state, render, setFeedback, label),
      currentUserId: () => currentUserId(state),
      createUserFoodEntry,
      defaultFoodForm,
      loadFoodEntries: loaders.loadFoodEntries,
      handlePossiblyStaleSession,
    });
  }

  async function onSubmitCupboardItem(event) {
    await handleSubmitCupboardItem(event, {
      state,
      render,
      setFeedback,
      ensureAuthenticated: (label) => ensureAuthenticated(state, render, setFeedback, label),
      currentUserId: () => currentUserId(state),
      createUserStorecupboardItem,
      defaultCupboardForm,
      loadCupboardItems: loaders.loadCupboardItems,
      handlePossiblyStaleSession,
    });
  }

  async function onSubmitCupboardUpdate(event) {
    await handleSubmitCupboardUpdate(event, {
      state,
      render,
      setFeedback,
      ensureAuthenticated: (label) => ensureAuthenticated(state, render, setFeedback, label),
      currentUserId: () => currentUserId(state),
      updateUserStorecupboardItem,
      loadCupboardItems: loaders.loadCupboardItems,
      handlePossiblyStaleSession,
    });
  }

  async function onDeleteCupboardItem(event) {
    await handleDeleteCupboardItem(event, {
      state,
      render,
      setFeedback,
      ensureAuthenticated: (label) => ensureAuthenticated(state, render, setFeedback, label),
      currentUserId: () => currentUserId(state),
      deleteUserStorecupboardItem,
      loadCupboardItems: loaders.loadCupboardItems,
      handlePossiblyStaleSession,
    });
  }

  async function onSubmitIngredient(event) {
    await handleSubmitIngredient(event, {
      state,
      render,
      setFeedback,
      ensureAuthenticated: (label) => ensureAuthenticated(state, render, setFeedback, label),
      createIngredient,
      defaultIngredientForm,
      loadIngredients: loaders.loadIngredients,
      handlePossiblyStaleSession,
    });
  }

  async function onSubmitIngredientUpdate(event) {
    await handleSubmitIngredientUpdate(event, {
      state,
      render,
      setFeedback,
      ensureAuthenticated: (label) => ensureAuthenticated(state, render, setFeedback, label),
      updateIngredient,
      loadIngredientById: loaders.loadIngredientById,
      handlePossiblyStaleSession,
    });
  }

  async function onDeleteIngredient(event) {
    await handleDeleteIngredient(event, {
      state,
      render,
      setFeedback,
      ensureAuthenticated: (label) => ensureAuthenticated(state, render, setFeedback, label),
      deleteIngredient,
      loadIngredients: loaders.loadIngredients,
      handlePossiblyStaleSession,
    });
  }

  async function onSubmitRecipe(event) {
    await handleSubmitRecipe(event, {
      state,
      render,
      setFeedback,
      ensureAuthenticated: (label) => ensureAuthenticated(state, render, setFeedback, label),
      currentUserId: () => currentUserId(state),
      createRecipe,
      defaultRecipeForm,
      loadRecipes: loaders.loadRecipes,
      handlePossiblyStaleSession,
    });
  }

  async function onSubmitRecipeUpdate(event) {
    await handleSubmitRecipeUpdate(event, {
      state,
      render,
      setFeedback,
      ensureAuthenticated: (label) => ensureAuthenticated(state, render, setFeedback, label),
      updateRecipe,
      loadRecipeById: loaders.loadRecipeById,
      handlePossiblyStaleSession,
    });
  }

  async function onDeleteRecipe(event) {
    await handleDeleteRecipe(event, {
      state,
      render,
      setFeedback,
      ensureAuthenticated: (label) => ensureAuthenticated(state, render, setFeedback, label),
      deleteRecipe,
      loadRecipes: loaders.loadRecipes,
      handlePossiblyStaleSession,
    });
  }

  async function onSubmitShoppingList(event) {
    await handleSubmitShoppingList(event, {
      state,
      render,
      setFeedback,
      ensureAuthenticated: (label) => ensureAuthenticated(state, render, setFeedback, label),
      currentUserId: () => currentUserId(state),
      createShoppingList,
      defaultShoppingListForm,
      loadShoppingLists: loaders.loadShoppingLists,
      handlePossiblyStaleSession,
    });
  }

  async function onSubmitShoppingListUpdate(event) {
    await handleSubmitShoppingListUpdate(event, {
      state,
      render,
      setFeedback,
      ensureAuthenticated: (label) => ensureAuthenticated(state, render, setFeedback, label),
      updateShoppingList,
      loadShoppingListDetail: loaders.loadShoppingListDetail,
      loadShoppingLists: loaders.loadShoppingLists,
      handlePossiblyStaleSession,
    });
  }

  async function onDeleteShoppingList(event) {
    await handleDeleteShoppingList(event, {
      state,
      render,
      setFeedback,
      ensureAuthenticated: (label) => ensureAuthenticated(state, render, setFeedback, label),
      deleteShoppingList,
      loadShoppingLists: loaders.loadShoppingLists,
      handlePossiblyStaleSession,
    });
  }

  async function onSubmitShoppingListItem(event) {
    await handleSubmitShoppingListItem(event, {
      state,
      render,
      setFeedback,
      ensureAuthenticated: (label) => ensureAuthenticated(state, render, setFeedback, label),
      createShoppingListItem,
      defaultShoppingListItemForm,
      loadShoppingListItems: loaders.loadShoppingListItems,
      loadShoppingListDetail: loaders.loadShoppingListDetail,
      handlePossiblyStaleSession,
    });
  }

  async function onSubmitShoppingListItemUpdate(event) {
    await handleSubmitShoppingListItemUpdate(event, {
      state,
      render,
      setFeedback,
      ensureAuthenticated: (label) => ensureAuthenticated(state, render, setFeedback, label),
      updateShoppingListItem,
      loadShoppingListItems: loaders.loadShoppingListItems,
      loadShoppingListDetail: loaders.loadShoppingListDetail,
      handlePossiblyStaleSession,
    });
  }

  async function onToggleShoppingListItem(event) {
    await handleToggleShoppingListItem(event, {
      state,
      render,
      setFeedback,
      updateShoppingListItem,
      loadShoppingListItems: loaders.loadShoppingListItems,
      loadShoppingListDetail: loaders.loadShoppingListDetail,
      handlePossiblyStaleSession,
    });
  }

  async function onDeleteShoppingListItem(event) {
    await handleDeleteShoppingListItem(event, {
      state,
      render,
      setFeedback,
      deleteShoppingListItem,
      loadShoppingListItems: loaders.loadShoppingListItems,
      loadShoppingListDetail: loaders.loadShoppingListDetail,
      handlePossiblyStaleSession,
    });
  }

  function onStartShoppingListItemEdit(event) {
    handleStartShoppingListItemEdit(event, { state, render });
  }

  function onCancelShoppingListItemEdit() {
    handleCancelShoppingListItemEdit({ state, render });
  }

  function onLogout() {
    handleLogout({ clearLocalSession, setFeedback, render });
  }

  function onStartCupboardEdit(event) {
    handleStartCupboardEdit(event, { state, render });
  }

  function onCancelCupboardEdit() {
    handleCancelCupboardEdit({ state, render });
  }

  return {
    onSubmitLogin,
    onSubmitFoodEntry,
    onSubmitCupboardItem,
    onSubmitCupboardUpdate,
    onDeleteCupboardItem,
    onSubmitIngredient,
    onSubmitIngredientUpdate,
    onDeleteIngredient,
    onSubmitRecipe,
    onSubmitRecipeUpdate,
    onDeleteRecipe,
    onSubmitShoppingList,
    onSubmitShoppingListUpdate,
    onDeleteShoppingList,
    onSubmitShoppingListItem,
    onSubmitShoppingListItemUpdate,
    onToggleShoppingListItem,
    onDeleteShoppingListItem,
    onStartShoppingListItemEdit,
    onCancelShoppingListItemEdit,
    onLogout,
    onStartCupboardEdit,
    onCancelCupboardEdit,
  };
}