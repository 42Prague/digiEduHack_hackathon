# CODEBOOK: Teacher Perception Survey Data
## Student Performance Assessment Study

---

## PURPOSE
This codebook provides detailed information about all variables in the dataset, including variable names, descriptions, coding schemes, and valid values.

---

## GENERAL INFORMATION

- **Dataset Name:** Teacher Performance Perception Survey
- **Unit of Analysis:** Individual survey response (teacher-time observation)
- **Data Structure:** Long format (one row per teacher per time point)
- **Missing Data Code:** NA or leave blank

---

## VARIABLE DEFINITIONS

### SECTION 1: IDENTIFICATION VARIABLES

| Variable Name | Description | Type | Valid Values | Notes |
|--------------|-------------|------|--------------|-------|
| `response_id` | Unique identifier for each survey response | String | Any unique ID (e.g., 001, 002, 003) | Must be unique across all responses |
| `survey_date` | Date survey was completed | Date | YYYY-MM-DD format | ISO 8601 format |
| `teacher_id` | Unique identifier for each teacher | String | T001, T002, etc. | Same teacher should have same ID across time |
| `school_id` | Unique identifier for each school | String | S001, S002, etc. | Must be consistent across surveys |
| `school_name` | Full name of school | String | Text | For reference only |
| `region` | Geographic or administrative region | Categorical | Region_1, Region_2, Region_3, etc. | Use consistent naming |

---

### SECTION 2: TEACHER DEMOGRAPHICS

| Variable Name | Description | Type | Valid Values | Notes |
|--------------|-------------|------|--------------|-------|
| `teaching_experience_years` | Years of teaching experience | Integer | 0-50 | Total years, not just at current school |
| `grade_level` | Grade level(s) taught | String | Grade_K, Grade_1, ... Grade_12 | Use underscore format |
| `subject_area` | Primary subject area | String | Math, Reading, Science, Social_Studies, etc. | Can be multiple, separated by semicolon |
| `class_size` | Approximate number of students | Integer | 1-50 | For the specific class being assessed |

---

### SECTION 3: INTERVENTION INFORMATION

| Variable Name | Description | Type | Valid Values | Notes |
|--------------|-------------|------|--------------|-------|
| `intervention_status` | Whether class participated in intervention | Categorical | Treatment, Control | Treatment = participated; Control = did not |
| `intervention_duration_months` | How long intervention has been in place | Integer | 0-120 | 0 for control group |
| `intervention_component_1` | Participation in Component 1 | Binary | 0 (No), 1 (Yes) | Define specific components |
| `intervention_component_2` | Participation in Component 2 | Binary | 0 (No), 1 (Yes) | |
| `intervention_component_3` | Participation in Component 3 | Binary | 0 (No), 1 (Yes) | |
| `intervention_component_4` | Participation in Component 4 | Binary | 0 (No), 1 (Yes) | |

**Note:** Define what each component actually is in your study (e.g., Component 1 = Professional Development, Component 2 = Curriculum Materials, etc.)

---

### SECTION 4: OUTCOME VARIABLES - CURRENT PERFORMANCE (Section B)

**Rating Scale:** 1 (Lowest) to 5 (Highest)

| Variable Name | Description | Valid Values | Questionnaire Item |
|--------------|-------------|--------------|-------------------|
| `b1_overall_performance` | Overall academic performance rating | 1-5 | B1 |
| `b2_problem_solving` | Problem-solving skills rating | 1-5 | B2 |
| `b3_critical_thinking` | Critical thinking skills rating | 1-5 | B3 |
| `b4_collaboration` | Collaboration and teamwork rating | 1-5 | B4 |
| `b5_communication` | Communication skills rating | 1-5 | B5 |
| `b6_engagement` | Student engagement rating | 1-5 | B6 |
| `b7_behavior` | Behavior and conduct rating | 1-5 | B7 |
| `b8_persistence` | Persistence and resilience rating | 1-5 | B8 |

**Coding Key:**
- 1 = Very weak / Very low / Very poor
- 2 = Weak / Low / Poor
- 3 = Adequate / Moderate
- 4 = Strong / High / Good
- 5 = Very strong / Very high / Excellent

