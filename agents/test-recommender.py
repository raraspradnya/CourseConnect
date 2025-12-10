from crewai import Agent, Task, Crew, Process
from crewai.tools import BaseTool
import rdflib
import os


current_script_dir = os.path.dirname(os.path.abspath(__file__))
TTL_FILENAME = os.path.join(current_script_dir, "../knowledge-graph/S-KG/INFO-SKG.ttl")
TTL_FILENAME = os.path.abspath(TTL_FILENAME)

if not os.path.exists(TTL_FILENAME):
    print(f"❌ Error: The file was not found at: {TTL_FILENAME}")
    print(f"   Current Working Directory: {os.getcwd()}")
    print("   Absolute path looked for: " + os.path.abspath(TTL_FILENAME))
    exit()

g = rdflib.Graph()
g.parse(TTL_FILENAME, format="ttl")


class SearchCoursesTool(BaseTool):
    name: str = "Search Courses by Topic"
    description: str = "Useful for finding courses that match a specific topic of interest (e.g., 'AI', 'Design'). Returns course codes and names."

    def _run(self, topic: str) -> str:
        # SPARQL query
        query = f"""
        PREFIX ex: <http://example.org/>
        PREFIX schema: <https://schema.org/>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

        SELECT DISTINCT ?courseCode ?courseName ?topicLabel
        WHERE {{
            ?course a schema:Course ;
                    schema:courseCode ?courseCode ;
                    schema:name ?courseName ;
                    ex:hasTopics ?topicLabel .
            
            # Case-insensitive string matching
            FILTER(CONTAINS(LCASE(?topicLabel), LCASE("{topic}")))
        }}
        LIMIT 10
        """
        results = g.query(query)
        
        courses = []
        for row in results:
            courses.append({
                "code": str(row.courseCode),
                "name": str(row.courseName),
                "matched_topic": str(row.topicLabel)
            })
        
        if not courses:
            return f"No courses found specifically matching the topic '{topic}'."
        
        return str(courses)

search_tool = SearchCoursesTool()

recommender_agent = Agent(
    role='Recommendation Specialist',
    goal='Identify courses that match the student\'s stated interests using the Knowledge Graph.',
    backstory="""You are an academic advisor specialist. Your job is to query the university 
    database to find courses that align with what a student is passionate about. 
    You look for keywords in course topics to make matches.""",
    verbose=True,
    allow_delegation=False,
    tools=[search_tool]
)

def create_recommendation_task(student_interest):
    return Task(
        description=f"""
        1. Search the knowledge graph for courses related to the topic: '{student_interest}'.
        2. Identify the top relevant courses.
        3. Return a structured list of these courses including their Course Code and Name.
        """,
        expected_output="A list of JSON objects containing course_code, course_name, and the matching_topic.",
        agent=recommender_agent
    )


if __name__ == "__main__":
    user_interest = input("Enter a topic to search for (e.g., AI, Python, Design): ") or "AI"
    print(f"\n🚀 Starting Recommendation Agent for topic: {user_interest}...\n")

    task = create_recommendation_task(user_interest)

    crew = Crew(
        agents=[recommender_agent],
        tasks=[task],
        verbose=True,
        process=Process.sequential
    )

    result = crew.kickoff()

    print("\n\n########################")
    print("##   FINAL RESULT     ##")
    print("########################\n")
    print(result)