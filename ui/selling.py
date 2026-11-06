"""Persistent booth, reservation and sale screens for the Kakina CLI."""
from ui.display import heading, section, show_table, show_summary, pesos
from ui.inputs import (ask_name, ask_optional, ask_date, intask, moneyask,
                       choose, confirm)
from ui.catalog import inventory, select_products
from ui.navigation import run_section, saved, cancelled, info


def show_booths(api):
    events = api.call('GET', '/api/events')
    show_table(['ID', 'Date', 'Booth', 'Status'],
               [(e['id'], e['date'], e['name'], e['status']) for e in events], 'EVENTS')
    return events


def open_booth(api, unused):
    heading('Open booth event')
    name = ask_name('Booth/location')
    day = ask_date('Event date')
    allocations = select_products(api, 'Allocate finished products', check_stock=True)
    if not allocations:
        return cancelled('No products were allocated.')
    if not confirm('Open booth with these allocations?'):
        return cancelled()
    record = api.call('POST', '/api/events', {
        'name': name, 'date': day, 'allocations': allocations,
    })
    return saved(f"Booth #{record['id']} opened. The event table has been refreshed.")


def close_booth(api, events):
    heading('Close booth and count unsold stock')
    open_events = [e for e in events if e['status'] == 'open']
    if not open_events:
        return info('No booths are currently open.')
    show_table(['ID', 'Date', 'Booth'],
               [(e['id'], e['date'], e['name']) for e in open_events], 'OPEN BOOTHS')
    eid = intask('Open booth ID', allowed={e['id'] for e in open_events})
    event = next(e for e in open_events if e['id'] == eid)
    names = {p['id']: p['name'] for p in api.call('GET', '/api/products')}
    counts = []
    for pid, allocated in event['allocations'].items():
        expected = allocated - event['sold'].get(pid, 0)
        section(names.get(int(pid), f'Product #{pid}'),
                f'Expected unsold: {expected}')
        actual = intask('Physically counted', expected, minimum=0)
        counts.append({'product_id': int(pid), 'quantity': actual})
    if not confirm('Close the booth?'):
        return cancelled()
    result = api.call('PUT', f'/api/events/{eid}/close', {'counts': counts})
    differences = {str(k): v for k, v in result['differences'].items() if v != 0}
    if differences:
        note = ', '.join(f"{names.get(int(k), k)}: {v:+}" for k, v in differences.items())
        return info(f'Booth closed. Check differences ({note}) before adjusting stock.')
    return saved('Booth closed; unsold stock returned to available inventory.')


def booths_menu(api):
    run_section('Booth events and unsold stock',
                'Open events, record sales, and close booths after a physical count.',
                lambda: show_booths(api),
                [('open', 'Open a booth'), ('close', 'Close booth and count unsold stock')],
                {'open': lambda events: open_booth(api, events),
                 'close': lambda events: close_booth(api, events)})


def show_reservations(api):
    rows = api.call('GET', '/api/reservations')
    names = {p['id']: p['name'] for p in api.call('GET', '/api/products')}
    show_table(['ID', 'Customer', 'Product', 'Qty', 'Status'],
               [(r['id'], r['customer'], names.get(r['product_id'], r['product_id']),
                 r['quantity'], r['status']) for r in rows], 'RESERVATIONS')
    return rows


def add_reservation(api, unused):
    heading('Add customer reservation')
    products = inventory(api)
    if not products:
        return info('No products are available to reserve.')
    pid = intask('Product ID', allowed={p['id'] for p in products})
    customer = ask_name('Customer name')
    quantity = intask('Quantity')
    method = choose('Pickup or delivery', ['pickup', 'delivery'], 'pickup')
    day = ask_date('Reservation date')
    if not confirm('Reserve these products?'):
        return cancelled()
    row = api.call('POST', '/api/reservations', {
        'customer': customer, 'product_id': pid, 'quantity': quantity,
        'method': method, 'date': day,
    })
    return saved(f"Reservation #{row['id']} saved; the list has been refreshed.")


