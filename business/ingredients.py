"""Ingredients, purchases, stock costs, and product recipes."""

from datetime import date as CalendarDate
from decimal import Decimal, ROUND_HALF_UP
from core import (RuleError, get, next_id, text_value, valid_choice,
                  active_product, peso, valid_date, optional_text,
                  decimal_amount, as_decimal)


def ingredient_add(state, name, unit):
    name = text_value(name, 'Ingredient name')
    unit = valid_choice(unit, ('g', 'kg', 'pcs'), 'Ingredient unit')

    for ingredient in state['ingredients']:
        if ingredient['active'] and ingredient['name'].casefold() == name.casefold():
            raise RuleError('An active ingredient with this name already exists.')

    base_unit = 'g' if unit == 'kg' else unit
    ingredient = {
        'id': next_id(state),
        'name': name,
        'unit': base_unit,
        'display_unit': unit,
        'quantity': 0,
        'stock_value': 0.0,
        'active': True
    }
    state['ingredients'].append(ingredient)
    return ingredient


def active_ingredient(state, ingredient_id):
    ingredient = get(state, 'ingredients', ingredient_id)
    if not ingredient['active']:
        raise RuleError('This ingredient is archived.')
    return ingredient


def display_unit(ingredient):
    return ingredient.get('display_unit', ingredient['unit'])


def quantity_in_base(value, unit, base_unit):
    if unit == 'kg':
        places = 6
    elif unit == 'g':
        places = 3
    else:
        places = 0

    amount = decimal_amount(value, 'Ingredient stock', allow_zero=True, places=places)
    if unit == 'kg':
        amount *= 1000

    base_places = 3 if base_unit == 'g' else 0
    return decimal_amount(amount, 'Ingredient stock', allow_zero=True, places=base_places)


def ingredient_update(state, ingredient_id, name=None, unit=None,
                      quantity=None, stock_value=None, unit_cost=None, reason=''):
    ingredient = active_ingredient(state, ingredient_id)
    old_quantity = as_decimal(ingredient['quantity'])
    old_value = as_decimal(ingredient['stock_value'])

    new_name = ingredient['name']
    if name is not None:
        new_name = text_value(name, 'Ingredient name')

    for other in state['ingredients']:
        if other['active'] and other['id'] != ingredient_id:
            if other['name'].casefold() == new_name.casefold():
                raise RuleError('An active ingredient with this name already exists.')

    current_unit = display_unit(ingredient)
    new_unit = current_unit
    if unit is not None:
        new_unit = valid_choice(unit, ('g', 'kg', 'pcs'), 'Ingredient unit')

    if ingredient['unit'] == 'pcs' and new_unit != 'pcs':
        raise RuleError('Pieces cannot be changed to a weight unit.')
    if ingredient['unit'] == 'g' and new_unit == 'pcs':
        raise RuleError('Weight cannot be changed to pieces.')

    new_quantity = old_quantity
    if quantity is not None:
        new_quantity = quantity_in_base(quantity, new_unit, ingredient['unit'])

    if stock_value is not None and unit_cost is not None:
        raise RuleError('Edit either stock value or unit cost, not both.')

    if stock_value is not None:
        new_value = as_decimal(peso(stock_value, 'Total stock value'))
    elif unit_cost is not None:
        cost_per_unit = decimal_amount(unit_cost, 'Cost per unit', allow_zero=True, places=4)
        displayed_quantity = new_quantity
        if new_unit == 'kg':
            displayed_quantity /= 1000
        new_value = cost_per_unit * displayed_quantity
        new_value = new_value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        new_value = as_decimal(peso(new_value, 'Total stock value'))
    elif quantity is not None:
        average = old_value / old_quantity if old_quantity else Decimal('0')
        new_value = (average * new_quantity).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    else:
        new_value = old_value

    if new_quantity == 0 and new_value != 0:
        raise RuleError('Stock value must be zero when quantity is zero.')

    if new_quantity != old_quantity or new_value != old_value:
        reason = text_value(reason, 'Adjustment reason', max_length=300)
        adjustment = {
            'id': next_id(state),
            'date': CalendarDate.today().isoformat(),
            'ingredient_id': ingredient_id,
            'old_quantity': float(old_quantity),
            'new_quantity': float(new_quantity),
            'old_value': float(old_value),
            'new_value': float(new_value),
            'unit': ingredient['unit'],
            'reason': reason
        }
        state.setdefault('ingredient_adjustments', []).append(adjustment)

    ingredient['name'] = new_name
    ingredient['display_unit'] = new_unit
    ingredient['quantity'] = float(new_quantity) if ingredient['unit'] == 'g' else int(new_quantity)
    ingredient['stock_value'] = round(float(new_value), 2)
    return ingredient


