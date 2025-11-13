# EduScale Engine - Entity Documentation

## Overview

This directory contains detailed documentation for all entities in the EduScale Engine system. The system follows a temporal data model where entities track changes over time using `valid_from` and `valid_to` timestamps.

## Entity Categories

### Core Entities

1. **[Region](region.md)** - Geographical or administrative area participating in the education system
2. **[Student](student.md)** - Learner enrolled in the education system
3. **[Parent](parent.md)** - Parent or guardian involved in a student's education
4. **[Teacher](teacher.md)** - Educator teaching subjects to students
5. **[Subject](subject.md)** - Academic discipline or topic being taught

### Governance & Measurement

6. **[Rule](rule.md)** - Normative document or requirement (government/school/EduZmena)
7. **[Criteria](criteria.md)** - Measurement standard or KPI for evaluating performance
8. **[Experiment](experiment.md)** - Controlled intervention to test educational improvements

### Feedback & Observations

9. **[Feedback](feedback.md)** - Qualitative and quantitative input from stakeholders

## Junction Tables (Many-to-Many Relationships)

### Student Relationships
- **StudentParent**: Links students to their parents/guardians with temporal validity
- **StudentTeacherSubject**: Captures "who teaches what to whom, when, and where"

### Region Relationships
- **RegionRule**: Links regions to applicable rules with adoption timeline
- **RegionCriteria**: Links regions to tracked criteria with baseline values
- **RegionExperiment**: Links regions to experiments they participate in

### Experiment Relationships
- **ExperimentCriteria**: Links experiments to criteria being measured with weights

## Entity Diagram

See [../class-diagram.puml](../class-diagram.puml) for the complete PlantUML class diagram.

## Common Patterns

### Temporal Tracking

All major entities include temporal fields:
- `valid_from`: When this record became active
- `valid_to`: When this record became inactive (NULL = currently active)

**Example**: Track teacher moving to new school
```sql
-- Close old record
UPDATE Teacher SET valid_to = '2024-08-31' WHERE id = :teacher_id AND valid_to IS NULL;

-- Create new record
INSERT INTO Teacher (id, name, current_school_id, valid_from, ...)
VALUES (:teacher_id, :name, :new_school_id, '2024-09-01', ...);
```

### Polymorphic Relationships

Feedback uses polymorphic associations:
- `author_type` + `author_id`: Who provided feedback (student/teacher/parent)
- `target_entity_type` + `target_entity_id`: What is being evaluated (optional)

**Example**: Query all feedback from students about teachers
```sql
SELECT * FROM Feedback
WHERE author_type = 'student'
  AND target_entity_type = 'teacher'
```

### Flexible Metadata

All entities include a `metadata` JSON field for:
- Region-specific attributes
- Evolving data structures
- Avoiding frequent schema migrations

**Example**: Store teacher certifications
```json
{
  "certifications": [
    {
      "name": "Advanced Math Teaching",
      "issued_date": "2020-06-15",
      "expiry_date": "2025-06-15"
    }
  ]
}
```

## Data Privacy Guidelines

### PII Classification

| Entity | PII Level | Access Controls |
|--------|-----------|-----------------|
| Student | CRITICAL | Role-based, region-scoped |
| Parent | CRITICAL | Role-based, family-scoped |
| Teacher | MEDIUM | Role-based, region-scoped |
| Feedback | CRITICAL | Aggregated views only |
| Region | LOW | Public within platform |
| Subject | NONE | Public |
| Rule | NONE | Public |
| Criteria | NONE | Public |
| Experiment | LOW | Public results, private participants |

### GDPR Compliance

All PII-containing entities support:
- **Right to access**: Export all data for an individual
- **Right to erasure**: Soft delete by setting `valid_to` and redacting PII
- **Right to rectification**: Create new record with corrected data
- **Data minimization**: Store only necessary fields
- **Purpose limitation**: Clear documentation of data usage

### EU-Only Storage

- All data stored in Google Cloud `europe-west1` region
- No cross-border data transfers
- Self-hosted AI models or explicitly EU-configured services only

## Validation Rules

### Common Validations

