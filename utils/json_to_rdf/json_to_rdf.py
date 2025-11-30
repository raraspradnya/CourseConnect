"""
JSON to RDF Triples Converter
Transforms JSON data into RDF triples using rdflib
"""

from rdflib import Graph, Namespace, Literal, URIRef, RDF, RDFS, XSD, SDO
from skill_extractor import load_ner_model, extract_skills_from_description
import json
import re

def create_slug(text, max_length=30):
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

def json_to_rdf(json_data, ner_model, skills_db, base_uri="http://example.org/"):
    """
    Convert JSON data to RDF triples.
    
    Args:
        json_data: JSON data (dict or list of dicts)
        base_uri: Base URI for creating resource URIs
    
    Returns:
        rdflib.Graph: Graph containing RDF triples
    """
    g = Graph()

    # Define namespace example.org
    ex = Namespace(base_uri)
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
    
    for item in json_data:

        if (item['course_id']):
            course_id = item.get("course_id").replace(" ", "")

            # Create subject URI
            if (item['course_id'] == "INFO 290"):
                name_course = create_slug(item['title'])
                course = ex[f"{course_id}_{name_course}"]
            else:
                course = ex[str(course_id)]
            g.add((course, RDF.type, SDO.Course))

            # Add course ID
            g.add((course, key_to_predicate['course_id'], Literal(item['course_id'], datatype=XSD.string)))
        
        # Add Course Title
        if (item['title']):
            g.add((course, key_to_predicate['title'], Literal(item['title'], datatype=XSD.string)))

        # Add Units
        if isinstance(item['units'], list):
            for unit in item['units']:
                g.add((course, key_to_predicate['units'], Literal(int(unit), datatype=XSD.integer)))
        elif isinstance(item['units'], float):
            g.add((course, key_to_predicate['units'], Literal(int(item['units']), datatype=XSD.integer)))

        # Add Course Topics
        if (item['description']):
            try:
                extracted_skills = extract_skills_from_description(item['description'], ner_model, skills_db)
            except ValueError as e:
                print(f"Error processing text: {e}") # Handle the error or skip this text
                
            for skill in extracted_skills:
                g.add((course, key_to_predicate['description'], Literal(skill, datatype=XSD.string)))
        
        if (item['year'] and item['semester']):
            g.add((course, key_to_predicate['semester'], Literal(f"{item['year']} {item['semester'].capitalize()}", datatype=XSD.string)))
        

    return g

# CONFIGURATION
ISCHOOL_COURSES_FILENAME = '../parse-html/ischool_courses_data.json'
SKILLS_JSON_FILENAME = 'skill_db_relax_20.json'

if __name__ == "__main__":
    # Read JSON Data
    with open(ISCHOOL_COURSES_FILENAME, 'r', encoding='utf-8') as f:
        ischool_json_data = json.load(f)
    
    with open(SKILLS_JSON_FILENAME, 'r', encoding='utf-8') as f:
        skills_db = json.load(f)    
    
    # Convert to RDF
    ner_model = load_ner_model()
    graph = json_to_rdf(ischool_json_data, ner_model, skills_db, base_uri="http://example.org/")
    
    # Serialize to turtle formats
    graph.serialize(destination='output.ttl', format='turtle')
    print("Saved to output.ttl")