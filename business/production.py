"""Record the actual ingredients used and finished chocolates produced."""

from decimal import Decimal, ROUND_HALF_UP
from core import (RuleError, next_id, active_product, whole_number, valid_date,
                  optional_text, decimal_amount, as_decimal)
from business.ingredients import active_ingredient


def produce(state, production_date, product_id, ingredients_used, finished_quantity, note=''):
    production_date = valid_date(production_date)
    product = active_product(state, product_id)
    finished_quantity = whole_number(finished_quantity, 'Finished count')
    note = optional_text(note)

    if not product['recipe']:
        raise RuleError('Create a recipe before recording production.')
    if not isinstance(ingredients_used, list) or not ingredients_used:
        raise RuleError('Enter actual ingredient usage.')

    recipe_ids = set()
    for recipe_item in product['recipe']:
        recipe_ids.add(recipe_item['ingredient_id'])

    used_ids = set()
    ingredient_lines = []

    # Check every ingredient before deducting stock.
    for item in ingredients_used:
        ingredient_id = item.get('ingredient_id')
        ingredient = active_ingredient(state, ingredient_id)

        if ingredient_id not in recipe_ids:
            raise RuleError(f"{ingredient['name']} is not in this recipe.")
        if ingredient_id in used_ids:
            raise RuleError('Enter each ingredient only once.')
        used_ids.add(ingredient_id)

        places = 3 if ingredient['unit'] == 'g' else 0
        amount = decimal_amount(item.get('quantity'), 'Amount used', places=places)
        stock = as_decimal(ingredient['quantity'])

        if amount > stock:
            raise RuleError(f"Not enough {ingredient['name']} in stock.")

        cost = as_decimal(ingredient['stock_value']) * amount / stock
        cost = cost.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        if amount == stock:
            cost = as_decimal(ingredient['stock_value'])

        saved_quantity = float(amount) if ingredient['unit'] == 'g' else int(amount)
        ingredient_lines.append({
            'ingredient_id': ingredient_id,
            'name': ingredient['name'],
            'quantity': saved_quantity,
            'unit': ingredient['unit'],
            'cost': float(cost)
        })

    if used_ids != recipe_ids:
        raise RuleError('Enter actual usage for every recipe ingredient.')

    # Save the deductions only after all input passes validation.
    for line in ingredient_lines:
        ingredient = active_ingredient(state, line['ingredient_id'])
        remaining = as_decimal(ingredient['quantity']) - as_decimal(line['quantity'])
        remaining_value = as_decimal(ingredient['stock_value']) - as_decimal(line['cost'])

        if ingredient['unit'] == 'g':
            ingredient['quantity'] = float(remaining)
        else:
            ingredient['quantity'] = int(remaining)

        if remaining:
            ingredient['stock_value'] = max(0.0, round(float(remaining_value), 2))
        else:
            ingredient['stock_value'] = 0.0

    product['stock'] += finished_quantity

    record = {
        'id': next_id(state),
        'date': production_date,
        'product_id': product_id,
        'product_name': product['name'],
        'ingredients_used': ingredient_lines,
        'total_cost': round(sum(line['cost'] for line in ingredient_lines), 2),
        'finished_quantity': finished_quantity,
        'outputs': [{'product_id': product_id, 'quantity': finished_quantity}],
        'note': note
    }
    state['production'].append(record)
    return record
