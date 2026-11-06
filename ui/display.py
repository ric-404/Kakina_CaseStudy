"""Reusable plain-text tables and menus. No colors or third-party UI library."""
import os
import shutil
import sys


def clear_screen():
    if sys.stdout.isatty():
        os.system('cls' if os.name == 'nt' else 'clear')


def heading(title, subtitle=''):
    clear_screen()
    print('\n' + '=' * 72)
    print(' ' + title.upper())
    print('=' * 72)
    if subtitle:
        print(' ' + subtitle)
    print()


def section(title, description=''):
    print('\n' + title.upper())
    print('-' * min(72, shutil.get_terminal_size((88, 24)).columns - 2))
    if description:
        print(description)


def step(number, title, description='', new_page=False, context=''):
    if new_page:
        heading(context or title)
    section(f'Step {number} - {title}', description)


def notice(message):
    print('  [INFO]', message)


def warn(message):
    print('  [NOTICE]', message)


def success(message):
    print('  [SAVED]', message)


def error(message):
    print('  [ERROR]', message)


def pesos(amount):
    return f'PHP {float(amount):,.2f}'


def qty_text(quantity):
    return f'{float(quantity):g}'


def wrap_name(value, width):
    """Only wrap long text fields; keep quantities and amounts on one line."""
    words = str(value).split()
    lines, current = [], ''
    for word in words:
        while len(word) > width:
            if current:
                lines.append(current)
                current = ''
            lines.append(word[:width])
            word = word[width:]
        if not word:
            continue
        if not current:
            current = word
        elif len(current) + 1 + len(word) <= width:
            current += ' ' + word
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or ['']


def show_table(headers, rows, title='RECORDS'):
    """Print a bordered table; on a narrow terminal, print bordered cards."""
    section(title)
    if not rows:
        notice('No records found.')
        return
    rows = [[str(x) for x in row] for row in rows]
    headers = [str(x) for x in headers]
    widths = [min(max(len(h), max(len(r[i]) for r in rows)), 31 if i <= 2 else 19)
              for i, h in enumerate(headers)]
    required = sum(widths) + 3 * len(widths) + 1
    terminal = shutil.get_terminal_size((96, 24)).columns
    if required > max(45, terminal - 2):
        for row in rows:
            print('  +' + '-' * (max(38, min(terminal - 6, 74))) + '+')
            for header, value in zip(headers, row):
                for line in wrap_name(value, max(18, min(terminal - len(header) - 9, 45))):
                    print(f'  | {header}: {line}')
            print('  +' + '-' * (max(38, min(terminal - 6, 74))) + '+')
        print()
        return
    line = '+' + '+'.join('-' * (w + 2) for w in widths) + '+'
    print(line)
    print('|' + '|'.join(f' {h:<{w}} ' for h, w in zip(headers, widths)) + '|')
    print(line)
    for row in rows:
        cells = [wrap_name(v, w) for v, w in zip(row, widths)]
        for index in range(max(map(len, cells))):
            print('|' + '|'.join(f' {(cell[index] if index < len(cell) else ""):<{w}} '
                               for cell, w in zip(cells, widths)) + '|')
        print(line)
    print()


def show_summary(title, fields):
    show_table(['Field', 'Value'], [(label, value) for label, value in fields], title)


def main_menu(title, dashboard, groups):
    heading(title, dashboard)
    for group, entries in groups:
        section(group)
        for number, label in entries:
            print(f' [{number}] {label}')
    print()


def shorten(value, width):
    """Keep numeric and status columns a single cell."""
    value = str(value)
    return value if len(value) <= width else value[:max(1, width - 1)] + '~'
