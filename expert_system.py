import json
from experta import *

# --- Definition of the Facts used by the system ---

class Condition(Fact):
    """Fact to represent any condition of a recipe."""
    pass

class Ingredient(Fact):
    """Fact to represent the ingredients the user has."""
    pass

class SuggestedRecipe(Fact):
    """Fact to store recipes that can be prepared."""
    pass

# --- Expert System Engine ---

class RecipeEngine(KnowledgeEngine):
    def __init__(self, rules_path):
        super().__init__()
        self.rules = self.load_rules(rules_path)
        self.possible_recipes = []
        self.nearly_possible_recipes = {}

    def load_rules(self, path):
        """Loads the rules from the JSON file."""
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    @DefFacts()
    def _initial_action(self):
        """Declares an initial fact to trigger the rule loading."""
        yield Fact(action="find_recipes")

    @Rule(Fact(action='find_recipes'), NOT(Condition()))
    def transform_rules_to_facts(self):
        """Reads the rules from the JSON and converts them into facts that Experta understands."""
        for rule in self.rules:
            name = rule['name']
            for type, value in rule['conditions'].items():
                if isinstance(value, list): 
                    for item in value:
                        self.declare(Condition(recipe=name, type=type, value=item))
                else: 
                    self.declare(Condition(recipe=name, type=type, value=value))

    # Main rule that checks if a recipe can be prepared
    @Rule(salience=1) # Higher priority to execute first
    def can_prepare_recipe(self):
        """
        This rule is dynamic. It iterates over all recipes and checks if all
        their conditions are met by the current facts.
        """
        current_facts = self.facts
        
        available_ingredients = {f['name'] for f in current_facts.values() if isinstance(f, Ingredient)}
        prepared_recipes = {f['name'] for f in current_facts.values() if isinstance(f, SuggestedRecipe)}
        
        available_time = next((f['available'] for f in current_facts.values() if isinstance(f, Fact) and 'available' in f), None)
        desired_category = next((f['category'] for f in current_facts.values() if isinstance(f, Fact) and 'category' in f), None)

        for recipe in self.rules:
            recipe_name = recipe['name']
            if recipe_name in self.possible_recipes:
                continue # We already know this one can be made

            conditions = recipe['conditions']
            missing = {'ingredients': [], 'recipes': []}
            is_met = True

            # 1. Validate ingredients
            if 'ingredients' in conditions:
                for ing in conditions['ingredients']:
                    if ing not in available_ingredients:
                        is_met = False
                        missing['ingredients'].append(ing)
            
            # 2. Validate sub-recipes
            if 'recipes' in conditions:
                for sub_recipe in conditions['recipes']:
                    if sub_recipe not in self.possible_recipes and sub_recipe not in prepared_recipes:
                        is_met = False
                        missing['recipes'].append(sub_recipe)

            # 3. Validate time (optional)
            if available_time and 'time' in conditions:
                if conditions['time'] > available_time:
                    is_met = False
            
            # 4. Validate category (optional)
            if desired_category and 'category' in conditions:
                if conditions['category'] != desired_category:
                    is_met = False

            if is_met:
                if recipe_name not in self.possible_recipes:
                    self.possible_recipes.append(recipe_name)
                    self.declare(SuggestedRecipe(name=recipe_name))
            elif any(missing.values()):
                self.nearly_possible_recipes[recipe_name] = missing




def find_recipes(ingredients, made_recipes=None, category=None, time=None):
    """
    Initializes the engine, declares initial facts, and RETURNS the results.
    """
    engine = RecipeEngine('data/rules.json') # Asegúrate que la ruta sea correcta
    engine.reset()

    # ... (El código para declarar hechos es el mismo) ...
    for ingredient in ingredients:
        engine.declare(Ingredient(name=ingredient))
    if made_recipes:
        for recipe in made_recipes:
            engine.declare(SuggestedRecipe(name=recipe))
    if category:
        engine.declare(Fact(category=category))
    if time:
        engine.declare(Fact(available=time))

    engine.run()

    initial_recipes = set(made_recipes or [])
    new_recipes = [r for r in engine.possible_recipes if r not in initial_recipes]

    nearly_possible_filtered = {}
    if engine.nearly_possible_recipes:
        for recipe, missing in engine.nearly_possible_recipes.items():
            
            if recipe not in engine.possible_recipes and recipe not in initial_recipes:
                
               
                num_missing_ingredients = len(missing.get('ingredients', []))
        
                if 1 <= num_missing_ingredients <= 2:
                    missing_message = []
                    if missing['ingredients']:
                        missing_message.append(f"you are missing: {', '.join(missing['ingredients'])}")
                    if missing['recipes']:
                        missing_message.append(f"you need to prepare: {', '.join(missing['recipes'])}")
                    
                    if missing_message:
                       nearly_possible_filtered[recipe] = ' and '.join(missing_message)

    
    if len(nearly_possible_filtered) > 4:
        
        nearly_possible_filtered = dict(list(nearly_possible_filtered.items())[:4])
    
    
    return {
        "new_recipes": new_recipes,
        "nearly_possible": nearly_possible_filtered
    }