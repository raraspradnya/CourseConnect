from typing import List, Union

class CourseQueryBuilder:
    """Builds domain-specific SPARQL queries"""
    
    @staticmethod
    def get_course_details_query(course_uri: str) -> str:
        """Get course name and code based on course URI"""
        return f"""
        PREFIX ex: <http://example.org/>
        PREFIX schema: <http://schema.org/>
        SELECT ?courseName ?courseCode
        WHERE {{
            <{course_uri}> schema:name ?courseName .
            <{course_uri}> schema:courseCode ?courseCode .
        }}
        """
    
    @staticmethod
    def get_prerequisites_query(course_id: str) -> str:
        """Get all direct prerequisites for a course"""
        return f"""
        PREFIX ex: <http://example.org/>
        PREFIX schema: <http://schema.org/>
        SELECT DISTINCT ?prereq ?directParent
        WHERE {{
            VALUES ?target {{ ex:{course_id} }}

            # Reachable prereqs (direct + indirect)
            ?target (ex:hasPrerequisite)+ ?prereq .

            # Get who that prereq depends on
            OPTIONAL {{
                ?prereq (ex:hasPrerequisite) ?directParent .
            }}
        }}
        """
    
    @staticmethod
    def check_eligibility_query(completed_courses: List[str]) -> str:
        """
        Find courses where all prerequisites are met.
        completed_courses should be course IDs like ['INFO101', 'INFO206B']
        """
        # Build the filter for completed courses
        completed_filter = ', '.join([f'ex:{c}' for c in completed_courses])
        
        return f"""
        PREFIX ex: <http://example.org/>
        PREFIX schema: <http://schema.org/>
        SELECT DISTINCT ?course ?courseName ?courseCode
        WHERE {{
            ?course a schema:Course ;
                    schema:name ?courseName ;
                    schema:courseCode ?courseCode .
            
            # Check if course has prerequisites
            OPTIONAL {{
                ?course ex:hasPrerequisite ?prereq .
                # If there's a prerequisite not in completed list, bind it
                FILTER(?prereq NOT IN ({completed_filter}))
            }}
            # Only return courses where no unmet prerequisites were found
            FILTER(!BOUND(?prereq))
        }}
        ORDER BY ?courseCode
        """
    
    # # Alternative approach to check eligibility, commented out for now
    # @staticmethod
    # def check_eligibility_query(completed_courses: List[str]) -> str:
    #     """
    #     Find courses where all prerequisites are met.
    #     completed_courses should be course IDs like ['INFO101', 'INFO206B']
    #     """
    #     # Build the filter for completed courses
    #     if not completed_courses:
    #         # If no courses taken, simple NOT IN isn't needed; 
    #         # we just look for courses with NO prerequisites.
    #         completed_filter = "" 
    #     else:
    #         # Format: ex:INFO101, ex:INFO206B
    #         completed_list_str = ', '.join([f'ex:{c}' for c in completed_courses])
    #         completed_filter = f"FILTER (?prereq IN ({completed_list_str}))"

    #     return f"""
    #     PREFIX ex: <http://example.org/>
    #     PREFIX schema: <http://schema.org/>

    #     SELECT DISTINCT ?course ?courseName ?courseCode
    #     WHERE {{
    #         ?course a schema:Course ;
    #                 schema:name ?courseName ;
    #                 schema:courseCode ?courseCode .

    #         # LOGIC: Exclude any course that HAS a prerequisite 
    #         # which the student has NOT taken.
    #         FILTER NOT EXISTS {{
    #             ?course ex:hasPrerequisite ?prereq .
    #             # If the student HAS taken this prereq, we don't want to exclude the course.
    #             # We only exclude if the prereq exists AND is NOT in the completed list.
                
    #             {completed_filter} if {completed_courses} else "ex:ImpossibleCourse"))
    #         }}
    #     }}
    #     ORDER BY ?courseCode
    #     """
    
    @staticmethod
    def check_time_conflicts_query(course_ids: List[str], semester: str) -> str:
        """
        Check for schedule conflicts between courses.
        Only returns conflicting pairs.
        """
        course_filter = ' '.join([f'ex:{c}' for c in course_ids])
        semester_filter = "\"" + semester +"\"^^xsd:string"
        
        return f"""
        PREFIX ex: <http://example.org/>
        PREFIX schema: <http://schema.org/>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

        # Check for time conflicts among a list of courses
        SELECT 
            ?course1 ?course1Name
            ?course2 ?course2Name
            ?semester
            ?comp1 ?comp2
            ?day
            ?start1 ?end1
            ?start2 ?end2
        WHERE {{
            # User input: list of courses
            VALUES ?course1 { {course_filter} }
            VALUES ?course2 { {course_filter} }
            FILTER(STR(?course1) < STR(?course2))

            # User input: semester to check
            VALUES ?selectedSemester { {semester_filter} }

            # Names
            ?course1 schema:name ?course1Name .
            ?course2 schema:name ?course2Name .

            # Offerings
            ?course1 ex:offeredIn ?off1 .
            ?course2 ex:offeredIn ?off2 .

            # Must match selected semester
            ?off1 ex:semester ?semester .
            ?off2 ex:semester ?semester .
            FILTER(?semester = ?selectedSemester)

            # Components in that offering
            ?off1 ex:hasComponent ?comp1 .
            ?off2 ex:hasComponent ?comp2 .

            # Time slots
            ?comp1 ex:hasTimeSlot ?slot1 .
            ?comp2 ex:hasTimeSlot ?slot2 .

            # Day + time
            ?slot1 ex:dayOfWeek ?day .
            ?slot1 ex:startTime ?start1 .
            ?slot1 ex:endTime ?end1 .

            ?slot2 ex:dayOfWeek ?day .
            ?slot2 ex:startTime ?start2 .
            ?slot2 ex:endTime ?end2 .

            # Overlap condition
            FILTER(
                ?start1 < ?end2 &&
                ?start2 < ?end1
            )
        }}

        """
    
    @staticmethod
    # def find_courses_by_topic_query(topics: List[str]) -> str:
    #     """Find courses related to specific topics"""
    #     # 1. Clean inputs to prevent SPARQL injection
    #     clean_topics = [t.replace('"', '').strip() for t in topics if t.strip()]
        
    #     if not clean_topics:
    #         # Fallback if list is empty, though tool should prevent this
    #         return ""
        
    #     # Create a regex pattern that matches any of the topics (case-insensitive)
    #     topic_pattern = '|'.join(clean_topics)
        
    #     return f"""
    #     PREFIX ex: <http://example.org/>
    #     PREFIX schema: <https://schema.org/>
    #     SELECT DISTINCT ?course ?courseName ?courseCode ?topic
    #     WHERE {{
    #         ?course a schema:Course ;
    #                 schema:name ?courseName ;
    #                 schema:courseCode ?courseCode ;
    #                 ex:hasTopics ?topic .
    #         FILTER(REGEX(?topic, "{topic_pattern}", "i"))
    #     }}
    #     ORDER BY ?courseCode
    #     """
    def find_courses_by_topic_query(topics: Union[str, List[str]]) -> str:
        """
        Find courses related to a specific topic.
        Uses case-insensitive matching.
        """
        # # distinct cleaning to prevent injection or broken quotes
        # safe_topic = topic.replace('"', '').strip()
        if isinstance(topics, str):
            topics = [topics]
            
        # 2. Clean inputs to prevent injection or broken quotes
        clean_topics = [t.replace('"', '').strip() for t in topics if t.strip()]
        
        if not clean_topics:
            return ""
        
        # Create a regex pattern that matches any of the topics (case-insensitive)
        topic_pattern = '|'.join(clean_topics)
        
        return f"""
        PREFIX ex: <http://example.org/>
        PREFIX schema: <https://schema.org/>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

        SELECT DISTINCT ?courseCode ?courseName ?topicLabel
        WHERE {{
            ?course a schema:Course ;
                    schema:courseCode ?courseCode ;
                    schema:name ?courseName ;
                    ex:hasTopics ?topicLabel .
            
            # Regex match: case-insensitive ("i") matching the joined pattern
            FILTER(REGEX(?topicLabel, "{topic_pattern}", "i"))
        }}
        ORDER BY ?courseCode
        LIMIT 10
        """
    
    @staticmethod
    def get_major_requirements_query(major: str) -> str:
        """
        Get courses that fulfill major requirements.
        Note: This assumes you have major/program data in your TTL.
        Adjust based on your actual schema for majors/programs.
        """
        return f"""
        PREFIX ex: <http://example.org/>
        PREFIX schema: <http://schema.org/>
        SELECT ?course ?courseName ?courseCode ?requirement
        WHERE {{
            ?major a ex:Major ;
                   schema:name "{major}" ;
                   ex:requires ?requirement .
            ?requirement ex:satisfiedBy ?course .
            ?course schema:name ?courseName ;
                    schema:courseCode ?courseCode .
        }}
        ORDER BY ?courseCode
        """
    
    @staticmethod
    def get_all_courses_query() -> str:
        """Get all courses in the knowledge graph"""
        return """
        PREFIX ex: <http://example.org/>
        PREFIX schema: <http://schema.org/>
        SELECT ?course ?courseName ?courseCode ?credits
        WHERE {
            ?course a schema:Course ;
                    schema:name ?courseName ;
                    schema:courseCode ?courseCode .
            OPTIONAL { ?course schema:numberOfCredits ?credits . }
        }
        ORDER BY ?courseCode
        """
    
    @staticmethod
    def get_full_course_details_query(course_id: str) -> str:
        """Get detailed information about a specific course"""
        return f"""
        PREFIX ex: <http://example.org/>
        PREFIX schema: <http://schema.org/>
        SELECT ?courseName ?courseCode ?credits ?topic ?prereq ?prereqName ?offering
        WHERE {{
            ex:{course_id} a schema:Course ;
                          schema:name ?courseName ;
                          schema:courseCode ?courseCode .
            OPTIONAL {{ ex:{course_id} schema:numberOfCredits ?credits . }}
            OPTIONAL {{ ex:{course_id} ex:hasTopics ?topic . }}
            OPTIONAL {{ 
                ex:{course_id} ex:hasPrerequisite ?prereq .
                ?prereq schema:name ?prereqName .
            }}
            OPTIONAL {{ ex:{course_id} ex:offeredIn ?offering . }}
        }}
        """
    
    @staticmethod
    def get_courses_offered_in_semester_query(semester: str, year: int) -> str:
        """
        Get courses offered in a specific semester and year.
        Example: semester='Spring', year=2025
        """
        offering_pattern = f".*{semester}{year}.*"
        
        return f"""
        PREFIX ex: <http://example.org/>
        PREFIX schema: <http://schema.org/>
        SELECT DISTINCT ?course ?courseName ?courseCode ?offering
        WHERE {{
            ?course a schema:Course ;
                    schema:name ?courseName ;
                    schema:courseCode ?courseCode ;
                    ex:offeredIn ?offering .
            FILTER(REGEX(STR(?offering), "{offering_pattern}", "i"))
        }}
        ORDER BY ?courseCode
        """