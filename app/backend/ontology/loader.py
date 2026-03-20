"""
loader.py — Loads the agentic-ai OWL ontology and exposes SPARQL query helpers.

The ontology is authored in OWL/Turtle format at:
    ontology/agentic-ai.owl

It is Protégé-compatible: open the .owl file directly in Protégé to browse
the class hierarchy, object/data properties, and named individuals.
"""
from __future__ import annotations

import os
from pathlib import Path
from functools import lru_cache
from typing import Any

try:
    from rdflib import Graph, Namespace, RDF, RDFS, OWL
    from rdflib.namespace import NamespaceManager
    RDFLIB_AVAILABLE = True
except ImportError:
    RDFLIB_AVAILABLE = False

# Namespace for our ontology
AAI_NS = "https://sandeep-diddi.github.io/agentic-ai-devflow/ontology#"
_OWL_PATH = Path(__file__).parent.parent.parent.parent / "ontology" / "agentic-ai.owl"


class OntologyLoader:
    """Loads agentic-ai.owl and provides query methods over the graph."""

    def __init__(self, owl_path: Path | None = None):
        self.owl_path = owl_path or _OWL_PATH
        self._graph: Any = None
        self._available = RDFLIB_AVAILABLE

    def _ensure_loaded(self):
        if self._graph is not None:
            return
        if not self._available:
            raise RuntimeError(
                "rdflib is not installed. Run: pip install rdflib"
            )
        if not self.owl_path.exists():
            raise FileNotFoundError(f"OWL file not found: {self.owl_path}")

        g = Graph()
        g.parse(str(self.owl_path), format="turtle")
        self._graph = g

    @property
    def graph(self) -> Any:
        self._ensure_loaded()
        return self._graph

    # ── Class queries ─────────────────────────────────────────────────────

    def get_classes(self) -> list[dict]:
        """Return all OWL classes with their labels and comments."""
        self._ensure_loaded()
        results = []
        query = """
            PREFIX owl:  <http://www.w3.org/2002/07/owl#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT ?cls ?label ?comment WHERE {
                ?cls a owl:Class .
                OPTIONAL { ?cls rdfs:label ?label . }
                OPTIONAL { ?cls rdfs:comment ?comment . }
            }
            ORDER BY ?label
        """
        for row in self._graph.query(query):
            uri = str(row.cls)
            if AAI_NS in uri:
                results.append({
                    "uri":     uri,
                    "name":    uri.split("#")[-1],
                    "label":   str(row.label) if row.label else "",
                    "comment": str(row.comment).strip() if row.comment else "",
                })
        return results

    def get_finding_classes(self) -> list[dict]:
        """Return all subclasses of ReviewFinding."""
        self._ensure_loaded()
        query = f"""
            PREFIX owl:  <http://www.w3.org/2002/07/owl#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX aai:  <{AAI_NS}>
            SELECT ?cls ?label WHERE {{
                ?cls rdfs:subClassOf+ aai:ReviewFinding .
                OPTIONAL {{ ?cls rdfs:label ?label . }}
            }}
            ORDER BY ?label
        """
        results = []
        for row in self._graph.query(query):
            results.append({
                "uri":   str(row.cls),
                "name":  str(row.cls).split("#")[-1],
                "label": str(row.label) if row.label else "",
            })
        return results

    def get_skill_classes(self) -> list[dict]:
        """Return all subclasses of Skill with their hasSkillName values."""
        self._ensure_loaded()
        query = f"""
            PREFIX owl:  <http://www.w3.org/2002/07/owl#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX aai:  <{AAI_NS}>
            SELECT ?inst ?skillName ?label WHERE {{
                ?inst a ?cls .
                ?cls rdfs:subClassOf* aai:Skill .
                OPTIONAL {{ ?inst aai:hasSkillName ?skillName . }}
                OPTIONAL {{ ?inst rdfs:label ?label . }}
            }}
        """
        results = []
        for row in self._graph.query(query):
            results.append({
                "uri":        str(row.inst),
                "skill_name": str(row.skillName) if row.skillName else "",
                "label":      str(row.label) if row.label else "",
            })
        return results

    # ── Property queries ──────────────────────────────────────────────────

    def get_object_properties(self) -> list[dict]:
        """Return all owl:ObjectProperty entries."""
        self._ensure_loaded()
        query = """
            PREFIX owl:  <http://www.w3.org/2002/07/owl#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT ?prop ?label ?domain ?range WHERE {
                ?prop a owl:ObjectProperty .
                OPTIONAL { ?prop rdfs:label  ?label  . }
                OPTIONAL { ?prop rdfs:domain ?domain . }
                OPTIONAL { ?prop rdfs:range  ?range  . }
            }
            ORDER BY ?label
        """
        results = []
        for row in self._graph.query(query):
            results.append({
                "uri":    str(row.prop),
                "name":   str(row.prop).split("#")[-1],
                "label":  str(row.label) if row.label else "",
                "domain": str(row.domain).split("#")[-1] if row.domain else "",
                "range":  str(row.range).split("#")[-1]  if row.range  else "",
            })
        return results

    # ── Summary ───────────────────────────────────────────────────────────

    def summary(self) -> dict:
        """High-level summary of the loaded ontology."""
        self._ensure_loaded()
        return {
            "owl_file":          str(self.owl_path),
            "total_triples":     len(self._graph),
            "classes":           len(self.get_classes()),
            "finding_classes":   len(self.get_finding_classes()),
            "skill_instances":   len(self.get_skill_classes()),
            "object_properties": len(self.get_object_properties()),
            "namespace":         AAI_NS,
        }

    def is_available(self) -> bool:
        """Returns True if rdflib is installed and the OWL file exists."""
        return self._available and self.owl_path.exists()


# Module-level singleton
@lru_cache(maxsize=1)
def get_loader() -> OntologyLoader:
    return OntologyLoader()
