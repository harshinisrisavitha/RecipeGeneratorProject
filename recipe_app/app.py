from flask import Flask, render_template, request, redirect
from db_config import get_connection

app = Flask(__name__)

@app.route('/')
def index():
    return redirect('/preferences')

@app.route('/preferences', methods=['GET', 'POST'])
def preferences():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM Dietary_Restrictions")
    restrictions = cursor.fetchall()

    if request.method == 'POST':
        selected_restrictions = request.form.getlist('restriction')
        selected_meal = request.form.get('meal_type')
        return redirect(f'/ingredients?meal_type={selected_meal}&restrictions={",".join(selected_restrictions)}')

    return render_template('preferences.html', restrictions=restrictions)

@app.route('/ingredients', methods=['GET', 'POST'])
def ingredients():
    meal_type = request.args.get('meal_type')
    restrictions = request.args.get('restrictions')

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Ingredients")
    ingredients = cursor.fetchall()

    if request.method == 'POST':
        selected_ingredients = request.form.getlist('ingredient')
        return redirect(f'/results?meal_type={meal_type}&restrictions={restrictions}&ingredients={",".join(selected_ingredients)}')

    return render_template('ingredients.html', ingredients=ingredients)

@app.route('/results')
def results():
    meal_type = request.args.get('meal_type')
    restrictions = request.args.get('restrictions').split(',')
    ingredients = request.args.get('ingredients').split(',')

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    restriction_filters = []
    if '1' in restrictions:
        restriction_filters.append("is_vegan = 1")
    if '2' in restrictions:
        restriction_filters.append("is_vegetarian = 1")

    filters = " AND ".join(restriction_filters)
    sql = f"SELECT * FROM Recipes WHERE meal_type = %s"
    if filters:
        sql += f" AND {filters}"

    cursor.execute(sql, (meal_type,))
    all_recipes = cursor.fetchall()

    # Filter by ingredients (must contain at least 1 selected ingredient)
    final_recipes = []
    for recipe in all_recipes:
        cursor.execute("""
            SELECT i.ingredient_id
            FROM Recipe_Ingredients ri
            JOIN Ingredients i ON ri.ingredient_id = i.ingredient_id
            WHERE ri.recipe_id = %s
        """, (recipe['recipe_id'],))
        ing_ids = [str(i['ingredient_id']) for i in cursor.fetchall()]
        if set(ingredients) & set(ing_ids):
            final_recipes.append(recipe)

    return render_template('results.html', recipes=final_recipes)

@app.route('/recipe/<int:recipe_id>')
def recipe_detail(recipe_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM Recipes WHERE recipe_id = %s", (recipe_id,))
    recipe = cursor.fetchone()

    cursor.execute("""
        SELECT i.name, ri.quantity, ri.unit
        FROM Recipe_Ingredients ri
        JOIN Ingredients i ON ri.ingredient_id = i.ingredient_id
        WHERE ri.recipe_id = %s
    """, (recipe_id,))
    ingredients = cursor.fetchall()

    cursor.execute("SELECT * FROM Steps WHERE recipe_id = %s ORDER BY step_number", (recipe_id,))
    steps = cursor.fetchall()

    return render_template('recipe_detail.html', recipe=recipe, ingredients=ingredients, steps=steps)

if __name__ == '__main__':
    app.run(debug=True)
