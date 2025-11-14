import click

# Import essential commands
from swx_api.core.cli.commands.db import db
from swx_api.core.cli.commands.make import make_group
from swx_api.core.cli.commands.tinker import tinker
from swx_api.core.cli.commands.format import format
from swx_api.core.cli.commands.lint import lint


@click.group()
def main():
    """Swifter-FS CLI for managing the project."""
    pass


# ✅ Register only the necessary commands
main.add_command(db, "db")  # Database management
main.add_command(make_group, "make")  # Code scaffolding
main.add_command(tinker, "tinker")  # Interactive shell
main.add_command(format, "format")  # Auto-formatting
main.add_command(lint, "lint")  # Linting & code checks

# ❌ Keep these commented out until needed
# main.add_command(serve, "serve")  # API Server
# main.add_command(test, "test")  # Run tests
# main.add_command(deploy, "deploy")  # Deployment utilities
# main.add_command(seed, "db:seed")  # Seed initial database data
# main.add_command(upgrade, "upgrade")  # Upgrade dependencies
# main.add_command(docker_group, "docker")  # Docker commands


if __name__ == "__main__":
    main(prog_name="swx")
