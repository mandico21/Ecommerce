import asyncio
import logging
from argparse import ArgumentParser
from pathlib import Path

from yoyo import get_backend, read_migrations

from app.pkg.logger import get_logger
from app.pkg.settings import PostgresSettings, get_settings

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS_DIR = (ROOT / "migrations").resolve()


logger = get_logger("migrate")


def _apply(backend, migrations):
    """Apply all migrations from `migrations`."""
    with backend.lock():
        backend.apply_migrations(backend.to_apply(migrations))


def _rollback(backend, migrations):
    """Rollback all migrations."""
    with backend.lock():
        backend.rollback_migrations(backend.to_rollback(migrations))


def _rollback_one(backend, migrations):
    """Rollback one migration."""
    with backend.lock():
        migrations = backend.to_rollback(migrations)
        for migration in migrations:
            backend.rollback_one(migration)
            break


def _reload(backend, migrations):
    """Rollback all and apply all migrations."""
    with backend.lock():
        backend.rollback_migrations(backend.to_rollback(migrations))
        backend.apply_migrations(backend.to_apply(migrations))


def _list(backend, migrations):
    """List all migrations, and their status (A=Applied, U=Unapplied)."""
    with backend.lock():
        applied = {m.id for m in backend.to_rollback(migrations)}
        for m in migrations:
            status = "A" if m.id in applied else "U"
            logger.info("%s %s", status, m.id)


async def inserter() -> None:
    """Function for pre-insert data before running main application instance"""
    # await asyncio.gather(*tasks)


def to_yoyo_dsn(dsn: str) -> str:
    return dsn.replace("postgresql://", "postgresql+psycopg://", 1)


def run(
    action,
    _postgres: PostgresSettings,
):
    """Run "yoyo-migrations“ based on cli_arguments.

    Notes:
        Before running backend migrations, `run` wiring injections.

    Args:
        action(Callable[..., None]): Target function.
        _postgres: Factory instance of a postgresql driver.

    Returns:
        None
    """
    dsn = to_yoyo_dsn(_postgres.DSN)
    backend = get_backend(dsn)
    migrations = read_migrations(str(MIGRATIONS_DIR))
    logger.info("Found %d migrations", len(migrations))
    action(backend, migrations)


def parse_cli_args():
    """Parse cli arguments."""

    parser = ArgumentParser(description="Apply migrations")
    parser.add_argument("--rollback", action="store_true", help="Rollback migrations")
    parser.add_argument(
        "--rollback-one",
        action="store_true",
        help="Rollback one migration",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Rollback all migration and applying again",
    )
    parser.add_argument(
        "--testing",
        action="store_true",
        help="Rollback all migration and applying again",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List migrations and their status",
    )
    args = parser.parse_args()

    return args


def cli():
    """Dispatch function, based on cli arguments."""

    args = parse_cli_args()
    settings = get_settings()

    if args.list:
        action = _list
    elif args.rollback:
        action = _rollback
    elif args.rollback_one:
        action = _rollback_one
    elif args.reload:
        action = _reload
    else:
        action = _apply
    logger.info(f"Running {action}")

    run(action, settings.POSTGRES)

    if args.testing:
        run(action, settings.POSTGRES)

    if not (args.rollback or args.rollback_one) or not args:
        asyncio.run(inserter())


if __name__ == "__main__":
    cli()
