.PHONY:  clean, container, list,lint, test,  serve_docs

SHELL := /bin/bash

UID := $(shell id -u)
GID := $(shell id -g)
USERNAME := $(shell id -u -n)

MKFILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
MKFILE_DIR := $(dir $(MKFILE_PATH))

list:
	@cat Makefile

clean:
	rm -rf src/*.egg-info dist venv public public docs/uml
	docker container prune -f


lint:
	ruff check src
	mypy src


test:
	coverage run -m pytest tests && coverage report -m


public:
	# build html documentation
	mkdocs build -d public


venv:
	# create virtual environment
	python3.12 -m venv venv
	venv/bin/pip install -r docker/requirements.txt
	venv/bin/pip install -e .

serve_docs:
	# serve html documentation
	mkdocs serve -a 0.0.0.0:8000 -w README.md



