"""Inventory, ingredient/purchase, product and recipe terminal screens."""
from ui.display import (heading, section, show_table, show_summary,
                        notice, warn, pesos, qty_text)
from ui.inputs import (ask, ask_name, ask_optional, ask_date, intask, moneyask,
                       amountask, choose, confirm, action_menu,
                       nonnegative_amount, costask)
from ui.navigation import run_section, saved, cancelled, info


def inventory(api, include_archived=False):
    """Show finished stock, reservations and booth allocations."""
    items = api.call('GET', '/api/inventory')
    show_table(['ID', 'Product', 'Price', 'Stock', 'Booth', 'Reserved', 'Available'],
               [(p['id'], p['name'], pesos(p['price']), p['stock'], p['allocated'],
                 p['reserved'], p['available']) for p in items], 'PRODUCT INVENTORY')
    if include_archived:
        archived = [p for p in api.call('GET', '/api/products') if not p['active']]
        show_table(['ID', 'Archived product'], [(p['id'], p['name']) for p in archived],
                   'ARCHIVED PRODUCTS')
    return items


def inventory_menu(api):
    """Inventory is a view, but users can refresh it without going home."""
    return run_section(
        'Finished product inventory', 'Review physical, reserved and available stocks.',
        lambda: inventory(api), [('refresh', 'Refresh inventory')],
        {'refresh': lambda rows: info('Inventory refreshed.')},
    )


def select_products(api, title, check_stock=False):
    heading(title)
    products = inventory(api)
    allowed = {p['id'] for p in products}
    chosen = []
    if not allowed:
        warn('There are no active products.')
        return []
    section('Select products', 'Enter 0 when you have finished selecting.')
    while True:
        pid = intask('Product ID (0 = done)', minimum=0, allowed=allowed | {0})
        if pid == 0:
            break
        if any(x['product_id'] == pid for x in chosen):
            warn('This product is already selected.')
            continue
        product = next(p for p in products if p['id'] == pid)
        maximum = product['available'] if check_stock else 1_000_000_000
        if maximum == 0:
            warn('No available stock.')
            continue
        quantity = intask('Quantity', maximum=maximum)
        chosen.append({'product_id': pid, 'quantity': quantity})
        notice(f"Added {quantity} x {product['name']} to this selection.")
    return chosen


def show_ingredients(api):
    items = api.call('GET', '/api/ingredients')
    show_table(['ID', 'Ingredient', 'Stock', 'Unit', 'Stock value', 'Cost/unit'],
               [(x['id'], x['name'], qty_text(x['display_quantity']),
                 x['display_unit'], pesos(x['stock_value']),
                 f"₱{x['average_display_cost']:.4f}") for x in items],
               'INGREDIENT INVENTORY')
    return items


def add_ingredient(api, unused):
    heading('Register new ingredient')
    section('Ingredient details')
    name = ask_name('Ingredient name')
    unit = choose('Measurement unit', ['g', 'kg', 'pcs'], 'g')
    if not confirm('Add ingredient to catalog?'):
        return cancelled()
    row = api.call('POST', '/api/ingredients', {'name': name, 'unit': unit})
    return saved(f"Ingredient #{row['id']} created. You can add another ingredient below.")


def purchase_ingredient(api, items):
    heading('Record ingredient purchase')
    if not items:
        return info('Register an ingredient before recording a purchase.')
    show_ingredients(api)
    iid = intask('Ingredient ID', allowed={x['id'] for x in items})
    item = next(x for x in items if x['id'] == iid)
    section('Purchase details')
    if item['unit'] == 'g':
        unit = choose('Purchased quantity measured in', ['g', 'kg'], item['display_unit'])
        entered = amountask(f'Purchased weight ({unit})', unit)
        quantity = entered * 1000 if unit == 'kg' else entered
    else:
        quantity = amountask('Purchased pieces', 'pcs')
    cost = moneyask('Total amount PAID for this purchase (PHP)', allow_zero=False)
    day = ask_date('Purchase date')
    note = ask_optional('Supplier / note (optional)', 300)
    show_summary('Review purchase', [
        ('Ingredient', item['name']),
        ('Quantity added', f"{qty_text(quantity)} {item['unit']}"),
        ('Total paid', pesos(cost)),
    ])
    if not confirm('Save purchase and increase stock?'):
        return cancelled()
    result = api.call('POST', '/api/purchases', {
        'ingredient_id': iid, 'quantity': quantity,
        'total_cost': cost, 'date': day, 'note': note,
    })
    return saved(f"Purchase #{result['id']} recorded. Ingredient stock has been refreshed.")


