-- ====================================================================
-- DATABASE SCHEMA FOR TEACHER SURVEY DATA
-- Student Performance Assessment Study
-- ====================================================================

-- This script creates the necessary tables for storing survey responses
-- Compatible with PostgreSQL, MySQL, SQLite (with minor modifications)

-- ====================================================================
-- MAIN SURVEY RESPONSES TABLE
-- ====================================================================

CREATE TABLE IF NOT EXISTS teacher_survey_responses (
    
    -- Identification fields
    response_id VARCHAR(50) PRIMARY KEY,
    survey_date DATE NOT NULL,
    teacher_id VARCHAR(50) NOT NULL,
    school_id VARCHAR(50) NOT NULL,
    school_name VARCHAR(255),
    region VARCHAR(100) NOT NULL,
    
    -- Teacher demographics
    teaching_experience_years INTEGER,
    grade_level VARCHAR(50),
    subject_area VARCHAR(255),
    class_size INTEGER,
    
    -- Intervention information
    intervention_status VARCHAR(20) CHECK (intervention_status IN ('Treatment', 'Control')),
    intervention_duration_months INTEGER DEFAULT 0,
    intervention_component_1 BOOLEAN DEFAULT FALSE,
    intervention_component_2 BOOLEAN DEFAULT FALSE,
    intervention_component_3 BOOLEAN DEFAULT FALSE,
    intervention_component_4 BOOLEAN DEFAULT FALSE,
    
    -- Section B: Current Performance (1-5 scale)
    b1_overall_performance INTEGER CHECK (b1_overall_performance BETWEEN 1 AND 5),
    b2_problem_solving INTEGER CHECK (b2_problem_solving BETWEEN 1 AND 5),
    b3_critical_thinking INTEGER CHECK (b3_critical_thinking BETWEEN 1 AND 5),
    b4_collaboration INTEGER CHECK (b4_collaboration BETWEEN 1 AND 5),
    b5_communication INTEGER CHECK (b5_communication BETWEEN 1 AND 5),
    b6_engagement INTEGER CHECK (b6_engagement BETWEEN 1 AND 5),
    b7_behavior INTEGER CHECK (b7_behavior BETWEEN 1 AND 5),
    b8_persistence INTEGER CHECK (b8_persistence BETWEEN 1 AND 5),
    
    -- Section C: Change Variables (1-5 scale, NULL for N/A)
    c1_performance_change INTEGER CHECK (c1_performance_change BETWEEN 1 AND 5 OR c1_performance_change IS NULL),
    c2_problem_solving_change INTEGER CHECK (c2_problem_solving_change BETWEEN 1 AND 5 OR c2_problem_solving_change IS NULL),
    c3_engagement_change INTEGER CHECK (c3_engagement_change BETWEEN 1 AND 5 OR c3_engagement_change IS NULL),
    c4_communication_change INTEGER CHECK (c4_communication_change BETWEEN 1 AND 5 OR c4_communication_change IS NULL),
    c5_behavior_change INTEGER CHECK (c5_behavior_change BETWEEN 1 AND 5 OR c5_behavior_change IS NULL),
    
    -- Section D: Intervention Effectiveness (1-5 scale, NULL for control group)
    d1_intervention_impact INTEGER CHECK (d1_intervention_impact BETWEEN 1 AND 5 OR d1_intervention_impact IS NULL),
    d2_skill_most_improved_1 VARCHAR(100),
    d2_skill_most_improved_2 VARCHAR(100),
    d2_skill_most_improved_3 VARCHAR(100),
    d3_component_rank_1 VARCHAR(100),
    d3_component_rank_2 VARCHAR(100),
    d3_component_rank_3 VARCHAR(100),
    
    -- Section E: Teaching Practices
    e1_important_element_1 VARCHAR(100),
    e1_important_element_2 VARCHAR(100),
    e1_important_element_3 VARCHAR(100),
    e2_teaching_practice_change VARCHAR(50),
    
    -- Section F: Qualitative Responses
    f1_performance_factors TEXT,
    f2_effective_practice TEXT,
    f3_challenges TEXT,
    f4_additional_comments TEXT,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Indexes for performance
    INDEX idx_survey_date (survey_date),
    INDEX idx_teacher (teacher_id),
    INDEX idx_school (school_id),
    INDEX idx_region (region),
    INDEX idx_intervention (intervention_status),
    INDEX idx_region_intervention (region, intervention_status)
);

