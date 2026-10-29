import sys
import logging

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.config import (
    NEO4J_URI,
    NEO4J_USERNAME,
    NEO4J_PASSWORD,
    NEO4J_DATABASE,
    QDRANT_PATH,
    CSV_DATA_PATH,
    MONOGRAPHS_DATA_PATH,
    EMBEDDING_MODEL_NAME
)
from src.graph_db import Neo4jGraphManager
from src.vector_db import VectorStoreManager
from src.agent import BiomedicalAgent

logging.basicConfig(level=logging.INFO, format="%(message)s")


def test_agent_pipeline():
    print("=" * 80)
    print("  RUNNING BIOMEDICAL AGENT TEST SUITE (LANGGRAPH HYBRID RAG)  ")
    print("=" * 80)

    # Initialize components
    graph_manager = Neo4jGraphManager(
        uri=NEO4J_URI,
        username=NEO4J_USERNAME,
        password=NEO4J_PASSWORD,
        database=NEO4J_DATABASE
    )
    graph_manager.ingest_from_csv(str(CSV_DATA_PATH))

    vector_manager = VectorStoreManager(
        path=QDRANT_PATH,
        model_name=EMBEDDING_MODEL_NAME
    )
    # Ensure index exists
    vector_manager.build_index(str(MONOGRAPHS_DATA_PATH), force_recreate=False)

    agent = BiomedicalAgent(graph_db=graph_manager, vector_db=vector_manager)

    test_queries = [
        {
            "category": "Relational Query (Direct Graph Lookup)",
            "query": "What drugs treat Type 2 Diabetes?",
            "expected_route": "relational"
        },
        {
            "category": "Relational Query (Adverse Reactions)",
            "query": "What side effects does Metformin cause?",
            "expected_route": "relational"
        },
        {
            "category": "Descriptive Query (Pharmacology / Mechanism)",
            "query": "How does Metformin work?",
            "expected_route": "descriptive"
        },
        {
            "category": "Hybrid Query (Relational + Mechanistic)",
            "query": "What drugs treat Asthma and how does Albuterol work?",
            "expected_route": "hybrid"
        },
        {
            "category": "Vector Fallback Query (Unstructured Clinical Concept)",
            "query": "What treatments help with chronic kidney failure hyperfiltration?",
            "expected_route": "relational" # will route, check graph, and fallback to vector
        }
    ]

    for idx, test_case in enumerate(test_queries, 1):
        print(f"\n[{idx}/{len(test_queries)}] Testing: {test_case['category']}")
        print(f"Query: \"{test_case['query']}\"")
        
        result = agent.run(test_case["query"])
        
        print("\n--- Execution Trace ---")
        for step in result["trace"]:
            print(f"  • {step}")

        print("\n--- Final Answer Preview ---")
        preview = result["final_answer"]
        print(preview[:400] + ("..." if len(preview) > 400 else ""))

        # Validations
        assert result["route"] in ["relational", "descriptive", "hybrid"], "Invalid route"
        assert len(result["final_answer"]) > 50, "Answer too short"
        print(f"✓ Test {idx} Passed!")

    print("\n" + "=" * 80)
    print("  ALL 5 TEST SUITE CASES COMPLETED SUCCESSFULLY!  ")
    print("=" * 80)

    graph_manager.close()


if __name__ == "__main__":
    test_agent_pipeline()
