import shutil
import subprocess
import click


@click.command()
@click.option(
    "--coverage", is_flag=True, help="Run tests with coverage reporting."
)
@click.option(
    "--watch", is_flag=True, help="Run tests in watch mode (rerun on file changes)."
)
def test(coverage: bool, watch: bool):
    """
    Run all unit tests using pytest.

    Options:
    - `--coverage` → Run tests with coverage report.
    - `--watch` → Automatically rerun tests when files change.
    """

    # ✅ Ensure `pytest` is installed
    if shutil.which("pytest") is None:
        click.secho("❌ 'pytest' is not installed. Install it with: pip install pytest", fg="red")
        return

    # ✅ Construct the base `pytest` command
    pytest_command = ["pytest"]

    # ✅ Add coverage flag if requested
    if coverage:
        pytest_command.extend(["--cov=swx_api", "--cov-report=term-missing"])

    # ✅ Add watch mode if requested (requires pytest-watch)
    if watch:
        if shutil.which("pytest-watch") is None:
            click.secho(
                "⚠️ 'pytest-watch' is not installed. Install it with: pip install pytest-watch",
                fg="yellow",
            )
            return
        pytest_command = ["pytest-watch"]

    click.secho("🧪 Running tests...", fg="cyan")
    try:
        subprocess.run(pytest_command, check=True)
        click.secho("✅ Tests completed successfully!", fg="green")
    except subprocess.CalledProcessError:
        click.secho("❌ Tests failed!", fg="red")


if __name__ == "__main__":
    test()
