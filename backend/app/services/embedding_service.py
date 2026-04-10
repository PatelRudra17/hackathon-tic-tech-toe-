import numpy as np
from typing import List, Dict, Optional, Tuple
from loguru import logger
from app.config import get_settings

settings = get_settings()


class EmbeddingService:
    """Manages skill embeddings using sentence-transformers and ChromaDB."""

    def __init__(self):
        self.model = None
        self.chroma_client = None
        self.skill_collection = None
        self._initialized = False

    def _ensure_initialized(self):
        if self._initialized:
            return

        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
            logger.info(f"Loaded embedding model: {settings.EMBEDDING_MODEL}")
        except Exception as e:
            logger.warning(f"Could not load sentence-transformers model: {e}. Using fallback.")
            self.model = None

        try:
            import chromadb
            self.chroma_client = chromadb.Client()
            self.skill_collection = self.chroma_client.get_or_create_collection(
                name="skills",
                metadata={"hnsw:space": "cosine"},
            )
            logger.info("ChromaDB initialized")
        except Exception as e:
            logger.warning(f"Could not initialize ChromaDB: {e}")
            self.chroma_client = None

        self._initialized = True

    def encode(self, texts: List[str]) -> Optional[np.ndarray]:
        """Encode texts into embeddings."""
        self._ensure_initialized()
        if self.model is None:
            return self._fallback_encode(texts)
        try:
            return self.model.encode(texts, normalize_embeddings=True)
        except Exception as e:
            logger.error(f"Encoding failed: {e}")
            return self._fallback_encode(texts)

    def _fallback_encode(self, texts: List[str]) -> np.ndarray:
        """Simple TF-IDF-like fallback when sentence-transformers isn't available."""
        # Build vocabulary from all texts
        all_words = set()
        for text in texts:
            all_words.update(text.lower().split())
        vocab = sorted(all_words)
        word_to_idx = {w: i for i, w in enumerate(vocab)}

        # Create vectors
        vectors = []
        for text in texts:
            vec = np.zeros(len(vocab))
            words = text.lower().split()
            for word in words:
                if word in word_to_idx:
                    vec[word_to_idx[word]] = 1.0
            # Normalize
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            vectors.append(vec)

        return np.array(vectors)

    def compute_similarity(self, text1: str, text2: str) -> float:
        """Compute cosine similarity between two texts."""
        embeddings = self.encode([text1, text2])
        if embeddings is None or len(embeddings) < 2:
            return 0.0

        # Cosine similarity
        sim = np.dot(embeddings[0], embeddings[1])
        return float(max(0.0, min(1.0, sim)))

    def compute_skill_similarity(self, candidate_skills: List[str], job_skills: List[str]) -> List[Dict]:
        """Compute semantic similarity between candidate skills and job requirements."""
        if not candidate_skills or not job_skills:
            return []

        all_texts = candidate_skills + job_skills
        embeddings = self.encode(all_texts)
        if embeddings is None:
            return []

        candidate_embeddings = embeddings[:len(candidate_skills)]
        job_embeddings = embeddings[len(candidate_skills):]

        matches = []
        for j, job_skill in enumerate(job_skills):
            best_match = None
            best_score = 0.0

            for c, cand_skill in enumerate(candidate_skills):
                sim = float(np.dot(candidate_embeddings[c], job_embeddings[j]))
                if sim > best_score:
                    best_score = sim
                    best_match = cand_skill

            match_type = "no_match"
            if best_score >= 0.95:
                match_type = "direct"
            elif best_score >= 0.7:
                match_type = "semantic"
            elif best_score >= 0.5:
                match_type = "inferred"

            matches.append({
                "job_skill": job_skill,
                "matched_candidate_skill": best_match,
                "similarity_score": round(best_score, 3),
                "match_type": match_type,
            })

        return matches

    def index_skills(self, skills: List[Dict]):
        """Index skills into ChromaDB for fast retrieval."""
        self._ensure_initialized()
        if self.skill_collection is None:
            return

        try:
            documents = [s["name"] for s in skills]
            ids = [f"skill_{i}" for i in range(len(skills))]
            metadatas = [{"category": s.get("category", ""), "type": s.get("skill_type", "")} for s in skills]

            self.skill_collection.add(
                documents=documents,
                ids=ids,
                metadatas=metadatas,
            )
        except Exception as e:
            logger.error(f"Failed to index skills: {e}")

    def search_similar_skills(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search for similar skills using vector similarity."""
        self._ensure_initialized()
        if self.skill_collection is None:
            return []

        try:
            results = self.skill_collection.query(
                query_texts=[query],
                n_results=n_results,
            )
            matches = []
            if results and results["documents"]:
                for i, doc in enumerate(results["documents"][0]):
                    matches.append({
                        "skill": doc,
                        "distance": results["distances"][0][i] if results.get("distances") else 0,
                        "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                    })
            return matches
        except Exception as e:
            logger.error(f"Skill search failed: {e}")
            return []


# Singleton
_embedding_service = None


def get_embedding_service() -> EmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
