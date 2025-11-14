"""
====================================================================
MOCK DATA GENERATOR
Generates realistic longitudinal survey data for testing
====================================================================
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy import text
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import after path is set
from database_utils import get_database_connection, insert_survey_response, generate_response_id, format_date

# Set random seed for reproducibility
np.random.seed(42)

# ====================================================================
# CONFIGURATION
# ====================================================================

# Study timeline
BASELINE_DATE = datetime(2024, 1, 15)  # January 2024
TIME_POINTS = [
    {'months': 0, 'label': 'Baseline'},
    {'months': 3, 'label': '3-Month Follow-up'},
    {'months': 6, 'label': '6-Month Follow-up'},
    {'months': 9, 'label': '9-Month Follow-up'},
    {'months': 12, 'label': '12-Month Follow-up'}
]

# Regions and schools configuration
REGIONS = [
    {
        'region_id': 'Region_1',
        'name': 'Northern District',
        'schools': [
            {'id': 'S101', 'name': 'Lincoln Elementary', 'intervention': 'Treatment'},
            {'id': 'S102', 'name': 'Washington Middle', 'intervention': 'Control'},
            {'id': 'S103', 'name': 'Roosevelt High', 'intervention': 'Treatment'},
            {'id': 'S104', 'name': 'Jefferson Elementary', 'intervention': 'Control'},
            {'id': 'S105', 'name': 'Kennedy Middle', 'intervention': 'Treatment'},
            {'id': 'S106', 'name': 'Reagan High', 'intervention': 'Control'},
            {'id': 'S107', 'name': 'Carter Elementary', 'intervention': 'Treatment'},
        ]
    },
    {
        'region_id': 'Region_2',
        'name': 'Central District',
        'schools': [
            {'id': 'S201', 'name': 'Adams Middle', 'intervention': 'Treatment'},
            {'id': 'S202', 'name': 'Madison High', 'intervention': 'Control'},
            {'id': 'S203', 'name': 'Monroe Elementary', 'intervention': 'Treatment'},
            {'id': 'S204', 'name': 'Jackson Middle', 'intervention': 'Control'},
            {'id': 'S205', 'name': 'Van Buren High', 'intervention': 'Treatment'},
            {'id': 'S206', 'name': 'Harrison Elementary', 'intervention': 'Control'},
            {'id': 'S207', 'name': 'Tyler Middle', 'intervention': 'Treatment'},
            {'id': 'S208', 'name': 'Polk High', 'intervention': 'Control'},
        ]
    },
    {
        'region_id': 'Region_3',
        'name': 'Southern District',
        'schools': [
            {'id': 'S301', 'name': 'Taylor Elementary', 'intervention': 'Treatment'},
            {'id': 'S302', 'name': 'Fillmore Middle', 'intervention': 'Control'},
            {'id': 'S303', 'name': 'Pierce High', 'intervention': 'Treatment'},
            {'id': 'S304', 'name': 'Buchanan Elementary', 'intervention': 'Control'},
            {'id': 'S305', 'name': 'Lincoln Academy', 'intervention': 'Treatment'},
            {'id': 'S306', 'name': 'Johnson Middle', 'intervention': 'Control'},
        ]
    },
    {
        'region_id': 'Region_4',
        'name': 'Eastern District',
        'schools': [
            {'id': 'S401', 'name': 'Grant Elementary', 'intervention': 'Treatment'},
            {'id': 'S402', 'name': 'Hayes Middle', 'intervention': 'Control'},
            {'id': 'S403', 'name': 'Garfield High', 'intervention': 'Treatment'},
            {'id': 'S404', 'name': 'Arthur Elementary', 'intervention': 'Control'},
            {'id': 'S405', 'name': 'Cleveland Middle', 'intervention': 'Treatment'},
            {'id': 'S406', 'name': 'McKinley High', 'intervention': 'Control'},
            {'id': 'S407', 'name': 'Roosevelt Academy', 'intervention': 'Treatment'},
            {'id': 'S408', 'name': 'Taft Elementary', 'intervention': 'Control'},
            {'id': 'S409', 'name': 'Wilson Middle', 'intervention': 'Treatment'},
        ]
    },
    {
        'region_id': 'Region_5',
        'name': 'Western District',
        'schools': [
            {'id': 'S501', 'name': 'Harding Elementary', 'intervention': 'Treatment'},
            {'id': 'S502', 'name': 'Coolidge Middle', 'intervention': 'Control'},
            {'id': 'S503', 'name': 'Hoover High', 'intervention': 'Treatment'},
            {'id': 'S504', 'name': 'Truman Elementary', 'intervention': 'Control'},
            {'id': 'S505', 'name': 'Eisenhower Middle', 'intervention': 'Treatment'},
            {'id': 'S506', 'name': 'Nixon High', 'intervention': 'Control'},
            {'id': 'S507', 'name': 'Ford Academy', 'intervention': 'Treatment'},
        ]
    }
]

# Teacher configuration
TEACHERS_PER_SCHOOL = {
    'Elementary': np.random.randint(6, 11),  # 6-10 teachers
    'Middle': np.random.randint(8, 13),      # 8-12 teachers
    'High': np.random.randint(10, 16),       # 10-15 teachers
    'Academy': np.random.randint(7, 11)      # 7-10 teachers
}

GRADE_LEVELS = {
    'Elementary': ['Grade_K', 'Grade_1', 'Grade_2', 'Grade_3', 'Grade_4', 'Grade_5'],
    'Middle': ['Grade_6', 'Grade_7', 'Grade_8'],
    'High': ['Grade_9', 'Grade_10', 'Grade_11', 'Grade_12'],
    'Academy': ['Grade_6', 'Grade_7', 'Grade_8', 'Grade_9', 'Grade_10']
}

SUBJECT_AREAS = ['Math', 'Science', 'English', 'Social Studies', 'Art', 'Physical Education', 'Music']
TEACHING_EXPERIENCE = ['0-2', '3-5', '6-10', '11-15', '16-20', '20+']

# ====================================================================
# HELPER FUNCTIONS
# ====================================================================

def get_school_type(school_name):
    """Determine school type from name."""
    if 'Elementary' in school_name:
        return 'Elementary'
    elif 'Middle' in school_name:
        return 'Middle'
    elif 'High' in school_name:
        return 'High'
    elif 'Academy' in school_name:
        return 'Academy'
    return 'Middle'  # default

def generate_baseline_performance():
    """Generate realistic baseline performance (slightly below average)."""
    # Baseline: mean=3.0, std=0.8
    return max(1, min(5, int(np.round(np.random.normal(3.0, 0.8)))))

def generate_performance_with_trend(baseline, time_point_index, intervention_status, outcome_type='performance'):
    """
    Generate performance that shows realistic intervention effect over time.
    
    Treatment group: gradual improvement
    Control group: minimal change (slight natural improvement)
    """
    
    if intervention_status == 'Treatment':
        # Treatment effect increases over time
        # Stronger effect for engagement and problem-solving
        if outcome_type == 'engagement':
            improvement = time_point_index * 0.35  # Engagement improves most
        elif outcome_type == 'problem_solving':
            improvement = time_point_index * 0.28
        elif outcome_type == 'critical_thinking':
            improvement = time_point_index * 0.25
        elif outcome_type == 'collaboration':
            improvement = time_point_index * 0.30
        else:  # general performance
            improvement = time_point_index * 0.22
            
        # Add some random variation (not all schools improve equally)
        improvement += np.random.normal(0, 0.15)
        
    else:  # Control group
        # Minimal natural improvement (learning effect, teacher experience)
        improvement = time_point_index * 0.05 + np.random.normal(0, 0.1)
    
    # Calculate new score
    new_score = baseline + improvement
    
    # Keep within bounds [1, 5]
    return max(1, min(5, int(np.round(new_score))))

def generate_change_rating(baseline, current, time_point_index):
    """Generate change rating based on actual performance difference."""
    if time_point_index == 0:
        return None  # N/A at baseline
    
    diff = current - baseline
    
    if diff <= -1.5:
        return 1  # Declined significantly
    elif diff <= -0.5:
        return 2  # Declined somewhat
    elif diff < 0.5:
        return 3  # Stayed the same
    elif diff < 1.5:
        return 4  # Improved somewhat
    else:
        return 5  # Improved significantly

def generate_intervention_impact(time_point_index, baseline_perf, current_perf):
    """Generate intervention impact rating."""
    if time_point_index == 0:
        return None  # N/A at baseline
    
    improvement = current_perf - baseline_perf
    
    if improvement < 0.3:
        return 1  # No noticeable impact
    elif improvement < 0.7:
        return 2  # Slight positive impact
    elif improvement < 1.2:
        return 3  # Moderate positive impact
    elif improvement < 1.8:
        return 4  # Significant positive impact
    else:
        return 5  # Very strong positive impact

# ====================================================================
# MAIN DATA GENERATION
# ====================================================================

def generate_mock_data():
    """Generate comprehensive mock survey data."""
    
    print("=" * 60)
    print("🎲 MOCK DATA GENERATOR")
    print("=" * 60)
    print()
    
    all_responses = []
    teacher_counter = 1
    
    # Generate data for each region
    for region in REGIONS:
        print(f"📍 Generating data for {region['name']} ({region['region_id']})")
        
        for school in region['schools']:
            school_type = get_school_type(school['name'])
            num_teachers = TEACHERS_PER_SCHOOL[school_type]
            
            print(f"   🏫 {school['name']} ({school['intervention']}) - {num_teachers} teachers")
            
            # Generate teachers for this school
            for t in range(num_teachers):
                teacher_id = f"T{teacher_counter:03d}"
                teacher_counter += 1
                
                # Teacher demographics (stay constant)
                grade = np.random.choice(GRADE_LEVELS[school_type])
                subject = np.random.choice(SUBJECT_AREAS)
                experience = np.random.choice(TEACHING_EXPERIENCE, p=[0.15, 0.25, 0.30, 0.20, 0.08, 0.02])
                class_size = int(np.random.normal(25, 5))
                class_size = max(10, min(40, class_size))
                
                # Generate baseline performance (will be used for all time points)
                baseline_perf = {
                    'b1': generate_baseline_performance(),
                    'b2': generate_baseline_performance(),
                    'b3': generate_baseline_performance(),
                    'b4': generate_baseline_performance(),
                    'b5': generate_baseline_performance(),
                    'b6': generate_baseline_performance(),
                    'b7': generate_baseline_performance(),
                    'b8': generate_baseline_performance(),
                }
                
                # Generate intervention components (random for treatment schools)
                if school['intervention'] == 'Treatment':
                    comp1 = int(np.random.random() > 0.3)  # 70% use component 1
                    comp2 = int(np.random.random() > 0.4)  # 60% use component 2
                    comp3 = int(np.random.random() > 0.5)  # 50% use component 3
                    comp4 = int(np.random.random() > 0.6)  # 40% use component 4
                else:
                    comp1 = comp2 = comp3 = comp4 = 0
                
                # Generate response for each time point
                for tp_idx, time_point in enumerate(TIME_POINTS):
                    survey_date = BASELINE_DATE + timedelta(days=int(time_point['months'] * 30.44))
                    
                    # 90% response rate (some teachers don't complete every survey)
                    if np.random.random() > 0.9:
                        continue
                    
                    # Generate current performance (with trend)
                    current_perf = {
                        'b1': generate_performance_with_trend(baseline_perf['b1'], tp_idx, school['intervention'], 'performance'),
                        'b2': generate_performance_with_trend(baseline_perf['b2'], tp_idx, school['intervention'], 'problem_solving'),
                        'b3': generate_performance_with_trend(baseline_perf['b3'], tp_idx, school['intervention'], 'critical_thinking'),
                        'b4': generate_performance_with_trend(baseline_perf['b4'], tp_idx, school['intervention'], 'collaboration'),
                        'b5': generate_performance_with_trend(baseline_perf['b5'], tp_idx, school['intervention'], 'performance'),
                        'b6': generate_performance_with_trend(baseline_perf['b6'], tp_idx, school['intervention'], 'engagement'),
                        'b7': generate_performance_with_trend(baseline_perf['b7'], tp_idx, school['intervention'], 'performance'),
                        'b8': generate_performance_with_trend(baseline_perf['b8'], tp_idx, school['intervention'], 'performance'),
                    }
                    
                    # Generate change ratings
                    c1 = generate_change_rating(baseline_perf['b1'], current_perf['b1'], tp_idx)
                    c2 = generate_change_rating(baseline_perf['b2'], current_perf['b2'], tp_idx)
                    c3 = generate_change_rating(baseline_perf['b6'], current_perf['b6'], tp_idx)
                    c4 = generate_change_rating(baseline_perf['b5'], current_perf['b5'], tp_idx)
                    c5 = generate_change_rating(baseline_perf['b7'], current_perf['b7'], tp_idx)
                    
                    # Generate intervention impact (Treatment only)
                    if school['intervention'] == 'Treatment':
                        composite_baseline = sum(baseline_perf.values()) / len(baseline_perf)
                        composite_current = sum(current_perf.values()) / len(current_perf)
                        d1 = generate_intervention_impact(tp_idx, composite_baseline, composite_current)
                    else:
                        d1 = None
                    
                    # Create response
                    response = {
                        'response_id': generate_response_id(),
                        'survey_date': format_date(survey_date),
                        'teacher_id': teacher_id,
                        'school_id': school['id'],
                        'school_name': school['name'],
                        'region': region['region_id'],
                        'teaching_experience_years': int(experience.split('-')[0]) if '-' in experience else 20,
                        'grade_level': grade,
                        'subject_area': subject,
                        'class_size': class_size,
                        'intervention_status': school['intervention'],
                        'intervention_duration_months': time_point['months'] if school['intervention'] == 'Treatment' else 0,
                        'intervention_component_1': comp1,
                        'intervention_component_2': comp2,
                        'intervention_component_3': comp3,
                        'intervention_component_4': comp4,
                        'b1_overall_performance': current_perf['b1'],
                        'b2_problem_solving': current_perf['b2'],
                        'b3_critical_thinking': current_perf['b3'],
                        'b4_collaboration': current_perf['b4'],
                        'b5_communication': current_perf['b5'],
                        'b6_engagement': current_perf['b6'],
                        'b7_behavior': current_perf['b7'],
                        'b8_persistence': current_perf['b8'],
                        'c1_performance_change': c1,
                        'c2_problem_solving_change': c2,
                        'c3_engagement_change': c3,
                        'c4_communication_change': c4,
                        'c5_behavior_change': c5,
                        'd1_intervention_impact': d1,
                        'd2_skill_most_improved_1': 'Problem-solving' if school['intervention'] == 'Treatment' else None,
                        'd2_skill_most_improved_2': 'Engagement' if school['intervention'] == 'Treatment' else None,
                        'd2_skill_most_improved_3': 'Critical thinking' if school['intervention'] == 'Treatment' else None,
                        'd3_component_rank_1': 'Component 1 has been most effective' if school['intervention'] == 'Treatment' and tp_idx > 0 else None,
                        'd3_component_rank_2': None,
                        'd3_component_rank_3': None,
                        'e1_important_element_1': 'Active engagement',
                        'e1_important_element_2': 'Clear learning objectives',
                        'e1_important_element_3': 'Regular feedback',
                        'e2_teaching_practice_change': 'Significant changes' if school['intervention'] == 'Treatment' and tp_idx > 1 else 'Minor changes',
                        'f1_performance_factors': f'Time point {tp_idx}: Observing student progress',
                        'f2_effective_practice': 'Student-centered activities showing good results',
                        'f3_challenges': 'Time constraints remain a challenge',
                        'f4_additional_comments': f'Survey completed at {time_point["label"]}'
                    }
                    
                    all_responses.append(response)
    
    print()
    print("=" * 60)
    print(f"✅ Generated {len(all_responses)} survey responses")
    print(f"   📊 Regions: {len(REGIONS)}")
    print(f"   🏫 Schools: {sum(len(r['schools']) for r in REGIONS)}")
    print(f"   👨‍🏫 Teachers: {teacher_counter - 1}")
    print(f"   📅 Time Points: {len(TIME_POINTS)}")
    print("=" * 60)
    
    return all_responses

# ====================================================================
# DATABASE OPERATIONS
# ====================================================================

def clear_database(engine):
    """Clear all existing survey responses."""
    print("\n🗑️  Clearing existing survey data...")
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("DELETE FROM teacher_survey_responses"))
            conn.commit()
            print(f"   ✓ Deleted {result.rowcount} existing responses")
    except Exception as e:
        print(f"   ❌ Error clearing database: {e}")
        return False
    
    return True

def insert_mock_data(engine, responses):
    """Insert mock data into database."""
    print("\n📥 Inserting mock data into database...")
    
    success_count = 0
    error_count = 0
    
    for i, response in enumerate(responses):
        try:
            insert_survey_response(engine, response)
            success_count += 1
            
            if (i + 1) % 100 == 0:
                print(f"   ⏳ Inserted {i + 1}/{len(responses)} responses...")
        except Exception as e:
            error_count += 1
            if error_count <= 5:  # Only show first 5 errors
                print(f"   ❌ Error inserting response {response['response_id']}: {e}")
    
    print()
    print("=" * 60)
    print(f"✅ Data insertion complete!")
    print(f"   ✓ Successfully inserted: {success_count}")
    print(f"   ❌ Errors: {error_count}")
    print("=" * 60)
    
    return success_count > 0

# ====================================================================
# MAIN
# ====================================================================

def main():
    """Main execution function."""
    
    print()
    print("=" * 60)
    print("🎲 MOCK DATA GENERATION FOR LONGITUDINAL STUDY")
    print("=" * 60)
    print()
    
    # Get database connection
    print("📡 Connecting to database...")
    engine = get_database_connection()
    print("   ✓ Connected")
    
    # Clear existing data
    if not clear_database(engine):
        print("\n❌ Failed to clear database. Exiting.")
        return
    
    # Generate mock data
    print("\n🎲 Generating mock survey responses...")
    responses = generate_mock_data()
    
    # Insert into database
    if insert_mock_data(engine, responses):
        print("\n🎉 SUCCESS! Mock data has been generated and loaded.")
        print()
        print("📊 Next steps:")
        print("   1. Refresh your Streamlit dashboard")
        print("   2. Go to the Dashboard page to see visualizations")
        print("   3. Try the Statistical Analysis page to run mixed effects models")
        print("   4. Use the Ask Questions page to query the data")
        print()
    else:
        print("\n❌ Failed to insert mock data.")

if __name__ == "__main__":
    main()

