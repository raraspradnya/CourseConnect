from crewai import Agent, Crew, Task
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import os

from utils.sparql.sparql_tool import initialize_knowledge_graph
from utils.sparql.sparql_query_builder import CourseQueryBuilder
from agents.eligibility_agent import EligibilityAgent
from agents.scheduler_agent import SchedulerAgent
from agents.recommender_agent import RecommenderAgent
from agents.prerequisite_agent import PrerequisiteAgent
from agents.requirement_agent import RequirementAgent

class CourseRecommenderSystem:
    """Main system orchestrating all agents"""
    
    def __init__(self, ttl_file_path: str):
        # Initialize the knowledge graph
        initialize_knowledge_graph(ttl_file_path)
        
        # Initialize query builder
        self.query_builder = CourseQueryBuilder()
        
        # Initialize agents
        self.eligibility_agent = EligibilityAgent(self.query_builder)
        self.conflict_agent = SchedulerAgent(self.query_builder)
        self.recommendation_agent = RecommenderAgent(self.query_builder)
        self.prerequisite_agent = PrerequisiteAgent(self.query_builder)
        self.requirement_agent = RequirementAgent(self.query_builder)
    
    def get_prerequisites(self, course_id: str) -> List[Dict]:
        """Get prerequisite chain"""
        return self.prerequisite_agent.initiate_prerequisite_agent(course_id)
    
# Example usage
if __name__ == "__main__":

    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    system = CourseRecommenderSystem("knowledge-graph/S-KG/INFO-SKG.ttl")
    
    # Check Prerequisites Courses
    result = system.get_prerequisites("INFO 258")