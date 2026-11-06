"""Booth events, customer reservations, and individual sales."""
from datetime import date
from core import (RuleError, get, next_id, text_value, valid_date,
                  whole_number, valid_choice, active_product, peso, optional_text)
from business.inventory import free_stock, allocated


def event_open(state, name, event_date, allocations):
    name, event_date = text_value(name, 'Booth location'), valid_date(event_date)
    if not isinstance(allocations, list) or not allocations:
        raise RuleError('Allocate at least one product to a booth.')
    chosen = {}
    for item in allocations:
        product = active_product(state, item['product_id'])
        quantity = whole_number(item['quantity'])
        key = str(product['id'])
        chosen[key] = chosen.get(key, 0) + quantity
    for key, count in chosen.items():
        if count > free_stock(state, int(key)):
            raise RuleError(f'Not enough free stock for product #{key}.')
    record = dict(id=next_id(state), name=name, date=event_date, status='open',
                  allocations=chosen, sold={}, physical_remaining={}, differences={})
    state['events'].append(record)
    return record


def event_close(state, event_id, counts):
    event = get(state, 'events', event_id)
    if event['status'] != 'open':
        raise RuleError('This booth is already closed.')
    expected = {key: qty - event['sold'].get(key, 0)
                for key, qty in event['allocations'].items()}
    actual = {}
    for item in counts:
        key = str(item['product_id'])
        if key in actual:
            raise RuleError('Count each booth product once.')
        actual[key] = whole_number(item['quantity'], 'Counted quantity', allow_zero=True)
    if set(actual) != set(expected):
        raise RuleError('Count every allocated booth product.')
    differences = {key: actual[key] - expected[key] for key in actual}
    event.update(physical_remaining=actual, differences=differences, status='closed')
    return {'event': event, 'expected': expected, 'differences': differences}


def reservation_add(state, customer, product_id, quantity, method='pickup', date_value=None):
    customer = text_value(customer, 'Customer')
    active_product(state, product_id)
    quantity = whole_number(quantity)
    method = valid_choice(method, ('pickup', 'delivery'), 'Fulfillment')
    day = valid_date(date_value or date.today().isoformat())
    if quantity > free_stock(state, product_id):
        raise RuleError('Not enough free stock to reserve.')
    record = dict(id=next_id(state), customer=customer, product_id=product_id,
                  quantity=quantity, method=method, date=day, status='reserved')
    state['reservations'].append(record)
    return record


def reservation_cancel(state, reservation_id):
    row = get(state, 'reservations', reservation_id)
    if row['status'] != 'reserved':
        raise RuleError('Only active reservations can be cancelled.')
    row['status'] = 'cancelled'
    return row


def sale_add(state, product_id, quantity, channel='direct', event_id=None,
             reservation_id=None, payment='cash', date_value=None,
             delivery_fee=0, customer=''):
    product = active_product(state, product_id)
    quantity = whole_number(quantity)
    channel = valid_choice(channel, ('direct', 'messenger', 'booth', 'reservation'), 'Channel')
    payment = valid_choice(payment, ('cash', 'gcash'), 'Payment')
    delivery_fee = peso(delivery_fee, 'Delivery fee')
    day = valid_date(date_value or date.today().isoformat())
    customer = optional_text(customer, 'Customer', 100)
    event_id_for_sale, reservation_id_for_sale = None, None
    event, reservation = None, None

    if channel == 'booth':
        if event_id is None:
            raise RuleError('Choose an open booth event.')
        event = get(state, 'events', event_id)
        if event['status'] != 'open':
            raise RuleError('This booth is closed.')
        key = str(product_id)
        left = event['allocations'].get(key, 0) - event['sold'].get(key, 0)
        if quantity > left:
            raise RuleError('Not enough products left at this booth.')
        event_id_for_sale = event_id
    elif channel == 'reservation':
        if reservation_id is None:
            raise RuleError('Choose an active reservation.')
        reservation = get(state, 'reservations', reservation_id)
        if reservation['status'] != 'reserved':
            raise RuleError('Reservation already completed or cancelled.')
        if (reservation['product_id'], reservation['quantity']) != (product_id, quantity):
            raise RuleError('Product and quantity must match the reservation.')
        if quantity > product['stock'] - allocated(state, product_id):
            raise RuleError('Not enough physical stock for this reservation.')
        customer = reservation['customer']
        reservation_id_for_sale = reservation_id
    elif quantity > free_stock(state, product_id):
        raise RuleError('Not enough available stock for this sale.')

    if quantity > product['stock']:
        raise RuleError('Not enough physical stock.')
    subtotal = round(product['price'] * quantity, 2)
    total = round(subtotal + delivery_fee, 2)
    record = {'id': next_id(state), 'date': day, 'product_id': product_id,
              'product_name': product['name'], 'quantity': quantity,
              'unit_price': product['price'], 'subtotal': subtotal,
              'delivery_fee': delivery_fee, 'total': total,
              'channel': channel, 'event_id': event_id_for_sale,
              'reservation_id': reservation_id_for_sale, 'payment': payment,
              'customer': customer}
    product['stock'] -= quantity
    if event:
        key = str(product_id)
        event['sold'][key] = event['sold'].get(key, 0) + quantity
    if reservation:
        reservation['status'] = 'completed'
    state['sales'].append(record)
    return record
