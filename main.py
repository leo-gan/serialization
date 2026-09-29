"""Render cards and fact sheets from data/catalog.yml.

Markdown pages call these macros. A fact that appears in the catalog should
be edited there, not copied into a second page.
"""

from __future__ import annotations

import os
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
CATALOG_PATH = ROOT / "data" / "catalog.yml"
DOCS = ROOT / "docs"


def _load() -> dict:
    with CATALOG_PATH.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    data["project_by_id"] = {item["id"]: item for item in data["projects"]}
    data["format_by_id"] = {item["id"]: item for item in data["formats"]}
    data["language_by_id"] = {item["id"]: item for item in data["languages"]}
    missing = []
    for project in data["projects"]:
        if not (DOCS / project["page"]).is_file():
            missing.append(project["page"])
    for fmt in data["formats"]:
        if not (DOCS / fmt["page"]).is_file():
            missing.append(fmt["page"])
    for language in data["languages"]:
        page = language.get("page")
        if page and not (DOCS / page).is_file():
            missing.append(page)
    if missing:
        joined = ", ".join(missing)
        raise FileNotFoundError(f"Catalog pages missing under docs/: {joined}")
    return data


def _cell(text: str) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ").strip()


def _rel(env, target: str) -> str:
    if target.startswith(("http://", "https://", "mailto:")):
        return target
    src = "index.md"
    if env.page is not None and env.page.file is not None:
        src = env.page.file.src_path
    start = os.path.dirname(src) or "."
    relative = os.path.relpath(target, start)
    return relative.replace(os.sep, "/")


def _link(env, target: str, label: str) -> str:
    return f"[{label}]({_rel(env, target)})"


