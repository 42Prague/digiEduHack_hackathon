"""
====================================================================
SURVEY FORM PAGE
Teacher Questionnaire for Student Performance Assessment
====================================================================
"""

import streamlit as st
import sys
import os
from datetime import datetime, date

# Add parent directory to path to import database_utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database_utils import (
    get_database_connection, 
    insert_survey_response,
    generate_response_id,
    format_date,
    check_duplicate_response,
    get_unique_values,
    get_active_regions,
    get_active_schools,
    get_grade_levels,
    get_subject_areas,
    get_teaching_experience_levels,
    get_intervention_components,
    get_learning_elements,
    get_skills_improvement
)

st.set_page_config(page_title="Survey Form", page_icon="📝", layout="wide")

# Custom CSS
st.markdown("""
    <style>
    .stButton>button {
        background-color: #C8A2C8;
        color: white;
        font-size: 18px;
        padding: 15px 30px;
        border-radius: 5px;
    }
    .section-header {
        background-color: #C8A2C8;
        padding: 15px;
        border-radius: 5px;
        margin: 20px 0 10px 0;
        border-left: 5px solid #C8A2C8;
    }
    </style>
    """, unsafe_allow_html=True)

# ====================================================================
# MAIN FORM
# ====================================================================

def main():
    st.title("📝 Teacher Survey Form")
    st.markdown("""
    ### Student Performance Assessment Questionnaire
    
    **Instructions:**  
    Please complete all sections honestly based on your observations of your students. 
    All responses are confidential and will be used for research purposes only.
    """)
    
    st.markdown("---")
    
    # Initialize session state for form data
    if 'form_submitted' not in st.session_state:
        st.session_state.form_submitted = False
    
    # Get database connection
    engine = get_database_connection()
    
    # Create form
    with st.form("teacher_survey_form"):
        
        # ============================================================
        # SECTION A: DEMOGRAPHIC & CONTEXTUAL INFORMATION
        # ============================================================
        
        st.markdown('<div class="section-header"><h2>📋 Section A: Background Information</h2></div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        # Initialize school variables
        school_id = ""
        school_name = ""
        
        with col1:
            survey_date = st.date_input(
                "Survey Date *",
                value=date.today(),
                help="Date you are completing this survey"
            )
            
            teacher_id = st.text_input(
                "Teacher ID *",
                help="Your unique teacher identification code",
                placeholder="e.g., T001"
            )
            
            region = st.selectbox(
                "Region *",
                options=[""] + get_active_regions(engine),
                help="Geographic or administrative region"
            )
            
            # Get schools for selected region (dynamic from database)
            if region:
                schools = get_active_schools(engine, region_id=region)
                
                # Debug: Show how many schools found
                st.caption(f"🔍 Found {len(schools) if schools else 0} schools in {region}")
                
                if schools and len(schools) > 0:
                    # Create dropdown options showing both ID and name
                    school_options = [""] + [f"{s['school_id']} - {s['school_name']}" for s in schools]
                    
                    selected_school = st.selectbox(
                        "School *",
                        options=school_options,
                        help="Select your school from the list"
                    )
                    
                    # Extract school_id and school_name from selection
                    if selected_school:
                        school_id = selected_school.split(" - ")[0]
                        school_name = selected_school.split(" - ", 1)[1]
                    else:
                        school_id = ""
                        school_name = ""
                else:
                    st.warning(f"⚠️ No schools found in {region}. Please check the demographics Excel file.")
                    school_id = ""
                    school_name = ""
            else:
                # No region selected yet
                school_id = ""
                school_name = ""
                st.info("👆 Please select a region first to see the school dropdown")
        
        with col2:
            teaching_experience_years = st.selectbox(
                "Years of Teaching Experience *",
                options=[""] + get_teaching_experience_levels(engine),
                help="Total years of teaching experience"
            )
            
            grade_level = st.text_input(
                "Grade Level(s) *",
                help="Grade level(s) you teach",
                placeholder="e.g., Grade_5"
            )
            
            subject_area = st.text_input(
                "Subject Area(s) *",
                help="Primary subject(s) you teach",
                placeholder="e.g., Math, Science"
            )
            
            class_size = st.number_input(
                "Approximate Class Size *",
                min_value=1,
                max_value=100,
                value=25,
                help="Number of students in the class you're assessing"
            )
            
            intervention_status = st.radio(
                "Intervention Status *",
                options=["Treatment", "Control"],
                help="Has your class participated in the intervention program?"
            )
        
        # Intervention details (conditional)
        if intervention_status == "Treatment":
            st.markdown("**Intervention Program Details**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                intervention_duration = st.number_input(
                    "Duration of Participation (months)",
                    min_value=0,
                    max_value=120,
                    value=12,
                    help="How long has your class been in the program?"
                )
            
            with col2:
                st.markdown("**Intervention Components** (Check all that apply)")
                comp1 = st.checkbox("Component 1: Intervention Type1")
                comp2 = st.checkbox("Component 2: Intervention Type2")
                comp3 = st.checkbox("Component 3: Intervention Type3")
                comp4 = st.checkbox("Component 4: Collaborative Learning")
        else:
            intervention_duration = 0
            comp1 = comp2 = comp3 = comp4 = False
        
        # ============================================================
        # SECTION B: CURRENT STUDENT PERFORMANCE
        # ============================================================
        
        st.markdown('<div class="section-header"><h2>📊 Section B: Current Student Performance</h2></div>', unsafe_allow_html=True)
        st.markdown("*Rate the CURRENT PERFORMANCE LEVEL of your students (1=Lowest, 5=Highest)*")
        
        col1, col2 = st.columns(2)
        
        with col1:
            b1 = st.select_slider(
                "B1. Overall Academic Performance",
                options=[1, 2, 3, 4, 5],
                value=1,
                help="Considering all aspects of academic work"
            )
            
            b2 = st.select_slider(
                "B2. Problem-Solving Skills",
                options=[1, 2, 3, 4, 5],
                value=1,
                help="Ability to approach and solve complex problems"
            )
            
            b3 = st.select_slider(
                "B3. Critical Thinking Skills",
                options=[1, 2, 3, 4, 5],
                value=1,
                help="Ability to analyze and evaluate information"
            )
            
            b4 = st.select_slider(
                "B4. Collaboration and Teamwork",
                options=[1, 2, 3, 4, 5],
                value=1,
                help="Ability to work effectively with peers"
            )
        
        with col2:
            b5 = st.select_slider(
                "B5. Communication Skills",
                options=[1, 2, 3, 4, 5],
                value=1,
                help="Ability to express ideas clearly"
            )
            
            b6 = st.select_slider(
                "B6. Student Engagement",
                options=[1, 2, 3, 4, 5],
                value=1,
                help="Level of active participation and interest"
            )
            
            b7 = st.select_slider(
                "B7. Behavior and Classroom Conduct",
                options=[1, 2, 3, 4, 5],
                value=1,
                help="Overall classroom behavior and attitude"
            )
            
            b8 = st.select_slider(
                "B8. Persistence and Resilience",
                options=[1, 2, 3, 4, 5],
                value=1,
                help="Ability to persist when facing challenges"
            )
        
        # ============================================================
        # SECTION C: CHANGES OVER TIME
        # ============================================================
        
        st.markdown('<div class="section-header"><h2>📈 Section C: Changes Over Time</h2></div>', unsafe_allow_html=True)
        st.markdown("*If you've been working with these students for 6+ months, indicate how their performance has changed*")
        
        col1, col2 = st.columns(2)
        
        with col1:
            c1 = st.selectbox(
                "C1. Change in Overall Performance",
                options=["N/A", "Declined significantly", "Declined somewhat", "Stayed the same", "Improved somewhat", "Improved significantly"]
            )
            
            c2 = st.selectbox(
                "C2. Change in Problem-Solving Skills",
                options=["N/A", "Declined significantly", "Declined somewhat", "Stayed the same", "Improved somewhat", "Improved significantly"]
            )
            
            c3 = st.selectbox(
                "C3. Change in Engagement",
                options=["N/A", "Declined significantly", "Declined somewhat", "Stayed the same", "Improved somewhat", "Improved significantly"]
            )
        
        with col2:
            c4 = st.selectbox(
                "C4. Change in Communication Skills",
                options=["N/A", "Declined significantly", "Declined somewhat", "Stayed the same", "Improved somewhat", "Improved significantly"]
            )
            
            c5 = st.selectbox(
                "C5. Change in Behavior/Attitude",
                options=["N/A", "Declined significantly", "Declined somewhat", "Stayed the same", "Improved somewhat", "Improved significantly"]
            )
        
        # ============================================================
        # SECTION D: INTERVENTION EFFECTIVENESS
        # ============================================================
        
        if intervention_status == "Treatment":
            st.markdown('<div class="section-header"><h2>🎯 Section D: Intervention Effectiveness</h2></div>', unsafe_allow_html=True)
            
            d1 = st.selectbox(
                "D1. Overall Intervention Impact",
                options=["No noticeable impact", "Slight positive impact", "Moderate positive impact", 
                        "Significant positive impact", "Very strong positive impact"]
            )
            
            st.markdown("**D2. Which skills have been MOST improved?** (Select up to 3)")
            skill_options = ["Academic knowledge", "Problem-solving", "Critical thinking", "Communication",
                           "Collaboration", "Creativity", "Engagement", "Behavior", "Self-regulation", "Persistence"]
            
            d2_skills = st.multiselect(
                "Select up to 3 skills",
                options=skill_options,
                max_selections=3
            )
            
            st.markdown("**D3. Most Effective Components**")
            d3_text = st.text_area(
                "Which intervention components have been most effective and why?",
                placeholder="Describe the components that have worked best..."
            )
        else:
            d1 = None
            d2_skills = []
            d3_text = ""
        
        # ============================================================
        # SECTION E: TEACHING PRACTICES
        # ============================================================
        
        st.markdown('<div class="section-header"><h2>👨‍🏫 Section E: Teaching and Learning</h2></div>', unsafe_allow_html=True)
        
        st.markdown("**E1. Most Important Elements for Effective Learning** (Select 1-3)")
        learning_elements = st.multiselect(
            "Select 1-3 most important elements",
            options=[
                "Clear learning objectives",
                "Active engagement",
                "Prior knowledge connections",
                "Personalized learning",
                "Motivation and interest",
                "Supportive environment",
                "Regular feedback"
            ],
            max_selections=3
        )
        
        e2 = st.selectbox(
            "E2. Has your teaching practice changed due to the program?",
            options=["No change", "Minor changes", "Moderate changes", "Significant changes", "N/A"]
        )
        
        # ============================================================
        # SECTION F: QUALITATIVE INSIGHTS
        # ============================================================
        
        st.markdown('<div class="section-header"><h2>💭 Section F: Additional Insights</h2></div>', unsafe_allow_html=True)
        
        f1 = st.text_area(
            "F1. Primary Factors Influencing Student Performance",
            placeholder="What do you believe are the main factors (positive or negative) affecting your students' performance this year?",
            height=100
        )
        
        f2 = st.text_area(
            "F2. Most Effective Practice or Activity",
            placeholder="Describe one specific practice or activity that has been particularly effective for improving student outcomes...",
            height=100
        )
        
        f3 = st.text_area(
            "F3. Challenges and Barriers",
            placeholder="What challenges or barriers have limited student performance or intervention effectiveness?",
            height=100
        )
        
        f4 = st.text_area(
            "F4. Additional Comments",
            placeholder="Any other comments or observations you'd like to share?",
            height=100
        )
        
        # ============================================================
        # FORM SUBMISSION
        # ============================================================
        
        st.markdown("---")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col2:
            submit_button = st.form_submit_button("✅ Submit Survey", use_container_width=True)
        
        if submit_button:
            # Validation
            required_fields = [teacher_id, school_id, school_name, region, grade_level, subject_area]
            
            if not all(required_fields):
                st.error("❌ Please fill in all required fields marked with *")
            elif teaching_experience_years == "":
                st.error("❌ Please select your teaching experience")
            else:
                # Check for duplicate
                if check_duplicate_response(engine, teacher_id, format_date(survey_date)):
                    st.warning("⚠️ You have already submitted a response for this date. Please use a different date or contact an administrator.")
                else:
                    # Prepare data
                    response_data = {
                        'response_id': generate_response_id(),
                        'survey_date': format_date(survey_date),
                        'teacher_id': teacher_id,
                        'school_id': school_id,
                        'school_name': school_name,
                        'region': region,
                        'teaching_experience_years': int(teaching_experience_years.split('-')[0]) if '-' in teaching_experience_years else 20,
                        'grade_level': grade_level,
                        'subject_area': subject_area,
                        'class_size': int(class_size),
                        'intervention_status': intervention_status,
                        'intervention_duration_months': int(intervention_duration),
                        'intervention_component_1': int(comp1),
                        'intervention_component_2': int(comp2),
                        'intervention_component_3': int(comp3),
                        'intervention_component_4': int(comp4),
                        'b1_overall_performance': int(b1),
                        'b2_problem_solving': int(b2),
                        'b3_critical_thinking': int(b3),
                        'b4_collaboration': int(b4),
                        'b5_communication': int(b5),
                        'b6_engagement': int(b6),
                        'b7_behavior': int(b7),
                        'b8_persistence': int(b8),
                        'c1_performance_change': None if c1 == "N/A" else ["Declined significantly", "Declined somewhat", "Stayed the same", "Improved somewhat", "Improved significantly"].index(c1) + 1 if c1 != "N/A" else None,
                        'c2_problem_solving_change': None if c2 == "N/A" else ["Declined significantly", "Declined somewhat", "Stayed the same", "Improved somewhat", "Improved significantly"].index(c2) + 1 if c2 != "N/A" else None,
                        'c3_engagement_change': None if c3 == "N/A" else ["Declined significantly", "Declined somewhat", "Stayed the same", "Improved somewhat", "Improved significantly"].index(c3) + 1 if c3 != "N/A" else None,
                        'c4_communication_change': None if c4 == "N/A" else ["Declined significantly", "Declined somewhat", "Stayed the same", "Improved somewhat", "Improved significantly"].index(c4) + 1 if c4 != "N/A" else None,
                        'c5_behavior_change': None if c5 == "N/A" else ["Declined significantly", "Declined somewhat", "Stayed the same", "Improved somewhat", "Improved significantly"].index(c5) + 1 if c5 != "N/A" else None,
                        'd1_intervention_impact': None if d1 is None else ["No noticeable impact", "Slight positive impact", "Moderate positive impact", "Significant positive impact", "Very strong positive impact"].index(d1) + 1,
                        'd2_skill_most_improved_1': d2_skills[0] if len(d2_skills) > 0 else None,
                        'd2_skill_most_improved_2': d2_skills[1] if len(d2_skills) > 1 else None,
                        'd2_skill_most_improved_3': d2_skills[2] if len(d2_skills) > 2 else None,
                        'd3_component_rank_1': d3_text if d3_text else None,
                        'd3_component_rank_2': None,
                        'd3_component_rank_3': None,
                        'e1_important_element_1': learning_elements[0] if len(learning_elements) > 0 else None,
                        'e1_important_element_2': learning_elements[1] if len(learning_elements) > 1 else None,
                        'e1_important_element_3': learning_elements[2] if len(learning_elements) > 2 else None,
                        'e2_teaching_practice_change': e2,
                        'f1_performance_factors': f1 if f1 else None,
                        'f2_effective_practice': f2 if f2 else None,
                        'f3_challenges': f3 if f3 else None,
                        'f4_additional_comments': f4 if f4 else None
                    }
                    
                    # Insert into database
                    success = insert_survey_response(engine, response_data)
                    
                    if success:
                        st.success("✅ Survey submitted successfully! Thank you for your participation.")
                        st.balloons()
                        st.info(f"Response ID: {response_data['response_id']}")
                        st.session_state.form_submitted = True
                    else:
                        st.error("❌ There was an error submitting your survey. Please try again or contact support.")
    
    # Show confirmation if just submitted
    if st.session_state.form_submitted:
        st.markdown("---")
        st.markdown("""
        ### What's Next?
        
        - **View Results:** Navigate to the Dashboard to see aggregated results
        - **Custom Analysis:** Use the "Ask Questions" page for specific queries
        - **Submit Another:** Refresh this page to submit another response
        """)

if __name__ == "__main__":
    main()

