from datetime import date
from decimal import Decimal, InvalidOperation
from ui.display import section, warn


def ask(label, default=None):
    suffix = f' [{default}]' if default is not None and str(default) else ''
    value = input(f'\n  {label}{suffix}: ').strip()
    if not value and default is not None:
        return str(default)
    return value


def ask_name(label, max_length=100):
    while True:
        value = ask(label)
        if value and len(value) <= max_length:
            if all(ord(char) >= 32 for char in value):
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
        default = '' if blank_allowed else date.today().isoformat()
        value = ask(label, default)
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
            within_range = minimum <= number <= maximum
            permitted = allowed is None or number in allowed
            if within_range and permitted:
                return number
        warn('Enter a valid number shown in the menu or table.')


def numberask(label, default=None, places=2, allow_zero=True, maximum=None):
    while True:
        text = ask(label, default)
        try:
            value = Decimal(text)
            limit = Decimal(str(maximum)) if maximum is not None else Decimal('1000000000')
            whole_and_decimal = value == value.quantize(Decimal(10) ** -places)

            if value.is_finite() and value >= 0 and value <= limit:
                if (allow_zero or value > 0) and whole_and_decimal:
                    return float(value)
        except (ValueError, InvalidOperation):
            pass
        warn(f'Enter a nonnegative value with at most {places} decimals.')


def moneyask(label, default=None, allow_zero=True):
    return numberask(label, default, 2, allow_zero)


def costask(label, default=None):
    return numberask(label, default, 4)


def amountask(label, unit='g', default=None, maximum=None):
    if unit == 'kg':
        places = 6
    elif unit == 'g':
        places = 3
    else:
        places = 0

    result = numberask(label, default, places, allow_zero=False, maximum=maximum)
    return int(result) if unit == 'pcs' else result


def nonnegative_amount(label, unit='g', default=0):
    if unit == 'kg':
        places = 6
    elif unit == 'g':
        places = 3
    else:
        places = 0

    value = numberask(label, default, places)
    return int(value) if unit == 'pcs' else value


def choose(label, options, default=None):
    section(label)
    for number, option in enumerate(options, 1):
        print(f'    [{number}] {option}')

    selected = options.index(default) + 1 if default in options else None
    number = intask('Select option', selected, 1, len(options))
    return options[number - 1]


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
    section('OPTIONS')
    for number, option in enumerate(options, 1):
        title = option[1]
        print(f'    [{number}] {title}')
    print('    [0] Back')

    selection = intask('Choose option', minimum=0, maximum=len(options))
    if selection == 0:
        return None
    return options[selection - 1][0]
