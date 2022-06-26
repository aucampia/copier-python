# ...


```bash
cookiecutter -v ./ --overwrite-if-exists -o var/baked/tmp


\rm -rv var/baked/tmp
cookiecutter -vvvv ./ --overwrite-if-exists --no-input --config-file test/data/cookie-config/basic.yaml -o var/baked/tmp
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
