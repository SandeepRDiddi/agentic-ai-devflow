"""Ontology module — loads and queries the agentic-ai OWL ontology using rdflib."""
from .loader import OntologyLoader
from .mapper import SkillMapper
from .validator import OntologyValidator

__all__ = ["OntologyLoader", "SkillMapper", "OntologyValidator"]
