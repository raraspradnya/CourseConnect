from crewai import Agent
from typing import List, Dict, Any, Optional
from utils.sparql.sparql_tool import query_knowledge_graph
from utils.sparql.sparql_query_builder import CourseQueryBuilder

class SchedulerAgent():
    """Agent for detecting schedule conflicts"""
    
    def __init__(self, query_builder: CourseQueryBuilder):
        self.query_builder = query_builder
    
    def create_agent(self) -> Agent:
        self.agent = Agent(
            role="Schedule Conflict Detector",
            goal="Identify time conflicts in proposed course schedules",
            backstory="""You are a scheduling expert who can analyze course 
            timetables and identify conflicts.""",
            tools=[query_knowledge_graph],
            verbose=True
        )
        return self.agent
    
    def detect_conflicts(self, course_ids: List[str]) -> List[Dict]:
        """Check for time conflicts in schedule"""
        query = self.query_builder.check_time_conflicts_query(course_ids)
        return query_knowledge_graph(query)