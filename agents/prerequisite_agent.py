from crewai import Agent, Task, Crew
from crewai.tools import tool
from typing import List, Dict, Optional
from rdflib import Namespace
import networkx as nx
import json

from utils.sparql.sparql_tool import query_knowledge_graph
from utils.sparql.sparql_query_builder import CourseQueryBuilder
from utils.sparql.sparql_prereq_tool import sparql_prerequisite_tool

class PrerequisiteAgent():
    """Agent for prerequisite chain discovery"""
    
    def __init__(self, query_builder: CourseQueryBuilder):
        self.query_builder = query_builder
        self.agent: Optional[Agent] = None
        self.sparql_results: Dict = {}

    # def create_agent(self) -> Agent:
    #     self.agent = Agent(
    #         role="SPARQL Knowledge Graph Specialist on Course Prerequisite Discovery",
    #         goal="Determine appropriate SPARQL queries for course information needs",
    #         backstory="""You are a SPARQL and RDF expert who understands how to query semantic 
    #         knowledge graphs for academic course information. You analyze what data is needed and 
    #         ensure the right SPARQL queries are executed.""",
    #         tools=[],
    #         verbose=True
    #     )
    #     return self.agent
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
    
    def get_course_details(self, course_code: str) -> Dict:
        """Get course name and code based on course ID"""
        query = self.query_builder.get_course_details_query(course_code)
        query_res = query_knowledge_graph.run(query)
        return query_res
    
    def get_course_prerequisites(self, course_code: str) -> List[Dict]:
        """Get list of course prerequisites, both direct and transitive, based on course ID"""
        
        strip_course_code = course_code.replace(" ", "")
        query = self.query_builder.get_prerequisites_query(strip_course_code)
        query_res = query_knowledge_graph.run(query)
        if not query_res:
            for courses in self.sparql_results['course_list']:
                if courses.get("course_code") == course_code:
                    courses["prerequisite_list"] = f"No prerequisites found for {course_code}."
        else:
            # Format results for agent explanation
            edges = []
            isolated_nodes = set()

            for row in query_res:
                prereq = str(row["prereq"])
                parent = row.get("directParent")

                if parent is not None:
                    edges.append((str(parent), prereq))     # parent → prereq
                else:
                    # No parent → must still be included in graph
                    isolated_nodes.add(prereq)

            G = nx.DiGraph()
            G.add_edges_from(edges)
            G.add_nodes_from(isolated_nodes)   # ensure parentless prereqs are included

            ordered_list = list(nx.topological_sort(G))

            for courses in self.sparql_results['course_list']:
                if courses.get("course_code") == course_code:
                    prereq_course_list_obj = courses.get("prerequisite_list")

            for idx, uri in enumerate(ordered_list, start=1):
                prereq_course_detail = self.get_course_details(uri)
                prereq_course_code = uri.split("/")[-1]
                if not prereq_course_detail:
                    prereq_course_list_obj.append({
                        "prerequisite_order": idx, 
                        "prerequisite_course_code": prereq_course_code, 
                        "prerequisite_course_name": "Unknown Course - No data available"})
                else:
                    prereq_course_list_obj.append({
                        "prerequisite_order": idx, 
                        "prerequisite_course_code": str(prereq_course_detail[0]["courseCode"]), 
                        "prerequisite_course_name": str(prereq_course_detail[0]["courseName"])})


    def sparql_query_callback(self, task_output):
        """Execute appropriate SPARQL queries based on detection"""
        output_text = str(task_output)
        
        # Parse detection results
        course_codes = []
        query_type = "general"
        
        if "COURSE_CODES:" in output_text:
            codes_line = output_text.split("COURSE_CODES:")[1].split("\n")[0].strip()
            course_codes = [code.strip() for code in codes_line.split(",")]
        
        if "QUERY_TYPE:" in output_text:
            query_type = output_text.split("QUERY_TYPE:")[1].split("\n")[0].strip().lower()
        
        print(f"\n📊 Executing SPARQL queries for: {course_codes}")
        print(f"📋 Query type: {query_type}")
        
        # Execute appropriate SPARQL queries based on query type
        if len(course_codes) == 1:
            course_code = course_codes[0]
            strip_course_code = course_code.replace(" ", "")
            EX = Namespace("http://example.org/")
            course_details = self.get_course_details(EX[strip_course_code])

            if self.sparql_results.get("course_list") == None:
                self.sparql_results["course_list"] = []

            if not course_details:
                self.sparql_results["course_list"].append({
                                                        "course_code":course_code,
                                                        "course_name":"Unknown Course: No data available ", 
                                                        "prerequisite_list":[]})
            else:
                self.sparql_results["course_list"].append({
                                                        "course_code":course_code,
                                                        "course_name":course_details[0]["courseName"], 
                                                        "prerequisite_list":[]})
            self.get_course_prerequisites(course_code)
        else:
            for course_code in course_codes:
                course_code = course_codes[0]
                strip_course_code = course_code.replace(" ", "")
                EX = Namespace("http://example.org/")
                course_details = self.get_course_details(EX[strip_course_code])

                if self.sparql_results.get("course_list") == None:
                    self.sparql_results["course_list"] = []

                if not course_details:
                    self.sparql_results["course_list"].append({
                                                            "course_code":course_code,
                                                            "course_name":"Unknown Course: No data available", 
                                                            "prerequisite_list":[]})
                else:
                    self.sparql_results["course_list"].append({
                                                            "course_code":course_code,
                                                            "course_name":course_details[0]["courseName"], 
                                                            "prerequisite_list":[]})
                self.get_course_prerequisites(course_code)

        # print(json.dumps(self.sparql_results, indent=2))
        
        # return json.dumps(self.sparql_results, indent=2)

    def sparql_callback(self, task_output):
        """
        Docstring for sparql_callback
        
        :param self: Description
        :param task_output: Description
        """
        self.sparql_query_callback(task_output)
        # print(result.get("course_list"))

        course_list = self.sparql_results["course_list"]

        explanation = ""
        for course in course_list:
            course_code = course["course_code"]
            course_name = course["course_name"]
            if course_name != "Unknown Course: No data available":
                explanation += (
                    f"To take the course:\n"
                    f"  {course_code} ({course_name})\n\n"
                    f"You must complete the following courses in order:\n\n")
                prereqs = course["prerequisite_list"]
                if prereqs != []:
                    for prereq in prereqs:
                        if prereq["prerequisite_course_name"] == "Unknown Course: No data available":
                            explanation += f"{prereq["prerequisite_order"]}. {prereq["prerequisite_course_code"]} - Unknown Course: No data available — please contact your department administrator.\n"
                        else:
                            explanation += f"{prereq["prerequisite_order"]}. {prereq["prerequisite_course_code"]} - {prereq["prerequisite_course_name"]}\n"
                else:
                    explanation += f"There is no prerequisite for this course.\n"
            else:
                explanation += (
                    f"The course {course_code} is not available in our database.\n"
                    f"Please contact your department administrator"
                )
            
        print(explanation)
        return explanation

    def create_task(self, user_query, agent, context):
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
            tools=[sparql_prerequisite_tool]
        )
        return synthesize_task

    # def create_task(self, agent, context):
    #     sparql_task = Task(
    #         description="""Based on detected course codes and query type, determine what 
    #         SPARQL queries should be executed against the RDF knowledge graph.
            
    #         The system will automatically execute appropriate queries:
    #         - Basic course info (always)
    #         - Prerequisites (if requested)
    #         - Prerequisite chain (if full chain requested)
    #         - Course offerings/schedule (if requested)
    #         - Related courses (if requested)
            
    #         Summarize what SPARQL queries were executed and what data was retrieved.""",
    #         agent=agent,
    #         expected_output="SPARQL query execution summary and results",
    #         context=context,
    #         # tools=[self.sparql_callback]
    #     )

    #     return sparql_task



    # def initiate_prerequisite_agent(self, course_code: str) -> str:
    #     """Initiate agent to explain prerequisite courses based on data fetched from KG"""

    #     if self.agent is None:
    #         self.create_agent()

    #     prerequisite_explanation = self.explain_course_prerequisites(course_code)

    #     task = Task(
    #         description=f"""
    #             You are an academic prerequisite validation assistant.
    #             You MUST use the provided prerequisite explanation exactly as given.
    #             DO NOT add new courses or make assumptions.
    #             Provided prerequisite explanation:\n
    #             {prerequisite_explanation}
    #             Your task is to rewrite this explanation cleanly and clearly for the user. 
    #             Preserve numbering and all details exactly.
    #         """,
    #         agent=self.agent,
    #         expected_output=(
    #             "Rewrite exactly what is provided in 'prerequisite_explanation'. "
    #             "Do NOT modify ordering, do NOT add new prerequisites, "
    #             "do NOT invent information. Simply present the explanation clearly."
    #         )
    #     )
    #     return task
    
    # def explain_course_prerequisites(self, course_code: str) -> str:
    #     """Get prerequisites and format raw data as context for agent"""

    #     # Fetch course details
    #     strip_course_code = course_code.replace(" ", "")
    #     EX = Namespace("http://example.org/")
    #     course_details = self.get_course_details(EX[strip_course_code])
    #     course_name = str(course_details[0]["courseName"])
    #     course_code = str(course_details[0]["courseCode"])
    #     if not course_details:
    #         return f"Unknown course. No data available - course {course_code} is not found in our system."
        
    #     # Fetch direct prerequisite 
    #     course_prereq_list = self.get_course_prerequisites(strip_course_code)
    #     if not course_prereq_list:
    #         return f"No prerequisites found for {course_code}."
    #     else:
    #         # Format results for agent explanation
    #         edges = []
    #         isolated_nodes = set()

    #         for row in course_prereq_list:
    #             prereq = str(row["prereq"])
    #             parent = row.get("directParent")
    #             print("row", row)
    #             print("prereq", prereq)
    #             print("parent", parent)


    #             if parent is not None:
    #                 edges.append((str(parent), prereq))     # parent → prereq
    #             else:
    #                 # No parent → must still be included in graph
    #                 isolated_nodes.add(prereq)

    #         G = nx.DiGraph()
    #         G.add_edges_from(edges)
    #         G.add_nodes_from(isolated_nodes)   # ensure parentless prereqs are included
    #         print("edges", G.edges)

    #         ordered_list = list(nx.topological_sort(G))
    #         print("ordered", ordered_list)
    #         explanation = (
    #                         f"To take the course:\n"
    #                         f"  {course_code} ({course_name})\n\n"
    #                         f"You must complete the following courses in order:\n\n"
    #                     )
    #         for idx, uri in enumerate(ordered_list, start=1):
    #             prereq_course_detail = self.get_course_details(uri)
    #             prereq_course_uri = uri.split("/")[-1]
    #             if not prereq_course_detail:
    #                 explanation += f"{idx}. {prereq_course_uri} - Unknown Course: No data available — please contact your department administrator.\n"
    #             else:
    #                 prereq_course_name = str(prereq_course_detail[0]["courseName"])
    #                 prereq_course_code = str(prereq_course_detail[0]["courseCode"])
    #                 explanation += f"{idx}. {prereq_course_code} - {prereq_course_name}\n"
    # #         return explanation
