#!/usr/bin/env python3
"""
Generate Comprehensive Mock Data for EduScale Engine
Creates realistic synthetic data covering all features and UI widgets
"""

import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List
import random

# Output directory
OUTPUT_DIR = Path("mock_data")
OUTPUT_DIR.mkdir(exist_ok=True)

# Constants
REGIONS = ["praha", "brno", "ostrava", "plzen", "liberec", "olomouc", "ceske_budejovice", "pardubice"]
SCHOOL_TYPES = ["primary", "secondary", "gymnasium", "kindergarten", "special"]
INTERVENTION_TYPES = ["mentoring_program", "leadership_workshop", "team_training", "municipal_collaboration", "teacher_course", "other"]
PARTICIPANT_ROLES = ["teacher", "principal", "coordinator", "municipality"]

# Themes pool
THEMES_POOL = [
    "collaboration", "communication", "leadership", "professional_development",
    "student_engagement", "parent_involvement", "curriculum_innovation",
    "technology_integration", "inclusive_education", "assessment_reform",
    "teacher_wellbeing", "school_culture", "community_partnerships",
    "data_driven_decision_making", "pedagogical_innovation"
]

def generate_transcript_text(index: int, school_type: str, intervention: str) -> str:
    """Generate realistic transcript text."""
    templates = [
        f"""During our {intervention.replace('_', ' ')}, we observed significant improvements in staff collaboration. Teachers began sharing resources more openly, and there was a noticeable increase in cross-grade level communication. The principal noted that the school culture has shifted towards more supportive interactions. However, some challenges remain with time management and balancing new initiatives with existing responsibilities.""",
        
        f"""The {intervention.replace('_', ' ')} has transformed how we approach professional development. Previously, teachers worked in isolation, but now we have regular team meetings where we discuss student progress and share best practices. The municipality has been supportive, providing additional resources. We've seen improvements in teacher confidence, especially among newer staff members.""",
        
        f"""Our {school_type} school has experienced positive changes since implementing the {intervention.replace('_', ' ')}. Teachers report feeling more valued and heard. There's been an increase in innovative teaching methods, and students are more engaged. The collaboration with local authorities has been particularly effective, leading to better resource allocation.""",
        
        f"""While the {intervention.replace('_', ' ')} showed promise initially, we've encountered some resistance from staff who prefer traditional approaches. Communication between departments needs improvement. However, the principal's leadership has been crucial in maintaining momentum. We're seeing gradual mindset shifts, particularly around student-centered learning.""",
        
        f"""The intervention has created a more collaborative environment. Teachers are working together on curriculum design, and there's increased peer observation. The municipality's involvement has helped address infrastructure needs. We've noticed improvements in teacher morale and student outcomes, though measuring long-term impact remains a challenge.""",
    ]
    
    base = templates[index % len(templates)]
    variations = [
        "The focus on professional growth has been transformative.",
        "We've seen measurable improvements in student engagement.",
        "Parent feedback has been overwhelmingly positive.",
        "The school leadership has been instrumental in driving change.",
        "There are still areas for improvement, particularly in resource allocation.",
    ]
    
    return base + " " + " ".join(random.sample(variations, 2))

