"""Render the link index from data/catalog.yml.

The start page calls hub_page. Run python main.py to rewrite README.md so it matches.
The standards page calls standards_table.
A URL must start with https://. A serializer type is schema or schema-less.
A library must name a standard that exists in the catalog.

To add a library, add a catalog entry and run python main.py.
The start page and the README then list its documentation link.
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

    return data


# The visible label is Learn. The address is the Serialization 101 course.
PERSPECTIVES = (
    ("History", "theory/101/historical_perspective/"),
    ("Data science", "theory/101/data_science_perspective/"),
    ("Engineering", "theory/101/engineer_perspective/"),
)


def _cell(text: str) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ").strip()


def _named_link(label: str, url: str) -> str:
    return f"[{_cell(label)}]({url})"


def hub_markdown(benchmark: dict, libraries: list[dict], *, page: bool = False) -> str:
    """Return the README, or the start page when page is true.

    Link to documentation only. Each docs site links to its repository.
    The page drops the colon after Mojo serializers and Learn. The badge
    already separates each label from the links that follow.
    """
    site = benchmark["site"].rstrip("/")
    # The space before the dot does not break, so a wrapped line does not start with "·".
    separator = "\u00a0· "
    mojo = separator.join(
        _named_link(library["name"], library["documentation"]) for library in libraries
    )
    perspectives = separator.join(
        _named_link(label, f"{site}/{path}") for label, path in PERSPECTIVES
    )
    course = _named_link("Learn", f"{site}/theory/101/")
    colon = "" if page else ":"
    lines = [
        "# Serialization",
        "",
        f"- {_named_link('Serializer Benchmarks', benchmark['site'])}",
        f"- **Mojo serializers**{colon} {mojo}",
        f"- **{course}**{colon} {perspectives}",
        "",
    ]
    return "\n".join(lines)


def define_env(env) -> None:
    catalog = _load()
    benchmark = catalog["benchmark"]
    standards = catalog["standards"]
    libraries = catalog["libraries"]

    expected = hub_markdown(benchmark, libraries)
    readme = ROOT / "README.md"
    actual = readme.read_text(encoding="utf-8")
    if actual != expected:
        raise ValueError(
            "README.md does not match data/catalog.yml. Run python main.py to rewrite it."
        )

    @env.macro
    def hub_page() -> str:
        return hub_markdown(benchmark, libraries, page=True)

    @env.macro
    def standards_table() -> str:
        rows = ["| Standard | Type |", "| --- | --- |"]
        for item in standards:
            rows.append(f"| {_cell(item['name'])} | {_cell(item['type'])} |")
        return "\n".join(rows)


def main() -> None:
    catalog = _load()
    text = hub_markdown(catalog["benchmark"], catalog["libraries"])
    (ROOT / "README.md").write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
