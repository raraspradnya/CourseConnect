from crewai import Agent
from typing import List, Dict, Any, Optional
from utils.sparql.sparql_query_builder import CourseQueryBuilder
from utils.sparql.sparql_tool import query_knowledge_graph

class RecommenderAgent():
    """Agent for topic-based course recommendations"""

    def __init__(self, query_builder: CourseQueryBuilder):
        self.query_builder = query_builder
    
    def create_agent(self) -> Agent:
        self.agent = Agent(
            role="Course Recommendation Specialist",
            goal="Recommend courses based on student interests and topics",
            backstory="""You are a curriculum advisor who matches student 
            interests with relevant courses.""",
            tools=[query_knowledge_graph],
            verbose=True
        )
        return self.agent
    
    def recommend_by_topics(self, topics: List[str]) -> List[Dict]:
        """Recommend courses based on topics"""
        query = self.query_builder.find_courses_by_topic_query(topics)
        return query_knowledge_graph(query)
