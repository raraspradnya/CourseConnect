from crewai import Agent, Task, Crew
from typing import List, Dict, Optional
from rdflib import Namespace
import networkx as nx

from utils.sparql.sparql_tool import query_knowledge_graph
from utils.sparql.sparql_query_builder import CourseQueryBuilder

class PrerequisiteAgent():
    """Agent for prerequisite chain discovery"""
    
    def __init__(self, query_builder: CourseQueryBuilder):
        self.query_builder = query_builder
        self.agent: Optional[Agent] = None

    def create_agent(self) -> Agent:
        self.agent = Agent(
            role="Prerequisite Chain Analyst",
            goal="Discover and explain complete prerequisite chains for courses",
            backstory="""You are an academic planner who maps out the full 
            path of prerequisites students need to complete.""",
            tools=[],
            verbose=True
        )
        return self.agent
    
    def get_course_details(self, course_uri: str) -> Dict:
        """Get course name and code based on course ID"""
        query = self.query_builder.get_course_details_query(course_uri)
        return query_knowledge_graph.run(query)
    
    def get_course_prerequisites(self, course_id: str) -> List[Dict]:
        """Get list of course prerequisites, both direct and transitive, based on course ID"""
        query = self.query_builder.get_prerequisites_query(course_id)
        return query_knowledge_graph.run(query)
    
    def explain_course_prerequisites(self, course_id: str) -> str:
        """Get prerequisites and format raw data as context for agent"""

        # Fetch course details
        strip_course_id = course_id.replace(" ", "")
        EX = Namespace("http://example.org/")
        course_details = self.get_course_details(EX[strip_course_id])
        course_name = str(course_details[0]["courseName"])
        course_code = str(course_details[0]["courseCode"])
        if not course_details:
            return f"Unknown course. No data available - course {course_id} is not found in our system."
        
        # Fetch direct prerequisite 
        course_prereq_list = self.get_course_prerequisites(strip_course_id)
        if not course_prereq_list:
            return f"No prerequisites found for {course_id}."
        else:
            # Format results for agent explanation
            edges = []
            isolated_nodes = set()

            for row in course_prereq_list:
                prereq = str(row["prereq"])
                parent = row.get("directParent")
                print("row", row)
                print("prereq", prereq)
                print("parent", parent)


                if parent is not None:
                    edges.append((str(parent), prereq))     # parent → prereq
                else:
                    # No parent → must still be included in graph
                    isolated_nodes.add(prereq)

            G = nx.DiGraph()
            G.add_edges_from(edges)
            G.add_nodes_from(isolated_nodes)   # ensure parentless prereqs are included
            print("edges", G.edges)

            ordered_list = list(nx.topological_sort(G))
            print("ordered", ordered_list)
            explanation = (
                            f"To take the course:\n"
                            f"  {course_id} ({course_name})\n\n"
                            f"You must complete the following courses in order:\n\n"
                        )
            for idx, uri in enumerate(ordered_list, start=1):
                prereq_course_detail = self.get_course_details(uri)
                prereq_course_uri = uri.split("/")[-1]
                if not prereq_course_detail:
                    explanation += f"{idx}. {prereq_course_uri} - Unknown Course: No data available — please contact your department administrator.\n"
                else:
                    prereq_course_name = str(prereq_course_detail[0]["courseName"])
                    prereq_course_code = str(prereq_course_detail[0]["courseCode"])
                    explanation += f"{idx}. {prereq_course_code} - {prereq_course_name}\n"
            return explanation

    def initiate_prerequisite_agent(self, course_id: str) -> str:
        """Initiate agent to explain prerequisite courses based on data fetched from KG"""

        if self.agent is None:
            self.create_agent()

        prerequisite_explanation = self.explain_course_prerequisites(course_id)

        task = Task(
            description=f"""
                You are an academic prerequisite validation assistant.
                You MUST use the provided prerequisite explanation exactly as given.
                DO NOT add new courses or make assumptions.
                Provided prerequisite explanation:\n
                {prerequisite_explanation}
                Your task is to rewrite this explanation cleanly and clearly for the user. 
                Preserve numbering and all details exactly.
            """,
            agent=self.agent,
            expected_output=(
                "Rewrite exactly what is provided in 'prerequisite_explanation'. "
                "Do NOT modify ordering, do NOT add new prerequisites, "
                "do NOT invent information. Simply present the explanation clearly."
            )
        )

        crew = Crew(agents=[self.agent], tasks=[task])
        return crew.kickoff()