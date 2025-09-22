"""Interactive selection helpers using Rich for terminal display.

This module provides `select_with_arrows` which displays options and
allows the user to navigate with arrow keys and select an option.

The `readchar` package is a required dependency for interactive use.
"""
from typing import Dict, Optional

import typer

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

console = Console()

# readchar is a hard dependency for the interactive selection helper.
import readchar
from readchar import key as _rkey


def get_key() -> str:
    """Read a single key via readchar and map to semantic tokens.

    Returns:
        One of: 'up', 'down', 'left', 'right', 'enter', 'escape', or the raw
        character string for other keys.
    """
    k = readchar.readkey()
    if k == _rkey.UP:
        return "up"
    if k == _rkey.DOWN:
        return "down"
    if k == _rkey.LEFT:
        return "left"
    if k == _rkey.RIGHT:
        return "right"
    if k == _rkey.ENTER:
        return "enter"
    if k == _rkey.ESC:
        return "escape"
    return k


def select_with_arrows(options: Dict[str, str], prompt_text: str = "Select an option", default_key: Optional[str] = None) -> str:
    """Interactive selection using arrow keys with Rich Live display.

    Args:
        options: Dict with keys as option keys and values as descriptions
        prompt_text: Text to show above the options
        default_key: Default option key to start with

    Returns:
        Selected option key
    """
    option_keys = list(options.keys())
    if default_key and default_key in option_keys:
        selected_index = option_keys.index(default_key)
    else:
        selected_index = 0

    selected_key = None

    def create_selection_panel():
        """Create the selection panel with current selection highlighted."""
        table = Table.grid(padding=(0, 2))
        table.add_column(style="cyan", justify="left", width=3)
        table.add_column(style="white", justify="left")

        for i, key in enumerate(option_keys):
            if i == selected_index:
                table.add_row("▶", f"[cyan]{key}[/cyan] [dim]({options[key]})[/dim]")
            else:
                table.add_row(" ", f"[cyan]{key}[/cyan] [dim]({options[key]})[/dim]")

        table.add_row("", "")
        table.add_row("", "[dim]Use ↑/↓ to navigate, Enter to select, Esc to cancel[/dim]")

        return Panel(
            table,
            title=f"[bold]{prompt_text}[/bold]",
            border_style="cyan",
            padding=(1, 2),
        )

    console.print()

    def run_selection_loop():
        nonlocal selected_key, selected_index
        with Live(create_selection_panel(), console=console, transient=True, auto_refresh=False) as live:
            while True:
                try:
                    key = get_key()
                    if key == "up":
                        selected_index = (selected_index - 1) % len(option_keys)
                    elif key == "down":
                        selected_index = (selected_index + 1) % len(option_keys)
                    elif key == "enter":
                        selected_key = option_keys[selected_index]
                        break
                    elif key == "escape":
                        console.print("\n[yellow]Selection cancelled[/yellow]")
                        raise typer.Exit(1)

                    live.update(create_selection_panel(), refresh=True)

                except KeyboardInterrupt:
                    console.print("\n[yellow]Selection cancelled[/yellow]")
                    raise typer.Exit(1)

    run_selection_loop()

    if selected_key is None:
        console.print("\n[red]Selection failed.[/red]")
        raise typer.Exit(1)

    # Suppress explicit selection print; tracker / later logic will report consolidated status
    return selected_key
