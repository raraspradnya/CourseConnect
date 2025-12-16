from crewai import Agent, Task
from typing import Optional

class ExtractorAgent():
    """Agent for extract details from user query"""
    
    def __init__(self):
        self.agent: Optional[Agent] = None

    def create_agent(self) -> Agent:
        self.agent = Agent(
            role="Course Code Detector",
            goal="Extract and identify course codes from user queries accurately",
            backstory="""You are an expert at identifying academic course codes from natural language queries. 
            Course codes typically follow patterns like:
            - Department abbreviation (4-6 letters) followed by numbers (e.g., CS 101, INFO 271B, MATH 1A)
            - May include letters after numbers (e.g., 271A, 101L)
            - May have spaces or no spaces between department and number
            
            You must extract ALL course codes from the query and return them in a structured format.""",
            tools=[],
            verbose=True, 
            allow_delegation=False
        )
        return self.agent
    
    def create_task(self, user_query, agent):
        """Initiate agent to extract course code based on user query"""

        course_id_task = Task(
            description=f"""Analyze the following user query and extract any course codes present:
        
            Query: "{user_query}"
            
            Your response MUST be in this exact format:
            COURSE_CODES: [list all detected course codes separated by commas]
            QUERY_TYPE: [what type of question is being asked - e.g., prerequisite, description, schedule, etc.]
            
            Example response format:
            COURSE_CODES: INFO 271B
            QUERY_TYPE: prerequisite
            
            If no course codes are found, respond with:
            COURSE_CODES: NONE
            QUERY_TYPE: [query type]
            """,
            agent=agent,
            expected_output="Course codes and query type in the specified format",
        )

        return course_id_task