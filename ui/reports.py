"""Reports and verified stock correction screens."""

import httpx
from ui.display import heading, section, show_summary
from ui.inputs import ask_date, intask, ask_name, confirm, action_menu
from ui.catalog import inventory
from ui.navigation import run_section, saved, cancelled, info
from ui.report_tables import render_report
from ui.client import ApiError


REPORTS = [
    ('summary', 'Business summary'),
    ('bestsellers', 'Best sellers'),
    ('booths', 'Sales by booth'),
    ('channels', 'Sales by channel'),
    ('daily', 'Daily revenue'),
    ('sales', 'Individual sales history'),
    ('production', 'Production and purchase history'),
    ('all', 'Show all reports'),
]


def reports_menu(api):
    heading('Sales, production and purchase reports',
            'Choose a date first. Leave it blank to include all dates.')
    day = ask_date('Report date (YYYY-MM-DD; blank = all)', blank_allowed=True)
    last_message = None

    while True:
        heading('Sales, production and purchase reports',
                f"Current date filter: {day or 'All dates'}")
        section('Select a report', 'View several reports without returning to the dashboard.')
        if last_message:
            print(f'  {last_message}\n')

        menu_options = REPORTS + [('date', 'Change report date')]
        action = action_menu(menu_options)

        if action is None:
            return
        if action == 'date':
            heading('Change report date')
            day = ask_date('Report date (blank = all)', blank_allowed=True)
            last_message = 'Date filter updated.'
            continue

        try:
            render_report(api, day, action)
        except (ApiError, ValueError, httpx.HTTPError) as exc:
            last_message = f'[ERROR] Could not load report: {exc}'
            continue

        input('\n  Press Enter to choose another report...')
        last_message = 'Select another report, change the date, or choose [0] Back.'


def adjust_stock(api, unused):
    heading('Verified inventory adjustment',
            'Correct finished product stock only after a physical count.')
    products = inventory(api)
    if not products:
        return info('No active products.')

    product_ids = {product['id'] for product in products}
    product_id = intask('Product ID', allowed=product_ids)
    product = None
    for item in products:
        if item['id'] == product_id:
            product = item
            break

    minimum = product['reserved'] + product['allocated']
    new_stock = intask('Correct physical stock', product['stock'], minimum=minimum)
    reason = ask_name('Reason for correction', max_length=300)

    show_summary('Confirm verified correction', [
        ('Product', product['name']),
        ('Old stock', product['stock']),
        ('Counted stock', new_stock),
        ('Reserved and allocated', minimum),
        ('Reason', reason),
    ])

    if not confirm('Save stock adjustment?', default=False):
        return cancelled()

    result = api.call('POST', '/api/adjustments', {
        'product_id': product_id,
        'new_stock': new_stock,
        'reason': reason,
    })
    return saved(f"Stock adjustment #{result['id']} saved. Inventory updated.")


def adjust_menu(api):
    def show_current_stock():
        return inventory(api)

    def record_adjustment(products):
        return adjust_stock(api, products)

    run_section('Verified inventory adjustment',
                'Changes must not reduce stock below existing reservations and booth allocations.',
                show_current_stock,
                [('adjust', 'Record a verified inventory adjustment')],
                {'adjust': record_adjustment})
