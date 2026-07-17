from __future__ import annotations

import argparse
import asyncio
import os
import sys

from src.config.settings import Database, Settings, load_settings
from src.db.introspect import get_schema
from src.render.render import render


async def process_one(db: Database, s: Settings) -> tuple[str, list[str] | Exception]:
    try:
        tables = await get_schema(db.url, db.schemas)
    except Exception as e:
        return db.name, e

    n = len(tables)
    n_fk = sum(len(t.fks) for t in tables)
    print(f"[{db.name}] Tables: {n}, FKs: {n_fk}")
    if n >= s.big_threshold and s.export_format in ("png", "jpeg") and s.split == "none":
        print(f"[{db.name}] Warning: {n} Big database detected, set EXPORT_FORMAT=svg or SPLIT=components")
    base = os.path.join(s.output_dir, db.name)
    try:
        paths = await asyncio.to_thread(
            render, tables, base,
            fmt=s.export_format, dpi=s.dpi,
            show_relations=s.show_relations, split=s.split,
            layout=s.layout, grid_columns=s.grid_columns,
        )
    except Exception as e:
        return db.name, e
    return db.name, paths


async def run(env_path: str) -> int:
    try:
        s = load_settings(env_path=env_path)
    except Exception as e:
        print(f"Error loading settings({env_path}):\n{e}", file=sys.stderr)
        return 1

    os.makedirs(s.output_dir, exist_ok=True)
    print(
        f"Output directory: {s.output_dir}. DBs: {len(s.databases)}. Type: {s.export_format}. Relations: {'yes' if s.show_relations else 'no'}. Split: {s.split} \n"
    )
    results = await asyncio.gather(*(process_one(db, s) for db in s.databases))
    ok = 0
    for name, outcome in results:
        if isinstance(outcome, Exception):
            print(f"[{name}] Error: {outcome}", file=sys.stderr)
        else:
            for path in outcome:
                print(f"[{name}] Saved to {path}")
                ok += 1
    print(f"Total: {ok}/{len(s.databases)} files saved.")

    return 0 if ok else 2


def cli() -> int:
    p = argparse.ArgumentParser(description="MySQL DB diagram")
    p.add_argument("--env", default=".env", help=".env path")
    args = p.parse_args()
    return asyncio.run(run(args.env))


if __name__ == "__main__":
    raise SystemExit(cli())
