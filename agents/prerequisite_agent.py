from crewai import Agent
from typing import List, Dict, Any, Optional
from utils.sparql.sparql_tool import query_knowledge_graph
from utils.sparql.sparql_query_builder import CourseQueryBuilder

class PrerequisiteAgent():
    """Agent for prerequisite chain discovery"""
    
    def __init__(self, query_builder: CourseQueryBuilder):
        self.query_builder = query_builder

    def create_agent(self) -> Agent:
        self.agent = Agent(
            role="Prerequisite Chain Analyst",
            goal="Discover and explain complete prerequisite chains for courses",
            backstory="""You are an academic planner who maps out the full 
            path of prerequisites students need to complete.""",
            tools=[query_knowledge_graph],
            verbose=True
        )
        return self.agent
    
    def get_prerequisite_chain(self, course_id: str) -> List[Dict]:
        """Get full prerequisite chain"""
        query = self.query_builder.get_prerequisite_chain_query(course_id)
        return query_knowledge_graph(query)
