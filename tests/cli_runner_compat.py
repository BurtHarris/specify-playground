import io
import contextlib
import importlib
import click


class CliRunner:
    """Compatibility shim that prefers Click's CliRunner but can
    also invoke Typer app callables by routing output to StringIO and
    returning a simple result object with `output` and `exit_code`.

    Tests may import this as a drop-in replacement for
    `click.testing.CliRunner` while migration to Typer proceeds.
    """

    def __init__(self):
        # click.testing may not be exposed as an attribute on some packaging
        # layouts; import the testing submodule explicitly as a fallback.
        try:
            testing = getattr(click, "testing")
        except AttributeError:
            testing = importlib.import_module("click.testing")

        self._click_runner = testing.CliRunner()

    def invoke(self, target, args=None, catch_exceptions=True, input=None):
        args = args or []
        # Prefer the real Click runner when the target is a click.Command
        try:
            if isinstance(target, click.Command):
                # forward input when using Click's CliRunner
                return self._click_runner.invoke(target, args, input=input, catch_exceptions=catch_exceptions)
        except Exception:
            # Fall through to generic invocation
            pass

        # Generic callable invocation (Typer app or other callables)
        buf_out = io.StringIO()
        buf_err = io.StringIO()

        exit_code = 0
        # Provide `input` to code that reads from stdin (click prompts etc.)
        stdin_buf = io.StringIO(input if input is not None else "")
        with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err), contextlib.redirect_stdin(stdin_buf):
            try:
                # Typer apps are callable: app(prog_name=..., args=[...])
                target(prog_name="specify-typer", args=args)
            except SystemExit as e:
                exit_code = e.code if isinstance(e.code, int) else 0
            except Exception:
                if catch_exceptions:
                    exit_code = 1
                else:
                    raise

        output = buf_out.getvalue() + buf_err.getvalue()

        class Result:
            def __init__(self, output, exit_code):
                self.output = output
                self.exit_code = exit_code

        return Result(output, exit_code)
