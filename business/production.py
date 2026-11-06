"""Ingredient usage, weighted costs and counted chocolate production."""
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

    allowed = {x['ingredient_id'] for x in product['recipe']}
    used, lines = set(), []
    for item in ingredients_used:
        iid = item.get('ingredient_id')
        row = active_ingredient(state, iid)
        if iid not in allowed:
            raise RuleError(f"{row['name']} is not in this recipe.")
        if iid in used:
            raise RuleError('Enter each ingredient only once.')
        used.add(iid)
        amount = decimal_amount(item.get('quantity'), 'Amount used',
                                places=3 if row['unit'] == 'g' else 0)
        stock = as_decimal(row['quantity'])
        if amount > stock:
            raise RuleError(f"Not enough {row['name']} in stock.")
        cost = (as_decimal(row['stock_value']) * amount / stock).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP)
        if amount == stock:
            cost = as_decimal(row['stock_value'])
        lines.append({'ingredient_id': iid, 'name': row['name'], 'quantity': float(amount) if row['unit'] == 'g' else int(amount),
                      'unit': row['unit'], 'cost': float(cost)})
    if used != allowed:
        raise RuleError('Enter actual usage for every recipe ingredient.')

    for line in lines:
        row = active_ingredient(state, line['ingredient_id'])
        quantity = as_decimal(row['quantity']) - as_decimal(line['quantity'])
        value = as_decimal(row['stock_value']) - as_decimal(line['cost'])
        row['quantity'] = float(quantity) if row['unit'] == 'g' else int(quantity)
        row['stock_value'] = max(0.0, round(float(value), 2)) if quantity else 0.0
    product['stock'] += finished_quantity
    record = {'id': next_id(state), 'date': production_date, 'product_id': product_id,
              'product_name': product['name'], 'ingredients_used': lines,
              'total_cost': round(sum(line['cost'] for line in lines), 2),
              'finished_quantity': finished_quantity,
              'outputs': [{'product_id': product_id, 'quantity': finished_quantity}], 'note': note}
    state['production'].append(record)
    return record
