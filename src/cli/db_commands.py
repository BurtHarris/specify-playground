import sqlite3
from pathlib import Path
from typing import Optional

import click
import shutil
import sys
import os


@click.group()
def db():
    """Database maintenance commands (schema reset, diagnostic dumps)."""
    pass


@db.command()
@click.option("--db-path", type=click.Path(dir_okay=False, path_type=Path), default=Path("spec_scan_fresh.db"))
@click.confirmation_option(prompt="This will DROP existing data and recreate the schema. Continue?")
def reset(db_path: Path):
    """Reset the SQLite DB to the bare schema defined in the project.

    The schema is expected to be at `src/services/schema.sql`. If the file
    cannot be found, the command will create an empty database file.
    """
    schema_path = Path(__file__).resolve().parents[2] / "services" / "schema.sql"
    db_path = Path(db_path)
    # Ensure parent dir exists
    db_path.parent.mkdir(parents=True, exist_ok=True)
    # Remove existing DB if present
    if db_path.exists():
        db_path.unlink()
    conn = sqlite3.connect(str(db_path))
    try:
        if schema_path.exists():
            with open(schema_path, "r", encoding="utf-8") as f:
                sql = f.read()
            conn.executescript(sql)
            click.echo(f"Created fresh database at: {db_path}")
        else:
            # Create an empty DB file
            conn.execute("VACUUM;")
            click.echo(f"Schema file not found; created empty DB at: {db_path}")
    finally:
        conn.close()


@db.command()
@click.option("--db-path", type=click.Path(dir_okay=False, path_type=Path), default=Path("spec_scan_fresh.db"), help="Path to the SQLite DB file")
@click.option("--dest", required=True, type=click.Path(dir_okay=False, path_type=Path), help="Destination path for the DB copy")
@click.option("--force", is_flag=True, default=False, help="Overwrite the destination without prompting")
def copy(db_path: Path, dest: Path, force: bool):
    """Create a filesystem copy of the SQLite database (safe, with confirmation).

    Attempts to use SQLite's online backup API for a consistent copy; falls back
    to a plain file copy when that is not possible.
    """
    db_path = Path(db_path)
    dest = Path(dest)

    # Ensure destination parent exists
    dest.parent.mkdir(parents=True, exist_ok=True)

    if dest.exists() and not force:
        if not click.confirm(f"Destination '{dest}' exists. Overwrite?"):
            click.echo("Aborted: destination exists")
            return

    try:
        # Try to perform a consistent backup using sqlite3 backup API
        try:
            src_conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            dest_conn = sqlite3.connect(str(dest))
            with dest_conn:
                src_conn.backup(dest_conn)
            src_conn.close()
            dest_conn.close()
        except Exception:
            # Fallback to file copy which may not be fully consistent if DB is live
            shutil.copy2(str(db_path), str(dest))

        click.echo(f"Database copied to {dest}")
    except Exception as e:
        click.echo(f"Failed to copy database: {e}")
        sys.exit(2)


@db.command()
@click.argument("view", type=click.Choice(["counts", "file_hashes", "directories"], case_sensitive=False))
@click.option("--db-path", type=click.Path(dir_okay=False, path_type=Path), default=Path("spec_scan_fresh.db"))
@click.option("--limit", type=int, default=100, help="Row limit for printable views")
def dump(view: str, db_path: Path, limit: int):
    """Dump diagnostic views from the DB.

    Supported views:
      - counts: simple counts of key tables
      - file_hashes: print rows from file_hashes (path,size,mtime,hash)
      - directories: print rows from directories table
    """
    db_path = Path(db_path)
    if not db_path.exists():
        click.echo(f"Database not found: {db_path}", err=True)
        raise click.Abort()

    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    try:
        if view == "counts":
            cur.execute("SELECT COUNT(*) FROM file_hashes")
            fh = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM directories")
            d = cur.fetchone()[0]
            click.echo(f"file_hashes: {fh}")
            click.echo(f"directories: {d}")
        elif view == "file_hashes":
            cur.execute("SELECT path,size,mtime,hash FROM file_hashes ORDER BY id LIMIT ?", (limit,))
            rows = cur.fetchall()
            for p,s,m,h in rows:
                click.echo(f"{p},{s},{m},{h}")
        elif view == "directories":
            cur.execute("SELECT id,path,scan_time FROM directories ORDER BY id LIMIT ?", (limit,))
            rows = cur.fetchall()
            for id_,p,st in rows:
                click.echo(f"{id_},{p},{st}")
    finally:
        conn.close()
