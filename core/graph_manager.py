"""Manage Neo4j knowledge graph and relationships."""

import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class GraphNode:
    """Node in knowledge graph."""
    id: str
    label: str
    properties: Dict
    created_at: datetime
    updated_at: datetime


@dataclass
class GraphRelationship:
    """Relationship between nodes."""
    source_id: str
    target_id: str
    relationship_type: str
    properties: Dict
    confidence: float
    created_at: datetime


class GraphManager:
    """Manages Neo4j knowledge graph."""

    def __init__(self, config: Dict):
        self.config = config
        self.driver = None
        self.connection_uri = config.get("neo4j_uri", "bolt://localhost:7687")
        self.username = config.get("neo4j_user", "neo4j")
        self.password = config.get("neo4j_password", "")
        self._initialize_connection()

    def _initialize_connection(self) -> None:
        """Initialize Neo4j driver."""
        try:
            from neo4j import GraphDatabase
            self.driver = GraphDatabase.driver(
                self.connection_uri,
                auth=(self.username, self.password)
            )
            logger.info("Neo4j connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {str(e)}")

    def add_node(self, entity_id: str, label: str, properties: Dict) -> bool:
        """Add or update a node in the graph."""
        try:
            with self.driver.session() as session:
                query = """
                MERGE (n {id: $id})
                SET n.label = $label
                SET n.properties = $properties
                SET n.updated_at = datetime()
                RETURN n
                """
                result = session.run(query, id=entity_id, label=label, properties=properties)
                return result.consume().summary.counters.nodes_created > 0 or True
        except Exception as e:
            logger.error(f"Failed to add node: {str(e)}")
            return False

    def add_relationship(
        self,
        source_id: str,
        target_id: str,
        relationship_type: str,
        properties: Dict,
        confidence: float = 1.0
    ) -> bool:
        """Add a relationship between two nodes."""
        try:
            with self.driver.session() as session:
                query = f"""
                MATCH (source {{id: $source_id}})
                MATCH (target {{id: $target_id}})
                MERGE (source)-[r:{relationship_type}]->(target)
                SET r.properties = $properties
                SET r.confidence = $confidence
                SET r.created_at = datetime()
                RETURN r
                """
                result = session.run(
                    query,
                    source_id=source_id,
                    target_id=target_id,
                    properties=properties,
                    confidence=confidence
                )
                return result.consume().summary.counters.relationships_created > 0 or True
        except Exception as e:
            logger.error(f"Failed to add relationship: {str(e)}")
            return False

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """Retrieve a node from the graph."""
        try:
            with self.driver.session() as session:
                query = "MATCH (n {id: $id}) RETURN n"
                result = session.run(query, id=node_id)
                record = result.single()
                
                if record:
                    node_data = record['n']
                    return GraphNode(
                        id=node_id,
                        label=node_data.get('label', ''),
                        properties=dict(node_data),
                        created_at=node_data.get('created_at', datetime.now()),
                        updated_at=node_data.get('updated_at', datetime.now())
                    )
                return None
        except Exception as e:
            logger.error(f"Failed to get node: {str(e)}")
            return None

    def find_connected_nodes(self, node_id: str, depth: int = 2) -> List[Tuple[str, str, float]]:
        """Find all nodes connected to a given node."""
        try:
            with self.driver.session() as session:
                query = f"""
                MATCH (start {{id: $id}})-[r*1..{depth}]-(connected)
                RETURN connected.id, type(r), avg(r.confidence)
                """
                result = session.run(query, id=node_id)
                
                connections = []
                for record in result:
                    connections.append((
                        record[0],
                        record[1],
                        record[2] or 1.0
                    ))
                return connections
        except Exception as e:
            logger.error(f"Failed to find connected nodes: {str(e)}")
            return []

    def find_shortest_path(self, start_id: str, end_id: str) -> Optional[List[str]]:
        """Find shortest path between two nodes."""
        try:
            with self.driver.session() as session:
                query = """
                MATCH path = shortestPath(
                    (start {id: $start_id})-[*]-(end {id: $end_id})
                )
                RETURN [node.id IN nodes(path)]
                """
                result = session.run(query, start_id=start_id, end_id=end_id)
                record = result.single()
                
                if record:
                    return record[0]
                return None
        except Exception as e:
            logger.error(f"Failed to find shortest path: {str(e)}")
            return None

    def detect_clusters(self, min_size: int = 3) -> List[List[str]]:
        """Detect clusters/communities in the graph."""
        try:
            with self.driver.session() as session:
                # Using label propagation algorithm
                query = """
                CALL algo.labelPropagation.stream()
                YIELD nodeId, label
                WITH label, collect(algo.getNodeById(nodeId).id) as nodes
                WHERE size(nodes) >= $min_size
                RETURN nodes
                """
                result = session.run(query, min_size=min_size)
                
                clusters = []
                for record in result:
                    clusters.append(record[0])
                return clusters
        except Exception as e:
            logger.error(f"Failed to detect clusters: {str(e)}")
            return []

    def get_graph_statistics(self) -> Dict:
        """Get overall graph statistics."""
        try:
            with self.driver.session() as session:
                result = session.run("""
                MATCH (n) RETURN count(n) as node_count
                """)
                node_count = result.single()[0] if result.single() else 0
                
                result = session.run("""
                MATCH ()-[r]->() RETURN count(r) as rel_count
                """)
                rel_count = result.single()[0] if result.single() else 0
                
                return {
                    "nodes": node_count,
                    "relationships": rel_count,
                    "density": rel_count / (node_count * (node_count - 1)) if node_count > 1 else 0
                }
        except Exception as e:
            logger.error(f"Failed to get statistics: {str(e)}")
            return {}

    def close(self) -> None:
        """Close Neo4j connection."""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")
