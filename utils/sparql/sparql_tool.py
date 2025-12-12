from rdflib import Graph
from typing import List, Dict, Any, Optional
from crewai.tools import tool

class SPARQLKnowledgeGraph:
    """Manages SPARQL queries against the knowledge graph"""
    
    def __init__(self, ttl_file_path: str):
        self.graph = Graph()
        try:
            self.graph.parse(ttl_file_path, format='ttl')
        except Exception as e:
            raise RuntimeError(f"Failed to load TTL file at {ttl_file_path}: {e}")
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """Execute a SPARQL query and return results"""
        try:
            results = self.graph.query(query)
            return [dict(row.asdict()) for row in results]
        except Exception as e:
            return [{"error": str(e)}]
        

# Create a global instance (will be initialized in main)
_kg_instance = None

def initialize_knowledge_graph(ttl_file_path: str):
    """Initialize the knowledge graph instance"""
    global _kg_instance
    _kg_instance = SPARQLKnowledgeGraph(ttl_file_path)

@tool("Query Knowledge Graph")
def query_knowledge_graph(query: str) -> List[Dict[str, Any]]:
    """
    Execute a SPARQL query against the course knowledge graph.
    
    Args:
        query: A SPARQL query string
    
    Returns:
        List of dictionaries containing query results
    """
    if _kg_instance is None:
        return [{"error": "Knowledge graph not initialized"}]
    return _kg_instance.execute_query(query)