def generate_cultural_analysis(transcript_id: str, region: str, intervention: str, index: int) -> Dict[str, Any]:
    """Generate realistic cultural analysis scores."""
    # Create variation: some high, some low, some mid
    if index < 5:  # High performers
        base_scores = {
            "mindset_shift_score": random.randint(75, 95),
            "collaboration_score": random.randint(70, 90),
            "teacher_confidence_score": random.randint(75, 95),
            "municipality_cooperation_score": random.randint(65, 85),
            "sentiment_score": random.randint(70, 90),
        }
    elif index < 10:  # Mid performers
        base_scores = {
            "mindset_shift_score": random.randint(50, 75),
            "collaboration_score": random.randint(45, 70),
            "teacher_confidence_score": random.randint(50, 75),
            "municipality_cooperation_score": random.randint(40, 65),
            "sentiment_score": random.randint(45, 70),
        }
    else:  # Low performers (needs support)
        base_scores = {
            "mindset_shift_score": random.randint(25, 50),
            "collaboration_score": random.randint(20, 45),
            "teacher_confidence_score": random.randint(25, 50),
            "municipality_cooperation_score": random.randint(15, 40),
            "sentiment_score": random.randint(20, 45),
        }
    
    # Adjust based on intervention type
    if intervention == "mentoring_program":
        base_scores["teacher_confidence_score"] = min(100, base_scores["teacher_confidence_score"] + 10)
    elif intervention == "municipal_collaboration":
        base_scores["municipality_cooperation_score"] = min(100, base_scores["municipality_cooperation_score"] + 15)
    elif intervention == "team_training":
        base_scores["collaboration_score"] = min(100, base_scores["collaboration_score"] + 10)
    
    # Generate themes (3-8 per transcript)
    num_themes = random.randint(3, 8)
    themes = random.sample(THEMES_POOL, num_themes)
    
    # Generate text summaries
    practical_changes = [
        "Teachers now regularly share lesson plans and resources through a common platform.",
        "Weekly team meetings have become standard practice across all departments.",
        "The school has implemented peer observation programs to support professional growth.",
        "Cross-grade collaboration projects have increased student engagement.",
        "New communication channels have improved parent-teacher relationships.",
    ]
    
    mindset_changes = [
        "Shift from individual teaching to collaborative learning communities.",
        "Increased focus on student-centered approaches rather than traditional methods.",
        "Greater openness to innovation and experimentation in pedagogy.",
        "Enhanced sense of collective responsibility for student outcomes.",
        "More proactive approach to addressing challenges and seeking solutions.",
    ]
    
    impact_summaries = [
        f"""The {intervention.replace('_', ' ')} has created a more cohesive school environment. Teachers report feeling more supported and valued, which has translated into improved classroom practices. Student engagement has increased, and there's a noticeable improvement in overall school climate. The collaboration with local authorities has been particularly effective, leading to better resource allocation and support.""",
        
        f"""While the intervention showed initial promise, implementation challenges have emerged. Some staff members remain resistant to change, and communication gaps persist between departments. However, the principal's leadership has been crucial in maintaining momentum. Gradual mindset shifts are occurring, particularly around student-centered learning approaches.""",
        
        f"""The program has transformed professional development practices. Teachers are now more open to sharing experiences and learning from each other. The focus on collaboration has led to innovative teaching methods and improved student outcomes. Parent feedback has been positive, and the school's reputation in the community has strengthened.""",
    ]
    
    return {
        "id": str(uuid.uuid4()),
        "transcript_id": transcript_id,
        "mindset_shift_score": base_scores["mindset_shift_score"],
        "collaboration_score": base_scores["collaboration_score"],
        "teacher_confidence_score": base_scores["teacher_confidence_score"],
        "municipality_cooperation_score": base_scores["municipality_cooperation_score"],
        "sentiment_score": base_scores["sentiment_score"],
        "themes": themes,
        "practical_change": random.choice(practical_changes),
        "mindset_change": random.choice(mindset_changes),
        "impact_summary": random.choice(impact_summaries),
        "culture_change_detected": base_scores["mindset_shift_score"] > 60,
        "created_at": (datetime.now() - timedelta(days=random.randint(0, 730))).isoformat(),
    }

