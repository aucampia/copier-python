# ...

```bash
poetry install
poetry run {{ cli_name }}

{% if build_tool == "go-task" %}
task help
task validate:fix validate
{% elif build_tool == "gnu-make" %}
make help
make validate-fix validate
{% else %}
{{ None["[ERROR] Invalid build_tool " ~ build_tool][0] }}
{% endif %}
```

## Using docker devtools

```bash
make -C devtools -B
docker compose build

{% if build_tool == "go-task" %}
docker compose run --rm python-devtools task help
docker compose run --rm python-devtools task validate:fix validate
{% elif build_tool == "gnu-make" %}
docker compose run --rm python-devtools make help
docker compose run --rm python-devtools make validate-fix validate
{% else %}
{{ None["[ERROR] Invalid build_tool " ~ build_tool][0] }}
{% endif %}
```

## Updating from template base

```bash
pipx run --spec=cruft cruft update
```
