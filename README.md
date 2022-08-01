# ...


```bash
cookiecutter -v gh:aucampia/cookiecutter-python --overwrite-if-exists --output-dir var/baked/tmp
cruft create ~/sw/d/github.com/aucampia/cookiecutter-python


\rm -rv var/baked/tmp
rm -rf ~/.cookiecutters/cookiecutter-*

cookiecutter -vvvv ./ --overwrite-if-exists --no-input --config-file tests/data/cookie-config/basic.yaml --output-dir var/baked/tmp
# WARNING: cruft works from HEAD
cruft create ./ --overwrite-if-exists --no-input --config-file tests/data/cookie-config/basic.yaml --output-dir var/baked/tmp
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