def edit_ingredient(api, items):
    heading('Edit ingredient')
    if not items:
        return info('Register an ingredient first.')
    show_ingredients(api)
    iid = intask('Ingredient ID to edit', allowed={x['id'] for x in items})
    item = next(x for x in items if x['id'] == iid)
    section('Selected ingredient', item['name'])
    action = action_menu([
        ('name', 'Edit ingredient name'),
        ('unit', 'Change displayed unit (g or kg)'),
        ('quantity', 'Correct ingredient stock'),
        ('cost', 'Edit cost per unit'),
        ('value', 'Edit total stock value'),
    ])
    if action is None:
        return cancelled()

    payload = {}
    if action == 'name':
        payload['name'] = ask('Ingredient name', item['name'])
    elif action == 'unit':
        units = ['pcs'] if item['unit'] == 'pcs' else ['g', 'kg']
        payload['unit'] = choose('Display unit', units, item['display_unit'])
    elif action == 'quantity':
        payload['quantity'] = nonnegative_amount(
            'Correct stock', item['display_unit'], item['display_quantity'])
    elif action == 'cost':
        payload['unit_cost'] = costask(
            f"Cost per {item['display_unit']} (PHP)", item['average_display_cost'])
    elif action == 'value':
        payload['stock_value'] = moneyask('Total stock value (PHP)', item['stock_value'])

    if action in ('quantity', 'cost', 'value'):
        payload['reason'] = ask_name('Reason for stock/value correction', 300)
    if not confirm('Save ingredient changes?'):
        return cancelled()
    updated = api.call('PUT', f'/api/ingredients/{iid}', payload)
    return saved(f"Ingredient #{updated['id']} updated.")


def archive_ingredient(api, items):
    heading('Archive unused ingredient')
    if not items:
        return info('There are no active ingredients.')
    show_ingredients(api)
    iid = intask('Ingredient ID to archive', allowed={x['id'] for x in items})
    warn('Recipe and production usage block archiving. Purchase history is kept.')
    warn('Remaining stock/value will be hidden from active inventory.')
    if not confirm('Archive this ingredient?', default=False):
        return cancelled()
    api.call('DELETE', f'/api/ingredients/{iid}')
    return saved('Ingredient archived; purchase records were preserved.')


def purchase_history(api, unused):
    heading('Ingredient purchase history')
    purchases = api.call('GET', '/api/purchases')
    names = {x['id']: x['name'] for x in
             api.call('GET', '/api/ingredients', params={'include_archived': True})}
    show_table(['ID', 'Date', 'Ingredient', 'Quantity', 'Total paid'],
               [(x['id'], x['date'], names.get(x['ingredient_id'], x['ingredient_id']),
                 f"{qty_text(x['quantity'])} {x['unit']}", pesos(x['total_cost']))
                for x in purchases], 'PURCHASE HISTORY')
    input('\n  Press Enter to return to Ingredients...')
    return info('Returned to ingredient inventory.')


def ingredient_changes(api, unused):
    heading('Ingredient stock/value corrections')
    rows = api.call('GET', '/api/ingredient-adjustments')
    names = {x['id']: x['name'] for x in
             api.call('GET', '/api/ingredients', params={'include_archived': True})}
    show_table(['Date', 'Ingredient', 'Old stock', 'New stock', 'Reason'],
               [(x['date'], names.get(x['ingredient_id'], x['ingredient_id']),
                 qty_text(x['old_quantity']), qty_text(x['new_quantity']), x['reason'])
                for x in rows], 'INGREDIENT CORRECTIONS (base g/pcs)')
    input('\n  Press Enter to return to Ingredients...')
    return info('Returned to ingredient inventory.')


