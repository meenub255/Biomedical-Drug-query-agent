import logging
from src.config import (
    NEO4J_URI,
    NEO4J_USERNAME,
    NEO4J_PASSWORD,
    NEO4J_DATABASE,
    QDRANT_PATH,
    QDRANT_URL,
    QDRANT_API_KEY,
    CSV_DATA_PATH,
    MONOGRAPHS_DATA_PATH,
    EMBEDDING_MODEL_NAME
)
from src.graph_db import Neo4jGraphManager
from src.vector_db import VectorStoreManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ingest")


def run_ingestion():
    print("=" * 70)
    print("  BIOMEDICAL KNOWLEDGE GRAPH & VECTOR STORE INGESTION PIPELINE  ")
    print("=" * 70)

    # 1. Ingest into Neo4j
    print("\n[Step 1/2] Connecting to Knowledge Graph & Ingesting Nodes/Relationships...")
    graph_manager = Neo4jGraphManager(
        uri=NEO4J_URI,
        username=NEO4J_USERNAME,
        password=NEO4J_PASSWORD,
        database=NEO4J_DATABASE
    )
    graph_manager.init_schema()
    graph_manager.ingest_from_csv(str(CSV_DATA_PATH))
    summary_graph = graph_manager.get_summary()

    print("\n Knowledge Graph Ingestion Summary:")
    for k, v in summary_graph.items():
        print(f"  • {k}: {v}")

    # 2. Ingest into Qdrant Vector Store
    print("\n[Step 2/2] Indexing Scientific Drug Monographs into Qdrant Vector Store...")
    vector_manager = VectorStoreManager(
        path=QDRANT_PATH,
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
        model_name=EMBEDDING_MODEL_NAME
    )
    vector_manager.build_index(str(MONOGRAPHS_DATA_PATH), force_recreate=True)
    summary_vector = vector_manager.get_summary()

    print("\n Vector Store Ingestion Summary:")
    for k, v in summary_vector.items():
        print(f"  • {k}: {v}")

    print("\n" + "=" * 70)
    print("  INGESTION COMPLETE: Graph & Vector RAG Databases Ready!  ")
    print("=" * 70)

    graph_manager.close()


if __name__ == "__main__":
    run_ingestion()

