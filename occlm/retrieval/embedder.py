"""Dense embedding generation for RAG."""

import logging

import numpy as np

logger = logging.getLogger(__name__)


class Embedder:
    """Generate dense embeddings using transformer models."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", device: str = "cpu"):
        """Initialize embedder with model and device."""
        self.model_name = model_name
        self.device = device
        self.model = None
        self._load_model()

    def _load_model(self):
        """Load embedding model with device fallback."""
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)
            self.model.to(self.device)
            logger.info(f"Loaded embedder: {self.model_name} on {self.device}")
        except Exception as e:
            logger.warning(f"Failed to load on {self.device}, trying CPU: {e}")
            self.device = "cpu"
            try:
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer(self.model_name)
                self.model.to(self.device)
            except ImportError:
                logger.error("sentence-transformers not installed. Install with: pip install sentence-transformers")
                raise

    def embed(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        """Generate embeddings for list of texts.

        Args:
            texts: List of text strings to embed
            batch_size: Batch size for processing

        Returns:
            Numpy array of shape (len(texts), embedding_dim)
        """
        if not texts:
            return np.array([]).reshape(0, 384)  # Empty array with correct shape

        try:
            embeddings = self.model.encode(texts, batch_size=batch_size, convert_to_numpy=True)
            return embeddings
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            raise

    def embed_query(self, query: str) -> np.ndarray:
        """Generate embedding for single query text.

        Args:
            query: Query text string

        Returns:
            Numpy array of shape (embedding_dim,)
        """
        if not query:
            return np.zeros(384)

        embedding = self.model.encode(query, convert_to_numpy=True)
        return embedding

    def set_device(self, device: str):
        """Switch device for embeddings."""
        if self.model:
            self.model.to(device)
            self.device = device
            logger.info(f"Embedder device switched to: {device}")

    def get_dimension(self) -> int:
        """Get embedding dimension."""
        return self.model.get_sentence_embedding_dimension() if self.model else 384