1. **Temporal Consistency**
   - `valid_to` must be after `valid_from` if provided
   - Cannot have overlapping active records for same entity
   - New records must have `valid_from > previous_record.valid_from`

2. **Referential Integrity**
   - Foreign keys must reference existing entities
   - Cannot delete entities with active relationships
   - Soft delete (set `valid_to`) instead of hard delete

3. **Enumeration Values**
   - `author_type`: `student`, `teacher`, `parent`
   - `target_entity_type`: `region`, `school`, `teacher`, `subject`, `rule`
   - `rule.type`: `government`, `school`, `eduzmena`
   - `experiment.status`: `planned`, `active`, `completed`, `cancelled`

## BigQuery Optimization

### Partitioning Strategy

```sql
-- Temporal entities: Partition by valid_from
PARTITION BY DATE(valid_from)

-- Event entities: Partition by timestamp
PARTITION BY DATE(timestamp)
```

### Clustering Strategy

```sql
-- Group related data together
CLUSTER BY region_id, school_id  -- For regional queries
CLUSTER BY author_type, category  -- For feedback analysis
CLUSTER BY status, type          -- For experiment filtering
```

### Access Policies

```sql
-- Restrict PII access
CREATE ROW ACCESS POLICY student_privacy ON students
GRANT TO ('teacher@project.iam.gserviceaccount.com')
FILTER USING (
  id IN (SELECT student_id FROM StudentTeacherSubject WHERE teacher_id = SESSION_USER())
);
```

## Query Examples

### Cross-Regional Comparison

```sql
-- Compare regions at same lifecycle stage
SELECT
  r.name,
  r.valid_from as join_date,
  AVG(f.sentiment_score) as avg_sentiment
FROM Region r
LEFT JOIN Feedback f ON f.target_entity_id = r.id
  AND f.timestamp BETWEEN r.valid_from AND r.valid_from + INTERVAL '6 months'
GROUP BY r.name, r.valid_from
ORDER BY avg_sentiment DESC
```

### Experiment Impact Analysis

```sql
-- Measure before/after experiment impact
SELECT
  e.name,
  c.name as criteria,
  AVG(CASE WHEN f.timestamp < e.start_date THEN f.sentiment_score END) as before,
  AVG(CASE WHEN f.timestamp >= e.start_date THEN f.sentiment_score END) as after,
  AVG(CASE WHEN f.timestamp >= e.start_date THEN f.sentiment_score END) -
  AVG(CASE WHEN f.timestamp < e.start_date THEN f.sentiment_score END) as improvement
FROM Experiment e
JOIN ExperimentCriteria ec ON e.id = ec.experiment_id
JOIN Criteria c ON ec.criteria_id = c.id
JOIN Feedback f ON c.id = ANY(f.related_criteria_ids)
GROUP BY e.name, c.name
```

### Teacher Workload Analysis

```sql
-- Calculate teaching load per teacher
SELECT
  t.name,
  COUNT(DISTINCT sts.subject_id) as subjects_count,
  COUNT(DISTINCT sts.student_id) as students_count,
  t.metadata->>'weekly_hours' as hours_per_week
FROM Teacher t
JOIN StudentTeacherSubject sts ON t.id = sts.teacher_id
WHERE t.valid_to IS NULL AND sts.valid_to IS NULL
GROUP BY t.id, t.name, t.metadata
ORDER BY students_count DESC
```

## Development Workflow

### Adding New Entity

1. Create entity documentation file in this directory
2. Update [class-diagram.puml](../class-diagram.puml)
3. Add BigQuery schema definition
4. Implement validation rules
5. Add access policies for PII protection
6. Create sample data for testing
7. Update this README with new entity

### Modifying Existing Entity

1. Update entity documentation
2. Update class diagram if relationships change
3. Add migration strategy for schema changes
4. Update validation rules if needed
5. Communicate breaking changes to team

## Resources

- **Architecture**: [../ARCHITECTURE.md](../ARCHITECTURE.md)
- **Data Flow**: [../DATA_FLOW.md](../DATA_FLOW.md)
- **Class Diagram**: [../class-diagram.puml](../class-diagram.puml)
- **Sequence Diagrams**: [../sequence-transform.puml](../sequence-transform.puml)