def define_env(env) -> None:
    catalog = _load()
    projects = catalog["projects"]
    formats = catalog["formats"]
    languages = catalog["languages"]
    project_by_id = catalog["project_by_id"]
    format_by_id = catalog["format_by_id"]
    language_by_id = catalog["language_by_id"]

    def language_name(language_id: str) -> str:
        return language_by_id[language_id]["name"]

    def format_of(project: dict) -> dict | None:
        format_id = project.get("format")
        if not format_id:
            return None
        return format_by_id[format_id]

    def matrix_row(project: dict) -> dict[str, str]:
        if "matrix" in project:
            return project["matrix"]
        fmt = format_of(project)
        traits = fmt["traits"]
        names = ", ".join(language_name(item) for item in project["languages"])
        return {
            "format": fmt["name"],
            "language": names,
            "benchmark": "Yes",
            "schema": traits["schema"],
            "zero_copy": traits["zero_copy"],
        }

    def implementation_prose(project: dict) -> str:
        fmt = format_of(project)
        sentences = [
            project["summary"],
            (
                "The runtime and the code generator are written in Mojo. "
                f"They do not wrap, link, or vendor {project['avoids']}."
            ),
            (
                f"The test oracle is {project['oracle']}. "
                "Runtime encode and decode run without that oracle."
            ),
            project["extra"].strip(),
            (
                "The repository is a standalone library. "
                "Install steps and examples stay in its own documentation."
            ),
        ]
        if fmt is None:
            raise KeyError(project["id"])
        return " ".join(sentences)

    @env.macro
    def project_cards() -> str:
        groups = [
            ("Benchmark", [item for item in projects if item["category"] == "benchmark"]),
            (
                "Implementations",
                [item for item in projects if item["category"] == "implementation"],
            ),
        ]
        blocks = []
        for title, items in groups:
            cards = ['<div class="grid cards" markdown>', ""]
            for project in items:
                note = _card_note(project)
                url = _rel(env, project["page"])
                cards.append(f"-   __{project['name']}__")
                cards.append("")
                cards.append("    ---")
                cards.append("")
                cards.append(f"    {project['summary']}")
                cards.append("")
                cards.append(f"    {note}")
                cards.append("")
                cards.append(f"    [Explore]({url})")
                cards.append("")
            cards.append("</div>")
            blocks.append(f"### {title}\n\n" + "\n".join(cards))
        return "\n\n".join(blocks)

    @env.macro
    def format_cards() -> str:
        cards = ['<div class="grid cards" markdown>', ""]
        for fmt in formats:
            url = _rel(env, fmt["page"])
            cards.append(f"-   __{fmt['name']}__")
            cards.append("")
            cards.append("    ---")
            cards.append("")
            cards.append(f"    {fmt['summary']}")
            cards.append("")
            cards.append(f"    [Read the format]({url})")
            cards.append("")
        cards.append("</div>")
        return "\n".join(cards)

    @env.macro
    def measurement_cards() -> str:
        cards = ['<div class="grid cards" markdown>', ""]
        for item in catalog["measurements"]:
            cards.append(f"-   __{item['name']}__")
            cards.append("")
            cards.append("    ---")
            cards.append("")
            cards.append(f"    {item['detail']}")
            cards.append("")
        cards.append("</div>")
        return "\n".join(cards)

    @env.macro
    def project_matrix() -> str:
        header = (
            "| Project | Format | Language | Benchmark | Schema | Zero-copy read |\n"
            "| --- | --- | --- | --- | --- | --- |"
        )
        rows = [header]
        for project in projects:
            row = matrix_row(project)
            if project["category"] == "benchmark":
                format_cell = _cell(row["format"])
            else:
                fmt = format_of(project)
                format_cell = _link(env, fmt["page"], row["format"])
            name = _link(env, project["page"], project["name"])
            rows.append(
                "| "
                + " | ".join(
                    [
                        name,
                        format_cell,
                        _cell(row["language"]),
                        _cell(row["benchmark"]),
                        _cell(row["schema"]),
                        _cell(row["zero_copy"]),
                    ]
                )
                + " |"
            )
        return "\n".join(rows)

    @env.macro
    def capability_legend() -> str:
        return "\n".join(
            [
                "| Column | How to read the cell |",
                "| --- | --- |",
                "| Benchmark | Yes means this repository is the benchmark, or the Mojo runner times that library. |",
                "| Schema | Required means a decoder needs a schema. Optional means a decoder can walk a value without one. Covers both means the benchmark runs both kinds of codec. A longer cell names an exception, which the format page explains. |",
                "| Zero-copy read | Yes means the repository documents a reader that takes fields from the encoded buffer. Not claimed means this index did not find that statement. |",
            ]
        )

    @env.macro
    def trait_legend() -> str:
        return "\n".join(
            [
                "| Cell | Meaning |",
                "| --- | --- |",
                "| Optional | A decoder can walk a value without a schema. The Mojo library may still generate code from a schema. |",
                "| Required | A decoder needs a schema. |",
                "| Required for tables | FlatBuffers tables need a .fbs file. FlexBuffers, in the same repository, does not. |",
                "| Yes, in Zero-copy read | The Mojo repository documents a reader that takes fields from the encoded buffer. |",
                "| Not claimed | This index did not find a zero-copy read claim in the repository. |",
            ]
        )

    @env.macro
    def format_comparison() -> str:
        header = (
            "| Format | Binary | Human-readable | Self-describing | Schema | Zero-copy read |\n"
            "| --- | --- | --- | --- | --- | --- |"
        )
        rows = [header]
        for fmt in formats:
            traits = fmt["traits"]
            rows.append(
                "| "
                + " | ".join(
                    [
                        _link(env, fmt["page"], fmt["name"]),
                        _cell(traits["binary"]),
                        _cell(traits["human_readable"]),
                        _cell(traits["self_describing"]),
                        _cell(traits["schema"]),
                        _cell(traits["zero_copy"]),
                    ]
                )
                + " |"
            )
        return "\n".join(rows)

    @env.macro
    def measurement_table() -> str:
        return _two_col("Measurement", "What the benchmark records", catalog["measurements"])

    @env.macro
    def planned_table() -> str:
        return _two_col("Measurement", "Status on the benchmark site", catalog["planned_measurements"])

    @env.macro
    def language_table() -> str:
        header = "| Language | On this hub | Benchmark runner |\n| --- | --- | --- |"
        rows = [header]
        for language in languages:
            page = language.get("page")
            hub = _link(env, page, "Notes on this hub") if page else "Runner only"
            rows.append(
                "| "
                + " | ".join(
                    [
                        _cell(language["name"]),
                        hub,
                        _link(env, language["url"], "Open the runner"),
                    ]
                )
                + " |"
            )
        return "\n".join(rows)

    @env.macro
    def project_page(project_id: str) -> str:
        project = project_by_id[project_id]
        if project["category"] == "benchmark":
            return _benchmark_page(env, project, languages, formats, projects)
        return _implementation_page(
            env, project, format_of(project), implementation_prose(project), projects
        )

    @env.macro
    def format_page(format_id: str) -> str:
        fmt = format_by_id[format_id]
        traits = fmt["traits"]
        rows = [
            "| Property | Value |",
            "| --- | --- |",
            f"| Binary | {_cell(traits['binary'])} |",
            f"| Human-readable | {_cell(traits['human_readable'])} |",
            f"| Self-describing | {_cell(traits['self_describing'])} |",
            f"| Schema | {_cell(traits['schema'])} |",
            f"| Zero-copy read in the Mojo library | {_cell(traits['zero_copy'])} |",
        ]
        related = _projects_for_format(env, format_id, projects, format_by_id)
        return "\n".join(
            [
                f"# {fmt['name']}",
                "",
                fmt["body"].strip(),
                "",
                "## Characteristics",
                "",
                "\n".join(rows),
                "",
                "The zero-copy cell is about the Mojo repository on this hub. "
                "Other implementations of the same format can make a different choice.",
                "",
                "## Projects",
                "",
                related,
                "",
                "## Benchmarks",
                "",
                "Timing and size for this format are published on the "
                "[live dashboard](https://leo-gan.github.io/GLD.SerializerBenchmark/dashboard/). "
                "Read them with the "
                + _link(env, "benchmarks/methodology.md", "methodology")
                + " on this site. This page does not copy the numbers.",
            ]
        )

    @env.macro
    def language_page(language_id: str) -> str:
        language = language_by_id[language_id]
        matched = [
            project
            for project in projects
            if language_id in project.get("languages", [])
        ]
        # A trailing "#" in "C#" would close the ATX heading and leave the title "C".
        heading = language["name"].replace("#", "\\#")
        lines = [
            f"# {heading}",
            "",
            _language_intro(language_id),
            "",
            "## Projects",
            "",
        ]
        if matched:
            lines.extend(_project_bullets(env, matched, format_by_id))
        else:
            lines.append("No repository on this hub is written in this language.")
        lines.extend(
            [
                "",
                "## Benchmark runner",
                "",
                "Serializer lists and results for this language are on the benchmark site: "
                + _link(env, language["url"], language["name"])
                + ".",
            ]
        )
        return "\n".join(lines)


