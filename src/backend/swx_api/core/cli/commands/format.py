import shutil
import subprocess
import os
import click


@click.command()
def format():
    """
    Automatically format the code using ruff and pre-commit.
    - Runs `ruff format` to apply code style.
    - Runs `pre-commit` hooks if installed and inside a Git repository.
    """

    # ✅ Check if `ruff` is installed
    if shutil.which("ruff") is None:
        click.secho(
            "❌ 'ruff' is not installed. Install it with: pip install ruff",
            fg="red",
        )
        return

    # ✅ Run `ruff format`
    try:
        click.secho("🎨 Running ruff format...", fg="cyan")
        subprocess.run(["ruff", "format", "."], check=True)
        click.secho("✅ Ruff formatting complete!", fg="green")
    except subprocess.CalledProcessError as e:
        click.secho(f"❌ Ruff formatting failed: {e}", fg="red")
        return

    # ✅ Check if `pre-commit` is installed
    if shutil.which("pre-commit") is None:
        click.secho(
            "⚠️ 'pre-commit' is not installed. Skipping pre-commit hooks...",
            fg="yellow",
        )
        return

    # ✅ Check if inside a Git repository
    if not os.path.isdir(".git"):
        click.secho("⚠️ Not a Git repository. Skipping pre-commit hooks...", fg="yellow")
        return

    # ✅ Run `pre-commit` hooks
    try:
        click.secho("🛠 Running pre-commit hooks...", fg="cyan")
        subprocess.run(["pre-commit", "run", "--all-files"], check=True)
        click.secho("✅ Pre-commit hooks executed successfully!", fg="green")
    except subprocess.CalledProcessError as e:
        click.secho(f"⚠️ Pre-commit hooks failed: {e}", fg="yellow")


if __name__ == "__main__":
    format()
