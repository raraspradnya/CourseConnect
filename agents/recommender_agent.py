# from crewai import Agent
# from typing import List, Dict, Any, Optional
# from utils.sparql.sparql_query_builder import CourseQueryBuilder
# from utils.sparql.sparql_tool import query_knowledge_graph

# class RecommenderAgent():
#     """Agent for topic-based course recommendations"""

#     def __init__(self, query_builder: CourseQueryBuilder):
#         self.query_builder = query_builder
    
#     def create_agent(self) -> Agent:
#         self.agent = Agent(
#             role="Course Recommendation Specialist",
#             goal="Recommend courses based on student interests and topics",
#             backstory="""You are a curriculum advisor who matches student 
#             interests with relevant courses.""",
#             tools=[query_knowledge_graph],
#             verbose=True
#         )
#         return self.agent
    
#     def recommend_by_topics(self, topics: List[str]) -> List[Dict]:
#         """Recommend courses based on topics"""
#         query = self.query_builder.find_courses_by_topic_query(topics)
#         return query_knowledge_graph(query)

from crewai import Agent
from utils.sparql.sparql_tool import search_courses_by_topic
from utils.sparql.sparql_query_builder import CourseQueryBuilder

class RecommenderAgent():
    """Agent for topic-based course recommendations"""
    def __init__(self, query_builder: CourseQueryBuilder):
        self.query_builder = query_builder

    def create_agent(self) -> Agent:
        return Agent(
            role="Course Recommendation Specialist",
            goal="Identify courses that match the student's stated interests using the Knowledge Graph.",
            backstory="""You are an academic advisor specialist. Your job is to query the university 
            database to find courses that align with what a student is passionate about. 
            You look for keywords in course topics to make matches.""",
            tools=[search_courses_by_topic],
            verbose=True,
            allow_delegation=False
        )