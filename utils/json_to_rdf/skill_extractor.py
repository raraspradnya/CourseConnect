# Model used : https://github.com/AnasAito/SkillNER

import json
import spacy
from spacy.matcher import PhraseMatcher
from skillNer.general_params import SKILL_DB
from skillNer.skill_extractor_class import SkillExtractor

# --- Configuration ---
INPUT_FILENAME = '../parse-html/ischool_courses_data.json'
SKILLS_JSON_FILENAME = 'skill_db_relax_20.json'
MODEL_NAME = 'en_core_web_lg'

def load_ner_model(model_name=MODEL_NAME):
    """Loads a pre-trained NER model from Hugging Face via SpaCy."""
    print(f"Loading NER model: {model_name}...")
    try:
        # Load the transformer model. This may take a moment and require internet access
        # on the first run to download the model.
        ner = spacy.load(model_name)
        print("Successfully loaded model.")
        return ner
    except OSError:
        print(f"---")
        print(f"Error: Could not load model '{model_name}'.")
        print("Please ensure you have run the following commands:")
        print("pip install skillNer")
        print("python -m spacy download en_core_web_lg")
        print(f"---")
        return None

def extract_skills_from_description(description, ner, skills_db):
    # Initiate skill extractor
    skill_extractor = SkillExtractor(ner, SKILL_DB, PhraseMatcher)
    annotations = skill_extractor.annotate(description)

    skills =[]
    # Get values from full_matches
    for match in annotations['results']['full_matches']:
        skill_id = match['skill_id']
        if skill_id in skills_db:
            skill_name = skills_db[skill_id]['skill_name']
            if skill_name not in skills:
                skills.append(skill_name)

    # Get values from ngram_scored
    for match in annotations['results']['ngram_scored']:
        skill_id = match['skill_id']
        if skill_id in skills_db:
            skill_name = skills_db[skill_id]['skill_name']
            if skill_name not in skills:
                skills.append(skill_name)
    return skills

def extract_skills_from_courses(course_data, ner, skills_db):
    """
    Extracts skills and topics from the description of each course.

    Args:
        course_data (list): A list of course dictionaries from the JSON file.
        ner: A loaded SpaCy ner pipeline.

    Returns:
        dict: A dictionary mapping each course_id to a set of extracted skill strings.
    """
    if not ner:
        print("ner model is not available. Aborting skill extraction.")
        return {}

    # Use dictionary to easily append to a set for each course
    course_skills = {}
    print(f"\nProcessing {len(course_data)} courses to extract skills...")

    for course in course_data:
        course_id = course.get('course_id', 'Unknown Course ID')
        description = course.get('description', '')

        if not description:
            continue

        # Process the description text with the ner model
        try:
            skills = extract_skills_from_description(description, ner, skills_db)
            course_skills[course_id] = skills
        except ValueError as e:
            print(f"Error processing text: {e}")
            # Handle the error or skip this text
    return course_skills

def main():
    """
    Main function to load data, run skill extraction, and print the results.
    """
    ner_model = load_ner_model(MODEL_NAME)
    if not ner_model:
        return

    with open(INPUT_FILENAME, 'r', encoding='utf-8') as f:
        all_courses = json.load(f)

    with open(SKILLS_JSON_FILENAME, 'r', encoding='utf-8') as f:
        skills_db = json.load(f)    

    extracted_skills = extract_skills_from_courses(all_courses, ner_model, skills_db)

    with open('extracted_skills.txt', 'w', encoding='utf-8') as f:
        f.write("--- Extracted Skills per Course ---\n")
        for courses in extracted_skills:
            f.write(f"\n[{courses}]\n")
            for skill in sorted(list(extracted_skills[courses])):
                f.write(f"  - {skill}\n")

if __name__ == "__main__":
    main()