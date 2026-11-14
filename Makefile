# One command per job, for people and agents. Run `make help`.
VENV := .venv
PY   := $(VENV)/bin/python

.PHONY: help setup test check workspace graph

help:
	@echo "make setup      create .venv and install test dependencies"
	@echo "make test       run pytest"
	@echo "make check      everything CI runs, plus terraform fmt and validate"
	@echo "make workspace  link the agent kit into the parent folder (one-time, per machine)"
	@echo "make graph      refresh the graphify code graphs for both repos"

$(VENV): lambda/requirements-test.txt
	python3 -m venv $(VENV)
	$(PY) -m pip install -q -r lambda/requirements-test.txt
	@touch $(VENV)

setup: $(VENV)

test: $(VENV)
	cd lambda && ../$(PY) -m pytest -q

# Terraform steps are skipped when terraform is not installed; CI does not run them either.
check: test
	@if command -v terraform >/dev/null; then \
		terraform -chdir=terraform fmt -check -recursive && \
		{ test -d terraform/.terraform || terraform -chdir=terraform init -backend=false -input=false >/dev/null; } && \
		terraform -chdir=terraform validate; \
	else echo "terraform not installed: skipped fmt and validate"; fi

# The parent folder holds both repos and is where agents are started. It is not
# a repository, so its files are generated here instead of committed.
workspace:
	mkdir -p ../.claude
	ln -sfn ../plantpass-backend/.agents/skills ../.claude/skills
	ln -sfn ../plantpass-backend/.claude/settings.json ../.claude/settings.json
	cp docs/workspace-CLAUDE.md ../CLAUDE.md
	@echo "Linked. Start agents from $$(cd .. && pwd)"

graph:
	graphify update .
	@test ! -d ../plantpass-frontend || graphify update ../plantpass-frontend