---

### SECTION 5: CHANGE VARIABLES (Section C)

**Rating Scale:** Change compared to previous period

| Variable Name | Description | Valid Values | Coding |
|--------------|-------------|--------------|--------|
| `c1_performance_change` | Change in overall performance | 1-5, NA | See below |
| `c2_problem_solving_change` | Change in problem-solving | 1-5, NA | See below |
| `c3_engagement_change` | Change in engagement | 1-5, NA | See below |
| `c4_communication_change` | Change in communication | 1-5, NA | See below |
| `c5_behavior_change` | Change in behavior | 1-5, NA | See below |

**Coding Key:**
- 1 = Declined significantly
- 2 = Declined somewhat
- 3 = Stayed about the same
- 4 = Improved somewhat
- 5 = Improved significantly
- NA = Not applicable (insufficient time to observe)

---

### SECTION 6: INTERVENTION EFFECTIVENESS (Section D)

| Variable Name | Description | Valid Values | Notes |
|--------------|-------------|--------------|-------|
| `d1_intervention_impact` | Overall intervention impact rating | 1-5, NA | Only for intervention group |
| `d2_skill_most_improved_1` | First skill most improved | Text | Free text or categorical |
| `d2_skill_most_improved_2` | Second skill most improved | Text | Optional |
| `d2_skill_most_improved_3` | Third skill most improved | Text | Optional |
| `d3_component_rank_1` | Most effective component (rank 1) | Text | Component name |
| `d3_component_rank_2` | Second most effective (rank 2) | Text | Component name |
| `d3_component_rank_3` | Third most effective (rank 3) | Text | Component name |

**D1 Coding Key:**
- 1 = No noticeable impact
- 2 = Slight positive impact
- 3 = Moderate positive impact
- 4 = Significant positive impact
- 5 = Very strong positive impact
- NA = Control group or too early to tell

**D2 Valid Options (Categorical Coding):**
- Academic_knowledge
- Problem_solving
- Critical_thinking
- Communication
- Collaboration
- Creativity
- Engagement
- Behavior
- Self_regulation
- Persistence
- Other (specify in qualitative notes)

---

### SECTION 7: TEACHING PRACTICES (Section E)

| Variable Name | Description | Valid Values | Notes |
|--------------|-------------|--------------|-------|
| `e1_important_element_1` | Most important learning element (1st choice) | Text | See coding below |
| `e1_important_element_2` | Most important learning element (2nd choice) | Text | Optional |
| `e1_important_element_3` | Most important learning element (3rd choice) | Text | Optional |
| `e2_teaching_practice_change` | Extent of teaching practice change | Categorical | See coding below |

**E1 Valid Options:**
- Clear_objectives
- Active_engagement
- Prior_knowledge
- Personalized_learning
- Motivation
- Supportive_environment
- Regular_feedback
- Real_world_application
- Collaborative_learning
- Technology_resources

**E2 Coding:**
- No_change
- Minor
- Moderate
- Significant
- NA (for control group)

---

### SECTION 8: QUALITATIVE RESPONSES (Section F)

| Variable Name | Description | Type | Notes |
|--------------|-------------|------|-------|
| `f1_performance_factors` | Primary factors influencing performance | Text | Open-ended response |
| `f2_effective_practice` | Most effective practice/activity | Text | Open-ended response |
| `f3_challenges` | Challenges and barriers | Text | Open-ended response |
| `f4_additional_comments` | Additional comments | Text | Open-ended response |

**Note:** These should be entered as verbatim text. Can be coded thematically later for qualitative analysis.

---

## DATA QUALITY CHECKS

### Before Analysis:

1. **Check for duplicates:**
   - No duplicate `response_id` values
   - Same teacher can appear multiple times (different time points)

2. **Date consistency:**
   - All dates in valid format
   - Survey dates should be chronological for same teacher

3. **Range checks:**
   - All B-section variables: 1-5
   - All C-section variables: 1-5 or NA
   - `teaching_experience_years`: 0-50
   - `class_size`: realistic values (5-50)

