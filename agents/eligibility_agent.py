from crewai import Agent
from typing import List, Dict, Any, Optional
from utils.sparql.sparql_query_builder import CourseQueryBuilder
from utils.sparql.sparql_tool import query_knowledge_graph

class EligibilityAgent():
    """Agent for checking course eligibility"""
    
    def __init__(self, query_builder: CourseQueryBuilder):
        self.query_builder = query_builder
    
    def create_agent(self) -> Agent:
        self.agent = Agent(
            role="Course Eligibility Specialist",
            goal="Determine which courses a student can take based on completed prerequisites",
            backstory="""You are an academic advisor expert who understands 
            prerequisite requirements and can determine course eligibility.""",
            tools=[query_knowledge_graph],  # Use the @tool function
            verbose=True
        )
        return self.agent
    
    def check_eligibility(self, completed_courses: List[str]) -> List[Dict]:
        """Check which courses the student is eligible for"""
        query = self.query_builder.check_eligibility_query(completed_courses)
        return query_knowledge_graph(query)  # Call the tool directly
