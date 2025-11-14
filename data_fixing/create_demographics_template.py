"""
Create Demographics Configuration Excel Template
This Excel file defines all dropdown options and database schema
"""

import pandas as pd

# Create Excel writer
with pd.ExcelWriter('demographics_config.xlsx', engine='openpyxl') as writer:
    
    # ================================================================
    # SHEET 1: REGIONS
    # ================================================================
    regions_df = pd.DataFrame({
        'region_id': ['Region_1', 'Region_2', 'Region_3', 'Region_4'],
        'region_name': ['Northern District', 'Central District', 'Southern District', 'Western District'],
        'description': ['Northern geographic area', 'Central urban area', 'Southern rural area', 'Western suburban area'],
        'active': [True, True, True, True]
    })
    regions_df.to_excel(writer, sheet_name='Regions', index=False)
    
    # ================================================================
    # SHEET 2: SCHOOLS
    # ================================================================
    schools_df = pd.DataFrame({
        'school_id': ['S001', 'S002', 'S003', 'S004', 'S005', 'S006', 'S007', 'S008', 'S009'],
        'school_name': [
            'Lincoln Elementary',
            'Washington Middle',
            'Roosevelt High',
            'Jefferson Elementary',
            'Adams Middle',
            'Madison High',
            'School_of_Bulshit',
            'Western Academy',
            'Another Bullshit'  # NEW SCHOOL in Region_4
        ],
        'region_id': ['Region_1', 'Region_1', 'Region_2', 'Region_2', 'Region_3', 'Region_3', 'Region_4', 'Region_4', 'Region_2'],
        'intervention_status': ['Treatment', 'Control', 'Treatment', 'Control', 'Treatment', 'Control', 'Treatment', 'Control', 'Control'],
        'total_students': [450, 600, 800, 400, 550, 750, 500, 600, 900],
        'total_teachers': [25, 35, 50, 22, 30, 45, 28, 32, 25],
        'active': [True, True, True, True, True, True, True, True, True]
    })
    schools_df.to_excel(writer, sheet_name='Schools', index=False)
    
    # ================================================================
    # SHEET 3: GRADE LEVELS
    # ================================================================
    grade_levels_df = pd.DataFrame({
        'grade_id': ['K', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12'],
        'grade_name': [
            'Kindergarten', 'Grade 1', 'Grade 2', 'Grade 3', 'Grade 4', 
            'Grade 5', 'Grade 6', 'Grade 7', 'Grade 8', 
            'Grade 9', 'Grade 10', 'Grade 11', 'Grade 12'
        ],
        'level': ['Elementary', 'Elementary', 'Elementary', 'Elementary', 'Elementary', 
                 'Elementary', 'Middle', 'Middle', 'Middle', 
                 'High', 'High', 'High', 'High'],
        'active': [True] * 13
    })
    grade_levels_df.to_excel(writer, sheet_name='GradeLevels', index=False)
    
    # ================================================================
    # SHEET 4: SUBJECT AREAS
    # ================================================================
    subjects_df = pd.DataFrame({
        'subject_id': ['MATH', 'READING', 'SCIENCE', 'SOCIAL', 'ARTS', 'PE', 'MUSIC', 'ALL'],
        'subject_name': [
            'Mathematics',
            'Reading/Language Arts',
            'Science',
            'Social Studies',
            'Arts',
            'Physical Education',
            'Music',
            'All Subjects (Elementary)'
        ],
        'active': [True] * 8
    })
    subjects_df.to_excel(writer, sheet_name='SubjectAreas', index=False)
    
    # ================================================================
    # SHEET 5: TEACHING EXPERIENCE LEVELS
    # ================================================================
    experience_df = pd.DataFrame({
        'experience_id': ['0-2', '3-5', '6-10', '11-20', '20+'],
        'experience_name': ['0-2 years', '3-5 years', '6-10 years', '11-20 years', '20+ years'],
        'min_years': [0, 3, 6, 11, 20],
        'max_years': [2, 5, 10, 20, 50],
        'active': [True] * 5
    })
    experience_df.to_excel(writer, sheet_name='TeachingExperience', index=False)
    
    # ================================================================
    # SHEET 6: INTERVENTION COMPONENTS
    # ================================================================
    components_df = pd.DataFrame({
        'component_id': ['COMP1', 'COMP2', 'COMP3', 'COMP4'],
        'component_name': [
            'Professional Development',
            'Curriculum Materials',
            'Technology Integration',
            'Collaborative Learning'
        ],
        'description': [
            'Teacher training and professional development workshops',
            'Enhanced curriculum materials and resources',
            'Technology tools and digital learning platforms',
            'Peer collaboration and learning communities'
        ],
        'active': [True, True, True, True]
    })
    components_df.to_excel(writer, sheet_name='InterventionComponents', index=False)
    
    # ================================================================
    # SHEET 7: PERFORMANCE OUTCOMES
    # ================================================================
    outcomes_df = pd.DataFrame({
        'outcome_id': ['b1', 'b2', 'b3', 'b4', 'b5', 'b6', 'b7', 'b8'],
        'outcome_name': [
            'Overall Academic Performance',
            'Problem-Solving Skills',
            'Critical Thinking Skills',
            'Collaboration and Teamwork',
            'Communication Skills',
            'Student Engagement',
            'Behavior and Conduct',
            'Persistence and Resilience'
        ],
        'db_column': [
            'b1_overall_performance',
            'b2_problem_solving',
            'b3_critical_thinking',
            'b4_collaboration',
            'b5_communication',
            'b6_engagement',
            'b7_behavior',
            'b8_persistence'
        ],
        'scale_min': [1] * 8,
        'scale_max': [5] * 8,
        'active': [True] * 8
    })
    outcomes_df.to_excel(writer, sheet_name='PerformanceOutcomes', index=False)
    
    # ================================================================
    # SHEET 8: LEARNING ELEMENTS
    # ================================================================
    learning_elements_df = pd.DataFrame({
        'element_id': ['ELEM1', 'ELEM2', 'ELEM3', 'ELEM4', 'ELEM5', 'ELEM6', 'ELEM7', 'ELEM8'],
        'element_name': [
            'Clear learning objectives',
            'Active engagement',
            'Prior knowledge connections',
            'Personalized learning',
            'Motivation and interest',
            'Supportive environment',
            'Regular feedback',
            'Real-world application'
        ],
        'description': [
            'Clear and specific learning goals',
            'Students actively participate in learning',
            'Connecting new material to existing knowledge',
            'Adjusted to individual student needs',
            'Building student interest and motivation',
            'Safe and supportive classroom environment',
            'Frequent feedback on student progress',
            'Connecting learning to real-world contexts'
        ],
        'active': [True] * 8
    })
    learning_elements_df.to_excel(writer, sheet_name='LearningElements', index=False)
    
    # ================================================================
    # SHEET 9: SKILLS FOR IMPROVEMENT (D2 options)
    # ================================================================
    skills_df = pd.DataFrame({
        'skill_id': ['SKILL1', 'SKILL2', 'SKILL3', 'SKILL4', 'SKILL5', 
                    'SKILL6', 'SKILL7', 'SKILL8', 'SKILL9', 'SKILL10'],
        'skill_name': [
            'Academic knowledge',
            'Problem-solving',
            'Critical thinking',
            'Communication',
            'Collaboration',
            'Creativity',
            'Engagement',
            'Behavior',
            'Self-regulation',
            'Persistence'
        ],
        'active': [True] * 10
    })
    skills_df.to_excel(writer, sheet_name='SkillsImprovement', index=False)
    
    # ================================================================
    # SHEET 10: CONFIGURATION METADATA
    # ================================================================
    config_df = pd.DataFrame({
        'setting': [
            'system_name',
            'database_version',
            'intervention_name',
            'intervention_description',
            'study_start_date',
            'study_end_date',
            'contact_email'
        ],
        'value': [
            'Student Performance Survey System',
            '1.0',
            'Enhanced Learning Program',
            'Comprehensive intervention focused on student-centered learning',
            '2024-01-01',
            '2025-12-31',
            'research@example.com'
        ],
        'description': [
            'Name of the survey system',
            'Database schema version',
            'Name of the intervention being studied',
            'Description of the intervention',
            'Start date of the study',
            'End date of the study',
            'Contact email for support'
        ]
    })
    config_df.to_excel(writer, sheet_name='Configuration', index=False)

print("✅ Demographics configuration Excel file created: demographics_config.xlsx")
print("\n📋 Sheets created:")
print("   1. Regions - Geographic/administrative regions")
print("   2. Schools - All participating schools")
print("   3. GradeLevels - Grade level options")
print("   4. SubjectAreas - Subject area options")
print("   5. TeachingExperience - Experience level categories")
print("   6. InterventionComponents - Components of the intervention")
print("   7. PerformanceOutcomes - Performance dimensions measured")
print("   8. LearningElements - Important learning elements")
print("   9. SkillsImprovement - Skills that can be improved")
print("   10. Configuration - System settings")
print("\n🎯 Next step: Edit the Excel file to match your study, then run load_demographics.py")



