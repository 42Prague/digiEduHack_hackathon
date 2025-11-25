import os
import shutil
import subprocess
import click


@click.command()
@click.option("--fix", is_flag=True, help="Automatically fix issues with ruff.")
@click.option("--unsafe-fixes", is_flag=True, help="Enable unsafe fixes with ruff.")
def lint(fix, unsafe_fixes):
    """
    Run linting tools:
    - Ruff (with optional auto-fixing)
    - MyPy (type checks)
    - Pre-commit (if installed and in a Git repository)
    """

    # ✅ Ensure `ruff` is installed
    if shutil.which("ruff") is None:
        click.secho("❌ 'ruff' is not installed. Install it with: pip install ruff", fg="red")
        return

    # ✅ Build `ruff` command dynamically
    ruff_command = ["ruff", "check", "swx_app"]
    if fix:
        ruff_command.append("--fix")
    if unsafe_fixes:
        ruff_command.append("--unsafe-fixes")

    click.secho("🔍 Running Ruff for linting...", fg="cyan")
    try:
        subprocess.run(ruff_command, check=True)
        click.secho("✅ Ruff check completed!", fg="green")
    except subprocess.CalledProcessError:
        click.secho("❌ Ruff check failed!", fg="red")

    # ✅ Ensure `mypy` is installed
    if shutil.which("mypy") is None:
        click.secho("❌ 'mypy' is not installed. Install it with: pip install mypy", fg="red")
        return

    # ✅ Run MyPy type checks
    click.secho("🔍 Running MyPy type checks on swx_api/...", fg="cyan")
    try:
        subprocess.run(["mypy", "swx_api"], check=True)
        click.secho("✅ MyPy check completed!", fg="green")
    except subprocess.CalledProcessError:
        click.secho("❌ MyPy check failed!", fg="red")

    # ✅ Ensure `pre-commit` is installed
    if shutil.which("pre-commit") is None:
        click.secho("⚠️ 'pre-commit' is not installed. Skipping pre-commit hooks...", fg="yellow")
    else:
        # ✅ Check if inside a Git repository
        if not os.path.isdir(".git"):
            click.secho("⚠️ Not a Git repository. Skipping pre-commit hooks...", fg="yellow")
        else:
            click.secho("🔍 Running pre-commit checks...", fg="cyan")
            try:
                subprocess.run(["pre-commit", "run", "--all-files"], check=True)
                click.secho("✅ Pre-commit hooks executed successfully!", fg="green")
            except subprocess.CalledProcessError:
                click.secho("❌ Pre-commit hooks failed!", fg="red")

    click.secho("✅ All linting checks completed!", fg="green")


if __name__ == "__main__":
    lint()
