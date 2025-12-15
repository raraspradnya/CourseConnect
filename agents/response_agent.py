from crewai import Agent, Task
from typing import Optional

class ResponseAgent():
    """Agent for synthesizing response from RDF data and other relevant information"""
    
    def __init__(self):
        self.agent: Optional[Agent] = None

    def create_agent(self) -> Agent:
        self.agent = Agent(
            role="Response Synthesizer",
            goal="Synthesize RDF/SPARQL query results into clear, helpful responses",
            backstory="""You are an academic advisor who takes structured data from RDF knowledge graphs 
            and creates helpful, personalized responses for students.""",
            verbose=True,
            allow_delegation=False
        )
        return self.agent
    
    def create_task(self, user_query, agent, context, tools):
        """Create task based on data retrieved via SPARQL"""

        synthesize_task = Task(
            description=f"""Using the RDF data retrieved via SPARQL from the previous task,
            create a complete answer to: "{user_query}"
            
            Only use data that is provided. 
            DO NOT modify ordering, DO NOT add new prerequisite, DO NOT add new information.
            Simply present the information provided from the JSON to a student-friendly natural respond.

            Use this structured data to provide direct answer to their question and relevant context from the knowledge graph""",
            agent=agent,
            expected_output="Complete synthesized response",
            context=context, 
            tools=tools
        )

        return synthesize_task