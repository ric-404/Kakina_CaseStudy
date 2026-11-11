
import argparse
import sys
import threading
import time

import httpx
import uvicorn

from api import app
from ui.client import ApiClient, ApiError, BASE_URL
from ui.display import warn, success, error
from ui.inputs import intask
from ui.catalog import inventory_menu, ingredients_menu, products_menu
from ui.production import production_menu
from ui.selling import booths_menu, reservations_menu, sales_menu
from ui.reports import reports_menu, adjust_menu


def dashboard(api):
    products = api.call('GET', '/api/inventory')
    events = api.call('GET', '/api/events')
    reservations = api.call('GET', '/api/reservations')

    stock = 0
    available = 0
    open_booths = 0
    active_reservations = 0

    for product in products:
        stock += product['stock']
        available += product['available']

    for event in events:
        if event['status'] == 'open':
            open_booths += 1

    for reservation in reservations:
        if reservation['status'] == 'reserved':
            active_reservations += 1

    print()
    print('=' * 72)
    print(' KAKINA FOOD PRODUCTS MFG.')
    print('=' * 72)
    print()
    print(f' Stock: {stock}   Available: {available}   Open booths: {open_booths}   Active reservations: {active_reservations}')
    print()
    print()
    print(' INVENTORY AND PRODUCTION')
    print('-' * 72)
    print(' [1] View finished product inventory')
    print(' [2] Ingredients and purchases')
    print(' [3] Products and recipes')
    print(' [4] Produce chocolates (weigh and count)')
    print()
    print(' ORDERS AND SELLING')
    print('-' * 72)
    print(' [5] Booth events and unsold stock')
    print(' [6] Customer reservations')
    print(' [7] Record an individual sale')
    print()
    print(' REPORTS AND CONTROL')
    print('-' * 72)
    print(' [8] Sales, production and purchase reports')
    print(' [9] Verified inventory adjustment')
    print()
    print(' EXIT')
    print('-' * 72)
    print(' [0] Exit program')
    print()


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
    parser.add_argument(
        '--connect',
        action='store_true',
        help='Connect to an API server already running on port 8765'
    )
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
