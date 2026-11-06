"""Chocolate product catalog CRUD."""
from core import RuleError, next_id, text_value, peso, active_product
from business.inventory import allocated, reserved


def product_add(state, name, price):
    name, price = text_value(name, 'Product name'), peso(price, 'Selling price', allow_zero=False)
    if any(p['active'] and p['name'].casefold() == name.casefold() for p in state['products']):
        raise RuleError('An active product already has this name.')
    row = dict(id=next_id(state), name=name, price=price, stock=0, active=True, recipe=[])
    state['products'].append(row)
    return row


def product_update(state, product_id, name=None, price=None):
    row = active_product(state, product_id)
    if name is None and price is None:
        raise RuleError('Enter a new name or price.')
    if name is not None:
        name = text_value(name, 'Product name')
        if any(p['active'] and p['id'] != product_id and p['name'].casefold() == name.casefold()
               for p in state['products']):
            raise RuleError('Another active product already has this name.')
        row['name'] = name
    if price is not None:
        row['price'] = peso(price, 'Selling price', allow_zero=False)
    return row


def product_delete(state, product_id):
    row = active_product(state, product_id)
    if row['stock'] or allocated(state, product_id) or reserved(state, product_id):
        raise RuleError('Cannot archive a product with stock, reservations or booth allocations.')
    row['active'] = False
    return row
