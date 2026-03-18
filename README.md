# devflow-lab 🤖

> **One deployable open-source app that teaches you Claude Skills, OpenSpec, GitHub PR automation, and agent benchmarking — end to end.**

[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue)](pyproject.toml)
[![Docker](https://img.shields.io/badge/docker-compose-blue)](docker-compose.yml)

## What's inside

| Layer | What it does | Project |
|---|---|---|
| **GitHub Actions** | Auto-fills PR templates from diffs using Claude | CommitCraft · P2 |
| **FastAPI backend** | LangGraph agent orchestrating all Claude Skills | DevFlow Hub · P4 |
| **Claude Skills** | 4 SKILL.md files — pr-reviewer, data-contract-bot, openspec-validator, agentbench-runner | SkillForge · P3 |
| **AgentBench** | Times 6 dev tasks: manual vs agent, writes results.csv | AgentBench · P5 |
| **OpenSpec** | spec.yaml contracts enforced by SpecBot | SpecBot · P1 |

## Quickstart

```bash
# 1. Clone
git clone https://github.com/SandeepRDiddi/devflow-lab
cd devflow-lab

# 2. Add your Anthropic API key
cp .env.example .env
# Edit .env → set ANTHROPIC_API_KEY=sk-ant-...

# 3. Run everything
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
# Outputs a table + agentbench/results.csv
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
devflow-lab/
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
├── evals/
│   └── pr-reviewer-evals.json
├── scripts/
│   └── run_eval.py
├── pyproject.toml                     # Hatch workspace
├── docker-compose.yml
└── Makefile
```

## Contributing

PRs welcome. The GitHub Action will auto-generate your PR description the moment you open one.

## License

MIT