def cancel_reservation(api, rows):
    heading('Cancel customer reservation')
    active = [r for r in rows if r['status'] == 'reserved']
    if not active:
        return info('There are no active reservations.')
    show_table(['ID', 'Customer', 'Product', 'Qty'],
               [(r['id'], r['customer'], r['product_id'], r['quantity']) for r in active],
               'ACTIVE RESERVATIONS')
    rid = intask('Active reservation ID', allowed={r['id'] for r in active})
    if not confirm('Cancel this reservation?', default=False):
        return cancelled()
    api.call('PUT', f'/api/reservations/{rid}/cancel')
    return saved('Reservation cancelled; its stock is now available again.')


def reservations_menu(api):
    run_section('Customer reservations', 'Create or cancel multiple reservations here.',
                lambda: show_reservations(api),
                [('add', 'Add reservation'), ('cancel', 'Cancel existing reservation')],
                {'add': lambda rows: add_reservation(api, rows),
                 'cancel': lambda rows: cancel_reservation(api, rows)})


def show_recent_sales(api):
    sales = api.call('GET', '/api/sales')
    recent = sales[-10:]
    show_table(['ID', 'Date', 'Product', 'Qty', 'Channel', 'Total'],
               [(s['id'], s['date'], s.get('product_name', s['product_id']),
                 s['quantity'], s['channel'], pesos(s['total'])) for s in recent],
               'RECENT SALES (LAST 10)')
    return recent


def record_sale(api, unused):
    heading('Record an individual sale')
    channel = choose('Sales channel', ['direct', 'messenger', 'booth', 'reservation'], 'direct')
    event_id, reservation_id = None, None
    if channel == 'booth':
        events = [e for e in api.call('GET', '/api/events') if e['status'] == 'open']
        if not events:
            return info('No booth is open.')
        show_table(['ID', 'Booth', 'Date'],
                   [(e['id'], e['name'], e['date']) for e in events], 'OPEN BOOTHS')
        event_id = intask('Booth ID', allowed={e['id'] for e in events})
    if channel == 'reservation':
        reservations = [r for r in api.call('GET', '/api/reservations')
                        if r['status'] == 'reserved']
        if not reservations:
            return info('No active reservations.')
        show_table(['ID', 'Customer', 'Product ID', 'Qty'],
                   [(r['id'], r['customer'], r['product_id'], r['quantity'])
                    for r in reservations], 'ACTIVE RESERVATIONS')
        reservation_id = intask('Reservation ID', allowed={r['id'] for r in reservations})
        reservation = next(r for r in reservations if r['id'] == reservation_id)
        pid, quantity = reservation['product_id'], reservation['quantity']
    else:
        products = inventory(api)
        if not products:
            return info('No products are available.')
        pid = intask('Product ID', allowed={p['id'] for p in products})
        quantity = intask('Quantity')
    payment = choose('Payment', ['cash', 'gcash'], 'cash')
    day = ask_date('Sale date')
    customer = ask_optional('Customer (optional)')
    delivery_fee = moneyask('Delivery fee (PHP)', 0)
    product = next((p for p in api.call('GET', '/api/products') if p['id'] == pid), None)
    show_summary('Review sale', [('Product', product['name'] if product else pid),
                                 ('Units', quantity), ('Channel', channel),
                                 ('Payment', payment), ('Date', day),
                                 ('Delivery', pesos(delivery_fee))])
    if not confirm('Save this sale?'):
        return cancelled('Sale cancelled; stock has not changed.')
    row = api.call('POST', '/api/sales', {
        'product_id': pid, 'quantity': quantity, 'channel': channel,
        'event_id': event_id, 'reservation_id': reservation_id,
        'payment': payment, 'date': day, 'customer': customer,
        'delivery_fee': delivery_fee,
    })
    return saved(f"Sale #{row['id']} recorded: {pesos(row['total'])}.")


def sales_menu(api):
    run_section('Record an individual sale',
                'Review recent transactions or record several sales in one visit.',
                lambda: show_recent_sales(api),
                [('record', 'Record another sale')],
                {'record': lambda sales: record_sale(api, sales)})
