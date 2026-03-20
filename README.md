# devflow-lab 🤖

> **One deployable open-source app that bridges PhD research in Ontology & Semantic Web with production Agentic AI — featuring Claude Skills, OWL ontology-driven code review, OpenSpec schema validation, GitHub PR automation, and agent benchmarking.**

[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue)](pyproject.toml)
[![Docker](https://img.shields.io/badge/docker-compose-blue)](docker-compose.yml)

## What's inside

| Layer | What it does | |
|---|---|---|
| **`review.py`** | One-command AI code reviewer — standard or ontology-aware mode | ⭐ Start here |
| **`ontology/agentic-ai.owl`** | OWL ontology: agent system + code review domain (Protégé-compatible) | 🧠 Ontology |
| **`app/backend/ontology/`** | Python module: OWL loader (rdflib), finding classifier, conformance validator | 🔍 Semantic layer |
| **5 Claude Skills** | pr-reviewer, data-contract-bot, openspec-validator, agentbench-runner, **ontology-validator** | 🎯 Skills |
| **GitHub Actions** | Auto-fills PR templates from diffs using Claude | CommitCraft |
| **FastAPI backend** | LangGraph agent + `/ontology` API endpoints | DevFlow Hub |
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

### Ontology-aware mode (new 🧠)

```bash
# Add --ontology to classify every finding into a formal OWL class
python review.py ../your-python-project --ontology
```

With `--ontology`, the `ontology-validator` skill is used. Each finding in the report is tagged with its OWL class URI from the `aai:ReviewFinding` hierarchy:

| OWL Class | What it flags |
|---|---|
| `aai:SecurityVulnerability` | SQL injection, hardcoded secrets, missing auth |
| `aai:BugFinding` | Logic errors, crashes, incorrect behaviour |
| `aai:PerformanceIssue` | N+1 queries, blocking async, memory waste |
| `aai:DesignIssue` | DRY violations, tight coupling, poor naming |
| `aai:CodeQualityIssue` | Missing type hints, test gaps, poor docs |
| `aai:Suggestion` | Optional improvements, nice-to-haves |

The report also includes a **conformance score** (how closely the file's structure matches ontological constraints) and an **ontological finding distribution table**.

### What you get

- **Terminal output** — live review with ontological class labels per finding
- **`review_report.md`** — full structured report including OWL class annotations, conformance scores, and finding distribution table

### Examples

```bash
# Standard review (pr-reviewer skill)
python review.py ../SOLO_NODE

# Ontology-aware review (ontology-validator skill)
python review.py ../SOLO_NODE --ontology

# Review a FastAPI app with ontology classification
python review.py ~/projects/my-fastapi-app --ontology

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
├── review.py                          # ⭐ AI code reviewer (--ontology for OWL mode)
├── ontology/
│   └── agentic-ai.owl                 # 🧠 OWL ontology in Turtle format (Protégé-compatible)
├── .github/
│   ├── PULL_REQUEST_TEMPLATE.md       # OpenSpec-driven PR template
│   └── workflows/
│       ├── pr-review.yml              # Auto-fills PRs with Claude
│       └── ci.yml                     # Lint + test + benchmark
├── spec/
│   ├── pr-spec.yaml                   # OpenSpec schema for PRs
│   └── data-contract.spec.yaml        # OpenSpec schema for data contracts
├── skills/
│   ├── pr-reviewer/SKILL.md           # Ontological role: senior code reviewer
│   ├── data-contract-bot/SKILL.md     # Ontological role: data architect
│   ├── openspec-validator/SKILL.md    # Ontological role: schema validator
│   ├── agentbench-runner/SKILL.md     # Ontological role: benchmark runner
│   └── ontology-validator/SKILL.md   # 🧠 Ontological role: OWL-aware code reviewer
├── app/
│   └── backend/
│       ├── main.py                    # FastAPI entry point + /ontology routes
│       ├── agent.py                   # LangGraph + Langfuse orchestrator
│       ├── ontology/                  # 🧠 Ontology Python module
│       │   ├── loader.py              # rdflib OWL loader + SPARQL queries
│       │   ├── mapper.py              # skill name → OWL class URI (no rdflib needed)
│       │   └── validator.py           # conformance checker + finding classifier
│       ├── specbot/validate.py        # OpenSpec validator
│       ├── commitcraft/diff_parser.py # Diff → PR description
│       └── agentbench/benchmark.py    # Timing harness
├── mini_reviewer/                     # Demo scripts
├── evals/
│   └── pr-reviewer-evals.json
├── scripts/
│   └── run_eval.py
├── pyproject.toml                     # Hatch workspace (includes rdflib)
├── docker-compose.yml
└── Makefile
```

## Ontology layer — PhD research in production

The `ontology/` directory contains a full OWL ontology (`agentic-ai.owl`) that formally models the entire agentic system. It is **Protégé-compatible** — open the file directly in [Protégé](https://protege.stanford.edu/) to browse the class hierarchy.

### Three-layer semantic architecture

```
Ontological Skill (SKILL.md = OWL role definition)
      +
Semantic Schema (OpenSpec YAML = OWL class constraints)
      +
Knowledge Input (Python code = aai:CodeFile instances)
          ↓
Claude Sonnet (aai:SkillAgent — semantic reasoner)
          ↓
Ontologically-classified Output (aai:ReviewReport with aai:hasFinding assertions)
```

### Key ontological classes

**Agent system:**
- `aai:SkillAgent` — any agent whose behaviour is defined by a Skill
- `aai:PRReviewerAgent`, `aai:OntologyValidatorAgent`, … — concrete agent types
- `aai:Skill` — formal role definition (SKILL.md as ontological constraint set)
- `aai:Schema` — OpenSpec YAML schema enforcing output structure

**Code review domain:**
- `aai:CodeFile` → `aai:PythonFile` — source files under review
- `aai:ReviewFinding` — base class for all findings
  - `aai:SecurityVulnerability` · `aai:BugFinding` · `aai:PerformanceIssue`
  - `aai:DesignIssue` · `aai:CodeQualityIssue` · `aai:Suggestion`

### Ontology API endpoints

```bash
GET  /ontology              # Summary: class count, triple count, namespace
GET  /ontology/classes      # All OWL classes with labels + comments
GET  /ontology/findings     # All subclasses of aai:ReviewFinding
GET  /ontology/skills       # Skill → agent class URI mapping
POST /ontology/validate     # Validate a review result, returns conformance score + finding classifications
```

### Install with rdflib (for full OWL queries)

```bash
pip install rdflib
```

Without rdflib, `review.py --ontology` and the `/ontology/validate` endpoint still work — they use the lightweight `SkillMapper` and `OntologyValidator` modules which have no rdflib dependency.

---

## How it works

The core pattern behind everything in this repo:

```
Ontological Skill (SKILL.md)  +  Your code  →  Claude (semantic reasoner)  →  Schema-validated structured output
```

Each `SKILL.md` is an **ontological role definition** that formally constrains the agent's domain, reasoning rules, and output structure. The `pr-reviewer` skill makes Claude behave like a senior engineer. The `ontology-validator` skill makes it reason over the formal OWL class hierarchy and tag every finding with its `aai:ReviewFinding` subclass URI. OpenSpec YAML schemas act as runtime ontological constraints on the output.

## Contributing

PRs welcome. The GitHub Action will auto-generate your PR description the moment you open one.

## License

MIT
