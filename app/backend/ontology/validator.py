"""
validator.py — Validates agent review results against ontological constraints.

Takes the dict produced by review_file() in review.py and enriches it with:
  - ontological class annotations for each finding
  - a conformance score (how many required fields are present)
  - a list of ontological violations (missing fields, unclassified findings)

Does NOT require rdflib — uses the SkillMapper for classification.
"""
from __future__ import annotations
import re
from typing import Any
from .mapper import SkillMapper, AAI

_mapper = SkillMapper()

# Required fields every review result must have
REQUIRED_FIELDS = {"file", "path", "elapsed", "lines", "review"}


class OntologyValidator:
    """Validates and enriches a review result dict with ontological annotations."""

    def validate(self, result: dict[str, Any], skill_name: str = "pr-reviewer") -> dict:
        """
        Validate a review result dict and return an enriched copy with:
          - ontological_class: the agent class URI
          - findings: list of {text, class_uri, class_name, severity}
          - conformance_score: 0.0–1.0
          - violations: list of violation messages
        """
        violations: list[str] = []
        findings:   list[dict] = []

        # ── 1. Required field check ───────────────────────────────────────
        missing = REQUIRED_FIELDS - set(result.keys())
        for f in missing:
            violations.append(f"Missing required field: '{f}' (expected by aai:Artifact)")

        # ── 2. Parse findings from markdown review text ───────────────────
        review_text = result.get("review", "")
        if review_text:
            findings = self._extract_findings(review_text)
        else:
            violations.append("Empty review text — no findings to classify (aai:ReviewReport must have aai:hasFinding)")

        # ── 3. Check elapsed time is a positive number ────────────────────
        elapsed = result.get("elapsed", 0)
        if not isinstance(elapsed, (int, float)) or elapsed <= 0:
            violations.append(f"aai:hasElapsedTime must be a positive decimal — got: {elapsed!r}")

        # ── 4. Check line count ───────────────────────────────────────────
        lines = result.get("lines", 0)
        if not isinstance(lines, int) or lines < 0:
            violations.append(f"aai:hasLineCount must be a non-negative integer — got: {lines!r}")

        # ── 5. Conformance score ──────────────────────────────────────────
        required_present = len(REQUIRED_FIELDS - missing)
        conformance_score = round(required_present / len(REQUIRED_FIELDS), 2)

        return {
            **result,
            "ontological_class":  _mapper.map_skill_to_agent_class(skill_name),
            "skill_class":        _mapper.map_skill_to_skill_class(skill_name),
            "findings":           findings,
            "finding_count":      len(findings),
            "conformance_score":  conformance_score,
            "violations":         violations,
            "ontology_valid":     len(violations) == 0,
        }

    def _extract_findings(self, text: str) -> list[dict]:
        """
        Parse markdown review text into a list of ontologically classified findings.
        Extracts ## headings and top-level bullet points as finding candidates.
        """
        findings = []

        # Extract ## headings (review sections)
        for match in re.finditer(r"^##\s+(.+)$", text, re.MULTILINE):
            heading = match.group(1).strip()
            if heading.lower() in {"summary", "what is done well", "overall"}:
                continue
            class_uri = _mapper.classify_finding(heading)
            findings.append({
                "text":       heading,
                "class_uri":  class_uri,
                "class_name": _mapper.short_name(class_uri),
                "severity":   _infer_severity(heading, class_uri),
                "source":     "heading",
            })

        # Extract bullet points that look like findings (start with 🚫, -, *, •)
        for match in re.finditer(r"^[\-\*•🚫💡]\s*(.{10,120})$", text, re.MULTILINE):
            bullet = match.group(1).strip()
            class_uri = _mapper.classify_finding(bullet)
            findings.append({
                "text":       bullet[:100] + ("…" if len(bullet) > 100 else ""),
                "class_uri":  class_uri,
                "class_name": _mapper.short_name(class_uri),
                "severity":   _infer_severity(bullet, class_uri),
                "source":     "bullet",
            })

        return findings

    def summarise_findings(self, findings: list[dict]) -> dict[str, int]:
        """Return a count of findings per ontological class name."""
        counts: dict[str, int] = {}
        for f in findings:
            name = f.get("class_name", "ReviewFinding")
            counts[name] = counts.get(name, 0) + 1
        return counts


def _infer_severity(text: str, class_uri: str) -> str:
    """Infer High/Medium/Low severity from class and text signals."""
    lower = text.lower()
    if "🚫" in text or class_uri.endswith("SecurityVulnerability"):
        return "High"
    if any(w in lower for w in ["critical", "must", "dangerous", "vulnerability", "injection"]):
        return "High"
    if any(w in lower for w in ["should", "issue", "bug", "error", "missing"]):
        return "Medium"
    return "Low"
