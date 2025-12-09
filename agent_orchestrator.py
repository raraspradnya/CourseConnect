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
        
        # Initialize agents (they all use the @tool function)
        self.eligibility_agent = EligibilityAgent(self.query_builder)
        self.conflict_agent = SchedulerAgent(self.query_builder)
        self.recommendation_agent = RecommenderAgent(self.query_builder)
        self.prerequisite_agent = PrerequisiteAgent(self.query_builder)
        self.requirement_agent = RequirementAgent(self.query_builder)
    
    def check_eligibility(self, completed_courses: List[str]):
        """Task 1: Check course eligibility"""
        agent = self.eligibility_agent.create_agent()
        task = Task(
            description=f"Find all courses eligible for a student who completed: {completed_courses}",
            agent=agent,
            expected_output="List of eligible courses with names"
        )
        crew = Crew(agents=[agent], tasks=[task])
        return crew.kickoff()
    
    def detect_conflicts(self, proposed_schedule: List[str]):
        """Task 2: Detect schedule conflicts"""
        agent = self.conflict_agent.create_agent()
        task = Task(
            description=f"Check for time conflicts in schedule: {proposed_schedule}",
            agent=agent,
            expected_output="List of conflicting courses if any"
        )
        crew = Crew(agents=[agent], tasks=[task])
        return crew.kickoff()
    
    # Add similar methods for other functionalities...


# Example usage
if __name__ == "__main__":

    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    system = CourseRecommenderSystem("knowledge-graph/S-KG/INFO-SKG.ttl")
    
    # Check eligibility
    result = system.check_eligibility(["INFO101", "CS150"])
    print(result)
    
    # Detect conflicts
    conflicts = system.detect_conflicts(["INFO206A", "CS266", "INFO253"])
    print(conflicts)