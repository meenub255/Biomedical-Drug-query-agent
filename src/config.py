import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# Neo4j Configuration (Free AuraDB or Local Neo4j)
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

# Qdrant Configuration
QDRANT_PATH = os.getenv("QDRANT_PATH", str(DATA_DIR / "qdrant_db"))
QDRANT_URL = os.getenv("QDRANT_URL", None)
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", None)
QDRANT_COLLECTION = "biomedical_monographs"

# LLM & Embedding Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", None)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", None)
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")

# Data File Paths
CSV_DATA_PATH = DATA_DIR / "biomedical_dataset.csv"
MONOGRAPHS_DATA_PATH = DATA_DIR / "drug_monographs.json"

