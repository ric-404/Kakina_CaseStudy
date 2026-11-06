"""Chocolate production screen; remains open for multiple production runs."""
from ui.display import heading, section, show_table, show_summary, qty_text
from ui.inputs import ask_date, intask, amountask, ask_optional, confirm
from ui.catalog import inventory, show_ingredients
from ui.navigation import run_section, saved, cancelled, info


def produce_chocolates(api, unused):
    heading('Produce chocolates', 'Weigh actual ingredients, then count finished products.')
    products = inventory(api)
    if not products:
        return info('No active products. Add one in function 3.')

    pid = intask('Product ID', allowed={p['id'] for p in products})
    product = api.call('GET', f'/api/products/{pid}')
    if not product['recipe']:
        return info('Create a recipe for this product in function 3 first.')

    day = ask_date('Production date')
    ingredients = {row['id']: row for row in show_ingredients(api)}
    used = []
    for item in product['recipe']:
        row = ingredients.get(item['ingredient_id'])
        if row is None:
            return info('A recipe ingredient is archived. Correct the recipe first.')
        section(f"Ingredient: {row['name']}",
                f"In stock: {qty_text(row['quantity'])} {row['unit']}")
        if row['quantity'] <= 0:
            return info('No ingredient stock available for this production run.')
        amount = amountask(f"Actual amount used ({row['unit']})",
                           row['unit'], maximum=row['quantity'])
        used.append({'ingredient_id': row['id'], 'quantity': amount})

    section('Finished products')
    finished = intask('Actual finished products counted')
    note = ask_optional('Production note (optional)')
    show_summary('Confirm production', [
        ('Product', product['name']), ('Date', day), ('Finished units', finished),
    ])
    show_table(['Ingredient', 'Actual amount'],
               [(ingredients[x['ingredient_id']]['name'],
                 f"{qty_text(x['quantity'])} {ingredients[x['ingredient_id']]['unit']}")
                for x in used], 'INGREDIENTS TO DEDUCT')
    if not confirm('Deduct ingredients and add finished stock?'):
        return cancelled()
    result = api.call('POST', '/api/production', {
        'date': day, 'product_id': pid, 'ingredients_used': used,
        'finished_quantity': finished, 'note': note,
    })
    return saved(f"Production #{result['id']} saved: {finished} finished units added.")


def production_menu(api):
    run_section('Produce chocolates', 'Repeat production runs without returning home.',
                lambda: inventory(api),
                [('produce', 'Record a new production run')],
                {'produce': lambda items: produce_chocolates(api, items)})
