# Serialization

This site stores links to GLD.SerializerBenchmark and to the Mojo gld-* libraries.

Each linked repository stays usable on its own. The address is [leo-gan.github.io/serialization](https://leo-gan.github.io/serialization/) after GitHub Pages is set to publish the `gh-pages` branch.

## Preview

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
mkdocs serve
```

## Change a link

Names, serializer types, and URLs live in [`data/catalog.yml`](data/catalog.yml). The Mojo pages call `library_page` in [`main.py`](main.py).

To add a library, add a catalog entry, add `docs/mojo/<name>.md` containing the `library_page` call, and add that page under `Mojo serializers` in [`mkdocs.yml`](mkdocs.yml). The Mojo index lists every library in the catalog.

Add a repository when it has code and a GitHub remote.

## Deploy

A push to `main` runs [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml). The job publishes the site with `mkdocs gh-deploy`.
