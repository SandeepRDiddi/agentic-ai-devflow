"""
mapper.py — Maps skill names and finding keywords to ontological class URIs.

This is the bridge between the runtime system (skill directory names, free-text
review output) and the formal OWL ontology. No rdflib required for the mapper
itself — it's a pure lookup layer so review.py can work without rdflib installed.
"""
from __future__ import annotations

AAI = "https://sandeep-diddi.github.io/agentic-ai-devflow/ontology#"

# ── Skill name → ontological class URI ───────────────────────────────────────

SKILL_TO_CLASS: dict[str, str] = {
    "pr-reviewer":         f"{AAI}PRReviewerAgent",
    "data-contract-bot":   f"{AAI}DataContractAgent",
    "openspec-validator":  f"{AAI}OpenSpecValidatorAgent",
    "agentbench-runner":   f"{AAI}AgentBenchAgent",
    "ontology-validator":  f"{AAI}OntologyValidatorAgent",
}

SKILL_TO_SKILL_CLASS: dict[str, str] = {
    "pr-reviewer":         f"{AAI}PRReviewerSkill",
    "data-contract-bot":   f"{AAI}DataContractSkill",
    "openspec-validator":  f"{AAI}OpenSpecValidatorSkill",
    "agentbench-runner":   f"{AAI}AgentBenchSkill",
    "ontology-validator":  f"{AAI}OntologyValidatorSkill",
}

# ── Finding keyword → ontological class URI ───────────────────────────────────
# Keywords are matched (case-insensitive) against finding headings/bullets

FINDING_KEYWORDS: list[tuple[list[str], str]] = [
    (
        ["sql injection", "xss", "csrf", "hardcoded secret", "hardcoded key",
         "missing auth", "unvalidated input", "injection", "secret", "password",
         "token", "credential", "privilege", "sanitiz", "escape"],
        f"{AAI}SecurityVulnerability",
    ),
    (
        ["bug", "error", "exception", "crash", "incorrect", "wrong", "broken",
         "null pointer", "index error", "key error", "attribute error", "race condition",
         "off-by-one", "logic error", "undefined", "none check"],
        f"{AAI}BugFinding",
    ),
    (
        ["performance", "n+1", "slow", "blocking", "async", "await", "latency",
         "memory", "cache", "index", "query", "bottleneck", "timeout", "inefficient"],
        f"{AAI}PerformanceIssue",
    ),
    (
        ["design", "architecture", "coupling", "cohesion", "dry", "single responsibility",
         "separation of concerns", "naming", "readability", "structure", "pattern",
         "abstraction", "refactor", "modular"],
        f"{AAI}DesignIssue",
    ),
    (
        ["test", "coverage", "unit test", "missing test", "assertion", "mock",
         "fixture", "edge case", "regression"],
        f"{AAI}CodeQualityIssue",
    ),
    (
        ["suggest", "consider", "improvement", "could", "might", "optional",
         "nice to have", "recommend", "tip", "hint"],
        f"{AAI}Suggestion",
    ),
]


class SkillMapper:
    """Maps skill names and free-text findings to ontological class URIs."""

    def map_skill_to_agent_class(self, skill_name: str) -> str:
        """Return the OWL class URI for an agent given its skill name."""
        return SKILL_TO_CLASS.get(skill_name, f"{AAI}SkillAgent")

    def map_skill_to_skill_class(self, skill_name: str) -> str:
        """Return the OWL Skill class URI for a given skill name."""
        return SKILL_TO_SKILL_CLASS.get(skill_name, f"{AAI}Skill")

    def classify_finding(self, text: str) -> str:
        """
        Given a finding's text (heading or bullet), return the best-matching
        ontological class URI from the ReviewFinding hierarchy.
        """
        lower = text.lower()
        for keywords, class_uri in FINDING_KEYWORDS:
            if any(kw in lower for kw in keywords):
                return class_uri
        return f"{AAI}ReviewFinding"

    def short_name(self, uri: str) -> str:
        """Return the local name from a full URI (e.g. 'SecurityVulnerability')."""
        return uri.split("#")[-1]

    def all_finding_classes(self) -> list[dict]:
        """Return all finding class URIs with their short names."""
        seen = {}
        for _, uri in FINDING_KEYWORDS:
            name = self.short_name(uri)
            seen[uri] = name
        seen[f"{AAI}ReviewFinding"] = "ReviewFinding"
        return [{"uri": k, "name": v} for k, v in seen.items()]
