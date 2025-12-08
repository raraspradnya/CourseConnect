"""
JSON to RDF Triples Converter
Transforms JSON data into RDF triples using rdflib
"""

from rdflib import Graph, Namespace, Literal, URIRef, RDF, RDFS, XSD, SDO
from skill_extractor import SkillExtractorWrapper
from course_code_parser import CourseCodeParser
import json
import re

class JsonToRdfConverter:
    """Convert JSON data to RDF triples using rdflib"""
    def __init__(self, course_data_filepath, skills_db_filepath, model_name, base_uri):
        """
        Initialize JsonToRdfConverter
        
        Args:
            course_data_filepath: Path to JSON file with course data
            skills_db_filepath: Path to skills database JSON
            model_name: Name of the SpaCy model to load
        """

        with open(course_data_filepath, 'r', encoding='utf-8') as f:
            self.course_data = json.load(f)

        with open(skills_db_filepath, 'r', encoding='utf-8') as f:
            self.skills_db = json.load(f)
        
        self.model_name = model_name
        self.base_uri=base_uri

    def create_slug(self, text, max_length=30):
        """
        Convert course name to URL-friendly slug
        Example: "Front-End Web Architecture" -> "frontend_web_architecture"
        """
        # Convert to lowercase
        slug = text.lower()
        
        # Replace special characters and spaces with hyphens
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '_', slug)
        
        # Truncate to max length
        slug = slug[:max_length].strip('-')
        
        return slug

    def parse_time(self, time_str):
        """Convert '9:00 am' to time and minutes from midnight"""
        if not time_str:
            return None, None
            
        time_str = time_str.strip().lower()
        match = re.match(r'(\d{1,2}):(\d{2})\s*(am|pm)', time_str)
        if match:
            hour, minute, period = match.groups()
            hour = int(hour)
            minute = int(minute)
            
            if period == 'pm' and hour != 12:
                hour += 12
            elif period == 'am' and hour == 12:
                hour = 0
                
            minutes_from_midnight = hour * 60 + minute
            time_obj = f"{hour:02d}:{minute:02d}:00"
            
            return time_obj, minutes_from_midnight
        return None, None
    
    def validate_course_code(self, graph, course_code: str) -> bool:
        """Check if a course code exists in the knowledge graph"""
        query = f"""
        PREFIX schema: <{self.base_uri}>
        
        ASK {{
            ?course a schema:Course ;
                   schema:courseCode "{course_code}" .
        }}
        """
        
        return bool(graph.query(query))

    def json_to_rdf(self):
        """
        Convert JSON data to RDF triples.
        
        Args:
            ner_model_name: Name of NER model for skill extraction
            base_uri: Base URI for RDF resources
        
        Returns:
            rdflib.Graph: Graph containing RDF triples
        """
        g = Graph()

        # Define namespace example.org
        ex = Namespace(self.base_uri)
        g.bind("ex", ex)
        g.bind("schema", SDO)

        # Map JSON keys to appropriate predicates
        key_to_predicate = {
            "course_id": SDO.courseCode,
            "title": SDO.name,
            "units": SDO.numberOfCredits,
            "description": ex.hasTopics,
            "semester": ex.semester
        }

        # Initialize skill extractor                    
        extractor = SkillExtractorWrapper(self.course_data, self.skills_db, self.model_name)
        ner_model = extractor.load_ner_model()

        for item in self.course_data:

            if (item['course_id']):
                course_id = item.get("course_id").replace(" ", "")

                # Create subject URI
                if (item['course_id'] == "INFO 290"):
                    name_course = self.create_slug(item['title'])
                    unique_course_id = f"{course_id}_{name_course}"
                else:
                    unique_course_id = str(course_id)
                course_uri = ex[unique_course_id]
                g.add((course_uri, RDF.type, SDO.Course))

                # Add course ID
                g.add((course_uri, key_to_predicate['course_id'], Literal(item['course_id'], datatype=XSD.string)))
            
            # Add Course Title
            if (item['title']):
                g.add((course_uri, key_to_predicate['title'], Literal(item['title'], datatype=XSD.string)))

            # Add Units
            if isinstance(item['units'], list):
                for unit in item['units']:
                    g.add((course_uri, key_to_predicate['units'], Literal(int(unit), datatype=XSD.integer)))
            elif isinstance(item['units'], float):
                g.add((course_uri, key_to_predicate['units'], Literal(int(item['units']), datatype=XSD.integer)))

            # Add Course Topics
            if (item['description']):
                try:
                    extracted_skills = extractor.extract_skills_from_description(ner_model, item['description'])
                except ValueError as e:
                    print(f"Error processing text: {e}") # Handle the error or skip this text
                    
                for skill in extracted_skills:
                    g.add((course_uri, key_to_predicate['description'], Literal(skill, datatype=XSD.string)))
            
            # Add Semester
            # UNUSED - ALREADY COVERED IN COURSE OFFERING OBJECT
            if (item['year'] and item['semester']):
                semester_string= f"{item['year']} {item['semester'].capitalize()}"
                # g.add((course_uri, key_to_predicate['semester'], Literal(semester_string, datatype=XSD.string))) - ALREADY COVERED IN COURSE OFFERING OBJECT

            # Create offering
            offering_uri = ex[f"{unique_course_id}_{item['semester'].capitalize()}{item['year']}"]
            g.add((offering_uri, RDF.type, ex.CourseOffering))
            g.add((course_uri, ex.offeredIn, offering_uri))
            g.add((offering_uri, ex.semester, Literal(semester_string, datatype=XSD.string)))

            # Create Prerequisites
            if (item.get('prerequisites')):
                parser = CourseCodeParser()
                courses = parser.parse_prerequisite_text(item['prerequisites'].get('text'))
                for course_code in courses:
                    if(self.validate_course_code(g, course_code)):
                        g.add((course_uri, ex.hasPrerequisite, Literal(course_code, datatype=XSD.string)))
                
            # Process sections
            for section_idx, section in enumerate(item.get('sections', [])):
                # Create lecture component
                lecture_uri = ex[f"{unique_course_id}_{item['semester'].capitalize()}{item['year']}_LEC_{section_idx}"]
                g.add((lecture_uri, RDF.type, ex.LectureComponent))
                g.add((lecture_uri, ex.componentType, Literal("Lecture")))
                g.add((lecture_uri, ex.sectionNumber, Literal(section.get('section_number', section_idx), datatype=XSD.integer)))
                g.add((offering_uri, ex.hasComponent, lecture_uri))
                
                # Add instructor
                if section.get('instructor'):
                    g.add((lecture_uri, ex.instructor, Literal(section['instructor'], datatype=XSD.string)))
                
                # Create lecture time slot
                lecture_slot_uri = ex[f"{unique_course_id}_{item['semester'].capitalize()}{item['year']}_LEC_{section_idx}_Slot"]
                g.add((lecture_slot_uri, RDF.type, ex.TimeSlot))
                g.add((lecture_uri, ex.hasTimeSlot, lecture_slot_uri))
                
                # Add days
                for day in section.get('days', []):
                    g.add((lecture_slot_uri, ex.dayOfWeek, ex[day.capitalize()]))
                
                # Add times
                if section.get('start_time'):
                    start_time, start_minutes = self.parse_time(section['start_time'])
                    if start_time:
                        g.add((lecture_slot_uri, ex.startTime, Literal(start_time, datatype=XSD.time)))
                        g.add((lecture_slot_uri, ex.startMinutes, Literal(start_minutes, datatype=XSD.integer)))
                
                if section.get('end_time'):
                    end_time, end_minutes = self.parse_time(section['end_time'])
                    if end_time:
                        g.add((lecture_slot_uri, ex.endTime, Literal(end_time, datatype=XSD.time)))
                        g.add((lecture_slot_uri, ex.endMinutes, Literal(end_minutes, datatype=XSD.integer)))
                
                # Add location
                if section.get('location'):
                    g.add((lecture_slot_uri, ex.location, Literal(section['location'])))
                
                # Add notes if present
                if section.get('notes'):
                    g.add((lecture_uri, ex.notes, Literal(section['notes'])))
                
                # Process lab section if exists
                if section.get('lab_section_info') and section['lab_section_info']!= 'N/A':
                    lab_info = section['lab_section_info']
                    
                    # Create lab component
                    lab_uri = ex[f"{unique_course_id}_{item['semester'].capitalize()}{item['year']}_LAB_{section_idx}"]
                    g.add((lab_uri, RDF.type, ex.LabComponent))
                    g.add((lab_uri, ex.componentType, Literal("Lab")))
                    g.add((offering_uri, ex.hasComponent, lab_uri))
                    
                    # Add lab instructor
                    if lab_info.get('instructor'):
                        g.add((lab_uri, ex.instructor, Literal(lab_info['instructor'], datatype=XSD.string)))
                    
                    # Create lab time slot
                    lab_slot_uri = ex[f"{unique_course_id}_{item['semester'].capitalize()}{item['year']}_LAB_{section_idx}_Slot"]
                    g.add((lab_slot_uri, RDF.type, ex.TimeSlot))
                    g.add((lab_uri, ex.hasTimeSlot, lab_slot_uri))
                    
                    # Add lab days
                    for day in lab_info.get('days', []):
                        g.add((lab_slot_uri, ex.dayOfWeek, ex[day.capitalize()]))
                    
                    # Add lab times
                    if lab_info.get('start_time'):
                        start_time, start_minutes = self.parse_time(lab_info['start_time'])
                        if start_time:
                            g.add((lab_slot_uri, ex.startTime, Literal(start_time, datatype=XSD.time)))
                            g.add((lab_slot_uri, ex.startMinutes, Literal(start_minutes, datatype=XSD.integer)))
                    
                    if lab_info.get('end_time'):
                        end_time, end_minutes = self.parse_time(lab_info['end_time'])
                        if end_time:
                            g.add((lab_slot_uri, ex.endTime, Literal(end_time, datatype=XSD.time)))
                            g.add((lab_slot_uri, ex.endMinutes, Literal(end_minutes, datatype=XSD.integer)))
                    
                    # Add lab location
                    if lab_info.get('location'):
                        g.add((lab_slot_uri, ex.location, Literal(lab_info['location'])))

        return g

if __name__ == "__main__":
    # CONFIGURATION
    ISCHOOL_COURSES_FILENAME = '../parse-html/ischool_courses_data.json'
    SKILLS_JSON_FILENAME = 'skill_db_relax_20.json'
    MODEL_NAME = 'en_core_web_lg'
    BASE_URI = 'http://example.org/'
    
    # Convert to RDF
    converter = JsonToRdfConverter(ISCHOOL_COURSES_FILENAME, SKILLS_JSON_FILENAME, MODEL_NAME, BASE_URI)
    graph = converter.json_to_rdf()

    # Serialize to turtle formats
    graph.serialize(destination='output.ttl', format='turtle')
    print("Saved to output.ttl")