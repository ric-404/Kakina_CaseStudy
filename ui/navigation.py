"""Shared navigation for all CLI features.

A feature stays open until the operator selects [0] Back.  Every operation
returns a short message, then the feature reloads its records from the API.
"""
from dataclasses import dataclass

import httpx

from ui.client import ApiError
from ui.display import heading, error, notice, success, warn
from ui.inputs import action_menu


@dataclass(frozen=True)
class Feedback:
    text: str
    level: str = 'success'


def saved(message):
    return Feedback(message)


def cancelled(message='No changes were saved.'):
    return Feedback(message, 'notice')


def info(message):
    return Feedback(message, 'info')


def print_feedback(feedback):
    if feedback is None:
        return
    if feedback.level == 'success':
        success(feedback.text)
    elif feedback.level == 'error':
        error(feedback.text)
    elif feedback.level == 'info':
        notice(feedback.text)
    else:
        warn(feedback.text)
    print()


def run_section(title, subtitle, load_records, options, handlers):
    """Display one feature, perform actions, and refresh without going home.

    load_records() displays the feature's current table and returns any data
    needed by the handlers. Handlers return Feedback or None; they never need
    to re-display the main menu themselves.
    """
    last_message = None
    while True:
        heading(title, subtitle)
        records = load_records()
        print_feedback(last_message)

        choice = action_menu(options)
        if choice is None:
            return

        try:
            last_message = handlers[choice](records) or cancelled()
        except (ApiError, ValueError, httpx.HTTPError) as exc:
            last_message = Feedback(f'Could not complete action: {exc}', 'error')
        except KeyboardInterrupt:
            last_message = cancelled('Action cancelled. No changes saved.')