def _card_note(project: dict) -> str:
    if project["category"] == "benchmark":
        return "The suite covers thirteen languages. Measured numbers stay on the benchmark site."
    return "This Mojo library is timed by the benchmark's Mojo runner."


def _two_col(left: str, right: str, items: list[dict]) -> str:
    rows = [f"| {left} | {right} |", "| --- | --- |"]
    for item in items:
        rows.append(f"| {_cell(item['name'])} | {_cell(item['detail'])} |")
    return "\n".join(rows)


def _project_bullets(env, matched: list[dict], format_by_id: dict) -> list[str]:
    lines = []
    for project in matched:
        label = project["name"]
        if project.get("format"):
            label = f"{project['name']} ({format_by_id[project['format']]['name']})"
        lines.append(f"- {_link(env, project['page'], label)}")
    return lines


def _projects_for_format(env, format_id: str, projects: list[dict], format_by_id: dict) -> str:
    matched = []
    for project in projects:
        if project.get("format") == format_id or (
            project["category"] == "benchmark" and format_id in project.get("formats", [])
        ):
            matched.append(project)
    return "\n".join(_project_bullets(env, matched, format_by_id))


def _language_intro(language_id: str) -> str:
    if language_id == "mojo":
        return (
            "The implementation repositories on this hub are Mojo libraries. "
            "The benchmark's Mojo runner times those libraries. "
            "That runner also times libraries that are not indexed here, "
            "including other JSON implementations and a TOML implementation. "
            "The Mojo runner's own page says those times cannot be ranked against another language."
        )
    if language_id in {"csharp", "python"}:
        name = "C#" if language_id == "csharp" else "Python"
        return (
            f"The {name} work in this collection is a benchmark runner inside "
            "GLD.SerializerBenchmark. The implementation repositories on this hub are "
            f"Mojo libraries. {name} serializers, modes, and results are documented with the benchmark."
        )
    return "This language is a benchmark runner. It does not have a separate page of implementation repositories."


