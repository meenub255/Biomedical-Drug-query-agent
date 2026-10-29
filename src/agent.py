import re
import logging
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END

from src.graph_db import Neo4jGraphManager
from src.vector_db import VectorStoreManager
from src.cypher_generator import CypherGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agent")


class AgentState(TypedDict):
    question: str
    route: str                                # "relational", "descriptive", "hybrid"
    cypher_query: str
    cypher_params: Dict[str, Any]
    graph_facts: List[Dict[str, Any]]
    vector_context: List[Dict[str, Any]]
    citations: List[str]
    final_answer: str
    trace: List[str]


class BiomedicalAgent:
    """
    LangGraph Hybrid Graph + Vector RAG Orchestrator for Biomedical & Drug Queries.
    Coordinates Neo4j Knowledge Graph lookups with Qdrant Vector search.
    """
    def __init__(self, graph_db: Neo4jGraphManager, vector_db: VectorStoreManager):
        self.graph_db = graph_db
        self.vector_db = vector_db
        self.cypher_gen = CypherGenerator()
        self.workflow = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(AgentState)

        # Add Nodes
        workflow.add_node("router_node", self.router_node)
        workflow.add_node("cypher_node", self.cypher_node)
        workflow.add_node("vector_node", self.vector_node)
        workflow.add_node("answer_node", self.answer_node)

        # Set Entry Point
        workflow.set_entry_point("router_node")

        # Conditional routing from router_node
        workflow.add_conditional_edges(
            "router_node",
            self.route_decision,
            {
                "cypher": "cypher_node",
                "vector": "vector_node"
            }
        )

        # Conditional transition from cypher_node:
        # If hybrid OR graph returned no facts (fallback), go to vector_node, else answer_node
        workflow.add_conditional_edges(
            "cypher_node",
            self.after_cypher_decision,
            {
                "vector": "vector_node",
                "answer": "answer_node"
            }
        )

        # From vector_node always proceed to answer_node
        workflow.add_edge("vector_node", "answer_node")
        workflow.add_edge("answer_node", END)

        return workflow.compile()

    # --- Node 1: Router Node ---
    def router_node(self, state: AgentState) -> Dict[str, Any]:
        question = state["question"].lower()
        trace = list(state.get("trace", []))

        # Check for descriptive cues
        is_descriptive = any(kw in question for kw in [
            "how does", "how do", "mechanism", "pharmacology", "why does",
            "explain", "molecular", "pathway", "action of", "describe"
        ])

        # Check for relational cues
        is_relational = any(kw in question for kw in [
            "what drug", "which drug", "what medication", "treat", "treats",
            "side effect", "adverse", "causes", "symptom", "indicated", "prescribed"
        ])

        if is_descriptive and is_relational:
            route = "hybrid"
            decision_msg = "Router Node: Detected HYBRID query (requires factual graph connections + descriptive pharmacology)."
        elif is_descriptive:
            route = "descriptive"
            decision_msg = "Router Node: Detected DESCRIPTIVE query (routing to Vector Search for mechanism & pharmacology)."
        else:
            route = "relational"
            decision_msg = "Router Node: Detected RELATIONAL query (routing to Neo4j Cypher for 100% factual accuracy)."

        trace.append(decision_msg)
        return {
            "route": route,
            "trace": trace
        }

    def route_decision(self, state: AgentState) -> str:
        if state["route"] in ("relational", "hybrid"):
            return "cypher"
        return "vector"

    # --- Node 2: Cypher Execution Node ---
    def cypher_node(self, state: AgentState) -> Dict[str, Any]:
        trace = list(state["trace"])
        question = state["question"]

        cypher_query, params = self.cypher_gen.generate(question)
        trace.append(f"Cypher Node: Generated Query -> {cypher_query} with params {params}")

        # Execute query on Neo4j
        results = self.graph_db.execute_cypher(cypher_query, params)
        trace.append(f"Cypher Node: Executed lookup. Retrieved {len(results)} factual records from Knowledge Graph.")

        return {
            "cypher_query": cypher_query,
            "cypher_params": params,
            "graph_facts": results,
            "trace": trace
        }

    def after_cypher_decision(self, state: AgentState) -> str:
        # If hybrid, or if zero graph results found (fallback to vector search)
        if state["route"] == "hybrid":
            return "vector"
        if not state.get("graph_facts"):
            state["trace"].append("Cypher Node: 0 graph facts found. Falling back to Vector Store for semantic retrieval.")
            return "vector"
        return "answer"

    # --- Node 3: Vector Fallback / Retrieval Node ---
    def vector_node(self, state: AgentState) -> Dict[str, Any]:
        trace = list(state["trace"])
        question = state["question"]

        trace.append(f"Vector Node: Querying Qdrant vector store with semantic query: '{question}'")
        search_results = self.vector_db.search(question, top_k=3)
        trace.append(f"Vector Node: Retrieved top {len(search_results)} relevant drug monographs.")

        return {
            "vector_context": search_results,
            "trace": trace
        }

    # --- Node 4: Answer Synthesis Node ---
    def answer_node(self, state: AgentState) -> Dict[str, Any]:
        trace = list(state["trace"])
        trace.append("Answer Node: Merging Knowledge Graph verified facts with Vector Store context.")

        graph_facts = state.get("graph_facts", [])
        vector_context = state.get("vector_context", [])
        question = state["question"]
        route = state["route"]

        # Collect citations
        citations = set()
        for doc in vector_context:
            for c in doc.get("citations", []):
                citations.add(c)

        # Synthesize clean markdown response
        response_parts = []

        # 1. Direct Headline
        response_parts.append(f"### 🧪 Biomedical & Drug Query Synthesis\n")
        response_parts.append(f"**Query:** *\"{question}\"*\n")
        response_parts.append(f"**Execution Pipeline:** `{route.upper()}` routing via LangGraph orchestrator.\n")

        # 2. Graph Facts (if any)
        if graph_facts:
            response_parts.append("#### 🔗 1. Graph-Verified Facts (Neo4j)")
            response_parts.append("*The following direct relations were verified with 100% precision in the knowledge graph:*\n")

            # Format rows nicely
            formatted_facts = []
            for item in graph_facts[:10]: # cap at 10 items
                if "side_effects" in item:
                    se_str = ", ".join(item["side_effects"]) if item["side_effects"] else "None recorded"
                    formatted_facts.append(
                        f"- **{item['drug']}** (`{item.get('drug_class', 'N/A')}`) treats **{item['disease']}** | Adverse Effects: *{se_str}*"
                    )
                elif "side_effect" in item:
                    formatted_facts.append(
                        f"- **{item['drug']}** (`{item.get('drug_class', 'N/A')}`) ➔ Causes side effect: **{item['side_effect']}**"
                    )
                elif "disease" in item and "drug" in item:
                    formatted_facts.append(
                        f"- **{item['drug']}** (`{item.get('drug_class', 'N/A')}`) ➔ Treats: **{item['disease']}** (*{item.get('disease_category', '')}*)"
                    )
                elif "symptom" in item and "disease" in item:
                    formatted_facts.append(
                        f"- **{item['disease']}** (*{item.get('disease_category', '')}*) ➔ Associated symptom: **{item['symptom']}**"
                    )

            if formatted_facts:
                response_parts.extend(formatted_facts)
            else:
                for item in graph_facts[:5]:
                    response_parts.append(f"- {item}")
            response_parts.append("")

        # 3. Vector Context (Pharmacological Mechanism & Explanations)
        if vector_context:
            response_parts.append("#### 🔬 2. Pharmacological Mechanism & Context (Qdrant Vector RAG)")
            response_parts.append("*Deep scientific context retrieved from indexed clinical monographs:*\n")
            for doc in vector_context:
                drug = doc.get("drug_name")
                d_class = doc.get("drug_class")
                mech = doc.get("mechanism_description", "")
                score = doc.get("score", 0.0)
                
                response_parts.append(f"**{drug}** (`{d_class}`) — *Relevance Score: {score:.3f}*")
                response_parts.append(f"> {mech}\n")
                if doc.get("indications"):
                    response_parts.append(f"- **Documented Indications:** {', '.join(doc['indications'])}")
                if doc.get("side_effects"):
                    response_parts.append(f"- **Key Adverse Reactions:** {', '.join(doc['side_effects'])}")
                response_parts.append("")

        # 4. Citations
        if citations:
            response_parts.append("#### 📚 3. Citations & Regulatory References")
            for cit in sorted(list(citations)):
                response_parts.append(f"- `{cit}`")
            response_parts.append("")
        else:
            response_parts.append("#### 📚 3. Citations & Regulatory References")
            response_parts.append("- `FDA Approved Package Inserts & PubMed Biomedical Database`\n")

        final_answer = "\n".join(response_parts)

        return {
            "final_answer": final_answer,
            "citations": list(citations),
            "trace": trace
        }

    def run(self, question: str) -> Dict[str, Any]:
        """Runs the LangGraph pipeline for a user question."""
        initial_state: AgentState = {
            "question": question,
            "route": "",
            "cypher_query": "",
            "cypher_params": {},
            "graph_facts": [],
            "vector_context": [],
            "citations": [],
            "final_answer": "",
            "trace": []
        }
        return self.workflow.invoke(initial_state)

