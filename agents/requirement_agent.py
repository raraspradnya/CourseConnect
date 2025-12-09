from crewai import Agent
from typing import List, Dict, Any, Optional
from utils.sparql.sparql_tool import query_knowledge_graph
from utils.sparql.sparql_query_builder import CourseQueryBuilder

class RequirementAgent():
    """Agent for program requirement fulfillment"""
    
    def __init__(self, query_builder: CourseQueryBuilder):
        self.query_builder = query_builder

    def create_agent(self) -> Agent:
        self.agent = Agent(
            role="Program Requirement Advisor",
            goal="Match courses to major and degree requirements",
            backstory="""You are a degree audit specialist who knows program 
            requirements and which courses satisfy them.""",
            tools=[query_knowledge_graph],
            verbose=True
        )
        return self.agent
    
    def get_requirement_courses(self, major: str) -> List[Dict]:
        """Get courses that satisfy major requirements"""
        query = self.query_builder.get_major_requirements_query(major)
        return query_knowledge_graph(query)
