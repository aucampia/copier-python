# ...

## TODO

- [ ] ???

## ...

```bash
#\rm -rvf var/copied/tmp; PYTHON_LOGGING_LEVEL=DEBUG copier --vcs-ref HEAD --defaults --data copy ./ var/copied/tmp/defaults
\rm -rvf var/copied/tmp; PYTHON_LOGGING_LEVEL=DEBUG copier --vcs-ref HEAD --defaults copy ./ var/copied/tmp/defaults
PYTHON_LOGGING_LEVEL=DEBUG copier --vcs-ref HEAD --defaults update var/copied/tmp/defaults

git -C var/copied/tmp/defaults status
git -C var/copied/tmp/defaults log -p
(cd var/copied/tmp/defaults; bash)


PYTHON_LOGGING_LEVEL=DEBUG copier --vcs-ref HEAD copy ~/sw/d/github.com/aucampia/copier-python/ .
```

```bash
cookiecutter -v gh:aucampia/cookiecutter-python --overwrite-if-exists --output-dir var/baked/tmp

cookiecutter -vvvv ~/sw/d/github.com/aucampia/cookiecutter-python --overwrite-if-exists --no-input --config-file tests/data/cookie-config/basic.yaml --output-dir var/baked/tmp
cruft create ~/sw/d/github.com/aucampia/cookiecutter-python

\rm -rv var/baked/tmp

cookiecutter -vvvv ./ --overwrite-if-exists --no-input --config-file tests/data/cookie-config/basic.yaml --output-dir var/baked/tmp
cookiecutter -vvvv ./ --overwrite-if-exists --no-input --config-file tests/data/cookie-config/basic-make.yaml --output-dir var/baked/tmp

# WARNING: cruft works from HEAD so commit first
PYLOGGING_LEVEL=DEBUG cruft create ./ --overwrite-if-exists --no-input --config-file tests/data/cookie-config/basic.yaml --output-dir var/baked/tmp

(cd var/baked/tmp/example.project.basic && task configure)
(cd var/baked/tmp/example.project.basic && task validate:fix validate)
```

## Inspiration

- https://github.com/hackebrot/cookiecutter-examples/tree/master/create-directories
- https://github.com/audreyfeldroy/cookiecutter-pypackage
  - https://github.com/audreyfeldroy/cookiecutter-pypackage/blob/master/cookiecutter.json
- https://github.com/timhughes/cookiecutter-poetry
  - https://github.com/timhughes/cookiecutter-poetry/blob/master/cookiecutter.json
- https://github.com/johanvergeer/cookiecutter-poetry
  - https://github.com/johanvergeer/cookiecutter-poetry/blob/develop/cookiecutter.json
- https://github.com/cjolowicz/cookiecutter-hypermodern-python
  -  https://github.com/cjolowicz/cookiecutter-hypermodern-python/blob/main/cookiecutter.json

## devtools

```bash
docker compose build
docker compose run --rm python-devtools task help
```


## monkey sync

```bash
## Diff summary ...
diff -u -r -q \
    --exclude={.git,TEMPLATE-*.md,poetry.lock,__pycache__,*.egg-info,.pytest_cache,.mypy_cache,.venv,.tox,setup.py,.cache-*,dist,.coverage,coverage.xml,extra,LICENSE} \
    ~/sw/d/github.com/aucampia/cookiecutter-python/var/baked/tmp/example.project.basic/ ./

## vimdiff
diff -u -r \
    --exclude={.git,TEMPLATE-*.md,poetry.lock,__pycache__,*.egg-info,.pytest_cache,.mypy_cache,.venv,.tox,setup.py,.cache-*,dist,.coverage,coverage.xml,extra,LICENSE} \
    ~/sw/d/github.com/aucampia/cookiecutter-python/var/baked/tmp/example.project.basic/ ./ \
    | sed -E -n 's,^diff.* /,vimdiff /,gp'

## diff
diff -u -r \
    --exclude={.git,TEMPLATE-*.md,poetry.lock,__pycache__,*.egg-info,.pytest_cache,.mypy_cache,.venv,.tox,setup.py,.cache-*,dist,.coverage,coverage.xml,extra,LICENSE} \
    ~/sw/d/github.com/aucampia/cookiecutter-python/var/baked/tmp/example.project.basic/ ./
```

## ...

```
TEST_RAPID=true task test
```
