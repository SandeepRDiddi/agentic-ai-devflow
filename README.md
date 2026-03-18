# devflow-lab 🤖

> **One deployable open-source app that teaches you Claude Skills, OpenSpec, GitHub PR automation, and agent benchmarking — end to end.**

[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue)](pyproject.toml)
[![Docker](https://img.shields.io/badge/docker-compose-blue)](docker-compose.yml)

## What's inside

| Layer | What it does | |
|---|---|---|
| **`review.py`** | One-command AI code reviewer — point at any Python project | ⭐ Start here |
| **GitHub Actions** | Auto-fills PR templates from diffs using Claude | CommitCraft |
| **FastAPI backend** | LangGraph agent orchestrating all Claude Skills | DevFlow Hub |
| **Claude Skills** | 4 SKILL.md files — pr-reviewer, data-contract-bot, openspec-validator, agentbench-runner | SkillForge |
| **AgentBench** | Times 6 dev tasks: manual vs agent, writes results.csv | AgentBench |
| **OpenSpec** | spec.yaml contracts enforced by SpecBot | SpecBot |

---

## ⭐ Quickstart — AI code review on any Python project

```bash
# 1. Clone this repo
git clone https://github.com/SandeepRDiddi/agentic-ai-devflow.git
cd agentic-ai-devflow

# 2. Add your Anthropic API key
cp .env.example .env
# Open .env and set: ANTHROPIC_API_KEY=sk-ant-...

# 3. Install dependencies
pip install anthropic rich httpx python-dotenv

# 4. Point at any Python project and get a full AI review
python review.py ../your-python-project
```

That's it. Claude reviews every Python file using the `pr-reviewer` skill and saves a full Markdown report to `review_report.md`.

### What you get

- **Terminal output** — live review of each file printed as Claude reads it
- **`review_report.md`** — structured report saved to disk covering security issues, bugs, performance, test coverage, and concrete code suggestions

### Examples

```bash
# Review any project by passing its folder path
python review.py ../SOLO_NODE

# Review a FastAPI app
python review.py ~/projects/my-fastapi-app

# Review the current directory
python review.py .
```

### Benchmark — what this actually saves you

Running `review.py` on a 5-file Python transaction pipeline:

| File | Lines | Agent time | Manual estimate |
|---|---|---|---|
| security.py | 18 | 27s | ~45 min |
| fee.py | 14 | 22s | ~45 min |
| validation.py | 22 | 24s | ~45 min |
| audit.py | 20 | 21s | ~45 min |
| main.py | 38 | 26s | ~45 min |
| **Total** | **112** | **~2 min** | **~3h 45m** |

**~99% time saved. ~108x faster than a manual review.**

---

## Full setup (Docker)

```bash
# 1. Clone and configure
git clone https://github.com/SandeepRDiddi/agentic-ai-devflow
cd agentic-ai-devflow
cp .env.example .env
# Edit .env → set ANTHROPIC_API_KEY=sk-ant-...

# 2. Run everything
docker compose up
```

- Backend API:  http://localhost:8000
- API docs:     http://localhost:8000/docs

## Manual setup (no Docker)

```bash
pip install hatch
hatch env create
hatch run dev       # starts FastAPI on port 8000
```

## Run the AgentBench

```bash
hatch run benchmark
# Outputs a rich table + agentbench/results.csv
```

| Task | Manual | Agent | Saved |
|---|---|---|---|
| Write PR description | 25 min | ~1.5 min | 94% |
| Validate data contract | 40 min | ~2 min | 95% |
| Code review + comments | 55 min | ~3 min | 95% |
| Generate OpenSpec YAML | 30 min | ~1 min | 97% |
| Write unit tests | 60 min | ~5 min | 92% |
| README + changelog | 20 min | ~1 min | 95% |
| **Total** | **3h 50m** | **~14 min** | **~17x faster** |

## Run skill evals

```bash
hatch run eval
# Measures how reliably each SKILL.md triggers
```

## Project structure

```
agentic-ai-devflow/
├── review.py                          # ⭐ AI code reviewer — point at any project
├── .github/
│   ├── PULL_REQUEST_TEMPLATE.md       # OpenSpec-driven PR template
│   └── workflows/
│       ├── pr-review.yml              # Auto-fills PRs with Claude
│       └── ci.yml                     # Lint + test + benchmark
├── spec/
│   ├── pr-spec.yaml                   # OpenSpec schema for PRs
│   └── data-contract.spec.yaml        # OpenSpec schema for data contracts
├── skills/
│   ├── pr-reviewer/SKILL.md
│   ├── data-contract-bot/SKILL.md
│   ├── openspec-validator/SKILL.md
│   └── agentbench-runner/SKILL.md
├── app/
│   └── backend/
│       ├── main.py                    # FastAPI entry point
│       ├── agent.py                   # LangGraph + Langfuse orchestrator
│       ├── specbot/validate.py        # OpenSpec validator
│       ├── commitcraft/diff_parser.py # Diff → PR description
│       └── agentbench/benchmark.py    # Timing harness
├── mini_reviewer/                     # Demo scripts
├── evals/
│   └── pr-reviewer-evals.json
├── scripts/
│   └── run_eval.py
├── pyproject.toml                     # Hatch workspace
├── docker-compose.yml
└── Makefile
```

## How it works

The core pattern behind everything in this repo:

```
Skill (SKILL.md)  +  Your code  →  Claude  →  Structured output
```

Each `SKILL.md` is a system prompt that turns Claude into a specialist. The `pr-reviewer` skill makes Claude behave like a senior engineer doing code reviews. The `data-contract-bot` skill makes it behave like a data architect. You pass your code as the task, and Claude produces professional-quality output in seconds.

## Contributing

PRs welcome. The GitHub Action will auto-generate your PR description the moment you open one.

## License

MIT
