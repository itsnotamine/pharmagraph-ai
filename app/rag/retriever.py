from pathlib import Path
import re
import os

import numpy as np

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from openai import OpenAI
from dotenv import load_dotenv


# ============================================================
# CONFIGURATION
# ============================================================

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "corpus"

load_dotenv(ROOT / ".env")


# ============================================================
# HYBRID RETRIEVER
# TF-IDF + SEMANTIC EMBEDDINGS + RRF
# ============================================================

class HybridRetriever:

    def __init__(self):

        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL")
        )

        self.embedding_model = os.getenv(
            "OPENAI_EMBEDDING_MODEL"
        )

        self.chunks = []

        self.vectorizer = None
        self.tfidf_matrix = None
        self.embedding_matrix = None

    # --------------------------------------------------------
    # STEP 1: LOAD DOCUMENTS
    # --------------------------------------------------------

    def load_documents(self):

        self.chunks = []

        for path in sorted(CORPUS.glob("*.md")):

            text = path.read_text(encoding="utf-8")

            sections = re.split(
                r"(?=^#{1,4} )",
                text,
                flags=re.MULTILINE
            )

            for section in sections:

                if not section.strip():
                    continue

                heading = section.splitlines()[0].strip()

                width = 1200
                overlap = 250
                step = width - overlap

                for start in range(0, len(section), step):

                    piece = section[start:start + width].strip()

                    if not piece:
                        continue

                    # Preserve section context in every chunk
                    chunk_text = (
                        f"Document: {path.name}\n"
                        f"Section: {heading}\n\n"
                        f"{piece}"
                    )

                    self.chunks.append({
                        "id": len(self.chunks),
                        "source": path.name,
                        "section": heading,
                        "text": chunk_text
                    })

        if not self.chunks:
            raise RuntimeError(
                f"No Markdown documents found in {CORPUS}"
            )

    # --------------------------------------------------------
    # STEP 2: BUILD HYBRID INDEX
    # --------------------------------------------------------

    def build_index(self):

        print("Loading pharmaceutical documents...")

        self.load_documents()

        texts = [
            chunk["text"]
            for chunk in self.chunks
        ]

        print(f"Loaded {len(texts)} chunks")

        # Lexical index
        print("Building TF-IDF index...")

        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            max_features=25000
        )

        self.tfidf_matrix = self.vectorizer.fit_transform(
            texts
        )

        # Semantic index
        print("Generating semantic embeddings...")

        if not self.embedding_model:
            raise RuntimeError(
                "OPENAI_EMBEDDING_MODEL is missing from .env"
            )

        embeddings = []
        batch_size = 32

        for i in range(0, len(texts), batch_size):

            batch = texts[i:i + batch_size]

            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=batch
            )

            ordered_data = sorted(
                response.data,
                key=lambda item: item.index
            )

            embeddings.extend(
                item.embedding
                for item in ordered_data
            )

            print(
                f"Embedded {min(i + batch_size, len(texts))}"
                f"/{len(texts)} chunks"
            )

        self.embedding_matrix = np.asarray(
            embeddings,
            dtype=np.float32
        )

        if len(self.embedding_matrix) != len(self.chunks):
            raise RuntimeError(
                "Embedding count does not match chunk count"
            )

        print("Hybrid RAG index ready!")

    # --------------------------------------------------------
    # STEP 3: HYBRID SEARCH
    # --------------------------------------------------------

    def search(self, query: str, top_k: int = 6):

        if self.embedding_matrix is None:
            raise RuntimeError(
                "Index not initialized. Call build_index() first."
            )

        if not query.strip():
            return []

        # A. Lexical retrieval
        query_tfidf = self.vectorizer.transform(
            [query]
        )

        lexical_scores = cosine_similarity(
            query_tfidf,
            self.tfidf_matrix
        ).ravel()

        # B. Semantic retrieval
        response = self.client.embeddings.create(
            model=self.embedding_model,
            input=query
        )

        query_embedding = np.asarray(
            response.data[0].embedding,
            dtype=np.float32
        ).reshape(1, -1)

        semantic_scores = cosine_similarity(
            query_embedding,
            self.embedding_matrix
        ).ravel()

        # C. Reciprocal Rank Fusion (RRF)
        lexical_ranking = np.argsort(
            lexical_scores
        )[::-1]

        semantic_ranking = np.argsort(
            semantic_scores
        )[::-1]

        rrf_scores = np.zeros(
            len(self.chunks),
            dtype=np.float32
        )

        rrf_k = 60
        candidate_count = min(
            30,
            len(self.chunks)
        )

        for rank, idx in enumerate(
            lexical_ranking[:candidate_count]
        ):
            if lexical_scores[idx] > 0:
                rrf_scores[idx] += 1.0 / (
                    rrf_k + rank + 1
                )

        for rank, idx in enumerate(
            semantic_ranking[:candidate_count]
        ):
            rrf_scores[idx] += 1.0 / (
                rrf_k + rank + 1
            )

        # D. Select top results
        best_ids = np.argsort(
            rrf_scores
        )[::-1]

        results = []

        for idx in best_ids:

            if rrf_scores[idx] <= 0:
                continue

            chunk = self.chunks[int(idx)]

            results.append({
                "id": chunk["id"],
                "source": chunk["source"],
                "section": chunk["section"],
                "text": chunk["text"],
                "score": float(rrf_scores[idx])
            })

            if len(results) >= top_k:
                break

        return results