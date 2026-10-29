import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.http import models
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vector_db")


class VectorStoreManager:
    """
    Manages vector embeddings and Qdrant storage for biomedical drug monographs.
    Provides semantic search over mechanisms of action, pharmacology, and trial findings.
    """
    def __init__(
        self,
        collection_name: str = "biomedical_monographs",
        path: Optional[str] = None,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        model_name: str = "all-MiniLM-L6-v2"
    ):
        self.collection_name = collection_name
        self.model_name = model_name
        self.embedding_dim = 384
        
        # Initialize embedding model
        logger.info(f"[VectorDB] Loading embedding model '{model_name}'...")
        self.model = SentenceTransformer(model_name)
        
        # Initialize Qdrant Client (Cloud URL > Local Path > In-Memory)
        if url:
            logger.info(f"[VectorDB] Connecting to Qdrant Cloud at {url}")
            self.client = QdrantClient(url=url, api_key=api_key)
        elif path:
            Path(path).mkdir(parents=True, exist_ok=True)
            logger.info(f"[VectorDB] Initializing local Qdrant at {path}")
            try:
                self.client = QdrantClient(path=path)
            except Exception as e:
                logger.warning(f"[VectorDB] Failed to bind local path ({e}), using in-memory Qdrant client.")
                self.client = QdrantClient(":memory:")
        else:
            logger.info("[VectorDB] Initializing in-memory Qdrant client")
            self.client = QdrantClient(":memory:")

    def build_index(self, monographs_json_path: str, force_recreate: bool = False):
        """
        Encodes drug monographs and inserts them as points into Qdrant.
        """
        with open(monographs_json_path, mode="r", encoding="utf-8") as f:
            monographs: List[Dict[str, Any]] = json.load(f)

        # Check existing collections
        collections = [c.name for c in self.client.get_collections().collections]
        if self.collection_name in collections:
            if force_recreate:
                logger.info(f"[VectorDB] Recreating collection '{self.collection_name}'...")
                self.client.delete_collection(self.collection_name)
            else:
                count = self.client.count(self.collection_name).count
                if count >= len(monographs):
                    logger.info(f"[VectorDB] Collection '{self.collection_name}' already indexed with {count} documents.")
                    return

        # Create Collection
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(
                size=self.embedding_dim,
                distance=models.Distance.COSINE
            )
        )

        logger.info(f"[VectorDB] Encoding {len(monographs)} drug monographs...")
        texts_to_embed = []
        for m in monographs:
            text = (
                f"Drug: {m['drug_name']} ({m['drug_class']})\n"
                f"Indications: {', '.join(m['indications'])}\n"
                f"Symptoms: {', '.join(m['common_symptoms_treated'])}\n"
                f"Side Effects: {', '.join(m['key_side_effects'])}\n"
                f"Mechanism: {m['mechanism_description']}\n"
                f"Pharmacology: {m['pharmacology_summary']}"
            )
            texts_to_embed.append(text)

        embeddings = self.model.encode(texts_to_embed, show_progress_bar=False).tolist()

        points = []
        for idx, (m, emb, raw_text) in enumerate(zip(monographs, embeddings, texts_to_embed)):
            points.append(
                models.PointStruct(
                    id=idx + 1,
                    vector=emb,
                    payload={
                        "drug_name": m["drug_name"],
                        "drug_class": m["drug_class"],
                        "indications": m["indications"],
                        "common_symptoms_treated": m["common_symptoms_treated"],
                        "key_side_effects": m["key_side_effects"],
                        "mechanism_description": m["mechanism_description"],
                        "pharmacology_summary": m["pharmacology_summary"],
                        "citations": m.get("citations", []),
                        "content": raw_text
                    }
                )
            )

        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        logger.info(f"[VectorDB] Successfully indexed {len(points)} points into Qdrant '{self.collection_name}'.")

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Embeds the query and performs cosine vector similarity search in Qdrant.
        Supports both modern query_points and legacy search methods.
        """
        query_vec = self.model.encode(query).tolist()
        if hasattr(self.client, "query_points"):
            response = self.client.query_points(
                collection_name=self.collection_name,
                query=query_vec,
                limit=top_k
            )
            search_results = response.points
        else:
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vec,
                limit=top_k
            )

        results = []
        for hit in search_results:
            results.append({
                "score": float(hit.score),
                "drug_name": hit.payload.get("drug_name"),
                "drug_class": hit.payload.get("drug_class"),
                "indications": hit.payload.get("indications", []),
                "side_effects": hit.payload.get("key_side_effects", []),
                "mechanism_description": hit.payload.get("mechanism_description"),
                "pharmacology_summary": hit.payload.get("pharmacology_summary"),
                "citations": hit.payload.get("citations", [])
            })
        return results

    def get_summary(self) -> Dict[str, Any]:
        """Returns vector collection statistics."""
        try:
            count = self.client.count(self.collection_name).count
            return {
                "collection_name": self.collection_name,
                "vector_dimension": self.embedding_dim,
                "distance_metric": "Cosine",
                "indexed_monographs_count": count,
                "embedding_model": self.model_name
            }
        except Exception as e:
            return {"error": str(e)}