def ingredient_delete(state, ingredient_id):
    ingredient = active_ingredient(state, ingredient_id)

    # Recipes and production history must still be usable after archiving.
    for product in state['products']:
        for item in product.get('recipe', []):
            if item['ingredient_id'] == ingredient_id:
                raise RuleError('Ingredient is referenced in a product recipe. Remove the recipe link first.')

    for run in state['production']:
        for item in run.get('ingredients_used', []):
            if item['ingredient_id'] == ingredient_id:
                raise RuleError('Ingredient is referenced in production history and cannot be archived.')

    ingredient['active'] = False
    return ingredient


def purchase_add(state, ingredient_id, quantity, total_cost, purchase_date, note=''):
    ingredient = active_ingredient(state, ingredient_id)
    places = 3 if ingredient['unit'] == 'g' else 0
    quantity = decimal_amount(quantity, 'Purchased quantity', places=places)
    cost = peso(total_cost, 'Total purchase cost', allow_zero=False)
    purchase_date = valid_date(purchase_date)
    note = optional_text(note)

    new_quantity = as_decimal(ingredient['quantity']) + quantity
    if ingredient['unit'] == 'g':
        ingredient['quantity'] = float(new_quantity)
    else:
        ingredient['quantity'] = int(new_quantity)
    ingredient['stock_value'] = round(float(as_decimal(ingredient['stock_value']) + as_decimal(cost)), 2)

    record = {
        'id': next_id(state),
        'date': purchase_date,
        'ingredient_id': ingredient_id,
        'quantity': float(quantity) if ingredient['unit'] == 'g' else int(quantity),
        'unit': ingredient['unit'],
        'total_cost': cost,
        'note': note
    }
    state['purchases'].append(record)
    return record


def ingredient_inventory(state, include_archived=False):
    result = []
    for ingredient in state['ingredients']:
        if not ingredient['active'] and not include_archived:
            continue

        unit = display_unit(ingredient)
        quantity = as_decimal(ingredient['quantity'])
        value = as_decimal(ingredient['stock_value'])

        displayed_quantity = quantity
        if unit == 'kg':
            displayed_quantity = quantity / 1000

        displayed_cost = value / displayed_quantity if displayed_quantity else Decimal('0')
        average_cost = value / quantity if quantity else Decimal('0')

        row = ingredient.copy()
        row['display_unit'] = unit
        row['display_quantity'] = float(displayed_quantity)
        row['average_display_cost'] = round(float(displayed_cost), 4)
        row['average_unit_cost'] = round(float(average_cost), 4)
        result.append(row)

    return result


def recipe_set(state, product_id, items):
    product = active_product(state, product_id)
    if not isinstance(items, list) or not items:
        raise RuleError('Add at least one ingredient to the product recipe.')

    ingredient_ids = set()
    recipe = []
    for item in items:
        ingredient_id = item.get('ingredient_id')
        ingredient = active_ingredient(state, ingredient_id)

        if ingredient_id in ingredient_ids:
            raise RuleError('The same ingredient appears twice in one recipe.')
        ingredient_ids.add(ingredient_id)

        places = 3 if ingredient['unit'] == 'g' else 0
        amount = decimal_amount(item.get('quantity'), 'Recipe amount', places=places)
        saved_amount = float(amount) if ingredient['unit'] == 'g' else int(amount)
        recipe.append({'ingredient_id': ingredient_id, 'quantity': saved_amount})

    product['recipe'] = recipe
    return product
