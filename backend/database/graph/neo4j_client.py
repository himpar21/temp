"""Neo4j graph database client.

Manages the connection to Neo4j and provides helpers for:
  - Creating / upserting nodes and relationships
  - Running Cypher queries
  - Multi-hop path traversal for Graph RAG

Node labels used in this project:
    Application  Solution  Requirement  TestSuite  TestCase
    TestRun      Execution  Failure  Defect  Engineer  Environment
    Release  HistoricalFailure

Relationship types:
    BELONGS_TO  IMPLEMENTS  CONTAINS  HAS_EXECUTION
    PRODUCED    LINKED_TO   AFFECTS   ASSIGNED_TO
    PART_OF     OCCURRED_IN DEPENDS_ON

Environment variables:
    NEO4J_URI       — Bolt URI   (default: bolt://localhost:7687)
    NEO4J_USERNAME  — username   (default: neo4j)
    NEO4J_PASSWORD  — password   (default: password)
"""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Generator

from neo4j import GraphDatabase, Session
from neo4j.exceptions import ServiceUnavailable

from database.graph.graph_schema import KnowledgeGraph

logger = logging.getLogger(__name__)

_DEFAULT_URI      = "bolt://localhost:7687"
_DEFAULT_USERNAME = "neo4j"
_DEFAULT_PASSWORD = "password"


@dataclass(frozen=True)
class GraphPath:
    """A traversal path returned by multi-hop queries."""
    nodes: list[dict[str, Any]]          # [{id, label, properties}, ...]
    relationships: list[dict[str, Any]]  # [{type, start_id, end_id, properties}, ...]
    length: int


