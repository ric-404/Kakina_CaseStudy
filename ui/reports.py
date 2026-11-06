"""Date-filtered report menu and verified finished-stock adjustments."""
from ui.display import heading, section, show_summary
from ui.inputs import ask_date, intask, ask_name, confirm, action_menu
from ui.catalog import inventory
from ui.navigation import run_section, saved, cancelled, info
from ui.report_tables import render_report
from ui.client import ApiError
import httpx


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
    """Keep the chosen date while viewing multiple reports in one visit."""
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
        action = action_menu(REPORTS + [('date', 'Change report date')])
        if action is None:
            return
        if action == 'date':
            heading('Change report date')
            day = ask_date('Report date (blank = all)', blank_allowed=True)
            last_message = 'Date filter updated.'
            continue
        # Enter returns to the report list without visiting the dashboard.
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
    pid = intask('Product ID', allowed={p['id'] for p in products})
    product = next(p for p in products if p['id'] == pid)
    minimum = product['reserved'] + product['allocated']
    new_stock = intask('Correct physical stock', product['stock'], minimum=minimum)
    reason = ask_name('Reason for correction', max_length=300)
    show_summary('Confirm verified correction', [
        ('Product', product['name']), ('Old stock', product['stock']),
        ('Counted stock', new_stock), ('Reserved and allocated', minimum),
        ('Reason', reason),
    ])
    if not confirm('Save stock adjustment?', default=False):
        return cancelled()
    row = api.call('POST', '/api/adjustments', {
        'product_id': pid, 'new_stock': new_stock, 'reason': reason,
    })
    return saved(f"Stock adjustment #{row['id']} saved. Inventory updated.")


def adjust_menu(api):
    run_section('Verified inventory adjustment',
                'Changes must not reduce stock below existing reservations and booth allocations.',
                lambda: inventory(api),
                [('adjust', 'Record a verified inventory adjustment')],
                {'adjust': lambda products: adjust_stock(api, products)})
