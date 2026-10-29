import csv
import logging
import re
from typing import Dict, List, Any, Optional
from neo4j import GraphDatabase, exceptions

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("graph_db")


class InMemoryKnowledgeGraph:
    """
    Lightweight, robust in-memory Knowledge Graph that simulates Neo4j Cypher lookups.
    Enables immediate offline/local execution when Neo4j AuraDB credentials are not yet configured.
    """
    def __init__(self):
        self.drugs = {}      # name -> {name, drug_class, ...}
        self.diseases = {}   # name -> {name, category, ...}
        self.symptoms = {}   # name -> {name, ...}
        
        # Relationships: (source, target) -> properties
        self.treats = set()             # (drug_name, disease_name)
        self.causes_side_effect = set() # (drug_name, symptom_name)
        self.has_symptom = set()        # (disease_name, symptom_name)
        self.is_loaded = False

    def ingest_from_csv(self, csv_path: str):
        with open(csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                drug = row["drug_name"].strip()
                drug_class = row["drug_class"].strip()
                disease = row["disease_name"].strip()
                category = row["disease_category"].strip()
                symptom = row["symptom_name"].strip()
                side_effect = row["side_effect_name"].strip()

                if drug:
                    self.drugs[drug] = {"name": drug, "drug_class": drug_class}
                if disease:
                    self.diseases[disease] = {"name": disease, "category": category}
                if symptom:
                    self.symptoms[symptom] = {"name": symptom}
                if side_effect:
                    self.symptoms[side_effect] = {"name": side_effect}

                if drug and disease:
                    self.treats.add((drug, disease))
                if drug and side_effect:
                    self.causes_side_effect.add((drug, side_effect))
                if disease and symptom:
                    self.has_symptom.add((disease, symptom))

        self.is_loaded = True
        logger.info(
            f"[InMemoryGraph] Ingested {len(self.drugs)} Drugs, {len(self.diseases)} Diseases, "
            f"{len(self.symptoms)} Symptoms. Relationships: {len(self.treats)} TREATS, "
            f"{len(self.causes_side_effect)} CAUSES_SIDE_EFFECT, {len(self.has_symptom)} HAS_SYMPTOM."
        )

    def execute_cypher(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Interprets common biomedical Cypher query patterns on the in-memory graph.
        """
        if not self.is_loaded:
            return []

        q = query.strip()
        params = params or {}
        results = []

        # Extract search terms from WHERE clause or query params
        # Pattern 1: Drug -[:TREATS]-> Disease
        if "-[:TREATS]->" in q or "[:TREATS]" in q:
            # Check if filtering by disease or drug
            disease_term = ""
            drug_term = ""
            # Check params or string matches
            if "disease" in params:
                disease_term = params["disease"].lower()
            elif "drug" in params:
                drug_term = params["drug"].lower()
            else:
                dis_match = re.search(r"toLower\([a-zA-Z]+\.name\)\s*(?:CONTAINS|=)\s*toLower\(?['\"]([^'\"]+)['\"]", q, re.I)
                if dis_match:
                    term = dis_match.group(1).lower()
                    # Distinguish if it refers to disease or drug
                    if "dis.name" in q or "disease" in q.lower():
                        disease_term = term
                    elif "d.name" in q or "drug" in q.lower():
                        drug_term = term

            for drug, disease in self.treats:
                d_info = self.drugs.get(drug, {})
                dis_info = self.diseases.get(disease, {})
                
                match_dis = not disease_term or (disease_term in disease.lower())
                match_drug = not drug_term or (drug_term in drug.lower())
                generic_term = params.get("term", "").lower()
                if generic_term:
                    match_dis = match_drug = (generic_term in disease.lower()) or (generic_term in drug.lower())

                if match_dis and match_drug:
                    # Also collect side effects if queried
                    side_effects = [se for d, se in self.causes_side_effect if d == drug]
                    results.append({
                        "drug": drug,
                        "drug_class": d_info.get("drug_class", "N/A"),
                        "disease": disease,
                        "disease_category": dis_info.get("category", "N/A"),
                        "side_effects": side_effects
                    })

        # Pattern 2: Drug -[:CAUSES_SIDE_EFFECT]-> Symptom
        elif "-[:CAUSES_SIDE_EFFECT]->" in q or "[:CAUSES_SIDE_EFFECT]" in q:
            drug_term = ""
            symptom_term = ""
            if "drug" in params:
                drug_term = params["drug"].lower()
            elif "symptom" in params or "side_effect" in params:
                symptom_term = (params.get("symptom") or params.get("side_effect")).lower()
            else:
                match = re.search(r"toLower\([a-zA-Z]+\.name\)\s*(?:CONTAINS|=)\s*toLower\(?['\"]([^'\"]+)['\"]", q, re.I)
                if match:
                    term = match.group(1).lower()
                    if "d.name" in q or "drug" in q.lower():
                        drug_term = term
                    else:
                        symptom_term = term

            for drug, se in self.causes_side_effect:
                d_info = self.drugs.get(drug, {})
                match_drug = not drug_term or (drug_term in drug.lower())
                match_se = not symptom_term or (symptom_term in se.lower())

                if match_drug and match_se:
                    results.append({
                        "drug": drug,
                        "drug_class": d_info.get("drug_class", "N/A"),
                        "side_effect": se,
                        "symptom": se
                    })

        # Pattern 3: Disease -[:HAS_SYMPTOM]-> Symptom
        elif "-[:HAS_SYMPTOM]->" in q or "[:HAS_SYMPTOM]" in q:
            disease_term = ""
            symptom_term = ""
            if "disease" in params:
                disease_term = params["disease"].lower()
            elif "symptom" in params:
                symptom_term = params["symptom"].lower()
            else:
                match = re.search(r"toLower\([a-zA-Z]+\.name\)\s*(?:CONTAINS|=)\s*toLower\(?['\"]([^'\"]+)['\"]", q, re.I)
                if match:
                    term = match.group(1).lower()
                    if "dis.name" in q or "disease" in q.lower():
                        disease_term = term
                    else:
                        symptom_term = term

            for disease, sym in self.has_symptom:
                dis_info = self.diseases.get(disease, {})
                match_dis = not disease_term or (disease_term in disease.lower())
                match_sym = not symptom_term or (symptom_term in sym.lower())

                if match_dis and match_sym:
                    results.append({
                        "disease": disease,
                        "disease_category": dis_info.get("category", "N/A"),
                        "symptom": sym
                    })

        # Generic summary fallback / count queries
        elif "COUNT" in q.upper():
            return [{
                "drug_count": len(self.drugs),
                "disease_count": len(self.diseases),
                "symptom_count": len(self.symptoms),
                "treats_count": len(self.treats),
                "side_effects_count": len(self.causes_side_effect)
            }]

        return results

    def get_summary(self) -> Dict[str, Any]:
        return {
            "mode": "In-Memory Knowledge Graph (Fallback)",
            "drugs_count": len(self.drugs),
            "diseases_count": len(self.diseases),
            "symptoms_count": len(self.symptoms),
            "treats_relationships": len(self.treats),
            "side_effect_relationships": len(self.causes_side_effect),
            "has_symptom_relationships": len(self.has_symptom)
        }


class Neo4jGraphManager:
    """
    Primary interface for the Neo4j Knowledge Graph.
    Connects to live AuraDB/local instance if configured, or falls back to InMemoryKnowledgeGraph.
    """
    def __init__(self, uri: str, username: str, password: str, database: str = "neo4j"):
        self.uri = uri
        self.username = username
        self.password = password
        self.database = database
        self.driver = None
        self.use_live_neo4j = False
        self.fallback_graph = InMemoryKnowledgeGraph()
        
        self._init_connection()

    def _init_connection(self):
        """Attempts to connect to live Neo4j. If unavailable, logs and activates fallback."""
        if self.password and self.uri:
            try:
                self.driver = GraphDatabase.driver(
                    self.uri,
                    auth=(self.username, self.password),
                    connection_timeout=5
                )
                # Verify connectivity
                with self.driver.session(database=self.database) as session:
                    res = session.run("RETURN 1 AS test")
                    val = res.single()["test"]
                    if val == 1:
                        self.use_live_neo4j = True
                        logger.info(f"[Neo4j] Connected successfully to Neo4j instance at {self.uri}")
                        return
            except Exception as e:
                logger.warning(f"[Neo4j] Live connection failed ({e}). Activating in-memory fallback mode.")
                self.driver = None
                self.use_live_neo4j = False
        else:
            logger.info("[Neo4j] No Neo4j credentials provided. Operating in in-memory Graph mode.")
            self.use_live_neo4j = False

    def init_schema(self):
        """Creates unique constraints on Drug, Disease, and Symptom nodes."""
        if self.use_live_neo4j and self.driver:
            with self.driver.session(database=self.database) as session:
                session.run("CREATE CONSTRAINT drug_name_unique IF NOT EXISTS FOR (d:Drug) REQUIRE d.name IS UNIQUE")
                session.run("CREATE CONSTRAINT disease_name_unique IF NOT EXISTS FOR (dis:Disease) REQUIRE dis.name IS UNIQUE")
                session.run("CREATE CONSTRAINT symptom_name_unique IF NOT EXISTS FOR (s:Symptom) REQUIRE s.name IS UNIQUE")
                logger.info("[Neo4j] Uniqueness constraints created on (:Drug), (:Disease), (:Symptom)")

    def ingest_from_csv(self, csv_path: str):
        """
        Loads the CSV dataset into Neo4j graph using Cypher MERGE commands:
        Nodes: (:Drug), (:Disease), (:Symptom)
        Relationships: [:TREATS], [:CAUSES_SIDE_EFFECT], [:HAS_SYMPTOM]
        """
        # Always populate the in-memory fallback store as well
        self.fallback_graph.ingest_from_csv(csv_path)

        if not self.use_live_neo4j or not self.driver:
            logger.info("[Neo4jManager] Populated in-memory graph fallback.")
            return

        cypher_tx = """
        MERGE (d:Drug {name: $drug})
        ON CREATE SET d.drug_class = $drug_class
        MERGE (dis:Disease {name: $disease})
        ON CREATE SET dis.category = $disease_category
        MERGE (sym:Symptom {name: $symptom})
        MERGE (se:Symptom {name: $side_effect})

        MERGE (d)-[:TREATS]->(dis)
        MERGE (d)-[:CAUSES_SIDE_EFFECT]->(se)
        MERGE (dis)-[:HAS_SYMPTOM]->(sym)
        """

        with open(csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            records = list(reader)

        logger.info(f"[Neo4j] Ingesting {len(records)} records into live Neo4j AuraDB...")
        with self.driver.session(database=self.database) as session:
            for r in records:
                session.run(
                    cypher_tx,
                    drug=r["drug_name"].strip(),
                    drug_class=r["drug_class"].strip(),
                    disease=r["disease_name"].strip(),
                    disease_category=r["disease_category"].strip(),
                    symptom=r["symptom_name"].strip(),
                    side_effect=r["side_effect_name"].strip()
                )
        logger.info("[Neo4j] Live Graph Ingestion Completed!")

    def execute_cypher(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Executes a Cypher query on live Neo4j or in-memory fallback."""
        params = params or {}
        if self.use_live_neo4j and self.driver:
            try:
                with self.driver.session(database=self.database) as session:
                    result = session.run(query, params)
                    return [record.data() for record in result]
            except Exception as e:
                logger.error(f"[Neo4j] Error executing Cypher: {e}. Falling back to in-memory graph.")
                return self.fallback_graph.execute_cypher(query, params)
        else:
            return self.fallback_graph.execute_cypher(query, params)

    def get_summary(self) -> Dict[str, Any]:
        """Returns statistics of the Knowledge Graph."""
        if self.use_live_neo4j and self.driver:
            try:
                with self.driver.session(database=self.database) as session:
                    d_count = session.run("MATCH (d:Drug) RETURN count(d) AS count").single()["count"]
                    dis_count = session.run("MATCH (dis:Disease) RETURN count(dis) AS count").single()["count"]
                    s_count = session.run("MATCH (s:Symptom) RETURN count(s) AS count").single()["count"]
                    t_count = session.run("MATCH ()-[r:TREATS]->() RETURN count(r) AS count").single()["count"]
                    se_count = session.run("MATCH ()-[r:CAUSES_SIDE_EFFECT]->() RETURN count(r) AS count").single()["count"]
                    hs_count = session.run("MATCH ()-[r:HAS_SYMPTOM]->() RETURN count(r) AS count").single()["count"]

                    return {
                        "mode": "Live Neo4j AuraDB / Server",
                        "uri": self.uri,
                        "drugs_count": d_count,
                        "diseases_count": dis_count,
                        "symptoms_count": s_count,
                        "treats_relationships": t_count,
                        "side_effect_relationships": se_count,
                        "has_symptom_relationships": hs_count
                    }
            except Exception as e:
                logger.warning(f"[Neo4j] Failed to fetch live summary: {e}")

        return self.fallback_graph.get_summary()

    def close(self):
        if self.driver:
            self.driver.close()

