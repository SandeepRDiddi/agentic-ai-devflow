# devflow-lab 🤖

> **An open-source Agentic AI tool that automatically reviews your Python code, classifies every problem it finds, and produces a full report — in seconds instead of hours. Built on PhD research in Ontology & Semantic Web.**

[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue)](pyproject.toml)
[![Docker](https://img.shields.io/badge/docker-compose-blue)](docker-compose.yml)
[![Open Source](https://img.shields.io/badge/open--source-yes-brightgreen)](https://github.com/SandeepRDiddi/agentic-ai-devflow)

---

## What is this? (Plain English)

Imagine hiring a senior software engineer who can read every file in your codebase, spot every bug, security hole, and bad design — and hand you a detailed written report in under 2 minutes.

That is what this tool does. You point it at any Python project, and it:

1. Reads every `.py` file automatically
2. Sends each file to Claude (an AI made by Anthropic)
3. Gets back a full professional code review — bugs, security issues, performance problems, suggestions
4. Saves everything into a clean Markdown report you can share with your team

No setup complexity. No expensive consultants. One command.

**For business stakeholders:** A human senior engineer takes ~45 minutes to review a single file properly. This tool reviews the same file in ~25 seconds. On a 5-file project that is 3 hours 45 minutes of work done in under 2 minutes — a saving of 99%.

---

## The Research Behind It — Ontology & Semantic Web

This project is the production implementation of PhD research in **Ontology Engineering and Semantic Web** by [Sandeep Diddi](https://github.com/SandeepRDiddi).

The core idea from that research: *intelligent systems need formal knowledge structures, not just raw prompts.*

Here is how the research maps to the code:

| Research Concept | What it means | How it appears in this tool |
|---|---|---|
| **Ontological Role Definition** | Formally defining what an agent IS, its rules, and constraints | Each `SKILL.md` file — Claude's job description written as formal constraints |
| **Semantic Reasoner** | A system that reasons over structured knowledge | Claude Sonnet — given a formal skill, it reasons within those constraints |
| **OWL Ontology** | A machine-readable map of concepts and their relationships | `ontology/agentic-ai.owl` — 37 classes, openable in Protégé |
| **Schema Validation** | Enforcing that output matches a formal structure | OpenSpec YAML schemas — every review output is validated against them |
| **Knowledge Classification** | Sorting findings into formal categories | `aai:SecurityVulnerability`, `aai:BugFinding`, `aai:PerformanceIssue`, etc. |

**In simple terms:** Most AI tools just throw a prompt at a model and hope for the best. This tool gives Claude a *formal role definition* (like a job contract), structured rules (the ontology), and a *schema it must conform to* (OpenSpec). The result is structured, reproducible, and formally classifiable output — not just free-text.

---

## Before You Start — What You Need

You need three things before this will work. Do not skip any of them.

**1. Python 3.12 or higher**

Check your version:
```bash
python --version
# Must show Python 3.12.x or higher
```

If you do not have Python 3.12, download it from [python.org](https://www.python.org/downloads/).

**2. An Anthropic API Key**

This tool uses Claude (an AI by Anthropic) to do the actual reviewing. You need an API key to use Claude.

- Go to [console.anthropic.com](https://console.anthropic.com)
- Sign up or log in
- Click **API Keys** → **Create Key**
- Copy the key — it looks like `sk-ant-api03-...`

Keep this key private. Never commit it to git.

**3. Git**

To clone this repo you need git installed. Check with `git --version`. If not installed, download from [git-scm.com](https://git-scm.com).

---

## Setup — Step by Step

Follow every step in order. Each one builds on the previous.

### Step 1 — Clone the repository

```bash
git clone https://github.com/SandeepRDiddi/agentic-ai-devflow.git
cd agentic-ai-devflow
```

You should now be inside the `agentic-ai-devflow` folder. Verify with:
```bash
ls
# You should see: review.py, skills/, ontology/, app/, README.md, etc.
```

### Step 2 — Create your environment file

The tool needs your API key. It reads it from a file called `.env`.

```bash
# Copy the example file
cp .env.example .env
```

Now open `.env` in any text editor (TextEdit on Mac, Notepad on Windows, nano/vim in terminal):
```bash
# On Mac/Linux:
nano .env

# On Windows:
notepad .env
```

Find the line that says `ANTHROPIC_API_KEY=` and add your key after the equals sign:
```
ANTHROPIC_API_KEY=sk-ant-api03-your-actual-key-here
```

Save the file. Do not add quotes. Do not add spaces.

### Step 3 — Install Python dependencies

```bash
pip install anthropic rich httpx python-dotenv rdflib
```

This installs:
- `anthropic` — the Python library to talk to Claude
- `rich` — makes the terminal output look nice with colours and tables
- `httpx` — handles HTTP connections (handles corporate proxy/SSL issues)
- `python-dotenv` — reads your `.env` file
- `rdflib` — loads and queries the OWL ontology (needed for ontology mode)

If `pip` is not found, try `pip3` instead.

### Step 4 — Verify the setup works

Run this to confirm everything is connected:

```bash
python review.py
```

You should see a usage message like:
```
Usage: python review.py <path-to-project> [--ontology]
```

If you see an error about `ANTHROPIC_API_KEY not found`, go back to Step 2 and check your `.env` file.

---

## Running Your First Review

Point the tool at any Python project folder on your computer. You do not need to be inside that project — just pass its path.

```bash
# Review a project in a folder next to this one
python review.py ../my-python-project

# Review a project anywhere on your computer (use the full path)
python review.py /Users/yourname/projects/my-app

# Review this project itself
python review.py .
```

**What happens:**

1. The tool scans the folder for all `.py` files (skips `__pycache__`, `venv`, `__init__.py`, etc.)
2. It shows you a list of files it will review and asks nothing — it just starts
3. For each file, Claude reads it and writes a professional review live in your terminal
4. When all files are done, it saves a full report to `review_report.md` in this folder

**Open the report:**
```bash
# On Mac
open review_report.md

# Or open it in VS Code
code review_report.md
```

---

## Ontology-Aware Review (The PhD Research Feature)

Add `--ontology` to activate the research-driven mode. This uses the `ontology-validator` skill instead of the standard `pr-reviewer`.

```bash
python review.py ../my-python-project --ontology
```

**What is different in ontology mode:**

Instead of just writing a review, Claude classifies every single finding into a formal OWL (Web Ontology Language) category from the `aai:ReviewFinding` hierarchy:

| Category | OWL Class | What gets flagged |
|---|---|---|
| 🔴 Security | `aai:SecurityVulnerability` | SQL injection, hardcoded passwords, missing authentication, unvalidated input |
| 🟠 Bugs | `aai:BugFinding` | Logic errors, crashes, incorrect calculations, null pointer issues |
| 🟡 Performance | `aai:PerformanceIssue` | Slow database queries, blocking operations, memory waste |
| 🔵 Design | `aai:DesignIssue` | Messy structure, repeated code, tight coupling between parts |
| 🟢 Quality | `aai:CodeQualityIssue` | Missing documentation, no type hints, poor test coverage |
| 💡 Ideas | `aai:Suggestion` | Optional improvements, refactoring ideas |

Each finding in the report looks like:
```
[SecurityVulnerability] aai:SecurityVulnerability — Severity: High
> The authenticate() function passes raw user input directly into SQL —
> anyone can bypass login with ' OR 1=1 --
```

The report also includes:
- **Conformance score** per file — how well the file's structure matches ontological constraints (0–100%)
- **Finding distribution table** — how many of each type across the whole project
- **Agent OWL class** — which formal ontological agent performed the review

---

## Real Results — What This Actually Saves

Tested on a real 5-file Python payment pipeline (`security.py`, `fee.py`, `validation.py`, `audit.py`, `main.py`):

| File | Lines of code | Agent time | A human would take |
|---|---|---|---|
| security.py | 18 | 27 seconds | ~45 minutes |
| fee.py | 14 | 22 seconds | ~45 minutes |
| validation.py | 22 | 24 seconds | ~45 minutes |
| audit.py | 20 | 21 seconds | ~45 minutes |
| main.py | 38 | 26 seconds | ~45 minutes |
| **Total** | **112 lines** | **~2 minutes** | **~3 hours 45 minutes** |

**99% time saved. 108x faster. $450+ saved per review cycle** (at $150/hr developer rate).

---

## Business Performance Report

Want to show the ROI to your manager or team? Run:

```bash
python benchmark_report.py
```

Then open `benchmark_report.html` in your browser. It produces four interactive charts:
- Manual vs Agent time per file (bar chart)
- Percentage of time saved per file
- Cost comparison in dollars
- Speedup multiplier

No technical knowledge needed to read these charts. Share the HTML file directly in meetings.

---

## The Ontology File — For Researchers & Academics

The file `ontology/agentic-ai.owl` is a full **OWL (Web Ontology Language)** ontology in Turtle format. It formally defines the entire agentic system as a knowledge graph.

**To open it in Protégé** (the standard ontology editor used in academic research):

1. Download Protégé from [protege.stanford.edu](https://protege.stanford.edu) — it is free
2. Open Protégé
3. Go to **File → Open**
4. Select `ontology/agentic-ai.owl`

You will see the full class hierarchy, object properties (`hasSkill`, `produces`, `hasFinding`, etc.), data properties, and named individuals — all browsable and editable.

**What is in the ontology:**

- **37 OWL classes** across two domains:
  - Agent system classes: `SkillAgent`, `Task`, `Artifact`, `Skill`, `Schema` and their subtypes
  - Code review domain classes: `CodeFile`, `ReviewFinding` and its 6 subtypes
- **8 object properties** linking classes (e.g., `hasSkill`, `processesTask`, `produces`, `hasFinding`)
- **5 named skill individuals** — one for each skill in the `skills/` folder
- **242 RDF triples** total

---

## REST API — For Developers Integrating This

Start the API server:

```bash
# Option A — using hatch (recommended)
pip install hatch
hatch run dev

# Option B — direct uvicorn
pip install fastapi uvicorn
uvicorn app.backend.main:app --reload --port 8000
```

API is now running at `http://localhost:8000`. Open `http://localhost:8000/docs` for interactive documentation.

**Available endpoints:**

| Method | Endpoint | What it returns |
|---|---|---|
| `GET` | `/health` | Server status check |
| `GET` | `/skills` | List all installed Claude Skills |
| `GET` | `/ontology` | Ontology summary — class count, triple count, namespace |
| `GET` | `/ontology/classes` | All 37 OWL classes with labels and descriptions |
| `GET` | `/ontology/findings` | The 6 `ReviewFinding` subclasses |
| `GET` | `/ontology/skills` | Skill name → OWL class URI mapping |
| `POST` | `/ontology/validate` | Send a review result, get back conformance score and classified findings |

**Example API call:**
```bash
curl http://localhost:8000/ontology
# Returns: {"status":"ok","total_triples":242,"classes":37,...}
```

---

## Run AgentBench (Performance Benchmark)

AgentBench measures Claude against 6 real developer tasks and compares time to manual estimates:

```bash
pip install hatch
hatch run benchmark
```

Outputs a live terminal table plus saves `agentbench/results.csv`. Also uploaded automatically as a GitHub Actions artifact on every push to `main`.

---

## Common Problems & Fixes

**"ANTHROPIC_API_KEY not found"**
Your `.env` file is missing or the key is not set correctly. Open `.env` and make sure it contains:
```
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
```
No quotes. No spaces around the `=` sign.

**"No Python files found"**
The path you passed does not contain any `.py` files, or they are all in skipped folders (`venv`, `__pycache__`, etc.). Try passing the exact folder that contains your `.py` files directly.

**"SSL Certificate error" or "CERTIFICATE_VERIFY_FAILED"**
This is a corporate network/proxy issue. The tool handles this automatically using `httpx.Client(verify=False)`. If you still see it, check that your API key is valid first.

**"Skill 'ontology-validator' not found"**
You are running `--ontology` but the skill file is missing. Make sure you cloned the full repo and that `skills/ontology-validator/SKILL.md` exists.

**"ModuleNotFoundError: No module named 'anthropic'"**
You skipped Step 3. Run:
```bash
pip install anthropic rich httpx python-dotenv rdflib
```

**"pip not found"**
Try `pip3` instead of `pip`. On some systems Python 3 uses `pip3`.

**The review runs but output is empty**
Your API key may be invalid or out of credits. Check [console.anthropic.com](https://console.anthropic.com) to verify your key is active.

---

## Project Structure — Every File Explained

```
agentic-ai-devflow/
│
├── review.py                 ← ⭐ START HERE. Run this to review any Python project.
│                               Add --ontology for research-grade classified output.
│
├── benchmark_report.py       ← Run to generate business ROI charts (opens in browser)
│
├── ontology/
│   └── agentic-ai.owl        ← The OWL ontology (Protégé-compatible Turtle format).
│                               37 classes, 242 triples. The formal knowledge model.
│
├── skills/                   ← Each subfolder is a Claude "Skill" — a formal agent role.
│   ├── pr-reviewer/
│   │   └── SKILL.md          ← Makes Claude behave as a senior code reviewer
│   ├── data-contract-bot/
│   │   └── SKILL.md          ← Makes Claude behave as a data architect
│   ├── openspec-validator/
│   │   └── SKILL.md          ← Makes Claude validate schemas
│   ├── agentbench-runner/
│   │   └── SKILL.md          ← Makes Claude run performance benchmarks
│   └── ontology-validator/
│       └── SKILL.md          ← Makes Claude classify findings into OWL classes (PhD feature)
│
├── app/backend/
│   ├── main.py               ← FastAPI server. Exposes /health /skills /ontology routes.
│   ├── agent.py              ← LangGraph orchestrator. Runs any skill on any input.
│   ├── ontology/             ← Python module for the ontology layer
│   │   ├── loader.py         ← Loads agentic-ai.owl, runs SPARQL queries via rdflib
│   │   ├── mapper.py         ← Maps skill names to OWL class URIs (no rdflib needed)
│   │   └── validator.py      ← Validates review output, classifies findings, conformance
│   ├── specbot/
│   │   └── validate.py       ← Validates content against OpenSpec YAML schemas
│   ├── commitcraft/
│   │   └── diff_parser.py    ← Takes a git diff, generates a PR description via Claude
│   └── agentbench/
│       └── benchmark.py      ← Times 6 tasks, compares agent vs manual, saves CSV
│
├── spec/
│   ├── pr-spec.yaml          ← OpenSpec schema: what a PR description must contain
│   └── data-contract.spec.yaml ← OpenSpec schema: what a data contract must contain
│
├── .github/workflows/
│   ├── ci.yml                ← Runs lint + tests on every PR. Runs benchmark on main.
│   └── pr-review.yml         ← Auto-generates PR description when you open a PR.
│
├── evals/                    ← Test cases for checking skill trigger accuracy
├── scripts/run_eval.py       ← Runs the skill accuracy evaluation
├── mini_reviewer/            ← Demo scripts used in early development
├── .env.example              ← Copy this to .env and add your API key
├── pyproject.toml            ← Python project config and dependencies
├── docker-compose.yml        ← Run everything in Docker with one command
└── Makefile                  ← Shortcuts: make dev, make test, make benchmark
```

---

## How It All Works — The Full Picture

The entire project is built on one repeating pattern:

```
SKILL.md (formal role)  +  Your code (the task)
           ↓
      Claude Sonnet
    (semantic reasoner)
           ↓
  Structured output (validated against schema)
```

**Step 1 — The Skill defines the agent's role.**
A `SKILL.md` file is not a simple prompt. It is a formal specification: what the agent is, what domain it covers, what rules it must follow, and what its output must look like. In ontological terms it is a *role definition* — the same concept used in multi-agent systems research.

**Step 2 — The task is your code.**
You pass a Python file. The tool reads it and sends it to Claude along with the Skill as the system prompt.

**Step 3 — Claude reasons within the constraints.**
Claude does not just write free-text back. Because the Skill formally constrains its output, it produces structured, classifiable, reproducible results every time.

**Step 4 — The ontology validates and classifies.**
The `OntologyValidator` module checks the output against the formal OWL ontology. Every finding is mapped to its correct class URI. A conformance score tells you how well the reviewed file matches ontological constraints.

**Step 5 — You get a report.**
A clean Markdown file. Ready to share with your team, your manager, or publish alongside your research.

---

## Contributing

PRs are welcome. The moment you open a PR, the GitHub Action will automatically generate a PR description using the `commitcraft` module and Claude — so your PR fills itself in.

Please read the existing `SKILL.md` files before adding new ones. Each skill should have a clear, non-overlapping role definition.

---

## License

MIT — use it freely, commercially or academically. Attribution appreciated but not required.

---

## Author

Built by **Sandeep Diddi** — PhD Researcher in Ontology & Semantic Web.

- GitHub: [github.com/SandeepRDiddi](https://github.com/SandeepRDiddi)
- Repo: [github.com/SandeepRDiddi/agentic-ai-devflow](https://github.com/SandeepRDiddi/agentic-ai-devflow)

*This project is active research in progress. Watch this space.*
