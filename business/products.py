from core import RuleError, next_id, text_value, peso, active_product
from business.inventory import allocated, reserved


def product_add(state, name, price):
    name = text_value(name, 'Product name')
    price = peso(price, 'Selling price', allow_zero=False)

    for product in state['products']:
        if product['active'] and product['name'].casefold() == name.casefold():
            raise RuleError('An active product already has this name.')

    product = {
        'id': next_id(state),
        'name': name,
        'price': price,
        'stock': 0,
        'active': True,
        'recipe': []
    }
    state['products'].append(product)
    return product


def product_update(state, product_id, name=None, price=None):
    product = active_product(state, product_id)

    if name is None and price is None:
        raise RuleError('Enter a new name or price.')

    if name is not None:
        name = text_value(name, 'Product name')
        for other in state['products']:
            if other['active'] and other['id'] != product_id:
                if other['name'].casefold() == name.casefold():
                    raise RuleError('Another active product already has this name.')
        product['name'] = name

    if price is not None:
        product['price'] = peso(price, 'Selling price', allow_zero=False)

    return product


def product_delete(state, product_id):
    product = active_product(state, product_id)

    if product['stock'] or allocated(state, product_id) or reserved(state, product_id):
        raise RuleError('Cannot archive a product with stock, reservations or booth allocations.')

    product['active'] = False
    return product
