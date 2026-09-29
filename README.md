# Serialization

Index of serialization implementations and of the benchmark that measures them.

Each linked repository stays usable on its own. This site is the index. The address is [leo-gan.github.io/serialization](https://leo-gan.github.io/serialization/) after GitHub Pages is set to publish the `gh-pages` branch.

## Preview

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
mkdocs serve
```

## Change a fact once

Names, links, and the capability matrix live in [`data/catalog.yml`](data/catalog.yml). The pages call macros in [`main.py`](main.py). Edit the catalog, add the Markdown page the catalog names, add that page to `nav` in [`mkdocs.yml`](mkdocs.yml), then rebuild.

Add a repository when it has code and a GitHub remote.

## Deploy

A push to `main` runs [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml). The job publishes the site with `mkdocs gh-deploy`.
