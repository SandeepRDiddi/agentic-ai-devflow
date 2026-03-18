"""
mini_reviewer/api.py
────────────────────
A minimal FastAPI app that wires the devflow-lab skills system to a
real HTTP endpoint.  Run with:

    cd devflow-lab
    python -m uvicorn mini_reviewer.api:app --reload --port 8080

Endpoints:
    GET  /health          → liveness check
    GET  /skills          → list available skills
    POST /review          → AI code review (pr-reviewer skill)
    POST /contract        → data-contract validation
    POST /benchmark       → run 1 quick agent task and return timing
"""

import os, re, time
from pathlib import Path

# ── Load .env manually (handles quoted values in any environment) ────────────
_env_file = Path(__file__).parents[1] / ".env"
if _env_file.exists():
    for _line in _env_file.read_text().splitlines():
        m = re.match(r'^([A-Z_]+)\s*=\s*["\']?([^"\'#\n]+)["\']?', _line.strip())
        if m and m.group(1) not in os.environ:
            os.environ[m.group(1)] = m.group(2).strip()

import httpx
import anthropic
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ── Anthropic client — lazy init so env vars have time to propagate ──────────
_model  = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
_claude = None   # created on first call

def _get_claude() -> anthropic.Anthropic:
    global _claude
    if _claude is None:
        key = os.getenv("ANTHROPIC_API_KEY", "")
        _claude = anthropic.Anthropic(
            api_key=key,
            http_client=httpx.Client(verify=False),   # bypass self-signed proxy cert
        )
    return _claude

# ── Skills loader ────────────────────────────────────────────────────────────
SKILLS_DIR = Path(__file__).parents[1] / "skills"

def load_skill(name: str) -> str:
    path = SKILLS_DIR / name / "SKILL.md"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Skill '{name}' not found")
    return path.read_text()

def call_claude(system: str, user: str, max_tokens: int = 1500) -> tuple[str, float]:
    """Call Claude, return (text, elapsed_seconds)."""
    start = time.time()
    resp  = _get_claude().messages.create(
        model=_model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return resp.content[0].text, round(time.time() - start, 2)

# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="devflow-lab · mini reviewer",
    description="Agentic AI code review powered by Claude Skills",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request / Response models ─────────────────────────────────────────────────
class ReviewRequest(BaseModel):
    code: str
    context: str = "General code review"   # optional hint
    skill: str   = "pr-reviewer"           # which skill to use

class ReviewResponse(BaseModel):
    skill: str
    model: str
    elapsed_sec: float
    review: str

class ContractRequest(BaseModel):
    contract: str   # free-text description of the data contract

class BenchmarkRequest(BaseModel):
    task: str       # any dev task description
    manual_minutes: int = 30  # your honest estimate

class BenchmarkResponse(BaseModel):
    task: str
    manual_minutes: int
    agent_seconds: float
    speedup: str
    output_preview: str

# ── Endpoints ─────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "model": os.getenv("ANTHROPIC_MODEL", _model), "skills_dir": str(SKILLS_DIR)}


@app.get("/skills")
def list_skills():
    skills = []
    for d in sorted(SKILLS_DIR.iterdir()):
        skill_md = d / "SKILL.md"
        if skill_md.exists():
            # Read first non-frontmatter line as description
            lines = [l.strip() for l in skill_md.read_text().splitlines()
                     if l.strip() and not l.startswith("---") and not l.startswith("name:")
                     and not l.startswith("description:")]
            desc = lines[0] if lines else ""
            skills.append({"name": d.name, "description": desc[:80]})
    return {"count": len(skills), "skills": skills}


@app.post("/review", response_model=ReviewResponse)
def review_code(req: ReviewRequest):
    """
    Submit a code snippet for an AI review.
    Claude loads the requested skill as its system prompt and returns
    a structured Markdown review.
    """
    system = load_skill(req.skill)
    user   = f"Context: {req.context}\n\n```\n{req.code}\n```"
    text, elapsed = call_claude(system, user)
    return ReviewResponse(
        skill=req.skill,
        model=_model,
        elapsed_sec=elapsed,
        review=text,
    )


@app.post("/contract")
def validate_contract(req: ContractRequest):
    """Validate a data contract description using the data-contract-bot skill."""
    system = load_skill("data-contract-bot")
    text, elapsed = call_claude(system, req.contract)
    return {"elapsed_sec": elapsed, "result": text}


@app.post("/benchmark", response_model=BenchmarkResponse)
def quick_benchmark(req: BenchmarkRequest):
    """
    Run ONE agent task and compare to your manual time estimate.
    Proves agentic AI by showing real wall-clock speedup.
    """
    system = load_skill("pr-reviewer")
    text, elapsed = call_claude(system, req.task)

    agent_min = elapsed / 60
    speedup   = round(req.manual_minutes / max(agent_min, 0.001))

    return BenchmarkResponse(
        task=req.task,
        manual_minutes=req.manual_minutes,
        agent_seconds=elapsed,
        speedup=f"~{speedup}x faster",
        output_preview=text[:300].replace("\n", " ") + "...",
    )
