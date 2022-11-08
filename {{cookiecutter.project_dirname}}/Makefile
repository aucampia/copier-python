# https://www.gnu.org/software/make/manual/make.html
.PHONY: all
all:

########################################################################
# boiler plate
########################################################################
SHELL=bash
.SHELLFLAGS=-ec -o pipefail

current_makefile:=$(lastword $(MAKEFILE_LIST))
current_makefile_dirname:=$(dir $(current_makefile))
current_makefile_dirname_abspath:=$(dir $(abspath $(current_makefile)))
current_makefile_dirname_realpath:=$(dir $(realpath $(current_makefile)))

ifneq ($(filter all vars,$(VERBOSE)),)
dump_var=$(info var $(1)=$($(1)))
dump_vars=$(foreach var,$(1),$(call dump_var,$(var)))
else
dump_var=
dump_vars=
endif

ifneq ($(filter all targets,$(VERBOSE)),)
__ORIGINAL_SHELL:=$(SHELL)
SHELL=$(warning Building $@$(if $<, (from $<))$(if $?, ($? newer)))$(TIME) $(__ORIGINAL_SHELL)
endif

########################################################################
# variables
########################################################################

localstatedir?=var
generated_dir?=$(localstatedir)/generated

########################################################################
# targets
########################################################################


.PHONY: configure
configure: ## configure the project

.PHONY: validate
validate: ## validate everything

.PHONY: validate-fix
validate-fix: ## fix auto-fixable validation errors

.PHONY: test
test: ## run the project's tests

.PHONY: generate
generate: ## generate all outputs

.PHONY: all
all: ## do everything
all: validate generate

.PHONY: clean
clean: ## clean outputs
clean: clean-var/

########################################################################
# python
########################################################################

py_source=./src ./tests
poetry=python -m poetry

.PHONY: python-configure
configure: python-configure
python-configure:
	$(poetry) install

.PHONY: python-validate-static
validate-static: python-validate-static
python-validate-static:
	$(poetry) run mypy --show-error-codes --show-error-context \
		$(py_source)
	$(poetry) run codespell $(py_source) *.md
	$(poetry) run isort --check $(py_source)
	$(poetry) run black --check $(py_source)
	$(poetry) run flake8 $(py_source)
	$(poetry) export --without-hashes --dev --format requirements.txt | $(poetry) run safety check --full-report --stdin


.PHONY: python-validate-fix
validate-fix: python-validate-fix
python-validate-fix:
	$(poetry) run pycln --expand-stars --all $(py_source)
	$(poetry) run isort $(py_source)
	$(poetry) run black $(py_source)

.PHONY: python-test
test: python-test
python-test:
	$(poetry) run pytest --cov-report term --cov-report xml ./tests

.PHONY: python-validate
validate: python-validate
python-validate: python-validate-static python-test

########################################################################
# utility targets
########################################################################

.PHONY: help
help: ## Show this message.
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(current_makefile) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: .FORCE
.FORCE:
$(force_targets): .FORCE

## Create directories
.PRECIOUS: %/
%/:
	mkdir -vp $(@)

## Clean directories
.PHONY: clean-%/
clean-%/:
	@{ test -d $(*) && { set -x; rm -vr $(*); set +x; } } || echo "directory $(*) does not exist ... nothing to clean"
