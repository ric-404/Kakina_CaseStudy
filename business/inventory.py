"""Finished-product inventory, allocations, reservations and adjustments."""
from datetime import date
from core import RuleError, get, next_id, whole_number, text_value, active_product


def reserved(state, product_id):
    return sum(r['quantity'] for r in state['reservations']
               if r['product_id'] == product_id and r['status'] == 'reserved')


def allocated(state, product_id):
    key = str(product_id)
    return sum(e['allocations'].get(key, 0) - e['sold'].get(key, 0)
               for e in state['events'] if e['status'] == 'open')


def free_stock(state, product_id):
    return get(state, 'products', product_id)['stock'] - reserved(state, product_id) - allocated(state, product_id)


def inventory(state):
    return [{**p, 'reserved': reserved(state, p['id']),
             'allocated': allocated(state, p['id']), 'available': free_stock(state, p['id'])}
            for p in state['products'] if p['active']]


def adjust(state, product_id, new_stock, reason):
    """Correct counted stock while protecting customer and booth commitments."""
    product = active_product(state, product_id)  # Missing import fixed here.
    new_stock = whole_number(new_stock, 'Physical stock', allow_zero=True)
    reason = text_value(reason, 'Adjustment reason', max_length=300)
    minimum = reserved(state, product_id) + allocated(state, product_id)
    if new_stock < minimum:
        raise RuleError(f'Stock cannot be below reserved/booth stock ({minimum}).')
    record = dict(id=next_id(state), date=date.today().isoformat(), product_id=product_id,
                  old_stock=product['stock'], new_stock=new_stock, reason=reason)
    product['stock'] = new_stock
    state['adjustments'].append(record)
    return record
