"""Read-only staging schema check; never prints database credentials."""
from rag_postgres import PostgresRAGIndex


def main():
    index = PostgresRAGIndex()
    with index._connect() as cn:
        with cn.cursor() as cur:
            cur.execute("SELECT extversion FROM pg_extension WHERE extname='vector'")
            vector = cur.fetchone()
            cur.execute("SELECT to_regclass('rag_documents') AS documents,"
                        "to_regclass('rag_chunks') AS chunks,"
                        "to_regclass('rag_events') AS events")
            tables = cur.fetchone()
    if not vector or not all(tables.values()):
        raise SystemExit("Neon RAG staging schema is missing; run the explicit migration")
    print("Neon RAG staging schema ready. pgvector extension present. No user data changed.")


if __name__ == '__main__':
    main()
