"""RAG pipeline combining BM25 and dense retrieval with optional reranking."""

import logging
from typing import Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


class RAGPipeline:
    """Hybrid retrieval combining BM25 lexical and dense retrieval."""

    def __init__(
        self,
        embedder=None,
        vector_store=None,
        bm25_index=None,
        reranker=None,
        dense_weight: float = 0.7,
        bm25_weight: float = 0.3,
    ):
        """Initialize RAG pipeline.

        Args:
            embedder: Embedder instance for dense retrieval
            vector_store: VectorStore instance
            bm25_index: BM25 index (rank_bm25.BM25Okapi)
            reranker: Optional reranker model
            dense_weight: Weight for dense retrieval (0-1)
            bm25_weight: Weight for BM25 (0-1)
        """
        self.embedder = embedder
        self.vector_store = vector_store
        self.bm25_index = bm25_index
        self.reranker = reranker
        self.dense_weight = dense_weight
        self.bm25_weight = bm25_weight
        self.documents = []

    def add_documents(self, documents: List[Dict[str, str]]):
        """Index documents for retrieval.

        Args:
            documents: List of dicts with 'id' and 'text' keys
        """
        if not documents:
            return

        self.documents = documents
        texts = [d.get("text", "") for d in documents]

        # Index dense embeddings
        if self.embedder and self.vector_store:
            embeddings = self.embedder.embed(texts)
            self.vector_store.add(embeddings, documents)
            logger.info(f"Indexed {len(documents)} documents in dense store")

        # Index BM25
        if self.bm25_index:
            try:
                from rank_bm25 import BM25Okapi
                tokenized = [doc.split() for doc in texts]
                self.bm25_index = BM25Okapi(tokenized)
                logger.info(f"Indexed {len(documents)} documents in BM25")
            except ImportError:
                logger.warning("rank_bm25 not installed. BM25 retrieval disabled.")
                self.bm25_index = None

    def retrieve(
        self,
        query: str,
        k: int = 5,
        use_reranking: bool = False,
    ) -> List[Dict]:
        """Retrieve documents for query using hybrid search.

        Args:
            query: Query string
            k: Number of documents to retrieve
            use_reranking: Whether to apply reranking

        Returns:
            List of retrieved documents with scores
        """
        results = {}

        # Dense retrieval
        if self.embedder and self.vector_store:
            query_embedding = self.embedder.embed_query(query)
            dense_results = self.vector_store.search(query_embedding, k=k * 2)
            for idx, dist, metadata in dense_results:
                score = 1 / (1 + dist)  # Convert distance to similarity
                if idx not in results:
                    results[idx] = {"metadata": metadata, "scores": {}}
                results[idx]["scores"]["dense"] = score

        # BM25 retrieval
        if self.bm25_index:
            try:
                query_tokens = query.split()
                bm25_scores = self.bm25_index.get_scores(query_tokens)
                top_indices = np.argsort(bm25_scores)[-k * 2:][::-1]
                for idx in top_indices:
                    if bm25_scores[idx] > 0:
                        if idx not in results:
                            doc = self.documents[idx] if idx < len(self.documents) else {}
                            results[idx] = {"metadata": doc, "scores": {}}
                        results[idx]["scores"]["bm25"] = float(bm25_scores[idx])
            except Exception as e:
                logger.warning(f"BM25 retrieval failed: {e}")

        # Hybrid scoring
        final_results = []
        for idx, item in results.items():
            dense_score = item["scores"].get("dense", 0.0)
            bm25_score = item["scores"].get("bm25", 0.0) / 100  # Normalize
            hybrid_score = self.dense_weight * dense_score + self.bm25_weight * bm25_score
            final_results.append(
                {
                    "index": idx,
                    "score": hybrid_score,
                    "document": item["metadata"],
                    "component_scores": item["scores"],
                }
            )

        # Sort by score
        final_results.sort(key=lambda x: x["score"], reverse=True)
        final_results = final_results[:k]

        # Reranking
        if use_reranking and self.reranker:
            final_results = self._rerank(query, final_results)

        return final_results

    def _rerank(self, query: str, candidates: List[Dict], top_k: Optional[int] = None) -> List[Dict]:
        """Rerank candidates using cross-encoder.

        Args:
            query: Query string
            candidates: List of candidate documents
            top_k: Number of documents to keep after reranking

        Returns:
            Reranked documents
        """
        if not self.reranker or not candidates:
            return candidates

        try:
            docs = [c["document"].get("text", "") for c in candidates]
            scores = self.reranker.predict([[query, doc] for doc in docs])

            for candidate, score in zip(candidates, scores):
                candidate["rerank_score"] = float(score)

            candidates.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)

            if top_k:
                candidates = candidates[:top_k]

            logger.info(f"Reranked {len(candidates)} documents")
            return candidates

        except Exception as e:
            logger.warning(f"Reranking failed: {e}")
            return candidates

    def retrieve_with_score_breakdown(self, query: str, k: int = 5) -> List[Dict]:
        """Retrieve with detailed score breakdowns for analysis.

        Args:
            query: Query string
            k: Number of documents

        Returns:
            Documents with detailed score information
        """
        results = self.retrieve(query, k=k, use_reranking=False)

        for result in results:
            scores = result.get("component_scores", {})
            result["score_breakdown"] = {
                "dense": scores.get("dense", 0.0),
                "bm25": scores.get("bm25", 0.0),
                "hybrid": result["score"],
            }

        return results
