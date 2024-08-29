from bs4 import BeautifulSoup


class AetnaPolicyExtractor:
    def __init__(self):
        self.url = None
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.aetna.com',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        self.html_content = None
        self.soup = None
        self.criteria = []
        self.processed_elements = set()
        self.output_dir = os.path.join(os.getcwd(), 'aetna_raw_data')
        self.codes = {
            'CPT': {},
            'HCPCS': {},
            'ICD-10': {},
            'Other': {}
        }

    def load_url(self, url):
        self.url = url

    def extract_html(self):
        try:
            response = requests.get(self.url, headers=self.headers)
            response.raise_for_status()
            self.html_content = response.text
            self.soup = BeautifulSoup(self.html_content, 'html.parser')
            return True
        except requests.RequestException as e:
            print(f"An error occurred while fetching the URL: {e}")
            return False

    def extract_list_items(self, element):
        items = []
        for child in element.children:
            if child.name == 'li' and child not in self.processed_elements:
                item = self.extract_text_and_subitems(child)
                if item:
                    items.append(item)
                self.processed_elements.add(child)
        return items

    def extract_text_and_subitems(self, element):
        text = element.get_text(strip=True, separator=' ')
        subitems = []
        for child in element.children:
            if child.name in ['ol', 'ul']:
                subitems = self.extract_list_items(child)
                break
        item = {'text': text}
        if subitems:
            item['sub_items'] = subitems
        return item

    def extract_medical_necessity_criteria(self):
        med_necessity = self.soup.find('h3', string='Medical Necessity')
        if not med_necessity:
            print("Medical Necessity section not found")
            return

        current = med_necessity.find_next()
        while current and current.name != 'h3':
            if current not in self.processed_elements:
                if current.name in ['ol', 'ul']:
                    self.criteria.extend(self.extract_list_items(current))
                elif current.name in ['p', 'div']:
                    text = current.get_text(strip=True, separator=' ')
                    if text:
                        self.criteria.append({'text': text})
                self.processed_elements.add(current)
            current = current.find_next()

    def extract_codes(self):
        code_table = self.soup.find('table', id='complexTable')
        if not code_table:
            return

        current_code_type = None
        current_category = None
        current_coverage = None

        for row in code_table.find_all('tr'):
            heading = row.find('h3', class_='cptHeading')
            if heading:
                heading_text = heading.get_text(strip=True)
                if 'CPT' in heading_text:
                    current_code_type = 'CPT'
                elif 'HCPCS' in heading_text:
                    current_code_type = 'HCPCS'
                elif 'ICD-10' in heading_text:
                    current_code_type = 'ICD-10'

                if 'covered if selection criteria are met' in heading_text.lower():
                    current_coverage = 'Covered if criteria met'
                elif 'not covered for indications listed' in heading_text.lower():
                    current_coverage = 'Not covered'
                elif 'other' in heading_text.lower():
                    current_coverage = 'Other'

                current_category = f"{current_coverage}: {heading_text}"
                if current_code_type not in self.codes:
                    self.codes[current_code_type] = {}
                if current_category not in self.codes[current_code_type]:
                    self.codes[current_code_type][current_category] = []

            elif row.find('td', class_='cptCode'):
                code = row.find('td', class_='cptCode').get_text(strip=True)
                description = row.find_all('td')[1].get_text(strip=True)
                if current_code_type and current_category:
                    self.codes[current_code_type][current_category].append({
                        'code': code,
                        'description': description,
                        'coverage': current_coverage
                    })
            else:
                text = row.get_text(strip=True)
                if current_code_type and current_category:
                    self.codes[current_code_type][current_category].append({
                        'code': '',
                        'description': text,
                        'coverage': current_coverage
                    })

        for code_type in list(self.codes.keys()):
            self.codes[code_type] = {k: v for k, v in self.codes[code_type].items() if v}
        self.codes = {k: v for k, v in self.codes.items() if v}

    def save_to_json(self):
        if not self.criteria and not any(self.codes.values()):
            print("No data to save")
            return

        os.makedirs(self.output_dir, exist_ok=True)

        data = {
            'medical_necessity_criteria': self.criteria,
            'codes': self.codes
        }

        filename = f"aetna_policy_data_{self.url.split('/')[-1].split('.')[0]}.json"
        filepath = os.path.join(self.output_dir, filename)
        json_data = json.dumps(data, ensure_ascii=False, indent=2)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(json_data)
            print(f"Data has been saved to '{filepath}'")
        except IOError as e:
            print(f"An error occurred while saving to {filepath}: {e}")

    def run(self):
        if self.extract_html():
            self.extract_medical_necessity_criteria()
            self.extract_codes()
            self.save_to_json()
        else:
            print("Failed to extract HTML content")