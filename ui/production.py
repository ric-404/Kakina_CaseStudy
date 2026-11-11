"""Terminal screen for recording chocolate production."""

from ui.display import heading, section, show_table, show_summary, qty_text
from ui.inputs import ask_date, intask, amountask, ask_optional, confirm
from ui.catalog import inventory, show_ingredients
from ui.navigation import run_section, saved, cancelled, info


def produce_chocolates(api, unused):
    heading('Produce chocolates', 'Weigh actual ingredients, then count finished products.')
    products = inventory(api)
    if not products:
        return info('No active products. Add one in function 3.')

    product_ids = {product['id'] for product in products}
    product_id = intask('Product ID', allowed=product_ids)
    product = api.call('GET', f'/api/products/{product_id}')

    if not product['recipe']:
        return info('Create a recipe for this product in function 3 first.')

    production_date = ask_date('Production date')
    ingredients = {}
    for ingredient in show_ingredients(api):
        ingredients[ingredient['id']] = ingredient

    used = []
    for recipe_item in product['recipe']:
        ingredient = ingredients.get(recipe_item['ingredient_id'])
        if ingredient is None:
            return info('A recipe ingredient is archived. Correct the recipe first.')

        section(f"Ingredient: {ingredient['name']}",
                f"In stock: {qty_text(ingredient['quantity'])} {ingredient['unit']}")

        if ingredient['quantity'] <= 0:
            return info('No ingredient stock available for this production run.')

        quantity = amountask(f"Actual amount used ({ingredient['unit']})",
                             ingredient['unit'], maximum=ingredient['quantity'])
        used.append({'ingredient_id': ingredient['id'], 'quantity': quantity})

    section('Finished products')
    finished = intask('Actual finished products counted')
    note = ask_optional('Production note (optional)')

    show_summary('Confirm production', [
        ('Product', product['name']),
        ('Date', production_date),
        ('Finished units', finished),
    ])

    table_rows = []
    for item in used:
        ingredient = ingredients[item['ingredient_id']]
        amount = f"{qty_text(item['quantity'])} {ingredient['unit']}"
        table_rows.append((ingredient['name'], amount))
    show_table(['Ingredient', 'Actual amount'], table_rows, 'INGREDIENTS TO DEDUCT')

    if not confirm('Deduct ingredients and add finished stock?'):
        return cancelled()

    result = api.call('POST', '/api/production', {
        'date': production_date,
        'product_id': product_id,
        'ingredients_used': used,
        'finished_quantity': finished,
        'note': note,
    })
    return saved(f"Production #{result['id']} saved: {finished} finished units added.")


def production_menu(api):
    def show_current_stock():
        return inventory(api)

    def record_production(items):
        return produce_chocolates(api, items)

    run_section('Produce chocolates', 'Repeat production runs without returning home.',
                show_current_stock, [('produce', 'Record a new production run')],
                {'produce': record_production})
