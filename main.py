"""Render the link index from data/catalog.yml.

Mojo pages call library_page. The types page calls types_table.
A URL must start with https://. A serializer type is schema or schema-less.
A library must name a standard that exists in the catalog.
"""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
CATALOG_PATH = ROOT / "data" / "catalog.yml"

BENCHMARK_FIELDS = ("name", "repository", "site", "dashboard")
STANDARD_FIELDS = ("id", "name", "type")
LIBRARY_FIELDS = ("id", "name", "standard", "repository", "documentation")
SERIALIZER_TYPES = {"schema", "schema-less"}
RETIRED_KEYS = ("measurements", "planned_measurements", "languages")
URL_FIELDS = {
    "benchmark": ("repository", "site", "dashboard"),
    "library": ("repository", "documentation"),
}


def _require(item: dict, fields: tuple[str, ...], label: str) -> None:
    missing = [field for field in fields if item.get(field) in (None, "")]
    if missing:
        joined = ", ".join(missing)
        raise ValueError(f"{label} is missing {joined}")
    unexpected = sorted(set(item) - set(fields))
    if unexpected:
        joined = ", ".join(unexpected)
        raise ValueError(f"{label} has unexpected fields: {joined}")


def _unique(items: list[dict], field: str, label: str) -> None:
    seen: set[str] = set()
    for item in items:
        value = item[field]
        if value in seen:
            raise ValueError(f"Duplicate {label}: {value}")
        seen.add(value)


def _https(url: object, label: str) -> None:
    if not isinstance(url, str) or not url.startswith("https://"):
        raise ValueError(f"{label} must start with https://")


def _load() -> dict:
    with CATALOG_PATH.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError("catalog.yml must be a mapping")
    retired = [key for key in RETIRED_KEYS if key in data]
    if retired:
        joined = ", ".join(retired)
        raise ValueError(f"catalog.yml still has {joined}")
    for key in ("benchmark", "standards", "libraries"):
        if key not in data:
            raise ValueError(f"catalog.yml is missing {key}")

    benchmark = data["benchmark"]
    standards = data["standards"]
    libraries = data["libraries"]
    if not isinstance(benchmark, dict):
        raise ValueError("benchmark must be a mapping")
    if not isinstance(standards, list) or not isinstance(libraries, list):
        raise ValueError("standards and libraries must be lists")

    _require(benchmark, BENCHMARK_FIELDS, "benchmark")
    for field in URL_FIELDS["benchmark"]:
        _https(benchmark[field], f"benchmark.{field}")

    for index, standard in enumerate(standards):
        label = f"standards[{index}]"
        if not isinstance(standard, dict):
            raise ValueError(f"{label} must be a mapping")
        _require(standard, STANDARD_FIELDS, label)
        if standard["type"] not in SERIALIZER_TYPES:
            raise ValueError(f"{standard['id']} type must be schema or schema-less")
    _unique(standards, "id", "standard id")

    standard_ids = {item["id"] for item in standards}
    for index, library in enumerate(libraries):
        label = f"libraries[{index}]"
        if not isinstance(library, dict):
            raise ValueError(f"{label} must be a mapping")
        _require(library, LIBRARY_FIELDS, label)
        if library["standard"] not in standard_ids:
            raise ValueError(f"{library['id']} names an unknown standard")
        for field in URL_FIELDS["library"]:
            _https(library[field], f"{library['id']}.{field}")
    _unique(libraries, "id", "library id")

    data["standard_by_id"] = {item["id"]: item for item in standards}
    data["library_by_id"] = {item["id"]: item for item in libraries}
    return data


def _cell(text: str) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ").strip()


def _visible_url(url: str) -> str:
    return url.removeprefix("https://").rstrip("/")


def _link(url: str) -> str:
    return f"[{_visible_url(url)}]({url})"


def define_env(env) -> None:
    catalog = _load()
    benchmark = catalog["benchmark"]
    standards = catalog["standards"]
    standard_by_id = catalog["standard_by_id"]
    library_by_id = catalog["library_by_id"]

    @env.macro
    def standard_names() -> str:
        return "\n".join(f"- {_cell(item['name'])}" for item in standards)

    @env.macro
    def types_table() -> str:
        rows = ["| Standard | Type |", "| --- | --- |"]
        for item in standards:
            rows.append(f"| {_cell(item['name'])} | {_cell(item['type'])} |")
        return "\n".join(rows)

    @env.macro
    def benchmark_page() -> str:
        rows = [
            "| Link | URL |",
            "| --- | --- |",
            f"| Repository | {_link(benchmark['repository'])} |",
            f"| Documentation | {_link(benchmark['site'])} |",
            f"| Dashboard | {_link(benchmark['dashboard'])} |",
        ]
        return "\n".join(
            [
                "# serializer-benchmark",
                "",
                "These links open GLD.SerializerBenchmark.",
                "",
                "\n".join(rows),
            ]
        )

    @env.macro
    def mojo_index() -> str:
        """List libraries on the Mojo index. Page stems match docs/mojo/<stem>.md."""
        by_standard = {item["standard"]: item for item in catalog["libraries"]}
        blocks: list[str] = []
        current = None
        lines: list[str] = []

        def flush() -> None:
            if current is None:
                return
            title = "Schema-less" if current == "schema-less" else "Schema"
            blocks.append("## " + title)
            blocks.append("")
            blocks.append("\n".join(lines))

        for standard in standards:
            library = by_standard.get(standard["id"])
            if library is None:
                continue
            if standard["type"] != current:
                flush()
                current = standard["type"]
                lines = []
            stem = library["id"].removeprefix("gld-")
            lines.append(
                f"- [{library['name']}]({stem}.md) for {_cell(standard['name'])}"
            )
        flush()
        return "\n\n".join(blocks)

    @env.macro
    def library_page(library_id: str) -> str:
        library = library_by_id.get(library_id)
        if library is None:
            raise KeyError(library_id)
        standard = standard_by_id[library["standard"]]
        rows = [
            "| Link | URL |",
            "| --- | --- |",
            f"| Repository | {_link(library['repository'])} |",
            f"| Documentation | {_link(library['documentation'])} |",
        ]
        prose = (
            f"{library['name']} is a Mojo 1.1 library for {standard['name']}. "
            f"The serializer type is {standard['type']}."
        )
        return "\n".join(
            [
                f"# {library['name']}",
                "",
                prose,
                "",
                "\n".join(rows),
            ]
        )
