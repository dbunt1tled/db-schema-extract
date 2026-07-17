from __future__ import  annotations

from pydantic import BaseModel
from sqlalchemy import Connection, inspect
from sqlalchemy.ext.asyncio import create_async_engine

SYS_SCHEMAS = {"information_schema", "performance_schema", "sys", "mysql"}

class Column(BaseModel):
    name: str
    type: str
    nullable: bool
    is_pk: bool = False
    is_fk: bool = False

class ForeignKey(BaseModel):
    columns: list[str]
    ref_schema: str | None = None
    ref_table: str
    ref_columns: list[str] = []

class Table(BaseModel):
    schema_name: str | None = None
    name: str
    columns: list[Column] = []
    fks: list[ForeignKey] = []

    @property
    def qualified(self) -> str:
        return f"{self.schema_name}.{self.name}" if self.schema_name else self.name

def _reflect(sync_conn: Connection, requested: list[str]) -> list[Table]:
    inspection = inspect(sync_conn)
    schemas: list[str|None] = [None]
    if requested == ["*"]:
        try:
            schemas = [s for s in inspection.get_schema_names() if s not in SYS_SCHEMAS]
        except NotImplementedError:
            schemas = [None]
    elif requested:
        schemas = list(requested)
    else:
        # По умолчанию — только база, к которой подключились
        # (для MySQL это database из URL, для SQLite — 'main').
        schemas = [inspection.default_schema_name]

    tables: list[Table] = []
    for schema in schemas:
        for name in inspection.get_table_names(schema=schema):
            pk_cols = set(
                inspection.get_pk_constraint(name, schema=schema).get("constrained_columns") or []
            )

            fk_col_names: set[str] = set()
            fks: list[ForeignKey] = []
            for fk in inspection.get_foreign_keys(name, schema=schema):
                constrained = fk.get("constrained_columns") or []
                fk_col_names.update(constrained)
                fks.append(ForeignKey(
                    columns=constrained,
                    ref_schema=fk.get("referred_schema"),
                    ref_table=fk.get("referred_table") or "",
                    ref_columns=fk.get("referred_columns") or [],
                ))

            columns = [
                Column(
                    name=c["name"],
                    type=str(c["type"]),
                    nullable=bool(c.get("nullable", True)),
                    is_pk=c["name"] in pk_cols,
                    is_fk=c["name"] in fk_col_names,
                )
                for c in inspection.get_columns(name, schema=schema)
            ]

            tables.append(Table(schema_name=schema, name=name, columns=columns, fks=fks))
    return tables

async def get_schema(url: str, schemas: list[str] | None = None) -> list[Table]:
    engine = create_async_engine(url)
    try:
        async with engine.connect() as conn:
            return await conn.run_sync(_reflect, schemas or [])
    finally:
        await engine.dispose()