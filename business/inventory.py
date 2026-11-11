from datetime import date
from core import RuleError, get, next_id, whole_number, text_value, active_product


def reserved(state, product_id):
    total = 0
    for reservation in state['reservations']:
        if reservation['product_id'] == product_id and reservation['status'] == 'reserved':
            total += reservation['quantity']
    return total


def allocated(state, product_id):
    total = 0
    product_key = str(product_id)

    for event in state['events']:
        if event['status'] == 'open':
            sent = event['allocations'].get(product_key, 0)
            sold = event['sold'].get(product_key, 0)
            total += sent - sold

    return total


def free_stock(state, product_id):
    product = get(state, 'products', product_id)
    return product['stock'] - reserved(state, product_id) - allocated(state, product_id)


def inventory(state):
    result = []

    for product in state['products']:
        if not product['active']:
            continue

        product_id = product['id']
        row = product.copy()
        row['reserved'] = reserved(state, product_id)
        row['allocated'] = allocated(state, product_id)
        row['available'] = free_stock(state, product_id)
        result.append(row)

    return result


def adjust(state, product_id, new_stock, reason):
    product = active_product(state, product_id)
    new_stock = whole_number(new_stock, 'Physical stock', allow_zero=True)
    reason = text_value(reason, 'Adjustment reason', max_length=300)

    minimum = reserved(state, product_id) + allocated(state, product_id)
    if new_stock < minimum:
        raise RuleError(f'Stock cannot be below reserved/booth stock ({minimum}).')

    record = {
        'id': next_id(state),
        'date': date.today().isoformat(),
        'product_id': product_id,
        'old_stock': product['stock'],
        'new_stock': new_stock,
        'reason': reason
    }
    product['stock'] = new_stock
    state['adjustments'].append(record)
    return record
