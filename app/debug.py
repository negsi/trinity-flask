"""
Debugging Utilities Module.

Provides formatted terminal logging and object inspection using the Rich library.
"""

from rich.pretty import pprint
from rich.console import Console
from rich.table import Table
from rich.json import JSON
from rich import inspect
from rich.traceback import Traceback

console = Console()


def _sa_to_dict(obj):
    """
    Helper function to convert a SQLAlchemy model object into a dictionary.

    Args:
        obj: The object to convert.

    Returns:
        dict | Any: Dictionary of object attributes excluding private fields.
    """
    if not hasattr(obj, "__dict__"):
        return obj
    return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}


def debug(obj, label=None, *, json=False, table=False, inspect_obj=False):
    """
    Rich debugging printer for objects, exceptions, JSON payload, and tables.

    Args:
        obj: The target object or exception to debug.
        label (str, optional): Optional visual header rule.
        json (bool): If True, renders the object formatted as JSON.
        table (bool): If True, renders a list of dicts as a Rich table.
        inspect_obj (bool): If True, inspects object methods and attributes.
    """
    if label:
        console.rule(f"[bold cyan]{label}")

    # Exception handling with full stack trace and local variables
    if isinstance(obj, BaseException):
        tb = Traceback.from_exception(
            type(obj),
            obj,
            obj.__traceback__,
            show_locals=True,
            suppress=[]
        )
        console.print(tb)
        return

    # Normalize SQLAlchemy instance dictionary
    if hasattr(obj, "__dict__"):
        obj = _sa_to_dict(obj)

    # Normalize lists of SQLAlchemy objects
    if isinstance(obj, list) and len(obj) > 0 and hasattr(obj[0], "__dict__"):
        obj = [_sa_to_dict(o) for o in obj]

    # Render formatted JSON payload
    if json:
        console.print(JSON.from_data(obj))
        return

    # Render tabular data for list of dictionaries
    if table and isinstance(obj, list) and len(obj) > 0 and isinstance(obj[0], dict):
        t = Table(show_header=True, header_style="bold magenta")

        for col in obj[0].keys():
            t.add_column(col)

        for row in obj:
            t.add_row(*[str(v) for v in row.values()])

        console.print(t)
        return

    # Render full object inspection
    if inspect_obj:
        inspect(obj, methods=True)
        return

    # Fallback pretty printing
    pprint(obj)
