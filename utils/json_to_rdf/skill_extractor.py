"""
Skill Extractor Module

Extract skills and topics from course descriptions using a pre-trained NER model.
Model used : https://github.com/AnasAito/SkillNER

"""

import json
import spacy
from spacy.matcher import PhraseMatcher
from skillNer.general_params import SKILL_DB
from skillNer.skill_extractor_class import SkillExtractor


class SkillExtractorWrapper:

    def __init__(self, json_file, skills_db, model_name):
        """
        Initialize SkillExtractorWrapper
        Args:
            json_file: JSON object with course data
            skills_db: JSON object of skills database JSON
            model_name: Name of the SpaCy model to load
        """
        self.json_file = json_file
        self.skills_db = skills_db
        self.model_name = model_name


    def load_ner_model(self):
        """Loads a pre-trained NER model from Hugging Face via SpaCy."""
        print(f"Loading NER model: {self.model_name}...")
        try:
            # Load the transformer model. This may take a moment and require internet access
            # on the first run to download the model.
            ner = spacy.load(self.model_name)
            print("Successfully loaded model.")
            return ner
        except OSError:
            print(f"---")
            print(f"Error: Could not load model '{self.model_name}'.")
            print("Please ensure you have run the following commands:")
            print("pip install skillNer")
            print("python -m spacy download en_core_web_lg")
            print(f"---")
            return None

    def extract_skills_from_description(self, ner_model, description):
        """Extract skills from a course description using the NER model."""
        
        skill_extractor = SkillExtractor(ner_model, self.skills_db, PhraseMatcher)
        annotations = skill_extractor.annotate(description)

        skills =[]
        # Get values from full_matches
        for match in annotations['results']['full_matches']:
            skill_id = match['skill_id']
            if skill_id in self.skills_db:
                skill_name = self.skills_db[skill_id]['skill_name']
                if skill_name not in skills:
                    skills.append(skill_name)

        # Get values from ngram_scored
        for match in annotations['results']['ngram_scored']:
            skill_id = match['skill_id']
            if skill_id in self.skills_db:
                skill_name = self.skills_db[skill_id]['skill_name']
                if skill_name not in skills:
                    skills.append(skill_name)
        return skills

    def extract_skills_from_courses(self):
        """
        Extracts skills and topics from the description of each course.

        Returns:
            dict: A dictionary mapping each course_id to a set of extracted skill strings.
        """

        ner_model = self.load_ner_model()
        if not ner_model:
            return

        # Use dictionary to easily append to a set for each course
        course_skills = {}
        print(f"\nProcessing {len(self.json_file)} courses to extract skills...")

        for course in self.json_file:
            course_id = course.get('course_id', 'Unknown Course ID')
            description = course.get('description', '')

            if not description:
                continue

            # Process the description text with the ner model
            try:
                skills = self.extract_skills_from_description(ner_model, description)
                course_skills[course_id] = skills
            except ValueError as e:
                print(f"Error processing text: {e}")
                # Handle the error or skip this text
        return course_skills

    def export_skills_to_file(self, output_filepath, extracted_skills):
        """
        Export the extracted skills to a text file.

        Args:
            output_filepath: Path to the output text file.
            extracted_skills: Dictionary of extracted skills per course.
        """
        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write("--- Extracted Skills per Course ---\n")
            for course_id in extracted_skills:
                f.write(f"\n[{course_id}]\n")
                for skill in sorted(list(extracted_skills[course_id])):
                    f.write(f"  - {skill}\n")


if __name__ == "__main__":
    course_json_filepath = '../parse-html/ischool_courses_data.json'
    skills_json_filepath = 'skill_db_relax_20.json'
    model_name = 'en_core_web_lg'

    with open(course_json_filepath, 'r', encoding='utf-8') as f:
        course_json = json.load(f)

    with open(skills_json_filepath, 'r', encoding='utf-8') as f:
        skills_db = json.load(f)

    extractor = SkillExtractorWrapper(course_json, skills_db, model_name)
    extracted_skills = extractor.extract_skills_from_courses()
    extractor.export_skills_to_file('extracted_skills.txt', extracted_skills)