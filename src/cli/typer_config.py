from pathlib import Path
import typer

from .typer_cli import _typer_app


config_app = typer.Typer()


@config_app.command("show")
def show(key: str = None):
    """Show configuration values (Typer adapter)."""
    from src.cli import config_commands as _config

    impl = getattr(_config.show, "callback", _config.show)
    # click command may expect (ctx, key) or just (key)
    try:
        impl(key)
    except TypeError:
        # fallback for click-style signatures
        impl(None, key)


@config_app.command("set")
def set_value(key: str, value: str):
    """Set a configuration key (Typer adapter)."""
    from src.cli import config_commands as _config

    impl = getattr(_config.set, "callback", _config.set)
    try:
        impl(key, value)
    except TypeError:
        impl(None, key, value)


@config_app.command("history")
def history(key: str):
    """Show change history for a config key (Typer adapter)."""
    from src.cli import config_commands as _config

    impl = getattr(_config.history, "callback", _config.history)
    impl(key)


@config_app.command("clear-history")
def clear_history(key: str):
    """Clear change history for a config key (Typer adapter)."""
    from src.cli import config_commands as _config

    impl = getattr(_config.clear_history, "callback", _config.clear_history)
    impl(key)


@config_app.command("reset")
def reset_config():
    """Reset configuration to defaults (Typer adapter)."""
    from src.cli import config_commands as _config

    impl = getattr(_config.reset, "callback", _config.reset)
    impl()


# Register the `config` subcommands under the main Typer app
_typer_app.add_typer(config_app, name="config")
