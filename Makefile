# Development, test and container targets. `make help` lists them.

.DEFAULT_GOAL := help
SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c

IMAGE ?= demosift-runtime:dev
DATASET ?= lerobot/svla_so101_pickplace

.PHONY: help install lint format test inspect serve docker-build docker-run

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
	docker run --rm -p 8080:8080 -e DEMOSIFT_LOG_LEVEL=INFO -e OTEL_SDK_DISABLED=true $(IMAGE)
