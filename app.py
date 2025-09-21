# app.py
from flask import Flask, render_template, request, jsonify
import json
from expert_system import find_recipes # Importamos nuestra función modificada

app = Flask(__name__)

# Función para cargar los datos desde los JSON
def load_data():
    with open('data/ingredients.json', 'r') as f:
        ingredients = json.load(f)
    with open('data/rules.json', 'r') as f:
        # Extraemos todos los nombres de recetas para el selector de "recetas hechas"
        all_recipes = [rule['name'] for rule in json.load(f)]
    with open('data/recipe_details.json', 'r') as f:
        recipe_details = json.load(f)
    return ingredients, all_recipes, recipe_details

# Ruta principal que maneja tanto la carga inicial (GET) como el envío del formulario (POST)
@app.route('/', methods=['GET', 'POST'])
def index():
    ingredients_data, all_recipes, _ = load_data()
    results = None
    
   
    selected_data = {
        'ingredients': [],
        'category': '',
        'time': '',
        'made_recipes': []
    }
    
    if request.method == 'POST':
        # Obtenemos los datos del formulario y actualizamos el diccionario
        selected_data['ingredients'] = request.form.getlist('ingredients')
        selected_data['category'] = request.form.get('category')
        selected_data['time'] = request.form.get('time', '')
        selected_data['made_recipes'] = request.form.getlist('made_recipes')

        # El tiempo para el motor de inferencia sí necesita ser un número
        time_for_engine = int(selected_data['time']) if selected_data['time'] else None

        results = find_recipes(
            ingredients=selected_data['ingredients'],
            made_recipes=selected_data['made_recipes'],
            category=selected_data['category'],
            time=time_for_engine
        )

    return render_template(
        'index.html',
        ingredients_data=ingredients_data,
        all_recipes=all_recipes,
        results=results,
        selected_data=selected_data
    )

# Ruta de API para obtener los detalles de una receta específica (usada por JavaScript)
@app.route('/recipe_details/<recipe_name>')
def get_recipe_details(recipe_name):
    _, _, recipe_details = load_data()
    details = recipe_details.get(recipe_name, None)
    if details:
        return jsonify(details)
    return jsonify({"error": "Recipe not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)