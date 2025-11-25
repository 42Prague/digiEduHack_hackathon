
# Mock Data Generation Summary

Generated: 2025-11-14T07:41:49.899086

## Files Created

1. **transcripts.json** - 15 transcript records with metadata
2. **cultural_analyses.json** - 15 cultural analysis records
3. **dq_reports.json** - 5 diverse DQ reports
4. **api_responses.json** - Mock API responses for all endpoints
5. **insert_transcripts.sql** - SQL script to insert transcripts
6. **insert_cultural_analysis.sql** - SQL script to insert cultural analyses

## Data Coverage

### Transcripts
- **Total**: 15 transcripts
- **Regions**: 7 unique regions
- **School Types**: 4 types
- **Interventions**: 5 types
- **Roles**: 4 roles
- **Date Range**: 2023-01-01 to 2025-01-01

### Cultural Analysis Scores
- **High Performers**: 5 transcripts
- **Mid Performers**: 5 transcripts
- **Low Performers**: 5 transcripts

### Score Ranges
- **Mindset Shift**: 31 - 95
- **Collaboration**: 20 - 95
- **Teacher Confidence**: 30 - 90
- **Sentiment**: 28 - 84

### DQ Reports
- **High Quality**: 1 report (DQ Score: 95)
- **Missing Values**: 1 report (DQ Score: 72)
- **Schema Issues**: 1 report (DQ Score: 68)
- **PII Heavy**: 1 report (DQ Score: 78)
- **Mixed Issues**: 1 report (DQ Score: 65)

## Usage

### Load into Database
```bash
docker exec -i eduscale-db psql -U swx_user -d swx_db < mock_data/insert_transcripts.sql
docker exec -i eduscale-db psql -U swx_user -d swx_db < mock_data/insert_cultural_analysis.sql
```

### Use in Frontend Testing
The `api_responses.json` file contains mock responses for all endpoints that can be used for frontend testing.

## Next Steps

1. Load SQL scripts into database
2. Verify data appears in frontend
3. Test all charts and widgets
4. Verify all filters work correctly
