"""Show the main menu and start the local API server."""

import argparse
import sys
import threading
import time

import httpx
import uvicorn

from api import app
from ui.client import ApiClient, ApiError, BASE_URL
from ui.display import main_menu, warn, success, error
from ui.inputs import intask
from ui.catalog import inventory_menu, ingredients_menu, products_menu
from ui.production import production_menu
from ui.selling import booths_menu, reservations_menu, sales_menu
from ui.reports import reports_menu, adjust_menu


def dashboard(api):
    products = api.call('GET', '/api/inventory')
    events = api.call('GET', '/api/events')
    reservations = api.call('GET', '/api/reservations')

    stock_total = sum(product['stock'] for product in products)
    available_total = sum(product['available'] for product in products)
    open_booths = sum(event['status'] == 'open' for event in events)
    active_reservations = sum(row['status'] == 'reserved' for row in reservations)

    stats = (f'Stock: {stock_total}   '
             f'Available: {available_total}   '
             f'Open booths: {open_booths}   '
             f'Active reservations: {active_reservations}')

    groups = [
        ('INVENTORY AND PRODUCTION', [
            ('1', 'View finished product inventory'),
            ('2', 'Ingredients and purchases'),
            ('3', 'Products and recipes'),
            ('4', 'Produce chocolates (weigh and count)'),
        ]),
        ('ORDERS AND SELLING', [
            ('5', 'Booth events and unsold stock'),
            ('6', 'Customer reservations'),
            ('7', 'Record an individual sale'),
        ]),
        ('REPORTS AND CONTROL', [
            ('8', 'Sales, production and purchase reports'),
            ('9', 'Verified inventory adjustment'),
        ]),
        ('EXIT', [('0', 'Exit program')]),
    ]
    main_menu('Kakina Food Products Mfg.', stats, groups)


def menu(api):
    actions = {
        1: inventory_menu,
        2: ingredients_menu,
        3: products_menu,
        4: production_menu,
        5: booths_menu,
        6: reservations_menu,
        7: sales_menu,
        8: reports_menu,
        9: adjust_menu,
    }

    while True:
        try:
            dashboard(api)
            choice = intask('Choose menu', minimum=0, maximum=9)

            if choice == 0:
                success('Goodbye!')
                break

            selected_function = actions[choice]
            selected_function(api)

        except (ApiError, ValueError, httpx.HTTPError) as exc:
            error(f'Could not finish this action: {exc}')
        except (EOFError, KeyboardInterrupt):
            warn('Input cancelled. Returning to the main menu.')
            if not sys.stdin.isatty():
                break


def start_api():
    config = uvicorn.Config(
        app,
        host='127.0.0.1',
        port=8765,
        access_log=False,
        log_level='error'
    )
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    for attempt in range(60):
        if not thread.is_alive():
            raise RuntimeError('The local API could not start. Port 8765 may be busy.')
        try:
            response = httpx.get(BASE_URL + '/api/health', timeout=1)
            if response.status_code == 200:
                return server
        except httpx.RequestError:
            pass
        time.sleep(0.1)

    raise RuntimeError('The local API did not start. Port 8765 may be busy.')


def main():
    parser = argparse.ArgumentParser(description='Kakina CLI application')
    parser.add_argument('--connect', action='store_true',
                        help='Connect to an API server already running on port 8765')
    args = parser.parse_args()

    server = None
    try:
        if not args.connect:
            try:
                result = httpx.get(BASE_URL + '/api/health', timeout=0.5)
            except httpx.RequestError:
                result = None

            if result is not None:
                raise RuntimeError('Port 8765 is already serving HTTP. Stop it or use --connect.')
            server = start_api()

        client = ApiClient()
        try:
            menu(client)
        finally:
            client.close()

    except RuntimeError as exc:
        error(str(exc))
        sys.exit(1)
    finally:
        if server is not None:
            server.should_exit = True


if __name__ == '__main__':
    main()
