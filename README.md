# Medical-Policy-Extractor

### Objectives:

1. **Data Collection**:
    - Access medical policies from various sources such as:
        - [Oscar](https://www.hioscar.com/clinical-guidelines/medical)
        - [Aetna](https://www.aetna.com/health-care-professionals/clinical-policy-bulletins/medical-clinical-policy-bulletins.html)
        - [Anthem](https://www.anthem.com/provider/policies/clinical-guidelines/updates/)
        - [CMS Medicare Coverage Database](https://www.cms.gov/medicare-coverage-database/downloads/downloads.aspx)
    - You are highly encouraged to use other insurances like your own if you are curious about what they cover.
2. **Data Extraction and Standardization**:
    - Develop an algorithm to automatically extract medical necessity criteria from the aforementioned sources.
    - Candidates should choose one of the following approaches for data extraction:
        - Focus on a handful of similar categories (e.g., various types of surgeries) across multiple insurers.
        - Extract multiple categories of medical necessity criteria (e.g., surgeries, diagnostic tests, therapies) from a single insurer.
    - Standardize the extracted data to maintain consistency across categories or insurers, and keeping the text structure (medical necessity, coding, etc)
3. **Algorithm Evaluation**:
    - Design and implement a set of evaluation criteria to assess the performance of your extraction algorithm.
    - Criteria may include accuracy, completeness of data extraction, consistency across different data sources, efficiency of the process, and scalability.
4. **Documentation and Presentation**:
    - Document the methodology, challenges, and solutions encountered during the development process and be ready to talk about them in your code.
  
### Deliverables:

- A well documented Jupyter Notebook or python file with the extraction algorithm and evaluation code. Make sure you are ready to answer questions about it.
- Make sure you name the file in the following format firstname_lastname_position.ipynb (eg. hermine_tranie_ml_engineer_full_time.ipynb)

### Evaluation Criteria:

- **Effectiveness**: How well does the algorithm extract and standardize the medical necessity criteria?
- **Innovativeness**: How innovative are the solutions to challenges faced during the project?
- **Scalability**: Can the solution be scaled to accommodate larger datasets or multiple insurance policies?
