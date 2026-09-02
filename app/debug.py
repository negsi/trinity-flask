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
from rich.columns import Columns
from rich.text import Text
from rich.panel import Panel
from rich.console import Group
from rich.layout import Layout

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

def render_llm_request_dashboard(
    user_prompt: str,
    extracted_json: dict | None,
    accumulated_text: str,
    turn_count: int = 1,
    agent_id: str = "Unknown",
):
    """Renders a 2-column side-by-side debug dashboard that shrinks to content height."""

    # 1. Header Rule
    console.rule(
        f"[bold magenta]🤖 LLM Request Debugger (Turn {turn_count}) - Agent: {agent_id}"
    )

    # 2. Panels aufbauen
    input_panel = Panel(
        Text(user_prompt or "-", style="cyan"),
        title="[bold yellow]📥 User Input / Prompt",
        border_style="yellow",
    )

    if extracted_json:
        json_content = JSON.from_data(extracted_json)
    else:
        json_content = Text(
            "Kein JSON / Task-Chain in dieser Antwort", style="dim white"
        )

    right_panel = Panel(
        json_content,
        title="[bold cyan]⚙️ Task-Chain / Structured Plan",
        border_style="cyan",
    )

    # 3. Grid über Table erzeugen (keine festen Ränder, expandiert nicht nach unten)
    grid = Table.grid(expand=True, padding=(0, 1))
    grid.add_column(ratio=1)  # Linke Spalte (50%)
    grid.add_column(ratio=1)  # Rechte Spalte (50%)

    # 4. Inhalt zusammenbauen
    # Wenn Text im LLM Output ist, fügen wir das Panel links unten an.
    # Wenn nicht, lassen wir es einfach komplett weg oder zeigen nur den Prompt!
    has_output = bool(accumulated_text and accumulated_text.strip())

    if has_output:
        output_panel = Panel(
            Text(accumulated_text, style="green"),
            title="[bold green]💬 LLM Response Output",
            border_style="green",
        )
        # Linke Spalte hat zwei Panels (Prompt + Output)
        left_side = Table.grid(expand=True)
        left_side.add_column()
        left_side.add_row(input_panel)
        left_side.add_row(output_panel)
    else:
        # Linke Spalte besteht nur aus dem Prompt (keine unnötigen Lücken)
        left_side = input_panel

    grid.add_row(left_side, right_panel)

    # 5. Rendern
    console.print(grid)
    console.rule("[bold magenta]End of Turn Debug")