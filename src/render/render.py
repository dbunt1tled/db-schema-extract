from __future__ import annotations

import graphviz

from src.db.introspect import Table

MAX_PX = 30000

HEADER_BG = "#4C566A"
HEADER_FG = "#ECEFF4"
PK_BG = "#FFF3BF"
FK_BG = "#E7F5FF"
ROW_BG = "#FFFFFF"


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _html_label(t: Table) -> str:
    rows = [
        f'<TR><TD BGCOLOR="{HEADER_BG}" COLSPAN="3">'
        f'<FONT COLOR="{HEADER_FG}"><B>{_esc(t.name)}</B></FONT></TD></TR>'
    ]
    for c in t.columns:
        bg = PK_BG if c.is_pk else (FK_BG if c.is_fk else ROW_BG)
        marks = []
        if c.is_pk:
            marks.append("PK")
        if c.is_fk:
            marks.append("FK")
        mark = ("<B>" + "/".join(marks) + "</B>") if marks else ""
        name = f"<B>{_esc(c.name)}</B>" if c.is_pk else _esc(c.name)
        rows.append(
            f'<TR>'
            f'<TD BGCOLOR="{bg}" ALIGN="LEFT" PORT="{_esc(c.name)}">{mark}</TD>'
            f'<TD BGCOLOR="{bg}" ALIGN="LEFT">{name}</TD>'
            f'<TD BGCOLOR="{bg}" ALIGN="LEFT"><FONT POINT-SIZE="9">{_esc(c.type)}</FONT></TD>'
            f'</TR>'
        )
    return ('<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="4">'
            + "".join(rows) + "</TABLE>>")


def _index(tables: list[Table]) -> dict[str, Table]:
    idx = {t.qualified: t for t in tables}
    for t in tables:
        idx.setdefault(t.name, t)
    return idx


def _resolve_ref(fk, idx: dict[str, Table]) -> Table | None:
    if fk.ref_schema:
        if cand := idx.get(f"{fk.ref_schema}.{fk.ref_table}"):
            return cand
    return idx.get(fk.ref_table)


FORCE_ENGINES = {"neato", "fdp", "sfdp", "osage"}


def _build_graph(tables: list[Table], show_relations: bool, fmt: str, dpi: int,
                 layout: str = "dot", grid_columns: int = 6) -> graphviz.Digraph:
    idx = _index(tables)

    # Движок: grid реализуем на dot; остальные — как есть.
    engine = "dot" if layout in ("dot", "grid") else layout
    dot = graphviz.Digraph("schema", format=fmt, engine=engine)

    dot.attr("graph", bgcolor="white", dpi=str(dpi))
    dot.attr("node", shape="plaintext", fontname="Helvetica")
    dot.attr("edge", color="#868E96", arrowsize="0.8")

    if layout == "dot":
        dot.attr("graph", rankdir="LR", splines="ortho", nodesep="0.4", ranksep="1.2")
    elif layout == "grid":
        dot.attr("graph", rankdir="TB", nodesep="0.5", ranksep="0.8")
    else:  # neato / fdp / sfdp / osage — силовое/упаковочное 2D-размещение
        dot.attr("graph", overlap="prism", splines="true", pack="true")

    if fmt in ("png", "jpeg", "jpg"):
        inches = MAX_PX / dpi
        dot.attr("graph", size=f"{inches:.1f},{inches:.1f}")

    for t in tables:
        dot.node(t.qualified, label=_html_label(t))

    # Сетка: строим невидимый каркас из строк по grid_columns таблиц.
    # Внутри строки — rank=same + невидимые рёбра (порядок слева направо),
    # между строками — невидимые рёбра (укладка сверху вниз).
    if layout == "grid":
        cols = max(1, grid_columns)
        ids = [t.qualified for t in tables]
        rows = [ids[i:i + cols] for i in range(0, len(ids), cols)]
        for row in rows:
            with dot.subgraph() as s:
                s.attr(rank="same")
                for node in row:
                    s.node(node)
            for a, b in zip(row, row[1:], strict=False):
                dot.edge(a, b, style="invis")
        for top, bottom in zip(rows, rows[1:]):
            dot.edge(top[0], bottom[0], style="invis")

    if show_relations:
        for t in tables:
            for fk in t.fks:
                if (target := _resolve_ref(fk, idx)) is None:
                    continue
                src_port = f":{fk.columns[0]}" if fk.columns else ""
                attrs = {"constraint": "false"} if layout == "grid" else {}
                dot.edge(f"{t.qualified}{src_port}", target.qualified, **attrs)
    return dot


def _components(tables: list[Table]) -> list[list[Table]]:
    idx = _index(tables)
    parent = {t.qualified: t.qualified for t in tables}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for t in tables:
        for fk in t.fks:
            if (target := _resolve_ref(fk, idx)) is not None:
                parent[find(t.qualified)] = find(target.qualified)

    groups: dict[str, list[Table]] = {}
    for t in tables:
        groups.setdefault(find(t.qualified), []).append(t)

    linked = sorted((g for g in groups.values() if len(g) > 1), key=len, reverse=True)
    singles = [t for g in groups.values() if len(g) == 1 for t in g]
    if singles:
        linked.append(singles)
    return linked


def render(tables: list[Table], out_base: str, fmt: str = "svg",
           dpi: int = 96, show_relations: bool = True,
           split: str = "none", layout: str = "dot",
           grid_columns: int = 6) -> list[str]:
    if split == "none":
        groups = {"": tables}
    elif split == "schema":
        groups = {}
        for t in tables:
            groups.setdefault(t.schema_name or "default", []).append(t)
    elif split == "components":
        groups = {f"part{i+1:02d}": g for i, g in enumerate(_components(tables))}
    else:
        raise ValueError(f"Unknown mode split: {split}")

    produced: list[str] = []
    for suffix, group in groups.items():
        if not group:
            continue
        dot = _build_graph(group, show_relations, fmt, dpi, layout, grid_columns)
        name = out_base if not suffix else f"{out_base}__{suffix}"
        produced.append(dot.render(filename=name, cleanup=True))
    return produced