4. **Logical consistency:**
   - If `intervention_status` = "Control", then `intervention_duration_months` = 0
   - If `intervention_status` = "Control", D-section should be NA
   - If C-section = NA, likely first observation for that teacher

5. **Missing data patterns:**
   - Check which variables have most missing data
   - Determine if missing data is random or systematic

---

## DERIVED VARIABLES

These variables should be created during data preparation:

| Variable Name | Description | Calculation |
|--------------|-------------|-------------|
| `time_years` | Time in years from baseline | (survey_date - min(survey_date)) / 365.25 |
| `intervention` | Binary intervention indicator | 1 if Treatment, 0 if Control |
| `time_category` | Categorical time variable | Wave_1, Wave_2, Wave_3, etc. |
| `teaching_exp_centered` | Centered teaching experience | teaching_experience_years - mean(teaching_experience_years) |
| `class_size_centered` | Centered class size | class_size - mean(class_size) |
| `school_in_region` | Nested school identifier | paste(region, school_id) |

---

## MISSING DATA CODES

| Code | Meaning |
|------|---------|
| NA | Not applicable or not answered |
| -99 | Question not shown (skip logic) |
| -88 | Don't know |
| (blank) | Missing/not entered |

**Recommendation:** Use NA for all missing data. Distinguish reasons in separate documentation if needed.

---

## SAMPLE DATA ENTRY

Here's an example of properly coded data:

```
response_id: 001
survey_date: 2024-09-15
teacher_id: T001
school_id: S001
region: Region_1
teaching_experience_years: 10
grade_level: Grade_5
subject_area: Math
class_size: 25
intervention_status: Treatment
intervention_duration_months: 12
b1_overall_performance: 4
b2_problem_solving: 4
b3_critical_thinking: 4
c1_performance_change: 4
d1_intervention_impact: 4
d2_skill_most_improved_1: Problem_solving
e1_important_element_1: Active_engagement
e2_teaching_practice_change: Moderate
```

---

## DATA ENTRY TIPS

1. **Use consistent formatting:**
   - Always use underscores instead of spaces
   - Be consistent with capitalization
   - Use same date format throughout

2. **Create dropdown menus:**
   - For categorical variables, create dropdown lists in Excel/Google Sheets
   - Prevents typos and ensures consistency

3. **Data validation:**
   - Set valid ranges for numeric variables
   - Flag out-of-range values automatically

4. **Regular backups:**
   - Save data frequently
   - Keep original paper/digital surveys separate

5. **Double entry:**
   - For critical studies, consider double data entry
   - Compare and resolve discrepancies

---

## TRANSFORMATIONS FOR ANALYSIS

### Creating Long Format from Multiple Waves:

If you collect data at multiple time points, each teacher will have multiple rows:

```
teacher_id | survey_date | time_years | b1_overall_performance | ...
T001       | 2024-09-15  | 0.0        | 3                      | ...
T001       | 2025-03-15  | 0.5        | 4                      | ...
T001       | 2025-09-15  | 1.0        | 4                      | ...
```

### Creating Dummy Variables for Regression:

For categorical predictors with >2 levels:

**Region** (if 3 regions):
- `region_2`: 1 if Region_2, 0 otherwise (Region_1 is reference)
- `region_3`: 1 if Region_3, 0 otherwise

**Teaching Experience Categories:**
- If you want categories: create `exp_novice` (0-2 years), `exp_mid` (3-10), `exp_veteran` (11+)

---

## CONTACT INFORMATION

**Data Manager:** [Your Name]
**Email:** [Your Email]
**Last Updated:** [Date]

---

## REVISION HISTORY

| Version | Date | Changes | Updated By |
|---------|------|---------|------------|
| 1.0 | 2024-XX-XX | Initial version | [Name] |
| | | | |

---

## REFERENCES

This codebook was created following guidelines from:
- ICPSR (Inter-university Consortium for Political and Social Research)
- DDI (Data Documentation Initiative) standards
- Best practices for education research data management