def generate_transcripts() -> List[Dict[str, Any]]:
    """Generate 15 transcript records with full metadata."""
    transcripts = []
    base_date = datetime(2023, 1, 1)
    
    for i in range(15):
        transcript_id = str(uuid.uuid4())
        region = random.choice(REGIONS)
        school_type = random.choice(SCHOOL_TYPES)
        intervention = random.choice(INTERVENTION_TYPES)
        role = random.choice(PARTICIPANT_ROLES)
        school_id = f"SCHOOL_{region.upper()}_{i+1:03d}"
        
        # Spread dates over 2023-2025
        days_offset = random.randint(0, 730)
        interview_date = (base_date + timedelta(days=days_offset)).strftime("%Y-%m-%d")
        
        transcript_text = generate_transcript_text(i, school_type, intervention)
        clean_text = " ".join(transcript_text.split())  # Normalized
        
        transcript = {
            "id": transcript_id,
            "file_type": "transcript",
            "original_filename": f"interview_{school_id}_{interview_date}.md",
            "upload_metadata": {
                "school_id": school_id,
                "region_id": region,
                "school_type": school_type,
                "intervention_type": intervention,
                "participant_role": role,
                "interview_date": interview_date,
            },
            "transcript_text": transcript_text,
            "clean_text": clean_text,
            "raw_file_path": f"/data/raw/transcripts/{transcript_id}.md",
            "transcript_path": f"/data/processed/transcripts/{transcript_id}.txt",
            "created_at": interview_date + "T10:00:00Z",
            "updated_at": interview_date + "T10:00:00Z",
        }
        
        transcripts.append(transcript)
    
    return transcripts

def generate_dq_reports() -> List[Dict[str, Any]]:
    """Generate 5 diverse DQ reports."""
    reports = []
    
    # Report 1: High quality
    reports.append({
        "dataset_id": "dataset_high_quality",
        "dq_score": 95,
        "total_rows": 150,
        "valid_rows": 148,
        "invalid_rows": 2,
        "missing_values": {
            "email": 3,
            "phone": 1,
        },
        "pii_found_and_masked": {
            "names": 0,
            "emails": 0,
            "phones": 0,
        },
        "schema_issues": [],
        "normalization_fixes": ["Standardized date format", "Normalized region names"],
        "quarantined_rows_path": None,
    })
    
    # Report 2: Missing values
    reports.append({
        "dataset_id": "dataset_missing_values",
        "dq_score": 72,
        "total_rows": 200,
        "valid_rows": 180,
        "invalid_rows": 20,
        "missing_values": {
            "school_id": 15,
            "region_id": 8,
            "score": 25,
            "date": 12,
        },
        "pii_found_and_masked": {
            "names": 2,
            "emails": 5,
            "phones": 1,
        },
        "schema_issues": ["Inconsistent date formats"],
        "normalization_fixes": ["Fixed date formats", "Standardized region codes"],
        "quarantined_rows_path": "/data/processed/clean/dataset_missing_values_quarantined.json",
    })
    
    # Report 3: Schema issues
    reports.append({
        "dataset_id": "dataset_schema_issues",
        "dq_score": 68,
        "total_rows": 100,
        "valid_rows": 85,
        "invalid_rows": 15,
        "missing_values": {
            "name": 10,
        },
        "pii_found_and_masked": {
            "names": 8,
            "emails": 12,
            "phones": 3,
        },
        "schema_issues": [
            {"column": "score", "issue": "Mixed data types (string and numeric)"},
            {"column": "date", "issue": "Multiple date formats"},
            {"column": "region", "issue": "Inconsistent naming"},
        ],
        "normalization_fixes": [
            "Converted score column to numeric",
            "Standardized all dates to YYYY-MM-DD",
            "Normalized region names",
        ],
        "quarantined_rows_path": "/data/processed/clean/dataset_schema_issues_quarantined.json",
    })
    
    # Report 4: PII heavy
    reports.append({
        "dataset_id": "dataset_pii_heavy",
        "dq_score": 78,
        "total_rows": 120,
        "valid_rows": 115,
        "invalid_rows": 5,
        "missing_values": {
            "email": 5,
        },
        "pii_found_and_masked": {
            "names": 45,
            "emails": 38,
            "phones": 22,
        },
        "schema_issues": [],
        "normalization_fixes": ["Masked all PII", "Standardized formats"],
        "quarantined_rows_path": None,
    })
    
    # Report 5: Mixed issues
    reports.append({
        "dataset_id": "dataset_mixed_issues",
        "dq_score": 65,
        "total_rows": 180,
        "valid_rows": 150,
        "invalid_rows": 30,
        "missing_values": {
            "school_id": 20,
            "score": 15,
            "region": 8,
            "date": 12,
        },
        "pii_found_and_masked": {
            "names": 15,
            "emails": 20,
            "phones": 8,
        },
        "schema_issues": [
            {"column": "score", "issue": "Out of range values"},
            {"column": "date", "issue": "Invalid dates"},
        ],
        "normalization_fixes": [
            "Removed out of range scores",
            "Fixed invalid dates",
            "Masked PII",
        ],
        "quarantined_rows_path": "/data/processed/clean/dataset_mixed_issues_quarantined.json",
    })
    
    return reports

