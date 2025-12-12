from crewai import Agent, Task, Crew
from typing import List, Dict, Optional
from rdflib import Namespace

from utils.sparql.sparql_tool import query_knowledge_graph
from utils.sparql.sparql_query_builder import CourseQueryBuilder

class SchedulerAgent():
    """Agent for detecting schedule conflicts"""
    
    def __init__(self, query_builder: CourseQueryBuilder):
        self.query_builder = query_builder
        self.agent: Optional[Agent] = None
    
    def create_agent(self) -> Agent:
        self.agent = Agent(
            role="Schedule Conflict Detector",
            goal="Identify time conflicts in proposed course schedules",
            backstory="""You are a scheduling expert who can analyze course 
            timetables and identify conflicts.""",
            tools=[],
            verbose=True
        )
        return self.agent
    
    def get_course_details(self, course_uri: str) -> Dict:
        """Get course name and code based on course ID"""
        query = self.query_builder.get_course_details_query(course_uri)
        return query_knowledge_graph.run(query)
    
    def detect_conflicts(self, course_ids: List[str], semester: str) -> List[Dict]:
        """Check for time conflicts in schedule"""
        query = self.query_builder.check_time_conflicts_query(course_ids, semester)
        results = query_knowledge_graph.run(query)

        conflicts = []
        for r in results:
            conflicts.append({
                "course1": str(r.course1Name),
                "course2": str(r.course2Name),
                "semester": str(r.semester),
                "day": r.day.split("#")[-1],
                "course1_start": str(r.start1),
                "course1_end": str(r.end1),
                "course2_start": str(r.start2),
                "course2_end": str(r.end2),
            })

        # If no conflicts: return structure for agent
        if not conflicts:
            return {
                "conflicts": [],
                "message": "No schedule conflicts detected for the selected semester."
            }

        return {"conflicts": conflicts}
        
    
    def explain_conflicts(self, course_ids: List[str], semester: str) -> str:
        """Generate a student-friendly explanation of detected conflicts"""

        # Friendly header
        intro = (
            f"You asked to check schedule conflicts for the following courses "
            f"in semester **{semester}**:\n"
        )

        # Fetch course names for user-friendly output
        for course_id in course_ids:
            strip_course_id = course_id.replace(" ", "")
            EX = Namespace("http://example.org/")
            course_details = self.get_course_details(EX[strip_course_id])
            if not course_details:
                return ( "We don't have schedule information for one or more of these courses."
                "Please contact your department for clarification.")
            else:
                course_name = str(course_details[0]["courseName"])
                intro += f"- {course_id} : {course_name}\n"
        
        conflict_result = self.detect_conflicts(course_ids, semester)
        conflicts = conflict_result.get("conflicts", [])

        # No conflicts found
        if not conflicts:
            return intro + "Good news! There are **no schedule conflicts** among these courses."

        # Conflicts exist — list them
        messages = [intro + "I found the following schedule conflicts:\n"]

        for c in conflicts:
            messages.append(
                f"\n• **{c['course1']}** and **{c['course2']}** conflict in **{c['semester']}**:\n"
                f"  - Both meet on **{c['day']}**.\n"
                f"  - {c['course1']} meets **{c['course1_start']}-{c['course1_end']}**.\n"
                f"  - {c['course2']} meets **{c['course2_start']}-{c['course2_end']}**.\n"
                f"  → These times overlap, so you cannot take them together."
            )
        return "\n".join(messages)

    def initiate_scheduler_agent(self, course_ids: str, semester: str) -> str:
        """Initiate agent to validate schedule based on course IDs and semester"""

        if self.agent is None:
            self.create_agent()
        
        conflict_explanation = self.explain_conflicts(course_ids, semester)

        task = Task(
            description=f"""
                You are an academic course-planning assistant.            
                Your job is:
                1. Re-state what courses that is being validated, and what semester we are checking these courses in 
                2. Explain clearly whether there are conflicts between the list of courses for a semester. 
                3. If conflicts exist, explain:
                    - Which courses conflict
                    - On what days
                    - What time ranges overlap
                4. Use simple student-friendly language.
                5. Suggest possible next steps (e.g., pick another section).

                If no conflicts:
                Say: "Good news — no conflicts found for this semester."

                If data is missing:
                Say: "We do not have schedule information for one or more courses. Please contact your department."

                Never output raw URIs. Always use course names.
                You MUST use the provided explanation exactly as given.
                Conflict explanation:\n
                {conflict_explanation}
                Your task is to rewrite this explanation cleanly and clearly for the user. 
                Preserve all details exactly. DO NOT add new courses or make assumptions.
            """,
            agent=self.agent,
            expected_output=(
                "Rephrase information that is provided in 'conflict_explanation'. "
                "do NOT invent information. Simply present the explanation clearly."
            )
        )

        crew = Crew(agents=[self.agent], tasks=[task])
        return crew.kickoff()