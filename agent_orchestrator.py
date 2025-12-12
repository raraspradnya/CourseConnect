# from crewai import Agent, Crew, Task
# from typing import List, Dict, Any, Optional
# from dotenv import load_dotenv
# import os

# from utils.sparql.sparql_tool import initialize_knowledge_graph
# from utils.sparql.sparql_query_builder import CourseQueryBuilder
# from agents.eligibility_agent import EligibilityAgent
# from agents.scheduler_agent import SchedulerAgent
# from agents.recommender_agent import RecommenderAgent
# from agents.prerequisite_agent import PrerequisiteAgent
# from agents.requirement_agent import RequirementAgent

# class CourseRecommenderSystem:
#     """Main system orchestrating all agents"""
    
#     def __init__(self, ttl_file_path: str):
#         # Initialize the knowledge graph
#         initialize_knowledge_graph(ttl_file_path)
        
#         # Initialize query builder
#         self.query_builder = CourseQueryBuilder()
        
#         # Initialize agents
#         self.eligibility_agent = EligibilityAgent(self.query_builder)
#         self.conflict_agent = SchedulerAgent(self.query_builder)
#         self.recommendation_agent = RecommenderAgent(self.query_builder)
#         self.prerequisite_agent = PrerequisiteAgent(self.query_builder)
#         self.requirement_agent = RequirementAgent(self.query_builder)
    
#     def get_prerequisites(self, course_id: str) -> List[Dict]:
#         """Get prerequisite chain"""
#         return self.prerequisite_agent.initiate_prerequisite_agent(course_id)
    
# # Example usage
# if __name__ == "__main__":

#     load_dotenv()
#     api_key = os.getenv("OPENAI_API_KEY")
#     system = CourseRecommenderSystem("knowledge-graph/S-KG/INFO-SKG.ttl")
    
#     # Check Prerequisites Courses
#     result = system.get_prerequisites("INFO 258")

from crewai import Agent, Crew, Task, Process
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import os

# --- NEW IMPORTS FOR SERVER ---
from flask import Flask, request, jsonify
from flask_cors import CORS

# Import custom tools and agents
from utils.sparql.sparql_tool import initialize_knowledge_graph
from utils.sparql.sparql_query_builder import CourseQueryBuilder
from agents.eligibility_agent import EligibilityAgent
from agents.scheduler_agent import SchedulerAgent
from agents.recommender_agent import RecommenderAgent
from agents.prerequisite_agent import PrerequisiteAgent
from agents.requirement_agent import RequirementAgent

# --- EXISTING AGENT LOGIC ---

class OrchestratorAgent:
    """
    Manager agent that analyzes user intent and routes tasks 
    to specialist agents dynamically.
    """
    def __init__(self):
        self.agent = Agent(
            role="Academic Advising Orchestrator",
            goal="Analyze student requests, determine intent, and delegate tasks to the correct specialist agents.",
            backstory="""You are the head academic advisor. You do not look up data yourself; 
            instead, you listen to the student, decide which specialist (Scheduler, Recommender, etc.) 
            is needed, and coordinate their work to provide a complete answer.""",
            allow_delegation=True,
            verbose=True,
            llm="gpt-4o"
        )

    def classify_intent(self, user_query: str) -> str:
        query_lower = user_query.lower()
        if "prereq" in query_lower or "chain" in query_lower:
            return "prerequisite_query"
        elif "schedule" in query_lower or "conflict" in query_lower:
            return "schedule_building"
        elif "recommend" in query_lower or "interest" in query_lower or "topic" in query_lower:
            return "course_discovery"
        elif "eligible" in query_lower or "can i take" in query_lower:
            return "check_eligibility"
        elif "requirement" in query_lower or "major" in query_lower:
            return "program_requirement"
        else:
            return "general_query"

class CourseRecommenderSystem:
    def __init__(self, ttl_file_path: str):
        initialize_knowledge_graph(ttl_file_path)
        self.query_builder = CourseQueryBuilder()
        self.orchestrator = OrchestratorAgent()
        self.eligibility_agent_wrapper = EligibilityAgent(self.query_builder)
        self.conflict_agent_wrapper = SchedulerAgent(self.query_builder)
        self.recommendation_agent_wrapper = RecommenderAgent(self.query_builder)
        self.prerequisite_agent_wrapper = PrerequisiteAgent(self.query_builder)
        self.requirement_agent_wrapper = RequirementAgent(self.query_builder)

    def create_workflow(self, intent: str, user_query: str, context_data: Dict = None) -> Crew:
        # [Same logic as your previous code]
        agents = []
        tasks = []
        
        if intent == "prerequisite_query":
            target_course = context_data.get("course_id", "INFO 206B") 
            prereq_agent = self.prerequisite_agent_wrapper.create_agent()
            agents.append(prereq_agent)
            task = Task(
                description=f"Analyze the prerequisite chain for course {target_course}.",
                agent=prereq_agent,
                expected_output="A detailed list of direct and indirect prerequisites."
            )
            tasks.append(task)

        elif intent == "schedule_building":
            elig_agent = self.eligibility_agent_wrapper.create_agent()
            agents.append(elig_agent)
            task_elig = Task(
                description=f"Identify courses eligible for student with history: {context_data.get('completed_courses')}.",
                agent=elig_agent,
                expected_output="A list of valid course codes."
            )
            tasks.append(task_elig)
            
            sched_agent = self.conflict_agent_wrapper.create_agent()
            agents.append(sched_agent)
            task_sched = Task(
                description="Check for time conflicts in the proposed list.",
                agent=sched_agent,
                expected_output="A validated schedule.",
                context=[task_elig]
            )
            tasks.append(task_sched)

        elif intent == "course_discovery":
            rec_agent = self.recommendation_agent_wrapper.create_agent()
            agents.append(rec_agent)
            task = Task(
                description=f"Find courses related to: {context_data.get('interests')}",
                agent=rec_agent,
                expected_output="A list of recommended courses."
            )
            tasks.append(task)
            
        else:
            return None

        return Crew(agents=agents, tasks=tasks, process=Process.sequential, verbose=True)

    def process_query(self, user_query: str, user_context: Dict[str, Any]) -> str:
        intent = self.orchestrator.classify_intent(user_query)
        print(f"--- Detected Intent: {intent} ---")
        crew = self.create_workflow(intent, user_query, user_context)
        
        if not crew:
            return "I'm sorry, I didn't understand that request."

        result = crew.kickoff()
        return str(result)

# --- FLASK SERVER SETUP ---

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes so frontend can connect

# Global variable for the system
recommender_system = None

@app.route('/api/query', methods=['POST'])
def handle_query():
    data = request.json
    user_query = data.get('query')
    
    # Mock context - in a real app, you'd get this from the session or frontend
    user_context = {
        "student_id": "123",
        "completed_courses": ["INFO 206A", "INFO 206B", "CS 61A"],
        "interests": ["Machine Learning", "Python", "Design"],
        "course_id": "INFO 258" 
    }
    
    try:
        response_text = recommender_system.process_query(user_query, user_context)
        return jsonify({"response": response_text})
    except Exception as e:
        print(f"Error processing query: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    load_dotenv()
    # Initialize the system once when server starts
    recommender_system = CourseRecommenderSystem("knowledge-graph/S-KG/INFO-SKG.ttl")
    
    print("Server starting on http://localhost:5000")
    app.run(debug=True, port=5000)