def generate_api_responses(transcripts: List[Dict], cultural_analyses: List[Dict], dq_reports: List[Dict]) -> Dict[str, Any]:
    """Generate mock API responses for all endpoints."""
    
    # Aggregate data for summaries
    region_summaries = {}
    school_summaries = {}
    intervention_summaries = {}
    
    for i, transcript in enumerate(transcripts):
        region = transcript["upload_metadata"]["region_id"]
        school = transcript["upload_metadata"]["school_id"]
        intervention = transcript["upload_metadata"]["intervention_type"]
        ca = cultural_analyses[i]
        
        # Region aggregates
        if region not in region_summaries:
            region_summaries[region] = {
                "total_transcripts": 0,
                "scores": [],
            }
        region_summaries[region]["total_transcripts"] += 1
        region_summaries[region]["scores"].append({
            "mindset": ca["mindset_shift_score"],
            "collaboration": ca["collaboration_score"],
            "confidence": ca["teacher_confidence_score"],
            "municipality": ca["municipality_cooperation_score"],
            "sentiment": ca["sentiment_score"],
        })
        
        # School aggregates
        if school not in school_summaries:
            school_summaries[school] = {
                "scores": [],
                "region": region,
            }
        school_summaries[school]["scores"].append({
            "mindset": ca["mindset_shift_score"],
            "collaboration": ca["collaboration_score"],
            "confidence": ca["teacher_confidence_score"],
            "municipality": ca["municipality_cooperation_score"],
            "sentiment": ca["sentiment_score"],
        })
        
        # Intervention aggregates
        if intervention not in intervention_summaries:
            intervention_summaries[intervention] = {
                "scores": [],
                "count": 0,
            }
        intervention_summaries[intervention]["count"] += 1
        intervention_summaries[intervention]["scores"].append({
            "mindset": ca["mindset_shift_score"],
            "collaboration": ca["collaboration_score"],
            "confidence": ca["teacher_confidence_score"],
            "municipality": ca["municipality_cooperation_score"],
            "sentiment": ca["sentiment_score"],
        })
    
    # Calculate averages
    def avg_scores(scores_list):
        if not scores_list:
            return {}
        return {
            "avg_mindset": sum(s["mindset"] for s in scores_list) / len(scores_list),
            "avg_collaboration": sum(s["collaboration"] for s in scores_list) / len(scores_list),
            "avg_confidence": sum(s["confidence"] for s in scores_list) / len(scores_list),
            "avg_municipality": sum(s["municipality"] for s in scores_list) / len(scores_list),
            "avg_sentiment": sum(s["sentiment"] for s in scores_list) / len(scores_list),
        }
    
    # Generate region insights
    region_insights = {}
    for region, data in region_summaries.items():
        scores = data["scores"]
        region_insights[region] = {
            "region_id": region,
            "summary": {
                "total_transcripts": data["total_transcripts"],
                **avg_scores(scores),
            },
            "top_schools": sorted(
                [(s, avg_scores(school_summaries[s]["scores"])) for s in school_summaries if school_summaries[s]["region"] == region],
                key=lambda x: x[1].get("avg_sentiment", 0),
                reverse=True
            )[:5],
            "schools_needing_support": sorted(
                [(s, avg_scores(school_summaries[s]["scores"])) for s in school_summaries if school_summaries[s]["region"] == region],
                key=lambda x: x[1].get("avg_sentiment", 0),
            )[:5],
            "intervention_effectiveness": {
                interv: {
                    "avg_score": sum(s["sentiment"] for s in interv_data["scores"]) / len(interv_data["scores"]) if interv_data["scores"] else 0,
                    "count": interv_data["count"],
                }
                for interv, interv_data in intervention_summaries.items()
            },
            "frequent_themes": [
                {"theme": theme, "count": sum(1 for ca in cultural_analyses if theme in ca["themes"])}
                for theme in THEMES_POOL[:10]
            ],
        }
    
    # Generate sentiment trends (time series)
    sentiment_trends = []
    base_date = datetime(2023, 1, 1)
    for month in range(24):  # 2 years of data
        date = (base_date + timedelta(days=month * 30)).strftime("%Y-%m")
        # Get transcripts for this month
        month_transcripts = [
            t for t in transcripts
            if t["created_at"].startswith(date[:7])
        ]
        if month_transcripts:
            month_scores = [
                cultural_analyses[i]["sentiment_score"]
                for i, t in enumerate(transcripts)
                if t in month_transcripts
            ]
            sentiment_trends.append({
                "date": date,
                "value": sum(month_scores) / len(month_scores) if month_scores else 50,
            })
    
    return {
        "transcripts_list": transcripts,
        "transcript_details": [
            {
                **t,
                "cultural_analysis": ca,
                "dq_report": None,  # Can be added if needed
            }
            for t, ca in zip(transcripts, cultural_analyses)
        ],
        "analytics_summary": {
            "datasets": [f"dataset_{i}" for i in range(10)],
            "metrics": {
                "mindset_shift": {
                    "mean": sum(ca["mindset_shift_score"] for ca in cultural_analyses) / len(cultural_analyses),
                    "median": sorted([ca["mindset_shift_score"] for ca in cultural_analyses])[len(cultural_analyses) // 2],
                    "std": 15.5,
                    "min": min(ca["mindset_shift_score"] for ca in cultural_analyses),
                    "max": max(ca["mindset_shift_score"] for ca in cultural_analyses),
                },
                "collaboration": {
                    "mean": sum(ca["collaboration_score"] for ca in cultural_analyses) / len(cultural_analyses),
                    "median": sorted([ca["collaboration_score"] for ca in cultural_analyses])[len(cultural_analyses) // 2],
                    "std": 18.2,
                    "min": min(ca["collaboration_score"] for ca in cultural_analyses),
                    "max": max(ca["collaboration_score"] for ca in cultural_analyses),
                },
            },
            "generated_at": datetime.now().isoformat(),
        },
        "sentiment_trends": sentiment_trends,
        "region_insights": region_insights,
        "recommendations": {
            "school_recommendations": [
                "Consider implementing peer observation programs to improve collaboration scores.",
                "Focus on professional development workshops to boost teacher confidence.",
                "Strengthen communication channels between staff and administration.",
            ],
            "region_recommendations": [
                "Increase investment in mentoring programs for underperforming schools.",
                "Facilitate cross-school collaboration initiatives.",
                "Provide additional support for schools with low cultural scores.",
            ],
            "intervention_recommendations": [
                "Expand successful mentoring programs to more schools.",
                "Evaluate and refine leadership workshop curriculum.",
                "Increase municipality coordination efforts.",
            ],
            "culture_warnings": [
                "School SCHOOL_PRAHA_005 shows declining collaboration scores.",
                "Region brno has multiple schools needing support.",
            ],
            "strengths": [
                "Strong teacher confidence in praha region.",
                "Excellent municipality cooperation in plzen.",
                "High collaboration scores in mentoring programs.",
            ],
        },
        "school_comparison": {
            "comparisons": {
                transcripts[0]["upload_metadata"]["school_id"]: {
                    "mindset_shift_score": cultural_analyses[0]["mindset_shift_score"],
                    "collaboration_score": cultural_analyses[0]["collaboration_score"],
                    "teacher_confidence_score": cultural_analyses[0]["teacher_confidence_score"],
                    "municipality_cooperation_score": cultural_analyses[0]["municipality_cooperation_score"],
                    "sentiment_score": cultural_analyses[0]["sentiment_score"],
                },
                transcripts[1]["upload_metadata"]["school_id"]: {
                    "mindset_shift_score": cultural_analyses[1]["mindset_shift_score"],
                    "collaboration_score": cultural_analyses[1]["collaboration_score"],
                    "teacher_confidence_score": cultural_analyses[1]["teacher_confidence_score"],
                    "municipality_cooperation_score": cultural_analyses[1]["municipality_cooperation_score"],
                    "sentiment_score": cultural_analyses[1]["sentiment_score"],
                },
            },
        },
        "dq_reports": dq_reports,
    }

def main():
    """Generate all mock data."""
    print("🎯 Generating comprehensive mock data for EduScale Engine...")
    
    # Generate transcripts
    print("📝 Generating 15 transcripts...")
    transcripts = generate_transcripts()
    
    # Generate cultural analyses
    print("🧠 Generating cultural analyses...")
    cultural_analyses = [
        generate_cultural_analysis(t["id"], t["upload_metadata"]["region_id"], 
                                  t["upload_metadata"]["intervention_type"], i)
        for i, t in enumerate(transcripts)
    ]
    
    # Generate DQ reports
    print("📊 Generating DQ reports...")
    dq_reports = generate_dq_reports()
    
    # Generate API responses
    print("🔌 Generating API response mocks...")
    api_responses = generate_api_responses(transcripts, cultural_analyses, dq_reports)
    
    # Save all data
    print("💾 Saving mock data files...")
    
    # Save transcripts
    with open(OUTPUT_DIR / "transcripts.json", "w") as f:
        json.dump(transcripts, f, indent=2, ensure_ascii=False)
    
    # Save cultural analyses
    with open(OUTPUT_DIR / "cultural_analyses.json", "w") as f:
        json.dump(cultural_analyses, f, indent=2, ensure_ascii=False)
    
    # Save DQ reports
    with open(OUTPUT_DIR / "dq_reports.json", "w") as f:
        json.dump(dq_reports, f, indent=2, ensure_ascii=False)
    
    # Save API responses
    with open(OUTPUT_DIR / "api_responses.json", "w") as f:
        json.dump(api_responses, f, indent=2, ensure_ascii=False)
    
    # Save SQL insert scripts
    print("📄 Generating SQL insert scripts...")
    
    # Transcripts SQL
    sql_transcripts = []
    for t in transcripts:
        sql_transcripts.append(f"""
INSERT INTO transcripts (id, file_type, original_filename, upload_metadata, transcript_text, clean_text, raw_file_path, transcript_path, created_at, updated_at)
VALUES (
    '{t["id"]}',
    '{t["file_type"]}',
    '{t["original_filename"]}',
    '{json.dumps(t["upload_metadata"]).replace("'", "''")}',
    '{t["transcript_text"].replace("'", "''")}',
    '{t["clean_text"].replace("'", "''")}',
    '{t["raw_file_path"]}',
    '{t["transcript_path"]}',
    '{t["created_at"]}',
    '{t["updated_at"]}'
);
""")
    
    # Cultural analyses SQL
    sql_cultural = []
    for ca in cultural_analyses:
        sql_cultural.append(f"""
INSERT INTO cultural_analysis (id, transcript_id, mindset_shift_score, collaboration_score, teacher_confidence_score, municipality_cooperation_score, sentiment_score, themes, practical_change, mindset_change, impact_summary, culture_change_detected, created_at)
VALUES (
    '{ca["id"]}',
    '{ca["transcript_id"]}',
    {ca["mindset_shift_score"]},
    {ca["collaboration_score"]},
    {ca["teacher_confidence_score"]},
    {ca["municipality_cooperation_score"]},
    {ca["sentiment_score"]},
    '{json.dumps(ca["themes"]).replace("'", "''")}',
    '{ca["practical_change"].replace("'", "''")}',
    '{ca["mindset_change"].replace("'", "''")}',
    '{ca["impact_summary"].replace("'", "''")}',
    {str(ca["culture_change_detected"]).upper()},
    '{ca["created_at"]}'
);
""")
    
    with open(OUTPUT_DIR / "insert_transcripts.sql", "w") as f:
        f.write("-- Insert mock transcripts\n")
        f.writelines(sql_transcripts)
    
    with open(OUTPUT_DIR / "insert_cultural_analysis.sql", "w") as f:
        f.write("-- Insert mock cultural analyses\n")
        f.writelines(sql_cultural)
    
    # Generate summary document
    summary = f"""
# Mock Data Generation Summary

Generated: {datetime.now().isoformat()}

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
- **Regions**: {len(set(t['upload_metadata']['region_id'] for t in transcripts))} unique regions
- **School Types**: {len(set(t['upload_metadata']['school_type'] for t in transcripts))} types
- **Interventions**: {len(set(t['upload_metadata']['intervention_type'] for t in transcripts))} types
- **Roles**: {len(set(t['upload_metadata']['participant_role'] for t in transcripts))} roles
- **Date Range**: 2023-01-01 to 2025-01-01

### Cultural Analysis Scores
- **High Performers**: {sum(1 for ca in cultural_analyses if ca['mindset_shift_score'] > 75)} transcripts
- **Mid Performers**: {sum(1 for ca in cultural_analyses if 50 <= ca['mindset_shift_score'] <= 75)} transcripts
- **Low Performers**: {sum(1 for ca in cultural_analyses if ca['mindset_shift_score'] < 50)} transcripts

### Score Ranges
- **Mindset Shift**: {min(ca['mindset_shift_score'] for ca in cultural_analyses)} - {max(ca['mindset_shift_score'] for ca in cultural_analyses)}
- **Collaboration**: {min(ca['collaboration_score'] for ca in cultural_analyses)} - {max(ca['collaboration_score'] for ca in cultural_analyses)}
- **Teacher Confidence**: {min(ca['teacher_confidence_score'] for ca in cultural_analyses)} - {max(ca['teacher_confidence_score'] for ca in cultural_analyses)}
- **Sentiment**: {min(ca['sentiment_score'] for ca in cultural_analyses)} - {max(ca['sentiment_score'] for ca in cultural_analyses)}

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
"""
    
    with open(OUTPUT_DIR / "README.md", "w") as f:
        f.write(summary)
    
    print(f"\n✅ Mock data generation complete!")
    print(f"📁 Files saved to: {OUTPUT_DIR.absolute()}")
    print(f"\n📊 Summary:")
    print(f"  - Transcripts: {len(transcripts)}")
    print(f"  - Cultural Analyses: {len(cultural_analyses)}")
    print(f"  - DQ Reports: {len(dq_reports)}")
    print(f"  - API Response Mocks: {len(api_responses)}")
    print(f"\n🚀 To load into database:")
    print(f"  docker exec -i eduscale-db psql -U swx_user -d swx_db < mock_data/insert_transcripts.sql")
    print(f"  docker exec -i eduscale-db psql -U swx_user -d swx_db < mock_data/insert_cultural_analysis.sql")

if __name__ == "__main__":
    main()