class Neo4jClient:
    """Thin wrapper around the Neo4j Python driver."""

    def __init__(
        self,
        *,
        uri: str | None = None,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        self.uri      = uri      or os.getenv("NEO4J_URI",      _DEFAULT_URI)
        self.username = username or os.getenv("NEO4J_USERNAME",  _DEFAULT_USERNAME)
        self.password = password or os.getenv("NEO4J_PASSWORD",  _DEFAULT_PASSWORD)
        self._driver  = GraphDatabase.driver(
            self.uri, auth=(self.username, self.password)
        )
        logger.info("Neo4j client initialised — %s", self.uri)

    # ------------------------------------------------------------------
    # Connection helpers
    # ------------------------------------------------------------------

    def verify_connectivity(self) -> bool:
        """Return True if Neo4j is reachable."""
        try:
            self._driver.verify_connectivity()
            return True
        except ServiceUnavailable:
            return False

    def close(self) -> None:
        self._driver.close()

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        with self._driver.session() as s:
            yield s

    # ------------------------------------------------------------------
    # Schema / constraints
    # ------------------------------------------------------------------

    def create_constraints(self) -> None:
        """Create uniqueness constraints for all node types.
        Safe to call multiple times — uses CREATE CONSTRAINT IF NOT EXISTS.
        """
        node_types = [
            "Application", "Solution", "Requirement", "TestSuite",
            "TestCase", "TestRun", "Execution", "Failure", "Defect",
            "Engineer", "Environment", "Release", "HistoricalFailure",
        ]
        with self.session() as s:
            for label in node_types:
                s.run(
                    f"CREATE CONSTRAINT IF NOT EXISTS "
                    f"FOR (n:{label}) REQUIRE n.id IS UNIQUE"
                )
        logger.info("Neo4j constraints created/verified")

    # ------------------------------------------------------------------
    # Write helpers
    # ------------------------------------------------------------------

    def upsert_node(
        self,
        label: str,
        node_id: str,
        properties: dict[str, Any],
    ) -> None:
        """Create or update a node. `node_id` maps to the `id` property."""
        props = {k: v for k, v in properties.items() if v is not None}
        props["id"] = node_id
        with self.session() as s:
            s.run(
                f"MERGE (n:{label} {{id: $id}}) SET n += $props",
                id=node_id, props=props,
            )

    def upsert_relationship(
        self,
        from_label: str,
        from_id: str,
        rel_type: str,
        to_label: str,
        to_id: str,
        properties: dict[str, Any] | None = None,
    ) -> None:
        """Create or update a directed relationship between two nodes."""
        props = properties or {}
        with self.session() as s:
            s.run(
                f"MATCH (a:{from_label} {{id: $from_id}}) "
                f"MATCH (b:{to_label}   {{id: $to_id}}) "
                f"MERGE (a)-[r:{rel_type}]->(b) "
                f"SET r += $props",
                from_id=from_id, to_id=to_id, props=props,
            )

    def upsert_nodes_batch(
        self,
        label: str,
        rows: list[dict[str, Any]],
    ) -> int:
        """Batch upsert nodes. Each row must contain an 'id' key."""
        if not rows:
            return 0
        with self.session() as s:
            s.run(
                f"UNWIND $rows AS row "
                f"MERGE (n:{label} {{id: row.id}}) "
                f"SET n += row",
                rows=rows,
            )
        return len(rows)

    def upsert_relationships_batch(
        self,
        from_label: str,
        to_label: str,
        rel_type: str,
        pairs: list[dict[str, Any]],
    ) -> int:
        """Batch upsert relationships.
        Each pair dict: {from_id: str, to_id: str, **props}
        """
        if not pairs:
            return 0
        with self.session() as s:
            s.run(
                f"UNWIND $pairs AS pair "
                f"MATCH (a:{from_label} {{id: pair.from_id}}) "
                f"MATCH (b:{to_label}   {{id: pair.to_id}}) "
                f"MERGE (a)-[r:{rel_type}]->(b) "
                f"SET r += pair",
                pairs=pairs,
            )
        return len(pairs)

    def upsert_knowledge_graph(
        self, graph: KnowledgeGraph, *, replace: bool = False
    ) -> None:
        """Persist a graph projection, optionally pruning the previous snapshot."""

        with self.session() as session:
            session.run(
                "CREATE CONSTRAINT graph_entity_node_id IF NOT EXISTS "
                "FOR (node:GraphEntity) REQUIRE node.node_id IS UNIQUE"
            ).consume()
            if replace:
                session.run(
                    "MATCH (:GraphEntity)-[edge]-(:GraphEntity) DELETE edge"
                ).consume()
                session.run(
                    "MATCH (node:GraphEntity) WHERE NOT node.node_id IN $node_ids "
                    "DETACH DELETE node",
                    node_ids=list(graph.nodes),
                ).consume()
            node_rows = [
                {
                    "node_id": node.node_id,
                    "node_type": node.node_type.value,
                    "label": node.label,
                    "aliases": list(node.aliases),
                    "properties": node.properties,
                }
                for node in graph.nodes.values()
            ]
            for offset in range(0, len(node_rows), 500):
                session.run(
                    "UNWIND $rows AS row "
                    "MERGE (node:GraphEntity {node_id: row.node_id}) "
                    "SET node.node_type = row.node_type, node.label = row.label, "
                    "node.aliases = row.aliases, node += row.properties",
                    rows=node_rows[offset : offset + 500],
                ).consume()

            edges_by_relationship: dict[str, list[dict[str, Any]]] = {}
            for edge in graph.edges:
                relationship = edge.relationship.value.upper()
                edges_by_relationship.setdefault(relationship, []).append(
                    {
                        "source_id": edge.source_id,
                        "target_id": edge.target_id,
                        "strength": edge.strength,
                        "properties": edge.properties,
                    }
                )
            for relationship, rows in edges_by_relationship.items():
                for offset in range(0, len(rows), 500):
                    session.run(
                        "UNWIND $rows AS row "
                        "MATCH (source:GraphEntity {node_id: row.source_id}), "
                        "(target:GraphEntity {node_id: row.target_id}) "
                        f"MERGE (source)-[edge:{relationship}]->(target) "
                        "SET edge.strength = row.strength, edge += row.properties",
                        rows=rows[offset : offset + 500],
                    ).consume()

    # ------------------------------------------------------------------
    # Read helpers
    # ------------------------------------------------------------------

    def get_node(self, label: str, node_id: str) -> dict[str, Any] | None:
        """Fetch a single node by label and id."""
        with self.session() as s:
            result = s.run(
                f"MATCH (n:{label} {{id: $id}}) RETURN properties(n) AS props",
                id=node_id,
            )
            record = result.single()
            return dict(record["props"]) if record else None

    def get_neighbors(
        self,
        node_id: str,
        rel_types: list[str] | None = None,
        direction: str = "both",
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Return immediate neighbors of a node.

        Args:
            node_id:   The id of the seed node.
            rel_types: Optional list of relationship types to filter.
            direction: 'out' | 'in' | 'both'
            limit:     Max results.
        """
        rel_filter = (
            ":" + "|".join(rel_types) if rel_types else ""
        )
        if direction == "out":
            pattern = f"(n)-[r{rel_filter}]->(m)"
        elif direction == "in":
            pattern = f"(n)<-[r{rel_filter}]-(m)"
        else:
            pattern = f"(n)-[r{rel_filter}]-(m)"

        with self.session() as s:
            result = s.run(
                f"MATCH (n {{id: $id}}) "
                f"MATCH {pattern} "
                f"RETURN properties(m) AS props, labels(m) AS labels, type(r) AS rel "
                f"LIMIT $limit",
                id=node_id, limit=limit,
            )
            return [
                {**dict(rec["props"]), "_labels": rec["labels"], "_rel": rec["rel"]}
                for rec in result
            ]

    def multi_hop_paths(
        self,
        seed_ids: list[str],
        max_hops: int = 4,
        limit: int = 20,
    ) -> list[GraphPath]:
        """Return multi-hop paths starting from seed nodes.

        Args:
            seed_ids:  List of node IDs to start traversal from.
            max_hops:  Maximum relationship hops (1–6).
            limit:     Max paths to return.

        Returns:
            List of GraphPath objects sorted by ascending length.
        """
        if not 1 <= max_hops <= 6:
            raise ValueError("max_hops must be between 1 and 6")

        with self.session() as s:
            result = s.run(
                "MATCH path = (seed)-[*1..$hops]-(related) "
                "WHERE seed.id IN $seed_ids "
                "RETURN path "
                "ORDER BY length(path) ASC "
                "LIMIT $limit",
                seed_ids=seed_ids,
                hops=max_hops,
                limit=limit,
            )
            paths: list[GraphPath] = []
            for record in result:
                path = record["path"]
                nodes = [
                    {
                        "id":         node.get("id", ""),
                        "labels":     list(node.labels),
                        "properties": dict(node),
                    }
                    for node in path.nodes
                ]
                rels = [
                    {
                        "type":       rel.type,
                        "start_id":   rel.start_node.get("id", ""),
                        "end_id":     rel.end_node.get("id", ""),
                        "properties": dict(rel),
                    }
                    for rel in path.relationships
                ]
                paths.append(GraphPath(nodes=nodes, relationships=rels, length=len(rels)))
            return paths

    def run_cypher(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Run an arbitrary read Cypher query and return list of record dicts."""
        with self.session() as s:
            result = s.run(query, **(parameters or {}))
            return [dict(record) for record in result]

    def node_count(self, label: str | None = None) -> int:
        """Return the total count of nodes, optionally filtered by label."""
        query = f"MATCH (n{':' + label if label else ''}) RETURN count(n) AS cnt"
        with self.session() as s:
            result = s.run(query)
            record = result.single()
            return record["cnt"] if record else 0


# ── module-level singleton ────────────────────────────────────────────────────
_instance: Neo4jClient | None = None


def get_neo4j_client() -> Neo4jClient:
    """Return a module-level singleton Neo4jClient."""
    global _instance
    if _instance is None:
        _instance = Neo4jClient()
    return _instance
