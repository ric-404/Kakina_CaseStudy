"""Keyboard input helpers shared by every terminal form."""
from datetime import date
from decimal import Decimal, InvalidOperation

from ui.display import section, warn


def ask(label, default=None):
    """Add breathing room between form questions."""
    suffix = f' [{default}]' if default is not None and str(default) else ''
    value = input(f'\n  {label}{suffix}: ').strip()
    return str(default) if not value and default is not None else value


def ask_name(label, max_length=100):
    while True:
        value = ask(label)
        if value and len(value) <= max_length and all(ord(c) >= 32 for c in value):
            return value
        warn(f'Enter 1 to {max_length} printable characters.')


def ask_optional(label, max_length=300):
    while True:
        value = ask(label)
        if len(value) <= max_length:
            return value
        warn('Text is too long.')


def ask_date(label, blank_allowed=False):
    while True:
        value = ask(label, '' if blank_allowed else date.today().isoformat())
        if blank_allowed and not value:
            return ''
        try:
            if date.fromisoformat(value).isoformat() == value:
                return value
        except ValueError:
            pass
        warn('Enter a real date as YYYY-MM-DD.')


def intask(label, default=None, minimum=1, maximum=1_000_000_000, allowed=None):
    while True:
        text = ask(label, default)
        if text.isdigit():
            number = int(text)
            if minimum <= number <= maximum and (allowed is None or number in allowed):
                return number
        warn('Enter a valid number shown in the menu or table.')


def numberask(label, default=None, places=2, allow_zero=True, maximum=None):
    while True:
        text = ask(label, default)
        try:
            value = Decimal(text)
            if (value.is_finite() and value >= 0 and (allow_zero or value > 0)
                    and value <= (Decimal(str(maximum)) if maximum is not None else Decimal('1000000000'))
                    and value == value.quantize(Decimal(10) ** -places)):
                return float(value)
        except (ValueError, InvalidOperation):
            pass
        warn(f'Enter a nonnegative value with at most {places} decimals.')


def moneyask(label, default=None, allow_zero=True):
    return numberask(label, default, 2, allow_zero)


def costask(label, default=None):
    return numberask(label, default, 4)


def amountask(label, unit='g', default=None, maximum=None):
    places = 6 if unit == 'kg' else 3 if unit == 'g' else 0
    result = numberask(label, default, places, allow_zero=False, maximum=maximum)
    return int(result) if unit == 'pcs' else result


def nonnegative_amount(label, unit='g', default=0):
    places = 6 if unit == 'kg' else 3 if unit == 'g' else 0
    value = numberask(label, default, places)
    return int(value) if unit == 'pcs' else value


def choose(label, options, default=None):
    section(label)
    for i, entry in enumerate(options, 1):
        print(f'    [{i}] {entry}')
    selected = options.index(default) + 1 if default in options else None
    result = intask('Select option', selected, 1, len(options))
    return options[result - 1]


def confirm(label, default=True):
    default_input = 'y' if default else 'n'
    while True:
        answer = ask(f'{label} (y/n)', default_input).lower()
        if answer in ('y', 'yes'):
            return True
        if answer in ('n', 'no'):
            return False
        warn('Enter y or n.')


def action_menu(options):
    """Return an action key. [0] goes to the previous menu."""
    section('OPTIONS')
    for i, (_, title) in enumerate(options, 1):
        print(f'    [{i}] {title}')
    print('    [0] Back')
    selection = intask('Choose option', minimum=0, maximum=len(options))
    return None if selection == 0 else options[selection - 1][0]
