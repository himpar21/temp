"""Project uploaded documents into Graph RAG nodes and relationships."""

from __future__ import annotations

import logging
import re
import uuid
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from database.graph.graph_schema import (
    GraphEdge,
    GraphNode,
    KnowledgeGraph,
    NodeType,
    RelationshipType,
)
from database.postgres.models import (
    GraphEdge as StoredGraphEdge,
    GraphNode as StoredGraphNode,
    StoredDocument,
)
from ingestion.preprocessing import extract_entity_ids, normalize_scalar


logger = logging.getLogger(__name__)


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def _entity_type(identifier: str) -> NodeType:
    upper = identifier.upper()
    if upper.startswith("REQ-"):
        return NodeType.REQUIREMENT
    if upper.startswith("TC-"):
        return NodeType.TEST_CASE
    if upper.startswith("EXEC-") or upper.startswith("RUN-"):
        return NodeType.EXECUTION
    if upper.startswith("FAIL-"):
        return NodeType.FAILURE
    if upper.startswith(("DR-BUG-", "BUG-", "DEF-")):
        return NodeType.DEFECT
    if upper.startswith(("REPORT-", "LOG-")):
        return NodeType.EXECUTION_REPORT
    if upper.startswith("APP-"):
        return NodeType.APPLICATION
    return NodeType.DOCUMENT


def _field(text: str, metadata: dict[str, Any], *names: str) -> str:
    for name in names:
        metadata_value = metadata.get(name.lower().replace(" ", "_"))
        if metadata_value:
            return normalize_scalar(str(metadata_value)).strip("#* ")
        match = re.search(
            rf"(?im)^\s*(?:#+\s*)?(?:\*\*)?{re.escape(name)}(?:\*\*)?\s*:\s*([^\n]+)",
            text,
        )
        if match:
            return normalize_scalar(match.group(1)).strip("#* ")
    return ""


