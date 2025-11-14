# 🎯 Loading Demo Data

This directory contains mock data for demonstrating the EduScale Engine.

## Quick Load (Docker)

```bash
# Make sure services are running
docker compose up -d db backend

# Load transcripts
docker compose exec -T db psql -U swx_user -d swx_db < mock_data/insert_transcripts.sql

# Load cultural analyses
docker compose exec -T db psql -U swx_user -d swx_db < mock_data/insert_cultural_analysis.sql

# Verify data loaded
docker compose exec db psql -U swx_user -d swx_db -c "SELECT COUNT(*) FROM transcripts;"
docker compose exec db psql -U swx_user -d swx_db -c "SELECT COUNT(*) FROM cultural_analysis;"
```

## What's Included

- **15 Transcripts** - Diverse schools, regions, interventions, and dates
- **15 Cultural Analyses** - Complete scoring and insights
- **5 DQ Reports** - Various data quality scenarios
- **API Response Examples** - For frontend testing

## Data Coverage

- **Regions**: 7 unique regions (praha, brno, ostrava, plzen, liberec, olomouc, ceske_budejovice)
- **School Types**: 4 types (primary, secondary, kindergarten, gymnasium)
- **Interventions**: 5 types (mentoring_program, leadership_workshop, team_training, municipal_collaboration, teacher_course)
- **Roles**: 4 roles (teacher, principal, coordinator, municipality)
- **Date Range**: 2023-01-01 to 2025-01-01
- **Score Ranges**: 
  - Mindset Shift: 31-95
  - Collaboration: 20-95
  - Teacher Confidence: 30-90
  - Sentiment: 28-84

## Screenshots for Demo

After loading, you can take screenshots of:
1. Dashboard with data visualizations
2. Transcript analysis pages
3. School comparison charts
4. Region insights
5. Recommendations page
6. Data quality reports

## Regenerating Data

If you need to regenerate the mock data:

```bash
cd mock_data
python3 generate_mock_data.py
```

This will create fresh SQL files and JSON examples.
