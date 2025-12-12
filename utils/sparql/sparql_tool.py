from rdflib import Graph
from typing import List, Dict, Any, Optional
from crewai.tools import tool
from .sparql_query_builder import CourseQueryBuilder 

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

@tool("Search Courses by Topic")
def search_courses_by_topic(topics_string: str) -> str:
    """
    Useful for finding courses that match specific topics of interest.
    Input should be a string of topics, optionally comma-separated (e.g., "AI" or "AI, Design").
    Returns course codes, names, and matched topics.
    """
    if _kg_instance is None:
        return "Error: Knowledge graph not initialized."
    
    # 1. Convert Agent's string input to List[str]
    # Splits "AI, Machine Learning" -> ["AI", "Machine Learning"]
    topics_list = [t.strip() for t in topics_string.split(',')]
    
    # 2. Use Builder to generate the correct SPARQL
    query = CourseQueryBuilder.find_courses_by_topic_query(topics_list)
    
    if not query:
        return "Error: No valid topics provided."

    # 3. Execute against the Graph
    results = _kg_instance.execute_query(query)
    
    # 4. Return results
    if not results:
        return f"No courses found specifically matching the topics: {topics_list}."
    return str(results)
