# Development, test, container and infrastructure targets. `make help` lists them.

.DEFAULT_GOAL := help
SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c

ENV ?= dev
LAYER ?= foundation
TF_ROOT := infra/envs/$(ENV)/$(LAYER)
TF_ROOTS := $(shell find infra/envs -mindepth 2 -maxdepth 2 -type d 2>/dev/null | sort)
IMAGE ?= demosift-runtime:dev
DATASET ?= lerobot/svla_so101_pickplace

.PHONY: help install lint format test inspect serve docker-build docker-run tf-check tf-plan tf-apply

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies (uv sync --locked)
	uv sync --locked

lint: ## ruff (lint + format check) then mypy --strict
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy

format: ## Format and auto-fix what ruff can
	uv run ruff format .
	uv run ruff check --fix .

test: ## Unit tests with coverage
	uv run pytest --cov --cov-report=term --cov-report=xml

inspect: ## Inspect a dataset: make inspect DATASET=lerobot/svla_so101_pickplace
	uv run demosift inspect $(DATASET)

serve: ## Run the AgentCore Runtime server locally on :8080
	uv run demosift serve

docker-build: ## Build the runtime image for linux/arm64 (what AgentCore Runtime requires)
	docker build --platform linux/arm64 -f services/runtime/Dockerfile -t $(IMAGE) .

docker-run: ## Run the runtime image locally on :8080
	docker run --rm -p 8080:8080 -e DEMOSIFT_LOG_LEVEL=INFO $(IMAGE)

tf-check: ## terraform fmt -check, validate, tflint and trivy over infra/
	terraform fmt -check -recursive -diff infra
	@for root in $(TF_ROOTS); do \
		echo "== validate $$root"; \
		terraform -chdir=$$root init -backend=false -input=false >/dev/null; \
		terraform -chdir=$$root validate; \
	done
	tflint --init --config "$(CURDIR)/.tflint.hcl" >/dev/null
	cd infra && tflint --recursive --config "$(CURDIR)/.tflint.hcl"
	trivy config --exit-code 1 --severity HIGH,CRITICAL infra

tf-plan: ## Plan one layer: make tf-plan ENV=dev LAYER=foundation
	terraform -chdir=$(TF_ROOT) init -input=false -backend-config=backend.hcl
	terraform -chdir=$(TF_ROOT) plan -input=false -lock-timeout=60s

tf-apply: ## Apply locally, dev only; other environments go through CI
ifneq ($(ENV),dev)
	$(error local apply is refused for "$(ENV)": only dev is applied from a laptop)
endif
	terraform -chdir=$(TF_ROOT) init -input=false -backend-config=backend.hcl
	terraform -chdir=$(TF_ROOT) apply -input=false -lock-timeout=60s
