"""Generate an inspectable Cypher representation of a graph retrieval request."""

from ai_engine.graph_rag.entity_extractor import ProcessedGraphQuery
from ai_engine.graph_rag.entity_linker import LinkedEntity


def generate_graph_query(
    query: ProcessedGraphQuery,
    linked_entities: list[LinkedEntity],
    max_hops: int,
) -> str:
    """Return parameterized-style Cypher for diagnostics and Neo4j migration."""

    seed_ids = [entity.node.node_id for entity in linked_entities]
    return (
        "MATCH path=(seed)-[*1.."
        f"{max_hops}]-(related) "
        "WHERE seed.node_id IN $seed_ids "
        "RETURN path, related "
        "ORDER BY length(path) ASC "
        f"/* intent={query.intent}; seed_ids={seed_ids!r} */"
    )
