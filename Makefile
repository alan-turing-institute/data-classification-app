NAME := haven
POETRY := $(shell command -v poetry 2> /dev/null)
.DEFAULT_GOAL := help

.PHONY: help
help:
	@echo "Please use 'make <target>' where <target> is one of"
	@echo ""
	@echo "  local-install     install packages and prepare local environment"
	@echo "  prod-install      install packages and prepare production environment"
	@echo "  clean             remove all temporary files"
	@echo "  lint              run the code linters"
	@echo "  format            reformat code"
	@echo "  test              run all the tests"
	@echo ""
	@echo "Check the Makefile to know exactly what each target is doing."


local-install:
	$(POETRY) install

prod-install:
	$(POETRY) install --no-dev

.PHONY: clean
clean:
	find . -type d -name "__pycache__" | xargs rm -rf {};
	rm -rf .coverage .mypy_cache

.PHONY: lint
lint:
	$(POETRY) run isort --settings-file .isort.cfg --profile=black --lai=2 --check-only ./tests/ $(NAME)
	$(POETRY) run black --check ./tests/ $(NAME) --diff
	$(POETRY) run flake8 --config .flake8 --ignore=W503,E501 $(NAME)
	$(POETRY) run mypy ./tests/ $(NAME) --ignore-missing-imports
	$(POETRY) run bandit -r $(NAME) -s B608

.PHONY: format
format:
	$(POETRY) run isort --settings-file .isort.cfg  --profile=black --lai=2 ./tests/ $(NAME)
	$(POETRY) run black ./tests/ $(NAME)

.PHONY: test
test:
    # exclude node-modules as node-gyp triggers error on Windows 10
	$(POETRY) run pytest --ignore=node_modules --cov-config=./.coveragerc --cov-report term-missing

