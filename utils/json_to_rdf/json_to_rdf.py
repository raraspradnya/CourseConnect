"""
JSON to RDF Triples Converter
Transforms JSON data into RDF triples using rdflib
"""

from rdflib import Graph, Namespace, Literal, URIRef, RDF, RDFS, XSD, SDO
from skill_extractor import load_ner_model, extract_skills_from_description
import json

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
        "description": ex.hasTopics
    }
    
    for item in json_data:
        # Create subject URI
        course_id = item.get("course_id").replace(" ", "")
        course = ex[str(course_id)]
        g.add((course, RDF.type, SDO.Course)) # Each item is a Course
        
        # Convert each key-value pair to triples
        for key, value in item.items():
            # Use the mapped predicate, or fall back to the custom 'ex' namespace
            predicate = key_to_predicate.get(key)

            if (key == "course_id"):
                g.add((course, predicate, Literal(value, datatype=XSD.string)))
            elif (key == "title"):
                g.add((course, predicate, Literal(value, datatype=XSD.string)))
            elif (key == "units"):
                g.add((course, predicate, Literal(value, datatype=XSD.integer)))
            elif (key == "description"):
                try:
                    extracted_skills = extract_skills_from_description(value, ner_model, skills_db)
                except ValueError as e:
                    print(f"Error processing text: {e}") # Handle the error or skip this text
                    
                for skill in extracted_skills:
                    g.add((course, predicate, Literal(skill, datatype=XSD.string)))
    
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