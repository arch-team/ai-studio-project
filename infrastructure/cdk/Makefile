# =============================================================================
# AI Training Platform CDK - Makefile
# =============================================================================
# Common commands for development, testing, and deployment
#
# Usage:
#   make help          - Show this help message
#   make install       - Install dependencies
#   make lint          - Run linters
#   make test          - Run tests
#   make deploy-dev    - Deploy to dev environment
# =============================================================================

.PHONY: help install lint format type-check test test-cov synth diff deploy-dev deploy-staging deploy-prod clean

# Default target
.DEFAULT_GOAL := help

# Variables
PYTHON := python3
PIP := pip
CDK := cdk
PYTEST := pytest
RUFF := ruff
MYPY := mypy

# Colors for output
CYAN := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
RESET := \033[0m

# =============================================================================
# Help
# =============================================================================

help: ## Show this help message
	@echo "$(CYAN)AI Training Platform CDK - Available Commands$(RESET)"
	@echo ""
	@echo "$(GREEN)Setup:$(RESET)"
	@grep -E '^(install|setup-helm|bootstrap):.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-20s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Development:$(RESET)"
	@grep -E '^(lint|format|type-check):.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-20s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Testing:$(RESET)"
	@grep -E '^(test|test-cov|test-unit|test-integration):.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-20s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)CDK Operations:$(RESET)"
	@grep -E '^(synth|diff|deploy-dev|deploy-staging|deploy-prod):.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-20s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Utilities:$(RESET)"
	@grep -E '^(clean|pre-commit-install|pre-commit-run):.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-20s$(RESET) %s\n", $$1, $$2}'

# =============================================================================
# Setup
# =============================================================================

install: ## Install Python dependencies
	@echo "$(CYAN)Installing dependencies...$(RESET)"
	$(PIP) install -r requirements.txt
	$(PIP) install pre-commit
	@echo "$(GREEN)Dependencies installed successfully!$(RESET)"

setup-helm: ## Download HyperPod Helm Chart
	@echo "$(CYAN)Setting up HyperPod Helm Chart...$(RESET)"
	./scripts/setup_helm_chart.sh
	@echo "$(GREEN)Helm Chart setup complete!$(RESET)"

bootstrap: ## Bootstrap CDK (requires AWS credentials)
	@echo "$(CYAN)Bootstrapping CDK...$(RESET)"
	$(CDK) bootstrap
	@echo "$(GREEN)CDK bootstrap complete!$(RESET)"

# =============================================================================
# Development
# =============================================================================

lint: ## Run all linters (ruff + mypy)
	@echo "$(CYAN)Running linters...$(RESET)"
	$(RUFF) check .
	$(RUFF) format --check .
	$(MYPY) . --ignore-missing-imports
	@echo "$(GREEN)All linters passed!$(RESET)"

format: ## Format code with ruff
	@echo "$(CYAN)Formatting code...$(RESET)"
	$(RUFF) format .
	$(RUFF) check --fix .
	@echo "$(GREEN)Code formatted!$(RESET)"

type-check: ## Run mypy type checker
	@echo "$(CYAN)Running type checker...$(RESET)"
	$(MYPY) . --ignore-missing-imports
	@echo "$(GREEN)Type check passed!$(RESET)"

# =============================================================================
# Testing
# =============================================================================

test: ## Run all tests
	@echo "$(CYAN)Running tests...$(RESET)"
	$(PYTEST) tests/ -v
	@echo "$(GREEN)All tests passed!$(RESET)"

test-cov: ## Run tests with coverage report
	@echo "$(CYAN)Running tests with coverage...$(RESET)"
	$(PYTEST) tests/ --cov=stacks --cov=config --cov-report=term-missing --cov-report=html
	@echo "$(GREEN)Coverage report generated in htmlcov/$(RESET)"

test-unit: ## Run unit tests only
	@echo "$(CYAN)Running unit tests...$(RESET)"
	$(PYTEST) tests/unit/ -v

test-integration: ## Run integration tests only
	@echo "$(CYAN)Running integration tests...$(RESET)"
	$(PYTEST) tests/integration/ -v

# =============================================================================
# CDK Operations
# =============================================================================

synth: ## Synthesize CDK stacks (all environments)
	@echo "$(CYAN)Synthesizing CDK stacks...$(RESET)"
	@echo "$(YELLOW)Dev environment:$(RESET)"
	$(CDK) synth --context env=dev --quiet
	@echo "$(YELLOW)Staging environment:$(RESET)"
	$(CDK) synth --context env=staging --quiet
	@echo "$(YELLOW)Prod environment:$(RESET)"
	$(CDK) synth --context env=prod --quiet
	@echo "$(GREEN)All environments synthesized successfully!$(RESET)"

synth-dev: ## Synthesize dev environment only
	$(CDK) synth --context env=dev

synth-staging: ## Synthesize staging environment only
	$(CDK) synth --context env=staging

synth-prod: ## Synthesize prod environment only
	$(CDK) synth --context env=prod

diff: ## Show CDK diff for dev environment
	@echo "$(CYAN)Showing diff for dev environment...$(RESET)"
	$(CDK) diff --context env=dev

diff-staging: ## Show CDK diff for staging environment
	$(CDK) diff --context env=staging

diff-prod: ## Show CDK diff for prod environment
	$(CDK) diff --context env=prod

deploy-dev: ## Deploy to dev environment
	@echo "$(CYAN)Deploying to dev environment...$(RESET)"
	$(CDK) deploy --all --context env=dev --require-approval never
	@echo "$(GREEN)Dev deployment complete!$(RESET)"

deploy-staging: ## Deploy to staging environment (with approval)
	@echo "$(YELLOW)Deploying to staging environment...$(RESET)"
	$(CDK) deploy --all --context env=staging --require-approval broadening
	@echo "$(GREEN)Staging deployment complete!$(RESET)"

deploy-prod: ## Deploy to prod environment (with approval)
	@echo "$(RED)Deploying to PRODUCTION environment...$(RESET)"
	@echo "$(YELLOW)This will prompt for approval on security-sensitive changes.$(RESET)"
	$(CDK) deploy --all --context env=prod --require-approval broadening
	@echo "$(GREEN)Production deployment complete!$(RESET)"

destroy-dev: ## Destroy dev environment (DANGEROUS!)
	@echo "$(RED)WARNING: This will destroy the dev environment!$(RESET)"
	@read -p "Are you sure? [y/N] " confirm && [ "$$confirm" = "y" ] || exit 1
	$(CDK) destroy --all --context env=dev --force

# =============================================================================
# Utilities
# =============================================================================

pre-commit-install: ## Install pre-commit hooks
	@echo "$(CYAN)Installing pre-commit hooks...$(RESET)"
	pre-commit install
	@echo "$(GREEN)Pre-commit hooks installed!$(RESET)"

pre-commit-run: ## Run pre-commit on all files
	@echo "$(CYAN)Running pre-commit on all files...$(RESET)"
	pre-commit run --all-files

clean: ## Clean generated files
	@echo "$(CYAN)Cleaning generated files...$(RESET)"
	rm -rf cdk.out/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf **/__pycache__/
	rm -rf *.egg-info/
	@echo "$(GREEN)Clean complete!$(RESET)"

# =============================================================================
# Compound targets
# =============================================================================

check: lint test ## Run lint and tests
	@echo "$(GREEN)All checks passed!$(RESET)"

ci: lint test synth ## Run full CI pipeline locally
	@echo "$(GREEN)CI pipeline complete!$(RESET)"

all: install lint test synth ## Install, lint, test, and synth
	@echo "$(GREEN)All tasks complete!$(RESET)"
