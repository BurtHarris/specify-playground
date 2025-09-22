from pathlib import Path
import pytest
from unittest.mock import patch


def test_select_with_arrows_happy_path(tmp_path: Path):
    options = {"a": "Option A", "b": "Option B", "c": "Option C"}

    # Simulate: DOWN, DOWN, ENTER -> selects 'c' by mocking get_key()
    seq = iter(["down", "down", "enter"])  # use semantic tokens returned by get_key()

    import src.lib.selection as sel

    with patch.object(sel, "get_key", new=lambda: next(seq)):
        selected = sel.select_with_arrows(options, prompt_text="Pick", default_key="a")

    assert selected == "c"


def test_select_with_arrows_cancel():
    import typer

    options = {"x": "X", "y": "Y"}

    import src.lib.selection as sel

    # Simulate: ESC -> semantic 'escape' token
    with patch.object(sel, "get_key", new=lambda: "escape"):
        with pytest.raises(typer.Exit):
            sel.select_with_arrows(options)
