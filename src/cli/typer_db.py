from pathlib import Path
import typer

from .typer_cli import _typer_app


db_app = typer.Typer()


@db_app.command("reset")
def reset(db_path: Path = Path("spec_scan_fresh.db")):
    """Reset the SQLite DB to the bare schema (Typer adapter).

    Delegates to the existing implementation in `src.cli.db_commands`.
    """
    if not typer.confirm("This will DROP existing data and recreate the schema. Continue?"):
        typer.echo("Aborted: confirmation declined")
        raise typer.Exit(code=1)

    # Import lazily to avoid circular imports during module import time
    from src.cli import db_commands as _db_commands

    impl = getattr(_db_commands.reset, "callback", _db_commands.reset)
    impl(db_path)


@db_app.command("copy")
def copy(db_path: Path = Path("spec_scan_fresh.db"), dest: Path = typer.Option(...), force: bool = False):
    """Create a filesystem copy of the SQLite database (Typer adapter)."""
    from src.cli import db_commands as _db_commands

    impl = getattr(_db_commands.copy, "callback", _db_commands.copy)
    impl(db_path, dest, force)


@db_app.command("dump")
def dump(view: str, db_path: Path = Path("spec_scan_fresh.db"), limit: int = 100):
    """Dump diagnostic views from the DB (Typer adapter)."""
    from src.cli import db_commands as _db_commands

    impl = getattr(_db_commands.dump, "callback", _db_commands.dump)
    impl(view, db_path, limit)


# Register the `db` subcommands under the main Typer app
_typer_app.add_typer(db_app, name="db")
