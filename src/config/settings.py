from __future__ import annotations

from typing import Literal

from dotenv import dotenv_values
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ExportFormat = Literal["png", "svg", "jpeg"]
SplitMode = Literal["none", "scheme", "components"]
LayoutMode = Literal["dot", "grid", "neato", "fdp", "sfdp", "osage"]

_ALLOWED_MYSQL_DRV = ("mysql+aiomysql://", "mysql+asyncmy://")

class Database(BaseModel):
    name: str
    url: str
    schemas: list[str] = []

    @field_validator("url")
    @classmethod
    def _must_be_async_mysql(cls, v: str) -> str:
        if not v.startswith(_ALLOWED_MYSQL_DRV):
            raise ValueError(f"URL must start with one of: {_ALLOWED_MYSQL_DRV}")
        return v

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    export_format: ExportFormat = "svg"
    dpi: int = Field(default=96, ge=48, le=600)
    split: SplitMode = "none"
    layout: LayoutMode = "dot"
    grid_columns: int = Field(default=6, ge=1, le=50)
    show_relations: bool = True
    output_dir: str = "output"
    big_threshold: int = Field(default=60, ge=1)
    databases: list[Database] = Field(default_factory=list)

    @field_validator("databases")
    @classmethod
    def _non_empty(cls, v: list[Database]) -> list[Database]:
        if not v:
            raise ValueError("Databases not found")
        return v

def _collect_databases(env_path: str) -> list[Database]:
    """Собирает DB_<N>_URL / DB_<N>_NAME из .env и os.environ."""
    import os
    import re

    raw = {**dotenv_values(env_path), **os.environ}
    urls: dict[str, str] = {}
    names: dict[str, str] = {}
    schemas: dict[str, list[str]] = {}
    for key, value in raw.items():
        if not value:
            continue
        if m := re.fullmatch(r"DB_(\w+)_URL", key):
            urls[m.group(1)] = value.strip()
        elif m := re.fullmatch(r"DB_(\w+)_NAME", key):
            names[m.group(1)] = value.strip()
        elif m := re.fullmatch(r"DB_(\w+)_SCHEMA", key):
            schemas[m.group(1)] = [s.strip() for s in value.split(",") if s.strip()]

    return [
        Database(name=names.get(k, f"db_{k}"), url=urls[k], schemas=schemas.get(k, []))
        for k in sorted(urls, key=lambda x: (len(x), x))
    ]

def load_settings(env_path: str = ".env") -> Settings:
    databases = _collect_databases(env_path=env_path)
    return Settings(_env_file=env_path,databases=databases) # type: ignore[call-arg]