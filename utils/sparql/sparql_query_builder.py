from typing import List

class CourseQueryBuilder:
    """Builds domain-specific SPARQL queries"""
    
    @staticmethod
    def get_prerequisites_query(course_id: str) -> str:
        """Get all prerequisites for a course"""
        return f"""
        PREFIX course: <http://example.org/course#>
        SELECT ?prereq ?prereqName
        WHERE {{
            <{course_id}> course:requires ?prereq .
            ?prereq course:name ?prereqName .
        }}
        """
    
    @staticmethod
    def get_prerequisite_chain_query(course_id: str) -> str:
        """Get full prerequisite chain (transitive)"""
        return f"""
        PREFIX course: <http://example.org/course#>
        SELECT ?prereq ?prereqName
        WHERE {{
            <{course_id}> course:requires+ ?prereq .
            ?prereq course:name ?prereqName .
        }}
        """
    
    @staticmethod
    def check_eligibility_query(completed_courses: List[str]) -> str:
        """Find courses where all prerequisites are met"""
        completed_filter = ', '.join([f'<{c}>' for c in completed_courses])
        return f"""
        PREFIX course: <http://example.org/course#>
        SELECT ?course ?courseName
        WHERE {{
            ?course a course:Course ;
                    course:name ?courseName .
            OPTIONAL {{
                ?course course:requires ?prereq .
                FILTER(?prereq NOT IN ({completed_filter}))
            }}
            FILTER(!BOUND(?prereq))
        }}
        """
    
    @staticmethod
    def check_time_conflicts_query(course_ids: List[str]) -> str:
        """Check for schedule conflicts between courses"""
        return f"""
        PREFIX schedule: <http://example.org/schedule#>
        PREFIX course: <http://example.org/course#>
        SELECT ?course1 ?course2 ?day ?time
        WHERE {{
            ?course1 schedule:day ?day ;
                     schedule:time ?time ;
                     a course:Course .
            ?course2 schedule:day ?day ;
                     schedule:time ?time ;
                     a course:Course .
            FILTER(?course1 < ?course2)
            FILTER(?course1 IN ({', '.join([f'<{c}>' for c in course_ids])}))
            FILTER(?course2 IN ({', '.join([f'<{c}>' for c in course_ids])}))
        }}
        """
    
    @staticmethod
    def find_courses_by_topic_query(topics: List[str]) -> str:
        """Find courses related to specific topics"""
        topic_filter = '|'.join(topics)
        return f"""
        PREFIX course: <http://example.org/course#>
        SELECT ?course ?courseName ?topic
        WHERE {{
            ?course course:name ?courseName ;
                    course:topic ?topic .
            FILTER(REGEX(?topic, "{topic_filter}", "i"))
        }}
        """
    
    @staticmethod
    def get_major_requirements_query(major: str) -> str:
        """Get courses that fulfill major requirements"""
        return f"""
        PREFIX program: <http://example.org/program#>
        PREFIX course: <http://example.org/course#>
        SELECT ?course ?courseName ?requirement
        WHERE {{
            ?major a program:Major ;
                   program:name "{major}" ;
                   program:requires ?requirement .
            ?requirement program:satisfiedBy ?course .
            ?course course:name ?courseName .
        }}
        """

