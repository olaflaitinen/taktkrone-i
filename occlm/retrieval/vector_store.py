"""Vector store for dense retrieval with FAISS and Chroma support."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


class VectorStore:
    """Vector database supporting FAISS and Chroma backends."""

    def __init__(self, dimension: int, backend: str = "faiss", persist_dir: Optional[str] = None):
        """Initialize vector store.

        Args:
            dimension: Embedding dimension
            backend: "faiss" or "chroma"
            persist_dir: Directory to persist data
        """
        self.dimension = dimension
        self.backend = backend
        self.persist_dir = Path(persist_dir) if persist_dir else None
        self.index = None
        self.metadata = []
        self._init_backend()

    def _init_backend(self):
        """Initialize vector store backend."""
        if self.backend == "faiss":
            try:
                import faiss
                self.index = faiss.IndexFlatL2(self.dimension)
            except ImportError:
                logger.error("faiss not installed. Install with: pip install faiss-cpu")
                raise
        elif self.backend == "chroma":
            try:
                import chromadb
                self.chroma_client = chromadb.Client()
                self.collection = self.chroma_client.create_collection(name="vectors")
            except ImportError:
                logger.error("chromadb not installed. Install with: pip install chromadb")
                raise
        else:
            raise ValueError(f"Unknown backend: {self.backend}")

    def add(self, embeddings: np.ndarray, metadata: List[Dict[str, Any]], ids: Optional[List[str]] = None):
        """Add embeddings and metadata to store.

        Args:
            embeddings: Numpy array of shape (n, dimension)
            metadata: List of metadata dicts
            ids: Optional list of document IDs
        """
        if embeddings.shape[1] != self.dimension:
            raise ValueError(f"Embedding dimension mismatch: {embeddings.shape[1]} vs {self.dimension}")

        if len(embeddings) != len(metadata):
            raise ValueError("Number of embeddings and metadata must match")

        if self.backend == "faiss":
            self.index.add(embeddings.astype(np.float32))
            self.metadata.extend(metadata)

        elif self.backend == "chroma":
            if ids is None:
                ids = [str(len(self.metadata) + i) for i in range(len(embeddings))]

            self.collection.add(
                ids=ids,
                embeddings=embeddings.tolist(),
                documents=[m.get("text", "") for m in metadata],
                metadatas=metadata,
            )

        logger.info(f"Added {len(embeddings)} vectors to {self.backend} store")

    def search(self, query_embedding: np.ndarray, k: int = 5) -> List[Tuple[int, float, Dict]]:
        """Search for top-k nearest neighbors.

        Args:
            query_embedding: Query embedding of shape (dimension,)
            k: Number of results to return

        Returns:
            List of (idx, distance, metadata) tuples
        """
        if len(query_embedding.shape) == 1:
            query_embedding = query_embedding.reshape(1, -1)

        if self.backend == "faiss":
            if self.index.ntotal == 0:
                return []

            distances, indices = self.index.search(query_embedding.astype(np.float32), min(k, self.index.ntotal))
            results = [
                (int(idx), float(dist), self.metadata[idx] if idx < len(self.metadata) else {})
                for idx, dist in zip(indices[0], distances[0])
            ]
            return results

        elif self.backend == "chroma":
            results = self.collection.query(query_embeddings=query_embedding.tolist(), n_results=k)
            if not results or not results.get("ids") or not results["ids"][0]:
                return []

            output = []
            for i, doc_id in enumerate(results["ids"][0]):
                dist = results["distances"][0][i] if results.get("distances") else 0.0
                metadata = results["metadatas"][0][i] if results.get("metadatas") else {}
                output.append((int(doc_id) if doc_id.isdigit() else doc_id, float(dist), metadata))
            return output

    def delete(self, ids: List[int]):
        """Delete vectors by ID."""
        if self.backend == "faiss":
            # FAISS doesn't support deletion; reconstruct index
            logger.warning("FAISS doesn't support deletion; rebuild recommended")
        elif self.backend == "chroma":
            self.collection.delete(ids=[str(i) for i in ids])

    def size(self) -> int:
        """Get number of vectors in store."""
        if self.backend == "faiss":
            return self.index.ntotal if self.index else 0
        elif self.backend == "chroma":
            return self.collection.count()
        return 0

    def save(self, path: str):
        """Persist vector store to disk."""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)

        if self.backend == "faiss":
            import faiss
            faiss.write_index(self.index, str(path / "index.faiss"))
            with open(path / "metadata.json", "w") as f:
                json.dump(self.metadata, f)

        elif self.backend == "chroma":
            self.chroma_client.persist()

        logger.info(f"Vector store saved to {path}")

    def load(self, path: str):
        """Load vector store from disk."""
        path = Path(path)

        if self.backend == "faiss":
            import faiss
            self.index = faiss.read_index(str(path / "index.faiss"))
            with open(path / "metadata.json", "r") as f:
                self.metadata = json.load(f)

        elif self.backend == "chroma":
            # Chroma persists automatically
            pass

        logger.info(f"Vector store loaded from {path}")
