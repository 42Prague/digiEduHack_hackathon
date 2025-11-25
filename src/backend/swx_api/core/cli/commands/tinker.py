import os
import code
import click
import sys


@click.command()
def tinker():
    """Start an interactive Python shell with project context loaded."""
    click.secho("\n🐍 Entering Swifter-FS interactive shell (exit with Ctrl+D)...", fg="cyan")

    # ✅ If running inside an interactive session, use `code.interact`
    if sys.stdin.isatty():
        try:
            # ✅ Start an interactive shell with global variables
            code.interact(local=globals())
        except SystemExit:
            pass  # Prevents the script from exiting abruptly
    else:
        # ✅ Fall back to launching a new Python shell process
        os.system("python")


if __name__ == "__main__":
    tinker()
