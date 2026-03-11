"""pgvector client — store and search paper chunks using PostgreSQL + pgvector."""

import logging
from uuid import UUID

import psycopg
from pgvector.psycopg import register_vector

from sidecar.models.chunk import Chunk
from sidecar.models.paper import Paper

logger = logging.getLogger(__name__)


class PgVectorClient:
    def __init__(self, dsn: str) -> None:
        self.dsn = dsn
        self._conn: psycopg.Connection | None = None

    def connect(self) -> None:
        self._conn = psycopg.connect(self.dsn, autocommit=True)
        register_vector(self._conn)
        logger.info("Connected to pgvector DB")

    def close(self) -> None:
        if self._conn:
            self._conn.close()

    @property
    def conn(self) -> psycopg.Connection:
        if not self._conn:
            raise RuntimeError("Not connected — call connect() first")
        return self._conn

    # ── Papers ──────────────────────────────────────────────────────────────

    def upsert_paper(self, paper: Paper) -> UUID:
        """Insert or update a paper. Returns its DB UUID."""
        row = self.conn.execute(
            """
            INSERT INTO papers (arxiv_id, title, authors, abstract, categories, published, parser_used)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (arxiv_id) DO UPDATE
                SET title = EXCLUDED.title,
                    abstract = EXCLUDED.abstract,
                    parser_used = EXCLUDED.parser_used
            RETURNING id
            """,
            (
                paper.arxiv_id,
                paper.title,
                paper.authors,
                paper.abstract,
                paper.categories,
                paper.published,
                paper.parser_used,
            ),
        ).fetchone()
        return row[0]

    def get_paper_id(self, arxiv_id: str) -> UUID | None:
        row = self.conn.execute(
            "SELECT id FROM papers WHERE arxiv_id = %s", (arxiv_id,)
        ).fetchone()
        return row[0] if row else None

    # ── Chunks ───────────────────────────────────────────────────────────────

    def insert_chunks(self, chunks: list[Chunk], paper_db_id: UUID) -> int:
        """Bulk-insert chunks. Returns number inserted."""
        inserted = 0
        for chunk in chunks:
            if not chunk.embedding:
                logger.warning("Chunk %d has no embedding — skipping", chunk.chunk_index)
                continue
            self.conn.execute(
                """
                INSERT INTO chunks (paper_id, chunk_index, section, content, tokens, embedding)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING
                """,
                (paper_db_id, chunk.chunk_index, chunk.section, chunk.content, chunk.tokens, chunk.embedding),
            )
            inserted += 1
        logger.info("Inserted %d chunks for paper %s", inserted, paper_db_id)
        return inserted

    # ── Search ───────────────────────────────────────────────────────────────

    def vector_search(self, query_embedding: list[float], top_k: int = 10) -> list[dict]:
        """Cosine similarity search. Returns list of result dicts."""
        rows = self.conn.execute(
            """
            SELECT
                c.id,
                c.section,
                c.content,
                c.tokens,
                1 - (c.embedding <=> %s::vector) AS score,
                p.arxiv_id,
                p.title,
                p.authors,
                p.published
            FROM chunks c
            JOIN papers p ON p.id = c.paper_id
            ORDER BY c.embedding <=> %s::vector
            LIMIT %s
            """,
            (query_embedding, query_embedding, top_k),
        ).fetchall()

        return [
            {
                "chunk_id": r[0],
                "section": r[1],
                "content": r[2],
                "tokens": r[3],
                "score": float(r[4]),
                "arxiv_id": r[5],
                "title": r[6],
                "authors": r[7],
                "published": r[8],
            }
            for r in rows
        ]

    def hybrid_search(self, query: str, query_embedding: list[float], top_k: int = 10) -> list[dict]:
        """Hybrid search: combine vector cosine similarity + BM25 full-text ranking via RRF."""
        rows = self.conn.execute(
            """
            WITH vector_ranked AS (
                SELECT
                    c.id,
                    ROW_NUMBER() OVER (ORDER BY c.embedding <=> %s::vector) AS rank
                FROM chunks c
                LIMIT %s
            ),
            fts_ranked AS (
                SELECT
                    c.id,
                    ROW_NUMBER() OVER (ORDER BY ts_rank(to_tsvector('english', c.content), plainto_tsquery('english', %s)) DESC) AS rank
                FROM chunks c
                WHERE to_tsvector('english', c.content) @@ plainto_tsquery('english', %s)
                LIMIT %s
            ),
            rrf AS (
                SELECT
                    COALESCE(v.id, f.id) AS id,
                    (COALESCE(1.0 / (60 + v.rank), 0) + COALESCE(1.0 / (60 + f.rank), 0)) AS rrf_score
                FROM vector_ranked v
                FULL OUTER JOIN fts_ranked f ON v.id = f.id
            )
            SELECT
                c.id, c.section, c.content, c.tokens, rrf.rrf_score,
                p.arxiv_id, p.title, p.authors, p.published
            FROM rrf
            JOIN chunks c ON c.id = rrf.id
            JOIN papers p ON p.id = c.paper_id
            ORDER BY rrf.rrf_score DESC
            LIMIT %s
            """,
            (query_embedding, top_k * 2, query, query, top_k * 2, top_k),
        ).fetchall()

        return [
            {
                "chunk_id": r[0],
                "section": r[1],
                "content": r[2],
                "tokens": r[3],
                "score": float(r[4]),
                "arxiv_id": r[5],
                "title": r[6],
                "authors": r[7],
                "published": r[8],
            }
            for r in rows
        ]

    # ── Stats ─────────────────────────────────────────────────────────────────

    def stats(self) -> dict:
        papers = self.conn.execute("SELECT count(*) FROM papers").fetchone()[0]
        chunks = self.conn.execute("SELECT count(*) FROM chunks").fetchone()[0]
        with_embeddings = self.conn.execute("SELECT count(*) FROM chunks WHERE embedding IS NOT NULL").fetchone()[0]
        return {"papers": papers, "chunks": chunks, "chunks_with_embeddings": with_embeddings}


def make_pgvector_client(dsn: str) -> PgVectorClient:
    client = PgVectorClient(dsn)
    client.connect()
    return client