def ingredients_menu(api):
    """Stay in ingredient management after every save or cancellation."""
    options = [
        ('add', 'Register a new ingredient'),
        ('purchase', 'Record new ingredient purchase'),
        ('edit', 'Edit ingredient details, stock or value'),
        ('archive', 'Archive unused ingredient (stock may remain)'),
        ('history', 'View ingredient purchase history'),
        ('changes', 'View ingredient stock/value corrections'),
    ]
    handlers = {
        'add': lambda items: add_ingredient(api, items),
        'purchase': lambda items: purchase_ingredient(api, items),
        'edit': lambda items: edit_ingredient(api, items),
        'archive': lambda items: archive_ingredient(api, items),
        'history': lambda items: purchase_history(api, items),
        'changes': lambda items: ingredient_changes(api, items),
    }
    run_section('Ingredient inventory and purchases',
                'Weights are displayed in g or kg; all costs are in PHP.',
                lambda: show_ingredients(api), options, handlers)


def recipe_menu(api, unused):
    heading('Create or replace product recipe')
    products = inventory(api)
    if not products:
        return info('Register a product first.')
    pid = intask('Product ID for recipe', allowed={p['id'] for p in products})
    ingredients = show_ingredients(api)
    if not ingredients:
        return info('Register ingredients first.')
    chosen = []
    available = {x['id'] for x in ingredients}
    section('Choose recipe ingredients', 'Type 0 when you finish adding ingredients.')
    while True:
        iid = intask('Ingredient ID (0 = done)', minimum=0, allowed=available | {0})
        if iid == 0:
            break
        if any(x['ingredient_id'] == iid for x in chosen):
            warn('Ingredient already in this recipe.')
            continue
        ing = next(x for x in ingredients if x['id'] == iid)
        qty = amountask(f"Suggested {ing['name']} per finished product ({ing['unit']})", ing['unit'])
        chosen.append({'ingredient_id': iid, 'quantity': qty})
        notice(f"Added {ing['name']} to the recipe.")
    if not chosen:
        return cancelled('No recipe ingredients were selected.')
    if not confirm('Save this recipe?'):
        return cancelled()
    api.call('PUT', f'/api/products/{pid}/recipe', {'items': chosen})
    return saved('Recipe saved. You can select another product or recipe below.')


def add_product(api, unused):
    heading('Create product')
    name = ask_name('Product name')
    price = moneyask('Selling price (PHP)', allow_zero=False)
    if not confirm('Save product?'):
        return cancelled()
    result = api.call('POST', '/api/products', {'name': name, 'price': price})
    return saved(f"Product #{result['id']} added.")


def edit_product(api, items):
    heading('Edit product')
    if not items:
        return info('No active products.')
    inventory(api)
    pid = intask('Product ID', allowed={x['id'] for x in items})
    row = next(x for x in items if x['id'] == pid)
    section('Selected product', row['name'])
    change = action_menu([('name', 'Change name'), ('price', 'Change selling price')])
    if not change:
        return cancelled()
    payload = ({'name': ask_name('New product name')} if change == 'name' else
               {'price': moneyask('New price (PHP)', row['price'], allow_zero=False)})
    if not confirm('Save changes?'):
        return cancelled()
    api.call('PUT', f'/api/products/{pid}', payload)
    return saved('Product updated.')


def archive_product(api, items):
    heading('Archive product')
    if not items:
        return info('No active products.')
    inventory(api)
    pid = intask('Product ID', allowed={x['id'] for x in items})
    if not confirm('Archive this product?', default=False):
        return cancelled()
    api.call('DELETE', f'/api/products/{pid}')
    return saved('Product archived.')


def show_archived_products(api, unused):
    """Display archived chocolates in a separate read-only view."""
    heading('Archived products')
    products = api.call('GET', '/api/products')
    archived = [product for product in products if not product['active']]
    show_table(['ID', 'Archived product'],
               [(product['id'], product['name']) for product in archived],
               'ARCHIVED PRODUCTS')
    input('  Press Enter to return to Products and Recipes...')
    return info('Returned to active products.')


def products_menu(api):
    options = [
        ('add', 'Create product'),
        ('edit', 'Edit name or selling price'),
        ('archive', 'Archive product with no stock'),
        ('recipe', 'Create or replace a recipe'),
        ('archived', 'Show Archived Products'),
    ]
    handlers = {
        'add': lambda items: add_product(api, items),
        'edit': lambda items: edit_product(api, items),
        'archive': lambda items: archive_product(api, items),
        'recipe': lambda items: recipe_menu(api, items),
        'archived': lambda items: show_archived_products(api, items),
    }
    run_section('Products and recipes', 'Manage chocolates and their recipe ingredients.',
                lambda: inventory(api), options, handlers)
