# Medical-Policy-Extractor

### Objectives:

1. **Data Collection**:
        - [Oscar](https://www.hioscar.com/clinical-guidelines/medical)
        - [Aetna](https://www.aetna.com/health-care-professionals/clinical-policy-bulletins/medical-clinical-policy-bulletins.html)
        - [Anthem](https://www.anthem.com/provider/policies/clinical-guidelines/updates/)
        - [CMS Medicare Coverage Database](https://www.cms.gov/medicare-coverage-database/downloads/downloads.aspx)

2. **Data Extraction and Standardization Overview**:
    - The extraction algorithm extracts medical necessity criteria and medical coding from aforementioned sources.
    - It uses SciSpacy, Named Entity Recognition (NER) and fuzzy matching to standardize necessity criteria and coding.
3. **Performance**:
    - We evaluate our algorithms performance on scalability and accuracy using precision recall and knowledge graphs
      