-- ====================================================================
-- SCHOOLS REFERENCE TABLE
-- ====================================================================

CREATE TABLE IF NOT EXISTS schools (
    school_id VARCHAR(50) PRIMARY KEY,
    school_name VARCHAR(255) NOT NULL,
    region VARCHAR(100) NOT NULL,
    intervention_status VARCHAR(20) CHECK (intervention_status IN ('Treatment', 'Control')),
    intervention_start_date DATE,
    address TEXT,
    total_students INTEGER,
    total_teachers INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_region (region),
    INDEX idx_intervention_status (intervention_status)
);

-- ====================================================================
-- TEACHERS REFERENCE TABLE
-- ====================================================================

CREATE TABLE IF NOT EXISTS teachers (
    teacher_id VARCHAR(50) PRIMARY KEY,
    school_id VARCHAR(50) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255),
    teaching_experience_years INTEGER,
    grade_level VARCHAR(50),
    subject_area VARCHAR(255),
    employment_start_date DATE,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (school_id) REFERENCES schools(school_id) ON DELETE CASCADE,
    INDEX idx_school (school_id),
    INDEX idx_active (active)
);

-- ====================================================================
-- REGIONS REFERENCE TABLE
-- ====================================================================

CREATE TABLE IF NOT EXISTS regions (
    region_id VARCHAR(50) PRIMARY KEY,
    region_name VARCHAR(100) NOT NULL,
    description TEXT,
    population INTEGER,
    n_schools INTEGER,
    geographic_area VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ====================================================================
-- INTERVENTION COMPONENTS TABLE
-- ====================================================================

CREATE TABLE IF NOT EXISTS intervention_components (
    component_id VARCHAR(50) PRIMARY KEY,
    component_name VARCHAR(255) NOT NULL,
    description TEXT,
    implementation_year INTEGER,
    target_outcomes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ====================================================================
-- VIEWS FOR COMMON QUERIES
-- ====================================================================

-- View: Latest survey response per teacher
CREATE OR REPLACE VIEW latest_responses AS
SELECT tsr.*
FROM teacher_survey_responses tsr
INNER JOIN (
    SELECT teacher_id, MAX(survey_date) as max_date
    FROM teacher_survey_responses
    GROUP BY teacher_id
) latest ON tsr.teacher_id = latest.teacher_id 
        AND tsr.survey_date = latest.max_date;

-- View: Summary statistics by region
CREATE OR REPLACE VIEW regional_summary AS
SELECT 
    region,
    intervention_status,
    COUNT(DISTINCT teacher_id) as n_teachers,
    COUNT(DISTINCT school_id) as n_schools,
    COUNT(*) as n_responses,
    AVG(b1_overall_performance) as avg_performance,
    AVG(b2_problem_solving) as avg_problem_solving,
    AVG(b6_engagement) as avg_engagement,
    AVG((b1_overall_performance + b2_problem_solving + b3_critical_thinking + 
         b4_collaboration + b5_communication + b6_engagement + 
         b7_behavior + b8_persistence) / 8.0) as avg_composite
FROM teacher_survey_responses
GROUP BY region, intervention_status;

-- View: Temporal trends
CREATE OR REPLACE VIEW temporal_trends AS
SELECT 
    survey_date,
    region,
    intervention_status,
    COUNT(*) as n_responses,
    AVG(b1_overall_performance) as avg_performance,
    AVG((b1_overall_performance + b2_problem_solving + b3_critical_thinking + 
         b4_collaboration + b5_communication + b6_engagement + 
         b7_behavior + b8_persistence) / 8.0) as avg_composite
FROM teacher_survey_responses
GROUP BY survey_date, region, intervention_status
ORDER BY survey_date;

-- ====================================================================
-- SAMPLE DATA INSERT (FOR TESTING)
-- ====================================================================

-- Insert sample regions
INSERT INTO regions (region_id, region_name, description, n_schools) VALUES
('R1', 'Region_1', 'Northern district', 10),
('R2', 'Region_2', 'Central district', 12),
('R3', 'Region_3', 'Southern district', 8)
ON DUPLICATE KEY UPDATE region_name = region_name; -- MySQL
-- For PostgreSQL: ON CONFLICT (region_id) DO NOTHING;

-- Insert sample schools
INSERT INTO schools (school_id, school_name, region, intervention_status, total_students, total_teachers) VALUES
('S001', 'Lincoln Elementary', 'Region_1', 'Treatment', 450, 25),
('S002', 'Washington Middle', 'Region_1', 'Control', 600, 35),
('S003', 'Roosevelt High', 'Region_2', 'Treatment', 800, 50),
('S004', 'Jefferson Elementary', 'Region_2', 'Control', 400, 22),
('S005', 'Adams Middle', 'Region_3', 'Treatment', 550, 30),
('S006', 'Madison High', 'Region_3', 'Control', 750, 45)
ON DUPLICATE KEY UPDATE school_name = school_name; -- MySQL
-- For PostgreSQL: ON CONFLICT (school_id) DO NOTHING;

-- ====================================================================
-- USEFUL QUERIES FOR DASHBOARD
-- ====================================================================

-- Query 1: Get all responses for a specific region
-- SELECT * FROM teacher_survey_responses WHERE region = 'Region_1';

-- Query 2: Compare intervention vs control by region
-- SELECT 
--     region,
--     intervention_status,
--     AVG(b1_overall_performance) as avg_performance,
--     COUNT(*) as n_responses
-- FROM teacher_survey_responses
-- GROUP BY region, intervention_status;

-- Query 3: Temporal progression for a school
-- SELECT 
--     survey_date,
--     school_id,
--     AVG(b1_overall_performance) as avg_performance
-- FROM teacher_survey_responses
-- WHERE school_id = 'S001'
-- GROUP BY survey_date, school_id
-- ORDER BY survey_date;

-- Query 4: Teacher response history
-- SELECT 
--     teacher_id,
--     survey_date,
--     b1_overall_performance,
--     b2_problem_solving,
--     b6_engagement
-- FROM teacher_survey_responses
-- WHERE teacher_id = 'T001'
-- ORDER BY survey_date;

-- Query 5: School rankings within region
-- SELECT 
--     school_name,
--     AVG((b1_overall_performance + b2_problem_solving + b3_critical_thinking + 
--          b4_collaboration + b5_communication + b6_engagement + 
--          b7_behavior + b8_persistence) / 8.0) as composite_score
-- FROM teacher_survey_responses
-- WHERE region = 'Region_1'
-- GROUP BY school_name
-- ORDER BY composite_score DESC;

-- ====================================================================
-- MAINTENANCE QUERIES
-- ====================================================================

-- Check for duplicate responses
-- SELECT teacher_id, survey_date, COUNT(*) as count
-- FROM teacher_survey_responses
-- GROUP BY teacher_id, survey_date
-- HAVING count > 1;

-- Check for missing data
-- SELECT 
--     COUNT(*) as total_responses,
--     SUM(CASE WHEN b1_overall_performance IS NULL THEN 1 ELSE 0 END) as missing_b1,
--     SUM(CASE WHEN b2_problem_solving IS NULL THEN 1 ELSE 0 END) as missing_b2
-- FROM teacher_survey_responses;

-- Get data freshness
-- SELECT 
--     region,
--     MAX(survey_date) as last_survey,
--     COUNT(*) as total_responses
-- FROM teacher_survey_responses
-- GROUP BY region;

-- ====================================================================
-- END OF SCHEMA
-- ====================================================================






