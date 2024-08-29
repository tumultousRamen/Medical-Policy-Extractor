import json
from openai import OpenAI


class OntologyCreator:
    def __init__(self):
        self.openai_api_key = "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"
        self.client = OpenAI(api_key=self.openai_api_key)


        with open('/content/medical_categories.json', 'r') as f:
            self.medical_categories = json.load(f)

    def expand_category(self, category, items):
        prompt = f"""You are a trained medical professional with experience in handling medical policies.
        For the category '{category}', you're provided with the following list of items:
        {', '.join(items)}
    
        Please extend this list to be more comprehensive for the entire human body or medical field as appropriate.
        Provide the answer as a Python list of strings."""

        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        print(response.choices[0].message.content)

        return response.choices[0].message.content

    def run(self):
        for category, items in self.medical_categories.items():
            print(f"Expanding category: {category}")

            self.medical_categories[category] = self.expand_category(category, items)

        with open('expanded_medical_categories.json', 'w') as f:
            json.dump(self.medical_categories, f, indent=2)

        print("Expansion complete. Updated dictionary saved to 'expanded_medical_categories.json'")


