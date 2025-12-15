from crewai.tools import tool
from typing import Dict, List
from rdflib import Namespace
import networkx as nx

from utils.sparql.sparql_tool import query_knowledge_graph
from utils.sparql.sparql_query_builder import CourseQueryBuilder


@tool("sparql_prerequisite_tool")
def sparql_prerequisite_tool(task_output: str) -> str:
    """
    Executes SPARQL queries to retrieve course prerequisites
    and returns a student-friendly explanation.
    """

    query_builder = CourseQueryBuilder()
    sparql_results: Dict = {"course_list": []}

    output_text = str(task_output)
    # print(output_text)

    # -------------------------------
    # Parse task output
    # -------------------------------
    course_codes = [output_text]
    # if "COURSE_CODES:" in output_text:
    #     codes_line = output_text.split("COURSE_CODES:")[1].split("\n")[0].strip()
        # course_codes = [code.strip() for code in codes_line.split(",")]

    EX = Namespace("http://example.org/")

    # -------------------------------
    # Helper functions (local)
    # -------------------------------
    def get_course_details(course_uri):
        query = query_builder.get_course_details_query(course_uri)
        return query_knowledge_graph.run(query)

    def get_course_prerequisites(course_code):
        strip_code = course_code.replace(" ", "")
        query = query_builder.get_prerequisites_query(strip_code)
        query_res = query_knowledge_graph.run(query)

        edges = []
        isolated_nodes = set()

        for row in query_res or []:
            prereq = str(row["prereq"])
            parent = row.get("directParent")
            if parent:
                edges.append((str(parent), prereq))
            else:
                isolated_nodes.add(prereq)

        G = nx.DiGraph()
        G.add_edges_from(edges)
        G.add_nodes_from(isolated_nodes)

        ordered = list(nx.topological_sort(G))

        prereq_list = []
        for idx, uri in enumerate(ordered, start=1):
            details = get_course_details(uri)
            prereq_list.append({
                "prerequisite_order": idx,
                "prerequisite_course_code": uri.split("/")[-1],
                "prerequisite_course_name":
                    details[0]["courseName"] if details else "Unknown Course: No data available"
            })
        return prereq_list

    # -------------------------------
    # Execute logic
    # -------------------------------
    for course_code in course_codes:
        course_uri = EX[course_code.replace(" ", "")]
        details = get_course_details(course_uri)

        course_entry = {
            "course_code": course_code,
            "course_name":
                details[0]["courseName"] if details else "Unknown Course: No data available",
            "prerequisite_list": []
        }

        if details:
            course_entry["prerequisite_list"] = get_course_prerequisites(course_code)

        sparql_results["course_list"].append(course_entry)

    # -------------------------------
    # Build explanation
    # -------------------------------
    explanation = ""

    for course in sparql_results["course_list"]:
        explanation += f"\nTo take the course:\n"
        explanation += f"  {course['course_code']} ({course['course_name']})\n\n"

        if course["prerequisite_list"]:
            explanation += "You must complete the following courses in order:\n\n"
            for p in course["prerequisite_list"]:
                explanation += (
                    f"{p['prerequisite_order']}. "
                    f"{p['prerequisite_course_code']} - "
                    f"{p['prerequisite_course_name']}\n"
                )
        else:
            explanation += "There is no prerequisite for this course.\n"
    print("explanation", explanation)
    return explanation
