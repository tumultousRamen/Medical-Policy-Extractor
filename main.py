
import os

import time
from collections import defaultdict
from fuzzywuzzy import fuzz

import json
import spacy
from spacy.matcher import PhraseMatcher
from AetnaPolicyExtractor import AetnaPolicyExtractor
from MedicalPolicyProcessor import MedicalPolicyProcessor
from OntologyCreator import OntologyCreator


def setup_directories():
    input_dir = 'aetna_raw_data'
    output_dir = 'aetna_processed_data'

    if not os.path.exists(input_dir):
        os.makedirs(input_dir)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    return input_dir, output_dir


def load_json_file(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)


class Demo:
    def __init__(self):
        self.extractor = None
        self.standardizer = None
        self.ontologycreator = OntologyCreator()
        self.clinical_policy_dict = {
            "Cataract Surgery": "https://www.aetna.com/cpb/medical/data/500_599/0508.html",
            "Glaucoma Surgery": "https://www.aetna.com/cpb/medical/data/400_499/0484.html",
            "Brachial Plexus Surgery": "https://www.aetna.com/cpb/medical/data/800_899/0850.html",
            "Heart Transplantation": "https://www.aetna.com/cpb/medical/data/500_599/0586.html",
            "Influenza Rapid Diagnostic Tests": "https://www.aetna.com/cpb/medical/data/400_499/0476.html",
            "Fecal Incontinence": "https://www.aetna.com/cpb/medical/data/600_699/0611.html",
            "Salivary Tests": "https://www.aetna.com/cpb/medical/data/600_699/0608.html",
            "Lung Cancer Screening": "https://www.aetna.com/cpb/medical/data/300_399/0380.html",
            "Spinal Ultrasound": "https://www.aetna.com/cpb/medical/data/600_699/0628.html",
            "Transrectal Ultrasound": "https://www.aetna.com/cpb/medical/data/1_99/0001.html",
            "Speech Therapy": "https://www.aetna.com/cpb/medical/data/200_299/0243.html",
            "Voice Therapy": "https://www.aetna.com/cpb/medical/data/600_699/0646.html",
            "Infrared Therapy": "https://www.aetna.com/cpb/medical/data/600_699/0604.html",
            "Dysphagia Therapy": "https://www.aetna.com/cpb/medical/data/600_699/0625.html",
            "Brachytherapy": "https://www.aetna.com/cpb/medical/data/300_399/0371.html"
        }

    def generate_raw_data(self):
        for policy_name, policy_url in self.clinical_policy_dict.items():
            print(f"Processing {policy_name} policy...")

            self.extractor = AetnaPolicyExtractor()
            self.extractor.load_url(policy_url)
            self.extractor.run()

    def generate_processed_data(self):
        input_dir, output_dir = setup_directories()
        ontology = 'medical_ontology.json'
        start_time = time.time()
        self.standardizer = MedicalPolicyProcessor(input_dir, output_dir, ontology)
        self.standardizer.run()
        self.standardizer.print_statistics()
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Elapsed time: {elapsed_time:.2f} seconds")

    def generate_ontology(self):
        MEDICAL_CATEGORIES = load_json_file(
            '/content/extended_medical_categories.json')  # Generative dictionary - from OpenAI API call
        # MEDICAL_CATEGORIES = load_json_file('/content/medical_categories.json') # Dictionary created manually
        nlp = spacy.load("en_core_sci_sm")
        nlp.add_pipe("abbreviation_detector")
        nlp.add_pipe("scispacy_linker", config={"resolve_abbreviations": True, "linker_name": "umls"})

        # Creating phrase matchers for each category - categorize recognized entities
        category_matchers = {}
        for category, terms in MEDICAL_CATEGORIES.items():
            matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
            patterns = [nlp.make_doc(text) for text in terms]
            matcher.add(category, patterns)
            category_matchers[category] = matcher

        def extract_key_concepts(text):
            doc = nlp(text)
            concepts = set()
            for ent in doc.ents:
                if ent._.kb_ents:
                    concepts.add(ent.text.lower())
            return concepts

        def categorize_concept(concept, use_fuzzy_matching=False):
            doc = nlp(concept.lower())
            categories = set()
            for category, matcher in category_matchers.items():
                matches = matcher(doc)
                if matches:
                    categories.add(category)
                elif use_fuzzy_matching:
                    # Using fuzzy matching if no exact match found
                    for term in MEDICAL_CATEGORIES[category]:
                        if fuzz.partial_ratio(concept.lower(), term.lower()) > 85:
                            categories.add(category)
                            break
            return categories if categories else {"Uncategorized"}

        def create_ontology(data, use_fuzzy_matching=False):
            ontology = defaultdict(set)

            # Add predefined terms to the ontology
            for category, terms in MEDICAL_CATEGORIES.items():
                ontology[category].update(terms)

            for item in data.get("medical_necessity_criteria", []):
                text = item.get("text", "")
                concepts = extract_key_concepts(text)

                for concept in concepts:
                    categories = categorize_concept(concept, use_fuzzy_matching)
                    for category in categories:
                        ontology[category].add(concept)

                sub_items = item.get("sub_items", [])
                for sub_item in sub_items:
                    sub_text = sub_item.get("text", "")
                    sub_concepts = extract_key_concepts(sub_text)

                    for sub_concept in sub_concepts:
                        categories = categorize_concept(sub_concept, use_fuzzy_matching)
                        for category in categories:
                            ontology[category].add(sub_concept)

            return ontology

        def process_json_files(directory):
            all_data = []
            for filename in os.listdir(directory):
                if filename.endswith('.json'):
                    file_path = os.path.join(directory, filename)
                    data = load_json_file(file_path)
                    all_data.append(data)

            data_feed = {"medical_necessity_criteria": [item for sublist in all_data for item in
                                                        sublist["medical_necessity_criteria"]]}
            ontology = create_ontology(data_feed, use_fuzzy_matching=False)
            return ontology

        raw_data_file_path = os.path.join(os.getcwd(), 'aetna_raw_data')

        ontology = process_json_files(raw_data_file_path)

        output_file = os.path.join(os.getcwd(), 'medical_ontology.json')
        with open(output_file, 'w') as f:
            json.dump({k: list(v) for k, v in ontology.items() if k != "Uncategorized"}, f, indent=2)


if __name__ == '__main__':
    demo = Demo()
    demo.generate_raw_data()
    demo.generate_ontology()
    demo.generate_processed_data()
