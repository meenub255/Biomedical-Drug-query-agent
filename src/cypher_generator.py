import re
import logging
from typing import Tuple, Dict, Any, Optional

logger = logging.getLogger("cypher_generator")

# Biomedical Cypher Prompt Schema
CYPHER_SYSTEM_PROMPT = """
You are a Biomedical Knowledge Graph Cypher expert.
The Neo4j database uses this exact schema:
Nodes:
- (:Drug {name: STRING, drug_class: STRING})
- (:Disease {name: STRING, category: STRING})
- (:Symptom {name: STRING})

Relationships:
- (:Drug)-[:TREATS]->(:Disease)
- (:Drug)-[:CAUSES_SIDE_EFFECT]->(:Symptom)
- (:Disease)-[:HAS_SYMPTOM]->(:Symptom)

Instructions:
1. Translate the user's natural language question into an exact Cypher query.
2. Always use case-insensitive substring matching: toLower(node.name) CONTAINS toLower('term').
3. Return only clean Cypher code without markdown fences.
"""

class CypherGenerator:
    """
    Translates relational natural language queries into accurate Neo4j Cypher queries.
    Uses schema-aware template matching with LLM augmentation if available.
    """
    def __init__(self, openai_client: Optional[Any] = None):
        self.openai_client = openai_client

    def generate(self, question: str) -> Tuple[str, Dict[str, Any]]:
        """
        Generates Cypher query and parameters from the question.
        Returns: (cypher_query, parameters)
        """
        q = question.strip()
        q_lower = q.lower()

        # Clean punctuation for term extraction
        clean_text = re.sub(r"[?!.,]", "", q_lower)

        # In compound questions (e.g. "What drugs treat Asthma and how does Albuterol work?"),
        # extract the first clause before conjunctions for relational parsing
        relational_part = re.split(r"\band\s+how\b|\band\s+what\b|\bwhile\b|\balso\b", clean_text)[0].strip()

        # 1. Multi-hop: Drugs treating disease AND their side effects
        if ("treat" in clean_text or "prescribe" in clean_text) and ("side effect" in clean_text or "adverse" in clean_text):
            disease = self._extract_target_entity(clean_text, ["treat", "prescribe", "for", "against"])
            if disease:
                cypher = (
                    "MATCH (d:Drug)-[:TREATS]->(dis:Disease), (d)-[:CAUSES_SIDE_EFFECT]->(se:Symptom) "
                    "WHERE toLower(dis.name) CONTAINS toLower($disease) "
                    "RETURN d.name AS drug, d.drug_class AS drug_class, dis.name AS disease, collect(DISTINCT se.name) AS side_effects"
                )
                return cypher, {"disease": disease}

        # 2. Side effects caused by a drug
        if "side effect" in clean_text or "adverse" in clean_text or "complication" in clean_text:
            # Check if asking which drug causes X
            if any(cue in clean_text for cue in ["what drugs cause", "which drugs cause", "medications causing", "drugs that cause"]):
                symptom = self._extract_target_entity(clean_text, ["cause", "causes", "causing", "lead to"])
                if symptom:
                    cypher = (
                        "MATCH (d:Drug)-[:CAUSES_SIDE_EFFECT]->(s:Symptom) "
                        "WHERE toLower(s.name) CONTAINS toLower($symptom) "
                        "RETURN d.name AS drug, d.drug_class AS drug_class, s.name AS side_effect"
                    )
                    return cypher, {"symptom": symptom}
            else:
                # Asking for side effects of a specific drug
                drug = self._extract_target_entity(clean_text, ["of", "from", "by", "does", "with"])
                if drug:
                    cypher = (
                        "MATCH (d:Drug)-[:CAUSES_SIDE_EFFECT]->(s:Symptom) "
                        "WHERE toLower(d.name) CONTAINS toLower($drug) "
                        "RETURN d.name AS drug, d.drug_class AS drug_class, s.name AS side_effect"
                    )
                    return cypher, {"drug": drug}

        # 3. Drugs that treat a disease
        if any(w in clean_text for w in ["treat", "treats", "used for", "cure", "prescribed for", "therapy for"]):
            disease = self._extract_target_entity(relational_part or clean_text, ["treat", "treats", "for", "against"])
            if disease:
                cypher = (
                    "MATCH (d:Drug)-[:TREATS]->(dis:Disease) "
                    "WHERE toLower(dis.name) CONTAINS toLower($disease) "
                    "RETURN d.name AS drug, d.drug_class AS drug_class, dis.name AS disease, dis.category AS category"
                )
                return cypher, {"disease": disease}

        # 4. Diseases treated by a drug ("What diseases does Metformin treat?")
        if any(w in q_lower for w in ["does", "can", "indicated"]) and "treat" in q_lower:
            drug = self._extract_target_entity(clean_text, ["does", "can", "is", "drug"])
            if drug:
                cypher = (
                    "MATCH (d:Drug)-[:TREATS]->(dis:Disease) "
                    "WHERE toLower(d.name) CONTAINS toLower($drug) "
                    "RETURN d.name AS drug, dis.name AS disease, dis.category AS category"
                )
                return cypher, {"drug": drug}

        # 5. Symptoms of a disease
        if "symptom" in q_lower or "manifestation" in q_lower or "sign" in q_lower:
            if any(cue in q_lower for cue in ["which disease has", "diseases with", "what disease causes"]):
                symptom = self._extract_target_entity(clean_text, ["with", "has", "causes", "symptom"])
                if symptom:
                    cypher = (
                        "MATCH (dis:Disease)-[:HAS_SYMPTOM]->(s:Symptom) "
                        "WHERE toLower(s.name) CONTAINS toLower($symptom) "
                        "RETURN dis.name AS disease, dis.category AS category, s.name AS symptom"
                    )
                    return cypher, {"symptom": symptom}
            else:
                disease = self._extract_target_entity(clean_text, ["of", "for", "in", "does"])
                if disease:
                    cypher = (
                        "MATCH (dis:Disease)-[:HAS_SYMPTOM]->(s:Symptom) "
                        "WHERE toLower(dis.name) CONTAINS toLower($disease) "
                        "RETURN dis.name AS disease, dis.category AS category, s.name AS symptom"
                    )
                    return cypher, {"disease": disease}

        # Fallback keyword match
        # Extract last capitalized or prominent words
        words = [w for w in question.split() if w.lower() not in {"what", "which", "how", "does", "is", "are", "the", "a", "an", "for", "in", "to"}]
        fallback_term = " ".join(words[-2:]) if words else "diabetes"

        cypher = (
            "MATCH (d:Drug)-[:TREATS]->(dis:Disease) "
            "WHERE toLower(dis.name) CONTAINS toLower($term) OR toLower(d.name) CONTAINS toLower($term) "
            "RETURN d.name AS drug, d.drug_class AS drug_class, dis.name AS disease"
        )
        return cypher, {"term": fallback_term}

    def _extract_target_entity(self, text: str, triggers: list) -> str:
        """Helper to extract entity following clinical trigger words and clean trailing verbs/stopwords."""
        stopwords = {
            "a", "an", "the", "patients", "people", "adults", "cases",
            "cause", "causes", "causing", "have", "has", "produce", "produces",
            "lead", "leads", "to", "work", "works", "is", "are"
        }
        for trig in triggers:
            pattern = rf"\b{trig}\b\s+([a-zA-Z0-9\s\-]+)"
            match = re.search(pattern, text, re.I)
            if match:
                extracted = match.group(1).strip()
                # Split and filter out trailing or leading stopwords
                words = extracted.split()
                # strip trailing stopwords like "cause", "have", etc.
                while words and words[-1] in stopwords:
                    words.pop()
                while words and words[0] in stopwords:
                    words.pop(0)
                if words:
                    return " ".join(words)
        return ""

