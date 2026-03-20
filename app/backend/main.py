"""devflow-lab — FastAPI backend entry point."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="devflow-lab",
    description="Claude Skills + OpenSpec + Ontology + PR automation API",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "devflow-lab"}


@app.get("/skills")
async def list_skills():
    """List all installed Claude Skills."""
    import os
    from pathlib import Path
    skills_dir = Path("skills")
    skills = []
    for d in skills_dir.iterdir():
        skill_md = d / "SKILL.md"
        if skill_md.exists():
            skills.append({"name": d.name, "path": str(skill_md)})
    return {"skills": skills}


# ── Ontology routes ──────────────────────────────────────────────────────────

from app.backend.ontology.loader import get_loader
from app.backend.ontology.mapper import SkillMapper
from app.backend.ontology.validator import OntologyValidator

_mapper    = SkillMapper()
_validator = OntologyValidator()


class ValidateRequest(BaseModel):
    file: str
    path: str
    elapsed: float
    lines: int
    review: str
    skill: str = "pr-reviewer"


@app.get("/ontology", tags=["Ontology"])
async def ontology_info():
    """Return a summary of the loaded agentic-ai OWL ontology."""
    loader = get_loader()
    if not loader.is_available():
        return {
            "status": "unavailable",
            "reason": "rdflib not installed or ontology/agentic-ai.owl not found",
            "install": "pip install rdflib",
        }
    return {"status": "ok", **loader.summary()}


@app.get("/ontology/classes", tags=["Ontology"])
async def ontology_classes():
    """List all OWL classes defined in the agentic-ai ontology."""
    loader = get_loader()
    if not loader.is_available():
        raise HTTPException(status_code=503, detail="rdflib not installed — run: pip install rdflib")
    return {"classes": loader.get_classes()}


@app.get("/ontology/findings", tags=["Ontology"])
async def ontology_finding_classes():
    """List all subclasses of aai:ReviewFinding."""
    loader = get_loader()
    if not loader.is_available():
        # Fall back to mapper (no rdflib needed)
        return {"finding_classes": _mapper.all_finding_classes()}
    return {"finding_classes": loader.get_finding_classes()}


@app.get("/ontology/skills", tags=["Ontology"])
async def ontology_skill_mapping():
    """Map skill directory names to their ontological agent/skill class URIs."""
    skills = [
        "pr-reviewer", "data-contract-bot",
        "openspec-validator", "agentbench-runner", "ontology-validator",
    ]
    return {
        "skill_mapping": [
            {
                "skill_name":   s,
                "agent_class":  _mapper.map_skill_to_agent_class(s),
                "skill_class":  _mapper.map_skill_to_skill_class(s),
            }
            for s in skills
        ]
    }


@app.post("/ontology/validate", tags=["Ontology"])
async def ontology_validate(req: ValidateRequest):
    """
    Validate a review result against the agentic-ai OWL ontology.
    Returns ontological class annotations, finding classifications, and a conformance score.
    """
    result = req.model_dump(exclude={"skill"})
    enriched = _validator.validate(result, skill_name=req.skill)
    return {
        "ontology_valid":     enriched["ontology_valid"],
        "conformance_score":  enriched["conformance_score"],
        "ontological_class":  enriched["ontological_class"],
        "skill_class":        enriched["skill_class"],
        "finding_count":      enriched["finding_count"],
        "findings":           enriched["findings"],
        "violations":         enriched["violations"],
    }


# Uncomment as you build each module:
# from app.backend.specbot.routes import router as specbot_router
# from app.backend.commitcraft.routes import router as commitcraft_router
# from app.backend.agentbench.routes import router as agentbench_router
# app.include_router(specbot_router,    prefix="/specbot",    tags=["SpecBot"])
# app.include_router(commitcraft_router, prefix="/commitcraft", tags=["CommitCraft"])
# app.include_router(agentbench_router,  prefix="/agentbench",  tags=["AgentBench"])