def _implementation_page(env, project: dict, fmt: dict, prose: str, projects: list[dict]) -> str:
    facts = [
        "| Property | Value |",
        "| --- | --- |",
        f"| Language | Mojo |",
        f"| Format | {_link(env, fmt['page'], fmt['name'])} |",
        "| Category | Implementation |",
        f"| Schema | {_cell(fmt['traits']['schema'])} |",
        f"| Zero-copy read | {_cell(fmt['traits']['zero_copy'])} |",
        (
            f"| Package | `{project['package']}` on "
            f"{_link(env, project['channel'], 'prefix.dev/leo-gan/leo-gan')} |"
        ),
        f"| Test oracle | {_cell(project['oracle'])} |",
        f"| Repository | {_link(env, project['repository'], project['name'])} |",
        f"| Documentation | {_link(env, project['documentation'], 'Project site')} |",
        "| In the benchmark | Yes, on the Mojo runner |",
    ]
    related = [
        f"- {_link(env, other['page'], other['name'])}"
        for other in projects
        if other["id"] != project["id"]
    ]
    return "\n".join(
        [
            f"# {project['name']}",
            "",
            prose,
            "",
            "## Project information",
            "",
            "\n".join(facts),
            "",
            "## Benchmarking",
            "",
            "The Mojo runner in "
            + _link(env, "projects/serializer-benchmark.md", "GLD.SerializerBenchmark")
            + " times this library. Read numbers on the "
            "[live dashboard](https://leo-gan.github.io/GLD.SerializerBenchmark/dashboard/). "
            "This page does not copy them.",
            "",
            "## Related projects",
            "",
            "\n".join(related),
        ]
    )


def _benchmark_page(env, project: dict, languages: list[dict], formats: list[dict], projects: list[dict]) -> str:
    language_links = ", ".join(
        _link(env, language.get("page") or language["url"], language["name"])
        for language in languages
    )
    format_links = ", ".join(_link(env, fmt["page"], fmt["name"]) for fmt in formats)
    library_lines = [
        f"- {_link(env, other['page'], other['name'])}"
        for other in projects
        if other["category"] == "implementation"
    ]
    facts = [
        "| Property | Value |",
        "| --- | --- |",
        "| Category | Benchmark |",
        "| Languages | 13 |",
        "| Schema | Covers schema-based and schema-free codecs |",
        "| Zero-copy read | Not claimed as a finished metric |",
        f"| Repository | {_link(env, project['repository'], project['name'])} |",
        f"| Documentation | {_link(env, project['documentation'], 'Benchmark site')} |",
        f"| Dashboard | {_link(env, project['dashboard'], 'Live dashboard')} |",
        f"| Methodology | {_link(env, project['methodology'], 'Analysis methodology')} |",
        f"| Metrics | {_link(env, project['metrics'], 'Metrics catalog')} |",
    ]
    return "\n".join(
        [
            f"# {project['name']}",
            "",
            project["summary"],
            "",
            project["detail"].strip(),
            "",
            "## Project information",
            "",
            "\n".join(facts),
            "",
            "## Languages",
            "",
            language_links + ".",
            "",
            "## Formats with a repository on this hub",
            "",
            format_links + ".",
            "",
            "Those format pages cover the Mojo libraries indexed here. "
            "The benchmark also times other libraries and formats. "
            "The benchmark site has the full serializer list.",
            "",
            "## Mojo libraries timed by the runner",
            "",
            "\n".join(library_lines),
        ]
    )
