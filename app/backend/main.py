"""devflow-lab — FastAPI backend entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="devflow-lab",
    description="Claude Skills + OpenSpec + PR automation API",
    version="0.1.0",
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


# Uncomment as you build each module:
# from app.backend.specbot.routes import router as specbot_router
# from app.backend.commitcraft.routes import router as commitcraft_router
# from app.backend.agentbench.routes import router as agentbench_router
# app.include_router(specbot_router,    prefix="/specbot",    tags=["SpecBot"])
# app.include_router(commitcraft_router, prefix="/commitcraft", tags=["CommitCraft"])
# app.include_router(agentbench_router,  prefix="/agentbench",  tags=["AgentBench"])
