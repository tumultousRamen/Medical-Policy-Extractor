import uuid

class MedicalPolicyProcessor:
    MEDICAL_CATEGORIES = load_json_file('medical_categories.json')

    LOGICAL_RELATIONS = {
        'ANY': ['any of ', 'either of ', 'one of ', 'at least one of ', 'at least one ', 'at least one of the following', 'at least one of the following:'],
        'ALL': ['all of ', 'each of ', 'every of ', 'every ', 'each ', 'all of the following', 'all of the following']
    }

    def __init__(self, input_directory, output_directory, ontology_dict=None):
      self.input_directory = input_directory
      self.output_directory = output_directory
      self.ontology = self.create_ontology_dict(ontology_dict)
      self.processed_data = []

    def create_ontology_dict(self, ontology_dict):
      """
      Create or load the ontology dictionary.

      :param ontology_dict: Path to custom ontology JSON file
      :return: Ontology dictionary
      """
      if ontology_dict is None:
        print("No ontology provided. Using default ontology.")
        return self.MEDICAL_CATEGORIES

      with open(ontology_dict, 'r') as file:
        print('Loading custom ontology dictionary')
        return json.load(file)

    def process_document(self, source, document):
      """
      Process a single document.

      :param source: Filename of the document
      :param document: JSON content of the document
      :return: Processed document dictionary
      """

      criteria = self.extract_medical_necessity_criteria(document)
      codes = self.extract_codes(document)

      return {
          'source': source,
          'criteria': criteria,
          'codes': codes
      }

    def extract_medical_necessity_criteria(self, document, parent_id=None):
      """
      Extract and process medical necessity criteria from the document.

      :param document: Document or criteria list to process
      :param parent_id: ID of the parent criterion (for nested criteria)
      :return: List of processed criteria
      """
      if isinstance(document, dict):
          criteria = document.get('medical_necessity_criteria', [])
      else:
          criteria = document if isinstance(document, list) else []

      processed_criteria = []

      for item in criteria:
          text = item.get('text', '')
          # is_necessary = self.identify_medical_necessity(text)
          logical_relation = self.identify_logical_relation(text)

          item_id = str(uuid.uuid4())

          processed_item = {
              'id': item_id,
              'parent_id': parent_id,
              'text': text,
              'logical_relation': logical_relation,
              'entities': self.identify_entities(text),
              'child_relation': None,
              'next_sibling_id': None
          }

          sub_items = item.get('sub_items', [])
          if sub_items:
              processed_item['children'] = self.extract_medical_necessity_criteria(sub_items, item_id)
              if processed_item['children']:
                  processed_item['child_relation'] = logical_relation or None

          processed_criteria.append(processed_item)

      # Setting the next_sibling_id and handling trailing logical connectors here
      for i in range(len(processed_criteria) - 1):
          current_item = processed_criteria[i]
          next_item = processed_criteria[i + 1]

          current_item['next_sibling_id'] = next_item['id']

          logical_connector = self.identify_trailing_logical_connector(current_item['text'])
          if logical_connector:
              current_item['next_sibling_relation'] = 'OR' if logical_connector == 'or' else 'AND'
          else:
              current_item['next_sibling_relation'] = None

      return processed_criteria


    def identify_entities(self, text):
      """
      Identify medical entities in the text based on the ontology.

      :param text: Text to analyze
      :return: Dictionary of identified entities by category
      """
      identified_entities = defaultdict(set)

      for category, keywords in self.ontology.items():
          for keyword in keywords:
              matches = re.finditer(r'\b' + re.escape(keyword) + r'\b', text, re.IGNORECASE)
              for match in matches:
                  identified_entities[category].add(match.group().lower())

      return {k: list(v) for k, v in identified_entities.items()}

    def extract_codes(self, document):
      """
      Extract medical codes from the document.

      :param document: Document containing codes
      :return: Dictionary of extracted codes
      """
      codes = document.get('codes', {})
      extracted_codes = {}

      for code_type, code_categories in codes.items():
          extracted_codes[code_type] = {}

          for category, code_list in code_categories.items():
              coverage_policy = category.split(':')[0].strip()

              if coverage_policy not in extracted_codes[code_type]:
                  extracted_codes[code_type][coverage_policy] = []

              for code_item in code_list:
                  if isinstance(code_item, dict):
                      extracted_codes[code_type][coverage_policy].append({
                          'code': code_item.get('code', ''),
                          'description': code_item.get('description', ''),
                      })

      return extracted_codes

    # A basic test to identify medical necessity from text using regex matching - can be improved
    def identify_medical_necessity(self, text):
      """
      Identify if the text indicates medical necessity.

      :param text: Text to analyze
      :return: Boolean indicating medical necessity
      """

      positive_patterns = [
          r'Aetna considers .+ medically necessary',
          r'. considered medically necessary',
          r'are considered medically necessary',
          r'medical necessity criteria',
          r'medically necessary .+ include',
          r'following .+ medically necessary',
      ]

      negative_patterns = [
          r'not medically necessary',
          r'considered experimental',
          r'investigational',
          r'not covered'
      ]

      for pattern in negative_patterns:
          if re.search(pattern, text, re.IGNORECASE):
              return False

      for pattern in positive_patterns:
          if re.search(pattern, text, re.IGNORECASE):
              return True

      return False

    def identify_logical_relation(self, text):
      """
      Identify logical relations in the text.

      :param text: Text to analyze
      :return: Identified logical relation or None
      """
      for relation, phrases in self.LOGICAL_RELATIONS.items():
          for phrase in phrases:
              if phrase in text.lower():
                  return relation
      return None

    def identify_trailing_logical_connector(self, text):
      """
      Identify trailing logical connectors (and/or) in the text.

      :param text: Text to analyze
      :return: Identified logical connector or None
      """
      match = re.search(r';\s*(or|and)\s*$', text)
      return match.group(1) if match else None

    def run(self):
      """Process all JSON documents in the input directory."""

      for filename in os.listdir(self.input_directory):
          if filename.endswith('.json'):
              input_path = os.path.join(self.input_directory, filename)
              with open(input_path, 'r') as f:
                  document = json.load(f)

              processed_doc = self.process_document(filename, document)
              self.processed_data.append(processed_doc)

              output_filename = f"processed_{filename}"
              output_path = os.path.join(self.output_directory, output_filename)
              with open(output_path, 'w') as f:
                  json.dump(processed_doc, f, indent=2)

              print(f"Processed data saved to {output_path}")

    def print_statistics(self):
      """Print statistics about processed data."""

      total_criteria = sum(len(doc['criteria']) for doc in self.processed_data)

      print(f"\nTotal criteria processed: {total_criteria}")

      entity_counts = defaultdict(int)
      for doc in self.processed_data:
          for criterion in doc['criteria']:
              for category, entities in criterion['entities'].items():
                  entity_counts[category] += len(entities)

      print("\nEntity counts by category:")
      for category, count in sorted(entity_counts.items(), key=lambda x: x[1], reverse=True):
          print(f"{category}: {count}")