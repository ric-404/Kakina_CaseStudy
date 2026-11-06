"""JSON storage and reusable validation for the Kakina CLI application."""

import json
import os
import tempfile
from contextlib import contextmanager
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

try:
    import fcntl
except ImportError:  # Windows
    fcntl = None

DATA_PATH = Path(os.environ.get('KAKINA_DATA', Path(__file__).with_name('kakina_data.json')))

SEED_PRODUCTS = [
    ('Purong Cacao (Tablea) Pouch 100g (11 pcs)', 120),
    ('60% Dark Chocolate with Pistachio Nuts Pouch 20g', 40),
    ('60% Dark Chocolate with Pistachio Nuts Bar 60g', 150),
    ('60% Dark Chocolate with Mango Bits Pouch 20g', 40),
    ('60% Dark Chocolate with Mango Bits Bar 60g', 150),
]


class RuleError(ValueError):
    """A business operation cannot be completed safely."""


def new_state():
    products = [dict(id=i, name=name, price=price, stock=0, active=True, recipe=[])
                for i, (name, price) in enumerate(SEED_PRODUCTS, 1)]
    return {
        'next_id': 6, 'products': products, 'ingredients': [], 'purchases': [],
        'production': [], 'events': [], 'reservations': [], 'sales': [],
        'adjustments': [], 'ingredient_adjustments': [],
    }


@contextmanager
def locked_state(save=False):
    """Safely load and, on success only, atomically save the JSON records."""
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(str(DATA_PATH) + '.lock', 'a+', encoding='utf-8') as lock:
        if fcntl:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX if save else fcntl.LOCK_SH)
        try:
            if DATA_PATH.exists():
                try:
                    with DATA_PATH.open(encoding='utf-8') as f:
                        state = json.load(f)
                except (ValueError, UnicodeError) as exc:
                    raise RuleError('JSON data file is damaged. Restore your backup.') from exc
            else:
                state = new_state()
            for key in ('ingredients', 'purchases', 'production', 'events',
                        'reservations', 'sales', 'adjustments', 'ingredient_adjustments'):
                state.setdefault(key, [])
            for product in state.get('products', []):
                product.setdefault('recipe', [])
            for row in state['ingredients']:
                row.setdefault('display_unit', row['unit'])
            yield state
            if save:
                fd, temp = tempfile.mkstemp(prefix='kakina_', suffix='.tmp', dir=DATA_PATH.parent)
                try:
                    with os.fdopen(fd, 'w', encoding='utf-8') as f:
                        json.dump(state, f, indent=2, ensure_ascii=False)
                        f.flush()
                        os.fsync(f.fileno())
                    os.replace(temp, DATA_PATH)
                finally:
                    if os.path.exists(temp):
                        os.remove(temp)
        finally:
            if fcntl:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def read():
    with locked_state() as state:
        return state


def execute(function, *args, **kwargs):
    with locked_state(save=True) as state:
        return function(state, *args, **kwargs)


def get(state, collection, identifier):
    for record in state[collection]:
        if record['id'] == identifier:
            return record
    raise RuleError(f'{collection} record not found: {identifier}')


def next_id(state):
    result = state['next_id']
    state['next_id'] += 1
    return result


def as_decimal(value):
    return Decimal(str(value))


def decimal_amount(value, label='Quantity', allow_zero=False, places=3):
    if isinstance(value, bool) or value is None:
        raise RuleError(f'{label} must be a valid number.')
    try:
        amount = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        raise RuleError(f'{label} must be a valid number.') from None
    if (not amount.is_finite() or amount < 0 or (amount == 0 and not allow_zero)
            or amount > 1_000_000_000 or amount != amount.quantize(Decimal(10) ** -places)):
        raise RuleError(f'{label} must be positive and have at most {places} decimal places.'
                        if not allow_zero else f'{label} must be nonnegative with at most {places} decimals.')
    return amount


def whole_number(value, label='Quantity', allow_zero=False):
    if isinstance(value, bool):
        raise RuleError(f'{label} must be a whole number.')
    if isinstance(value, int):
        number = value
    elif isinstance(value, str) and value.strip().isdigit() and len(value.strip()) <= 12:
        number = int(value.strip())
    else:
        raise RuleError(f'{label} must be a whole number.')
    if number < (0 if allow_zero else 1) or number > 1_000_000_000:
        raise RuleError(f'{label} is outside the allowed range.')
    return number


def peso(value, label='Amount', allow_zero=True):
    amount = decimal_amount(value, label, allow_zero=allow_zero, places=2)
    return float(amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


def text_value(value, label='Name', max_length=100):
    if not isinstance(value, str):
        raise RuleError(f'{label} must be text.')
    value = value.strip()
    if not value or len(value) > max_length or any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise RuleError(f'{label} must be 1-{max_length} printable characters.')
    return value


def optional_text(value, label='Note', max_length=300):
    if value is None or value == '':
        return ''
    return text_value(value, label, max_length)


def valid_date(value):
    if not isinstance(value, str):
        raise RuleError('Enter a date as YYYY-MM-DD.')
    try:
        day = date.fromisoformat(value)
        if day.isoformat() != value:
            raise ValueError()
        return value
    except ValueError:
        raise RuleError('Enter a real date as YYYY-MM-DD.') from None


def valid_choice(value, options, label='Choice'):
    if value not in options:
        raise RuleError(f'{label} must be one of: {", ".join(options)}.')
    return value


def active_product(state, product_id):
    product = get(state, 'products', product_id)
    if not product['active']:
        raise RuleError('This product is archived.')
    return product
