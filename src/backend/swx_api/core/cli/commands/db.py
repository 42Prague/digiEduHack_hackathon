import click
import subprocess
import shutil


@click.group()
def db():
    """Database management commands for migrations, setup, and seeding."""
    pass


@db.command()
def setup():
    """
    Setup the database:
    - Runs migrations to ensure the database is up-to-date.
    - Creates the initial superuser (if applicable).
    - Checks database readiness.
    """
    try:
        subprocess.run(["python", "swx_api/core/database/db_setup.py"], check=True)
        click.secho("✅ Database setup completed successfully!", fg="green")
    except subprocess.CalledProcessError:
        click.secho("❌ Error: Database setup failed!", fg="red")


@db.command()
def seed():
    """
    Seed the database with initial data:
    - Populates essential tables (e.g., languages, roles).
    - Used for initial application setup.
    """
    try:
        subprocess.run(["python", "swx_api/core/database/db_seed.py"], check=True)
        click.secho("✅ Database seeding completed successfully!", fg="green")
    except subprocess.CalledProcessError:
        click.secho("❌ Error: Database seeding failed!", fg="red")


@db.command()
def migrate():
    """
    Run Alembic migrations:
    - Applies all unapplied migrations to the database.
    - Ensures the schema is up-to-date.
    """
    if not shutil.which("alembic"):
        click.secho("❌ Error: Alembic is not installed. Run `pip install alembic`.", fg="red")
        return

    try:
        subprocess.run(["alembic", "upgrade", "head"], check=True)
        click.secho("✅ Migrations applied successfully!", fg="green")
    except subprocess.CalledProcessError:
        click.secho("❌ Error: Migration process failed!", fg="red")


@db.command()
def downgrade():
    """
    Rollback the last Alembic migration:
    - Used to undo the most recent database migration.
    - Useful when debugging migration issues.
    """
    if not shutil.which("alembic"):
        click.secho("❌ Error: Alembic is not installed. Run `pip install alembic`.", fg="red")
        return

    try:
        subprocess.run(["alembic", "downgrade", "-1"], check=True)
        click.secho("✅ Last migration rolled back successfully!", fg="yellow")
    except subprocess.CalledProcessError:
        click.secho("❌ Error: Downgrade process failed!", fg="red")


@db.command()
@click.argument("message")
def revision(message):
    """
    Create a new Alembic migration revision:
    - Automatically generates a new migration script based on model changes.

    Usage:
        python cli.py db revision "Added new column to users table"
    """
    if not shutil.which("alembic"):
        click.secho("❌ Error: Alembic is not installed. Run `pip install alembic`.", fg="red")
        return

    try:
        subprocess.run(["alembic", "revision", "--autogenerate", "-m", message], check=True)
        click.secho(f"✅ Migration revision created: {message}", fg="green")
    except subprocess.CalledProcessError:
        click.secho("❌ Error: Migration revision failed!", fg="red")


if __name__ == "__main__":
    db()
