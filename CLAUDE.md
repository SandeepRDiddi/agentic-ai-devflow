# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**devflow-lab** — an open-source app demonstrating Claude Skills, OpenSpec schema validation, GitHub PR automation (CommitCraft), and agent benchmarking (AgentBench). All commands must be run from the `devflow-lab/` directory.

## Commands

All scripts are defined in `pyproject.toml` under `[tool.hatch.envs.default.scripts]` and run via `hatch run <script>`:

```bash
cd devflow-lab

hatch run dev          # Start FastAPI server on :8000 with hot reload
hatch run test         # Run all tests
hatch run lint         # ruff check + format check
hatch run fmt          # Auto-format with ruff
hatch run benchmark    # Run AgentBench (6 tasks, outputs agentbench/results.csv)
hatch run eval         # Run skill trigger accuracy evaluation
```

Run a single test file:
```bash
cd devflow-lab && hatch run pytest tests/path/to/test_file.py -v
```

Makefile aliases exist for the above (`make dev`, `make test`, etc.) plus `make docker-up` / `make docker-down`.

## Architecture

### Skills System (`skills/`)
Each skill is a directory containing a `SKILL.md` file that serves as a system prompt. The `agent.py` orchestrator loads skill files dynamically via `load_skill(skill_name)` — it looks up `skills/<name>/SKILL.md` relative to the working directory. Four skills exist: `pr-reviewer`, `data-contract-bot`, `openspec-validator`, `agentbench-runner`.

### LangGraph Agent (`app/backend/agent.py`)
Manages Claude interactions with optional Langfuse tracing. Uses `AgentState` TypedDict to track task/skill/result across graph nodes. Wraps `anthropic.Anthropic` client — the skill content becomes the `system` prompt, and task input becomes the user message.

### OpenSpec (`spec/`)
YAML schemas define the structure that Claude must produce. Two specs exist: `pr-spec.yaml` (PR descriptions) and `data-contract.spec.yaml` (ODCS data contracts). Both `commitcraft/diff_parser.py` and `specbot/validate.py` load these specs and inject them into Claude prompts to enforce structured output.

### CommitCraft (`app/backend/commitcraft/diff_parser.py`)
Takes a git diff, loads `spec/pr-spec.yaml`, builds a structured prompt, and calls Claude to produce a PR description written to a markdown file. Used by the `.github/workflows/pr-review.yml` GitHub Action to auto-comment on PRs.

### SpecBot (`app/backend/specbot/validate.py`)
Validates arbitrary content against a loaded OpenSpec YAML schema using Claude. Returns JSON with `valid`, `violations`, and `suggestions` fields.

### AgentBench (`app/backend/agentbench/benchmark.py`)
Runs 6 hardcoded dev tasks against Claude, measures wall-clock time vs. manual estimates, and outputs a rich terminal table plus `agentbench/results.csv`. Requires `.env` to be loaded (uses `python-dotenv`).

### Evals (`scripts/run_eval.py`, `evals/`)
Measures skill trigger accuracy: given a user prompt, would Claude invoke the right skill? Test cases in `evals/*.json` have `should_trigger: true/false` flags. The runner uses Claude to simulate skill routing and reports overall accuracy.

### FastAPI Backend (`app/backend/main.py`)
Minimal entry point — `/health` and `/skills` endpoints are active. Routes for `specbot`, `commitcraft`, and `agentbench` are scaffolded but commented out, ready to be wired up.

## Environment

Copy `.env.example` to `.env` in `devflow-lab/`. Required: `ANTHROPIC_API_KEY`. Optional: Langfuse keys for tracing. The benchmark and eval scripts load `.env` via `python-dotenv` relative to their `__file__` path.

## CI

`.github/workflows/ci.yml` runs lint + test on all PRs, and runs AgentBench on pushes to `main` (uploads `results.csv` as an artifact). `.github/workflows/pr-review.yml` auto-generates PR descriptions via CommitCraft on PR open/sync.
