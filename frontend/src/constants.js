import {
  BookOpen,
  ClipboardList,
  CookingPot,
  Home,
  PlusCircle,
  ScrollText,
  Soup,
  SquarePlus,
  UtensilsCrossed,
} from "https://esm.sh/lucide-react@0.469.0?deps=react@18.3.1";

export const mealTimeOptions = ["am", "breakfast", "lunch", "pm", "dinner", "evening", "snack", "late_night"];
export const inputMethodOptions = ["text", "voice", "imported"];
export const stockStatusOptions = ["in_stock", "low", "out_of_stock"];

export const ROUTE_META = [
  { route: "dashboard", label: "Dashboard", icon: Home },
  { route: "log-food", label: "Log food", icon: UtensilsCrossed },
  { route: "entries", label: "Food entries", icon: ClipboardList },
  { route: "cupboard", label: "Cupboard", icon: CookingPot },
  { route: "add-cupboard-item", label: "Add cupboard item", icon: PlusCircle },
  { route: "add-ingredient", label: "Add ingredient", icon: SquarePlus },
  { route: "ingredients", label: "Ingredients list", icon: Soup },
  { route: "recipes", label: "Recipes", icon: BookOpen },
  { route: "shopping-lists", label: "Shopping", icon: ClipboardList },
  { route: "add-recipe", label: "Add recipe", icon: ScrollText },
];

export const PRIMARY_TAB_ROUTES = ["dashboard", "ingredients", "cupboard", "shopping-lists", "recipes"];

export const PAGE_META = {
  dashboard: { title: "Dashboard", subtitle: "Track meals, cupboard stock, and recipes in one place." },
  login: { title: "Login", subtitle: "Sign in to access your synced Cupboard Chef data." },
  profile: { title: "Profile", subtitle: "View your current session and API connection status." },
  "log-food": { title: "Log food", subtitle: "Capture what you ate in seconds." },
  entries: { title: "Food entries", subtitle: "Review your recent meal logs." },
  cupboard: { title: "Cupboard", subtitle: "Keep your ingredients and stock levels up to date." },
  "add-cupboard-item": { title: "Add cupboard item", subtitle: "Add an ingredient to your cupboard inventory." },
  "add-ingredient": { title: "Add ingredient", subtitle: "Create a reusable ingredient in your catalog." },
  ingredients: { title: "Ingredients", subtitle: "Browse and edit your ingredient catalog." },
  "ingredient-detail": { title: "Ingredient detail", subtitle: "Update ingredient information." },
  recipes: { title: "Recipes", subtitle: "Browse and manage saved recipes." },
  "add-recipe": { title: "Add recipe", subtitle: "Create a new recipe for your collection." },
  "recipe-detail": { title: "Recipe detail", subtitle: "Edit recipe information and instructions." },
  "shopping-lists": { title: "Shopping lists", subtitle: "Plan your next shop and tick items off as you go." },
  "add-shopping-list": { title: "Add shopping list", subtitle: "Create a new shopping list for an upcoming shop." },
  "shopping-list-detail": { title: "Shopping list detail", subtitle: "Manage list details and item checklist." },
};

export const AUTH_STORAGE_KEYS = [
  "cupboard_chef_access_token",
  "access_token",
  "auth_token",
  "token",
];

export const USER_STORAGE_KEYS = {
  userId: "cupboard_chef_user_id",
  email: "cupboard_chef_email",
  displayName: "cupboard_chef_display_name",
};

export const defaultFoodForm = () => ({
  description: "",
  raw_input: "",
  input_method: "text",
  meal_time: "",
  rating: "",
});

export const defaultCupboardForm = () => ({
  ingredient_id: "",
  quantity: "",
  unit: "",
  stock_status: "in_stock",
  shelf_name: "",
  best_before_date: "",
  next_reminder_at: "",
});

export const defaultIngredientForm = () => ({
  canonical_name: "",
  display_name: "",
  category: "veg",
  is_seasonal: false,
  seasonal_months: "",
});

export const defaultRecipeForm = () => ({
  title: "",
  description: "",
  instructions: "",
  source_url: "",
  is_system: false,
});

export const defaultShoppingListForm = () => ({
  name: "",
  status: "active",
});

export const defaultShoppingListItemForm = () => ({
  ingredient_id: "",
  item_name: "",
  quantity: "",
  unit: "",
  note: "",
  source_type: "manual",
});