class GraphProjectionService:
    """Extract, persist, load, and synchronize uploaded-document graphs."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def project(self, document: StoredDocument) -> KnowledgeGraph:
        metadata = dict(document.document_metadata or {})
        text = document.text or ""
        entity_ids = sorted(
            {
                *(str(item).upper() for item in (document.entity_ids or [])),
                *extract_entity_ids(text, metadata),
            }
        )
        logical_id = str(document.logical_document_id or "").upper()
        if logical_id and extract_entity_ids(logical_id):
            entity_ids = sorted({*entity_ids, logical_id})

        common = {
            "title": _field(text, metadata, "title") or document.filename,
            "application": _field(text, metadata, "application", "project"),
            "component": _field(text, metadata, "component", "module", "feature"),
            "severity": _field(text, metadata, "severity"),
            "priority": _field(text, metadata, "priority"),
            "status": _field(text, metadata, "status"),
            "reported": _field(text, metadata, "reported"),
            "resolved": _field(text, metadata, "resolved"),
            "assigned_to": _field(text, metadata, "assigned to", "assigned_to"),
            "source": document.filename,
            "source_document_id": document.id,
        }
        common = {key: value for key, value in common.items() if value}

        nodes: dict[str, GraphNode] = {}
        edges: dict[tuple[str, str, RelationshipType], GraphEdge] = {}

        def add_node(node: GraphNode) -> None:
            nodes[node.node_id] = node

        def add_edge(
            source_id: str,
            target_id: str,
            relationship: RelationshipType,
            strength: float,
        ) -> None:
            if source_id != target_id:
                edge = GraphEdge(
                    source_id,
                    target_id,
                    relationship,
                    strength,
                    {"source_document_id": document.id},
                )
                edges[(source_id, target_id, relationship)] = edge

        primary_id = logical_id if logical_id in entity_ids else (entity_ids[0] if entity_ids else "")
        for identifier in entity_ids:
            node_id = f"entity:{identifier.lower()}"
            properties = {**common, "identifier": identifier}
            if identifier == primary_id:
                properties["content"] = text
            add_node(
                GraphNode(
                    node_id,
                    _entity_type(identifier),
                    identifier,
                    properties,
                    aliases=(common.get("title", ""),) if identifier == primary_id else (),
                )
            )

        if not nodes:
            fallback_label = document.logical_document_id or document.filename
            primary_id = fallback_label
            add_node(
                GraphNode(
                    f"document:{document.id}",
                    NodeType.DOCUMENT,
                    fallback_label,
                    {**common, "content": text},
                    aliases=(document.filename,),
                )
            )

        application = common.get("application", "")
        component = common.get("component", "")
        application_node_id = ""
        component_node_id = ""
        if application:
            application_node_id = f"application:{_slug(application)}"
            add_node(
                GraphNode(
                    application_node_id,
                    NodeType.APPLICATION,
                    application,
                    {"application": application, "source_document_id": document.id},
                )
            )
        if component:
            component_node_id = f"component:{_slug(application or 'general')}:{_slug(component)}"
            add_node(
                GraphNode(
                    component_node_id,
                    NodeType.COMPONENT,
                    component,
                    {
                        "application": application,
                        "component": component,
                        "source_document_id": document.id,
                    },
                )
            )
        if application_node_id and component_node_id:
            add_edge(application_node_id, component_node_id, RelationshipType.HAS_COMPONENT, 1.0)

        anchor = component_node_id or application_node_id
        entity_nodes = [
            node
            for node in nodes.values()
            if node.node_type not in {NodeType.APPLICATION, NodeType.COMPONENT}
        ]
        for requirement in (
            node for node in entity_nodes if node.node_type is NodeType.REQUIREMENT
        ):
            if anchor:
                add_edge(anchor, requirement.node_id, RelationshipType.DEFINES, 0.95)

        # Structured files can contain hundreds of independent rows. Relationships
        # are therefore inferred per row instead of forming a document-wide
        # Cartesian product. Unstructured reports describe one traceability chain.
        relationship_groups: list[list[GraphNode]] = []
        is_structured = str(document.document_type).startswith("structured_")
        if is_structured:
            nodes_by_label = {node.label.upper(): node for node in entity_nodes}
            for line in text.splitlines():
                group = [
                    nodes_by_label[identifier]
                    for identifier in extract_entity_ids(line)
                    if identifier in nodes_by_label
                ]
                if len(group) > 1:
                    relationship_groups.append(group)
        else:
            relationship_groups.append(entity_nodes)

        for group in relationship_groups:
            by_type: dict[NodeType, list[GraphNode]] = {
                node_type: [node for node in group if node.node_type is node_type]
                for node_type in NodeType
            }
            for test_case in by_type[NodeType.TEST_CASE]:
                for requirement in by_type[NodeType.REQUIREMENT]:
                    add_edge(requirement.node_id, test_case.node_id, RelationshipType.IMPLEMENTS, 0.98)
            for execution in by_type[NodeType.EXECUTION]:
                for test_case in by_type[NodeType.TEST_CASE]:
                    add_edge(test_case.node_id, execution.node_id, RelationshipType.HAS_EXECUTION, 0.98)
            for failure in by_type[NodeType.FAILURE]:
                sources = by_type[NodeType.EXECUTION] or by_type[NodeType.TEST_CASE]
                for source in sources:
                    add_edge(source.node_id, failure.node_id, RelationshipType.PRODUCES, 0.98)
            for defect in by_type[NodeType.DEFECT]:
                sources = by_type[NodeType.FAILURE] or by_type[NodeType.TEST_CASE]
                for source in sources:
                    add_edge(source.node_id, defect.node_id, RelationshipType.LINKED_TO, 0.98)
                if anchor and not sources:
                    add_edge(anchor, defect.node_id, RelationshipType.RELATED_TO, 0.9)

        primary_node = next(
            (node for node in nodes.values() if node.label.upper() == primary_id),
            next(iter(nodes.values())),
        )
        if not is_structured:
            connected = {
                edge.source_id for edge in edges.values()
            } | {edge.target_id for edge in edges.values()}
            for node in tuple(nodes.values()):
                if node.node_id != primary_node.node_id and node.node_id not in connected:
                    add_edge(primary_node.node_id, node.node_id, RelationshipType.RELATED_TO, 0.75)

        return KnowledgeGraph(nodes.values(), edges.values())

    def persist(self, document: StoredDocument, graph: KnowledgeGraph) -> None:
        stored_nodes = {
            item.node_id: item
            for item in self.session.scalars(
                select(StoredGraphNode).where(
                    StoredGraphNode.node_id.in_(tuple(graph.nodes))
                )
            ).all()
        }
        for node in graph.nodes.values():
            properties = {**node.properties, "_aliases": list(node.aliases)}
            stored = stored_nodes.get(node.node_id)
            if stored is None:
                self.session.add(
                    StoredGraphNode(
                        node_id=node.node_id,
                        node_type=node.node_type.value,
                        name=node.label,
                        properties=properties,
                    )
                )
            else:
                stored.node_type = node.node_type.value
                stored.name = node.label
                stored.properties = {**(stored.properties or {}), **properties}
        self.session.flush()
        edge_keys = {
            (edge.source_id, edge.relationship.value, edge.target_id)
            for edge in graph.edges
        }
        existing_edges = {
            (item.source_node, item.relationship_type, item.target_node): item
            for item in self.session.scalars(select(StoredGraphEdge)).all()
            if (item.source_node, item.relationship_type, item.target_node) in edge_keys
        }
        for edge in graph.edges:
            properties = {**edge.properties, "strength": edge.strength}
            existing = existing_edges.get(
                (edge.source_id, edge.relationship.value, edge.target_id)
            )
            if existing is None:
                self.session.add(
                    StoredGraphEdge(
                        id=str(uuid.uuid4()),
                        source_node=edge.source_id,
                        relationship_type=edge.relationship.value,
                        target_node=edge.target_id,
                        source_document_id=document.id,
                        properties=properties,
                    )
                )
            else:
                existing.properties = properties

    def project_and_persist(self, document: StoredDocument) -> KnowledgeGraph:
        graph = self.project(document)
        self.persist(document, graph)
        return graph

    def backfill(self) -> KnowledgeGraph | None:
        # These tables are a derived, Graph RAG-owned projection. Rebuilding them
        # avoids stale relationships when extraction rules evolve.
        self.session.execute(delete(StoredGraphEdge))
        self.session.execute(delete(StoredGraphNode))
        self.session.flush()
        for document in self.session.scalars(select(StoredDocument)).all():
            self.project_and_persist(document)
        self.session.flush()
        return self.load()

    def load(self) -> KnowledgeGraph | None:
        stored_nodes = self.session.scalars(select(StoredGraphNode)).all()
        if not stored_nodes:
            return None
        nodes = []
        for item in stored_nodes:
            properties = dict(item.properties or {})
            aliases = tuple(properties.pop("_aliases", []))
            try:
                node_type = NodeType(item.node_type)
            except ValueError:
                node_type = NodeType.DOCUMENT
            nodes.append(GraphNode(item.node_id, node_type, item.name, properties, aliases))
        edges = []
        for item in self.session.scalars(select(StoredGraphEdge)).all():
            try:
                relationship = RelationshipType(item.relationship_type)
            except ValueError:
                relationship = RelationshipType.RELATED_TO
            edges.append(
                GraphEdge(
                    item.source_node,
                    item.target_node,
                    relationship,
                    float((item.properties or {}).get("strength", 0.9)),
                    dict(item.properties or {}),
                )
            )
        return KnowledgeGraph(nodes, edges)

    @staticmethod
    def sync_neo4j(graph: KnowledgeGraph) -> None:
        try:
            from database.graph.neo4j_client import get_neo4j_client

            client = get_neo4j_client()
            if client.verify_connectivity():
                client.upsert_knowledge_graph(graph)
        except Exception as exc:  # Neo4j is an optional secondary projection.
            logger.warning("Neo4j graph synchronization failed: %s", exc)


def load_uploaded_graph() -> KnowledgeGraph | None:
    """Load the latest uploaded-document projection for a retrieval request."""

    from database.postgres.connection import SessionLocal

    with SessionLocal() as session:
        return GraphProjectionService(session).load()
