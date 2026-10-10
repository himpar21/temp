"""FastAPI application entrypoint."""

import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.dependencies import get_current_user
from api.routes.auth import router as auth_router
from api.routes.graph import router as graph_rag_router
from api.routes.hybrid_rag import router as hybrid_rag_router
from api.routes.ingestion import router as ingestion_router
from api.routes.query import router as query_router
from database.postgres.connection import init_database

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    # ── PostgreSQL ────────────────────────────────────────────────────
    init_database()
    logger.info("PostgreSQL tables initialised")

    dynamic_graph = None
    try:
        from database.postgres.connection import SessionLocal
        from services.graph_projection_service import GraphProjectionService

        with SessionLocal() as session:
            dynamic_graph = GraphProjectionService(session).backfill()
            session.commit()
        logger.info("Uploaded documents projected into the knowledge graph")
    except Exception as exc:
        logger.warning("Uploaded-document graph backfill failed: %s", exc)

    # ── Qdrant ───────────────────────────────────────────────────────
    try:
        from database.vector.qdrant_client import get_qdrant_client
        qdrant = get_qdrant_client()
        logger.info("Qdrant connected — collection '%s', %d vectors",
                    qdrant.collection, qdrant.count())
    except Exception as exc:
        logger.warning("Qdrant unavailable at startup: %s", exc)

    # ── Neo4j ────────────────────────────────────────────────────────
    try:
        from database.graph.neo4j_client import get_neo4j_client
        neo4j = get_neo4j_client()
        if neo4j.verify_connectivity():
            from ai_engine.graph_rag.graph_builder import GraphBuilder

            neo4j.create_constraints()
            graph = GraphBuilder().build()
            if dynamic_graph is not None:
                graph = graph.merged_with(dynamic_graph)
            neo4j.upsert_knowledge_graph(graph, replace=True)
            logger.info("Neo4j connected — %d nodes", neo4j.node_count())
        else:
            logger.warning("Neo4j not reachable at startup")
    except Exception as exc:
        logger.warning("Neo4j unavailable at startup: %s", exc)

    yield


app = FastAPI(title="AI Test Management Backend", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(ingestion_router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
app.include_router(query_router, prefix="/api/v1", dependencies=[Depends(get_current_user)])
app.include_router(hybrid_rag_router, dependencies=[Depends(get_current_user)])
app.include_router(graph_rag_router, dependencies=[Depends(get_current_user)])


@app.get("/health")
def health_check() -> dict:
    """Return service health and DB connectivity status."""
    status: dict = {"status": "ok", "postgres": "ok"}

    try:
        from database.vector.qdrant_client import get_qdrant_client
        count = get_qdrant_client().count()
        status["qdrant"] = f"ok ({count} vectors)"
    except Exception as exc:
        status["qdrant"] = f"unavailable: {exc}"

    try:
        from database.graph.neo4j_client import get_neo4j_client
        client = get_neo4j_client()
        status["neo4j"] = "ok" if client.verify_connectivity() else "unavailable"
    except Exception as exc:
        status["neo4j"] = f"unavailable: {exc}"

    return status
